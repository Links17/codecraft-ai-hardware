"""Release candidates require reviewed bytes; failed application preserves source."""
from contextlib import contextmanager
import importlib.util
import io
from pathlib import Path
import shutil
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/codecraft'))
from io_utils import ContractError, digest, object_digest, read_json, write_json
from skill_contracts import load_package

spec=importlib.util.spec_from_file_location('skill_release',ROOT/'tools/skill_packages/release.py')
release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)


@contextmanager
def workspace():
    with tempfile.TemporaryDirectory() as folder:
        base=Path(folder);root=base/'repo';root.mkdir()
        sources,_,_=release.inputs(ROOT)
        for relative in sources['files']:
            target=root/relative;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/relative,target)
        yield root,base


def rejects(fn):
    try:fn()
    except (ContractError,OSError):return
    raise AssertionError('Invalid release was accepted')


def next_version(root, pid):
    major, minor, patch_version=release.versions(release.registrations(root)[pid]['version'])
    return f'{major}.{minor}.{patch_version+1}'


def file_bytes(root):
    return {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*')
            if p.is_file() and '.codecraft' not in p.relative_to(root).parts and '__pycache__' not in p.parts}


def test_identical_inputs_produce_identical_complete_candidates_without_writes():
    with workspace() as (root,base):
        before=file_bytes(root)
        first=release.prepare(root,base/'first');second=release.prepare(root,base/'second')
        assert first['review_sha256']==second['review_sha256']
        assert file_bytes(base/'first')==file_bytes(base/'second')
        assert all(p['classification']=='none' for p in first['packages'].values())
        assert file_bytes(root)==before
        assert release.inspect(root,base/'first')[1]==first['review_sha256']


def test_reviewed_documentation_release_executes_isolated_clients_and_preserves_provenance():
    with workspace() as (root,base):
        source=root/'skills/codecraft-capabilities-asr/references/api.md'
        source.write_text(source.read_text()+'\nPackaging fixture documentation note.\n')
        before=file_bytes(root);provenance=(root/'tools/skill_packages/import.json').read_bytes()
        rejects(lambda:release.prepare(root,base/'unversioned'))
        assert not (base/'unversioned').exists() and file_bytes(root)==before
        version=next_version(root,'codecraft-capabilities-asr')
        candidate=release.prepare(root,base/'candidate',{'codecraft-capabilities-asr':{'skill_version':version}})
        assert candidate['packages']['codecraft-capabilities-asr']['classification']=='documentation'
        outcome=release.apply(root,base/'candidate',candidate['review_sha256'])
        assert outcome['repository_changed'] and len(outcome['checks'])==20
        assert all(x['status']=='passed' for x in outcome['checks'])
        assert next(x for x in outcome['checks'] if x['name']=='standalone-protocol-suite')['cases']==16
        assert next(x for x in outcome['checks'] if x['name']=='standalone-onboarding-suite')['cases']==7
        assert next(x for x in outcome['checks'] if x['name']=='codecraft-capabilities-asr::test_realtime')['cases']==6
        provider=load_package(root,'codecraft-capabilities-asr')[0]
        assert provider['version']==version
        assert provider['files']['references/api.md']==digest(source)
        assert (root/'tools/skill_packages/import.json').read_bytes()==provenance
        assert not (root/'.codecraft/skill-release.lock').exists()
        assert outcome['api_execution']=='not_run' and outcome['published'] is False


def test_shared_helper_candidates_classify_runtime_and_do_not_rewrite_distributions():
    with workspace() as (root,base):
        distribution=root/'skills/codecraft-capabilities-asr/scripts/device_api.py';original=distribution.read_bytes()
        distribution.write_bytes(original+b'\n# Local distribution edit must not be discarded.\n')
        edited=distribution.read_bytes()
        rejects(lambda:release.prepare(root,base/'conflicting-helper'))
        assert distribution.read_bytes()==edited and not (base/'conflicting-helper').exists()
        distribution.write_bytes(original)
        maintained=root/'tools/skill_packages/device_api.py'
        maintained.write_text(maintained.read_text()+'\n# Release fixture runtime source.\n')
        before=file_bytes(root)
        versions={pid:{'skill_version':next_version(root,pid)} for pid in release.registrations(root)}
        rejects(lambda:release.prepare(root,base/'no-versions'))
        candidate=release.prepare(root,base/'candidate',versions)
        assert all(p['classification']=='runtime' for p in candidate['packages'].values())
        for p in release.registrations(root).values():
            relative=('skills/'+p['id'])+'/scripts/device_api.py'
            assert (base/'candidate'/relative).read_bytes()==maintained.read_bytes()
            assert (root/relative).read_bytes()!=maintained.read_bytes()
        assert file_bytes(root)==before
        cache=base/'candidate/skills/codecraft-capabilities-asr/scripts/__pycache__/unregistered.pyc'
        cache.parent.mkdir();cache.write_bytes(b'unregistered candidate cache')
        outcome=release.apply(root,base/'candidate',candidate['review_sha256'])
        assert outcome['repository_changed'] and len(outcome['checks'])==20
        assert not (root/'skills/codecraft-capabilities-asr/scripts/__pycache__').exists()
        for p in release.registrations(root).values():
            assert (root/('skills/'+p['id'])/'scripts/device_api.py').read_bytes()==maintained.read_bytes()


def test_wrong_review_digest_candidate_drift_and_source_drift_fail_before_execution():
    with workspace() as (root,base):
        prepared=release.prepare(root,base/'candidate');before=file_bytes(root)
        with patch.object(release.subprocess,'run',side_effect=AssertionError('Unreviewed candidate executed')):
            rejects(lambda:release.apply(root,base/'candidate','0'*64))
            extra=base/'candidate/extra.txt';extra.write_text('unreviewed')
            rejects(lambda:release.validate(root,base/'candidate'));extra.unlink()
            package=base/'candidate/skills/codecraft-capabilities-asr/SKILL.md';original=package.read_bytes()
            package.write_bytes(original+b'\ndrift\n')
            rejects(lambda:release.validate(root,base/'candidate'));package.write_bytes(original)
            link=base/'candidate/symlink';link.symlink_to(package)
            rejects(lambda:release.validate(root,base/'candidate'));link.unlink()
            source=root/'tools/skill_packages/device_api.py';source.write_bytes(source.read_bytes()+b'\n# later edit\n')
            rejects(lambda:release.validate(root,base/'candidate',prepared['review_sha256']))
        source.write_bytes(before['tools/skill_packages/device_api.py'])
        assert file_bytes(root)==before and not (root/'.codecraft/skill-release.lock').exists()


def test_invalid_or_tampered_version_plans_cannot_bypass_release_validation():
    with workspace() as (root,base):
        invalid=[{'skill_version':'0.0.1'},{'contract_version':'99.0.0'},
                 {'policy_version':'0.0.1'},{'api_version':''},{'unexpected':True}]
        for index,entry in enumerate(invalid):
            rejects(lambda:release.prepare(root,base/str(index),{'codecraft-capabilities-asr':entry}))
        versions=base/'versions.json';versions.write_text('null\n')
        stdout=io.StringIO()
        with patch('sys.stdout',stdout):
            code=release.main(['prepare','--versions',str(versions),'--output',str(base/'null-versions')],root=root)
        assert code==1 and not (base/'null-versions').exists()
        path=root/'tools/skill_packages/packages/codecraft-capabilities-asr.json';original=path.read_bytes()
        for index,change in enumerate(({'id':'../outside'},{'id':'codecraft-capabilities-asr/extra'})):
            provider=read_json(path);provider.update(change);write_json(path,provider)
            rejects(lambda:release.prepare(root,base/('bad-path-'+str(index))))
            path.write_bytes(original)
        release.prepare(root,base/'candidate')
        path=base/'candidate/manifest.json';manifest=read_json(path)
        for invalid_manifest in (None,[],{**manifest,'schema_version':True},{**manifest,'unexpected':True}):
            write_json(path,invalid_manifest)
            rejects(lambda:release.inspect(root,base/'candidate'))
        write_json(path,manifest)
        entry=manifest['packages']['codecraft-capabilities-asr'];entry['proposed']['version']='0.0.1'
        provider=base/'candidate'/entry['record_path'];write_json(provider,entry['proposed'])
        manifest['files'][entry['record_path']]=digest(provider);write_json(path,manifest)
        rejects(lambda:release.inspect(root,base/'candidate',object_digest(manifest)))


def test_failed_candidate_cli_prevents_any_apply_changes():
    with workspace() as (root,base):
        source=root/'skills/codecraft-capabilities-asr/scripts/transcribe.py'
        source.write_text('raise SystemExit(7)\n')
        prepared=release.prepare(root,base/'candidate',{'codecraft-capabilities-asr':{'skill_version':next_version(root,'codecraft-capabilities-asr')}})
        before=file_bytes(root)
        rejects(lambda:release.apply(root,base/'candidate',prepared['review_sha256']))
        assert file_bytes(root)==before and not (root/'.codecraft/skill-release.lock').exists()


def test_mid_apply_failure_restores_all_packages_and_release_metadata():
    with workspace() as (root,base):
        maintained=root/'tools/skill_packages/device_api.py'
        maintained.write_text(maintained.read_text()+'\n# Transaction fixture.\n')
        versions={pid:{'skill_version':next_version(root,pid)} for pid in release.registrations(root)}
        prepared=release.prepare(root,base/'candidate',versions);before=file_bytes(root)
        replace=release.os.replace;calls=[]
        def fail_second_record(source,destination):
            calls.append(destination)
            if len(calls)==2:raise OSError('injected metadata write failure')
            return replace(source,destination)
        # Real validation is covered above; isolate the transaction fault here.
        with patch.object(release,'validate',return_value={'checks':[]}),patch.object(release.os,'replace',side_effect=fail_second_record):
            rejects(lambda:release.apply(root,base/'candidate',prepared['review_sha256']))
        assert len(calls)==2 and file_bytes(root)==before
        assert not list((root/'skills').glob('.release-*'))
        assert not (root/'.codecraft/skill-release.lock').exists()


def test_failed_backup_restoration_retains_the_original_package_for_recovery():
    with workspace() as (root,base):
        maintained=root/'tools/skill_packages/device_api.py'
        maintained.write_text(maintained.read_text()+'\n# Recovery fixture.\n')
        versions={pid:{'skill_version':next_version(root,pid)} for pid in release.registrations(root)}
        prepared=release.prepare(root,base/'candidate',versions)
        original=(root/'skills/codecraft-capabilities-asr/scripts/device_api.py').read_bytes()
        rename=Path.rename
        def refuse_restoration(path,destination):
            if path.name.startswith('old-'):raise OSError('injected restoration failure')
            return rename(path,destination)
        with patch.object(release,'validate',return_value={'checks':[]}),patch.object(release.os,'replace',side_effect=OSError('injected write failure')),patch.object(Path,'rename',refuse_restoration):
            try:release.apply(root,base/'candidate',prepared['review_sha256'])
            except ContractError as error:assert 'retained recovery files' in str(error)
            else:raise AssertionError('Failed restoration was not reported')
        stages=list((root/'skills').glob('.release-*'))
        assert len(stages)==1
        assert (stages[0]/'old-codecraft-capabilities-asr/scripts/device_api.py').read_bytes()==original
        assert not (root/'.codecraft/skill-release.lock').exists()
