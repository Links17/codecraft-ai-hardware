"""Source closure, native contracts, project integrity and evidence boundaries."""
from contextlib import contextmanager
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'skills/_shared'))
from io_utils import ContractError, digest, object_digest, read_json, source_files, write_json
from model import Catalog, load_cloud
from graph import SourceGraph
from project import generate_project, lock_project, verify_project, package_project
from runtime import check_envelope, envelope, load_adapter
from evidence import validate_evidence
from render import generate


@contextmanager
def fixture():
    with tempfile.TemporaryDirectory(prefix='codecraft-architecture-test-') as folder:
        root = Path(folder)/'repo'
        root.mkdir()
        for source in source_files(ROOT):
            out = root/source.relative_to(ROOT)
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, out, follow_symlinks=True)
        yield root


def rejected(fn, fragment):
    try:
        fn()
    except ContractError as exc:
        assert fragment.lower() in str(exc).lower(), str(exc)
    else:
        raise AssertionError('Expected rejection: '+fragment)


def edit(root, path, fn):
    data = read_json(root/path)
    fn(data)
    write_json(root/path, data)


def test_native_adapter_is_part_of_context_export_and_evidence_identity():
    with fixture() as root:
        c = Catalog(root)
        tid = 'esp-idf/reterminal-e1001'
        before = c.graph(tid).fingerprint()
        path = root/'platforms/esp-idf/adapter.py'
        assert str(path.relative_to(root)) in c.context(tid, 'epd_hello')['files']
        path.write_text(path.read_text()+'\n# Changed actual native build entry\n')
        after = Catalog(root).graph(tid).fingerprint()
        assert before != after
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'app'
            generate_project(Catalog(root), tid, 'epd_hello', output)
            assert digest(output/'platforms/esp-idf/adapter.py') == digest(path)


def test_transitive_cross_layer_dependency_is_exported_never_filtered():
    with fixture() as root:
        tid = 'esp-idf/reterminal-e1001'
        resource = 'capabilities/_fixtures/resource.json'
        leaf = 'capabilities/_fixtures/palette.bin'
        write_json(root/resource, {'schema_version':1,'kind':'resource','inputs':[leaf],'dependencies':[]})
        (root/leaf).write_text('test-only native resource\n')
        edit(root, 'platforms/esp-idf/targets/reterminal-e1001/target.json', lambda target: target['dependencies'].append(resource))
        c = Catalog(root)
        assert leaf in c.graph(tid).files
        before = c.graph(tid).fingerprint()
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'app'
            generate_project(c, tid, 'epd_hello', output)
            imported = read_json(output/'platforms/esp-idf/targets/reterminal-e1001/target.json')
            assert resource in imported['dependencies'] and (output/leaf).is_file()
            assert verify_project(output)['status'] == 'passed'
            package_project(output, Path(folder)/'source.zip')
            import zipfile
            with zipfile.ZipFile(Path(folder)/'source.zip') as archive:
                assert leaf in archive.namelist()
            (output/leaf).unlink()
            assert verify_project(output)['status'] == 'failed'
        (root/leaf).write_text('changed dependent resource\n')
        assert before != Catalog(root).graph(tid).fingerprint()
        (root/leaf).unlink()
        rejected(lambda: Catalog(root), 'missing reference')


def test_cycle_and_external_symlink_dependencies_are_rejected():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        write_json(root/'a/resource.json',{'schema_version':1,'kind':'resource','inputs':['b/resource.json'],'dependencies':[]})
        write_json(root/'b/resource.json',{'schema_version':1,'kind':'resource','inputs':['a/resource.json'],'dependencies':[]})
        rejected(lambda: SourceGraph(root).resolve(['a']), 'dependency cycle')
        (root/'escape').symlink_to('/etc/passwd')
        rejected(lambda: SourceGraph(root).resolve(['escape']), 'escapes repository')


def test_peripherals_are_target_interfaces_never_cloud_capabilities():
    c = Catalog(ROOT)
    for target in c.targets.values():
        assert 'capabilities' not in target and target['interfaces']
    for name in ('display','audio','gpio','touch','camera','led','power','rtc','storage','input','environment'):
        assert name not in c.capabilities
    with fixture() as root:
        edit(root, 'platforms/esp-idf/targets/reterminal-e1001/target.json', lambda target: target.update(capabilities=['display']))
        rejected(lambda: Catalog(root), 'not cloud Skill Capabilities')


def test_native_parameter_types_and_resource_limits_remain_explicit():
    c = Catalog(ROOT)
    interface = copy.deepcopy(next(item for item in c.target('esp-idf/reterminal-e1001')['interfaces'] if item['id']=='display'))
    assert c.platform_schema.match_interface(interface,{'configuration':{'width':800}})['status']=='match'
    assert c.platform_schema.match_interface(interface,{'configuration':{'width':100}})['status']=='unsupported'
    assert c.platform_schema.match_interface(interface,{'resources':{'peak_memory_bytes':64000}})['status']=='unknown'
    interface['resources']['peak_memory_bytes'].update(status='known',value=48000)
    assert c.platform_schema.match_interface(interface,{'resources':{'peak_memory_bytes':64000}})['status']=='match'
    assert c.platform_schema.match_interface(interface,{'resources':{'peak_memory_bytes':32000}})['status']=='unsupported'
    rejected(lambda:c.platform_schema.match_interface(interface,{'configuration':{'width':'wrong type'}}),'type mismatch')


def test_numeric_facts_cannot_contradict_their_source_or_localization():
    with fixture() as root:
        path = 'devices/reterminal-e1001/device.json'
        original = read_json(root/path)
        edit(root,path,lambda device:device['facts']['flash'].update(value=64))
        rejected(lambda: Catalog(root),'contradicts cited source')
        write_json(root/path,original)
        edit(root,path,lambda device:device.update(specs={'Controller':{'en':'64 MB','zh_CN':'32 MB'}}))
        rejected(lambda: Catalog(root),'translated facts must be derived')
        write_json(root/path,original)
        edit(root,path,lambda device:device['overview'].update(en='Flash {flash}.',zh_CN='Flash {psram}。'))
        rejected(lambda: Catalog(root),'bilingual fact references differ')


def test_device_target_backlinks_cannot_be_registered_twice():
    with fixture() as root:
        edit(root,'devices/reterminal/device.json',lambda device:device.update(targets=['linux/reterminal']))
        rejected(lambda: Catalog(root),'Target indexes')


def test_context_and_import_choose_declared_example_scope():
    c = Catalog(ROOT)
    context = c.context('linux/reterminal','buttons_evdev',task='build')
    assert 'skills/codecraft-build/SKILL.md' in context['files']
    assert 'skills/codecraft-device-test/SKILL.md' not in context['files']
    assert all(not path.endswith('/sensors_sysfs.py') for path in context['files'])
    assert 'platforms/esp-idf/components/sscma_client/camera.c' not in c.graph('esp-idf/reterminal-e1001').files
    assert 'platforms/esp-idf/components/sscma_client/camera.c' in c.graph('esp-idf/sensecap-watcher').files


def test_protocol_rejects_wrong_source_identity_partial_or_duplicate_cases():
    cases = [{'name':'native/a','status':'passed','reason':''},{'name':'native/b','status':'passed','reason':''}]
    original = envelope('native/device','build','a'*64,cases)
    for changed in [dict(original,target='wrong'),dict(original,operation='flash'),dict(original,source_digest='b'*64),dict(original,results=cases[:1]),dict(original,results=[cases[0],cases[0]])]:
        rejected(lambda: check_envelope(changed,'native/device','build','a'*64,['native/a','native/b'],0),'adapter')
    rejected(lambda:check_envelope(original,'native/device','build','a'*64,['native/a','native/b'],1),'exit/status')


def test_project_edits_have_explicit_relocking_without_losing_origin():
    with tempfile.TemporaryDirectory() as folder:
        output = Path(folder)/'app'
        generate_project(Catalog(ROOT),'linux/reterminal','buttons_evdev',output)
        original = read_json(output/'codecraft.lock')['origin']
        native = output/'platforms/linux/targets/reterminal/demos/buttons_evdev.py'
        native.write_text(native.read_text()+'\n# Deliberate application edit\n')
        assert verify_project(output)['status'] == 'failed'
        lock_project(output)
        assert verify_project(output)['status'] == 'passed'
        assert read_json(output/'codecraft.lock')['origin'] == original
        outcome = package_project(output,Path(folder)/'app.zip')
        assert outcome['kind'] == 'source-package' and not outcome['firmware_included']


def test_lock_checks_actual_toolchain_before_any_build():
    with tempfile.TemporaryDirectory() as folder:
        output = Path(folder)/'app'
        generate_project(Catalog(ROOT),'linux/reterminal','buttons_evdev',output)
        edit(output,'codecraft.lock',lambda lock:lock.update(resolved_toolchain={'status':'passed','python':'different'}))
        run = subprocess.run([sys.executable,str(output/'codecraft.py'),'build-project',str(output)],capture_output=True,text=True)
        payload = json.loads(run.stdout)['data']
        assert run.returncode == 2 and all(item['status']=='not_run' for item in payload['results'])
        assert not (output/'.codecraft/builds').exists()


def make_build_evidence(c, tid):
    target = c.target(tid)
    path = f'devices/{target["device"]}/tests/logs/synthetic.log'
    (c.root/path).parent.mkdir(parents=True, exist_ok=True)
    (c.root/path).write_text('Synthetic unit-test observation; no real device or build claim.\n')
    cases = [{'name':name,'status':'passed','toolchain':'synthetic fixture'} for name in load_adapter(c.root,c.platforms[target['platform']]).cases(c.root,target)]
    source = c.graph(tid).fingerprint()
    return {'schema_version':2,'target':tid,'kind':'build','repository_commit':'0'*40,'repository_dirty':True,
            'source_digest':source,'revision':'unknown','toolchain':'synthetic fixture','command':['test-fixture'],
            'environment':'isolated test','result':'passed','limitations':['Synthetic unit test only'],
            'operator':'test','log':path,'log_sha256':digest(c.root/path),'executed_at':'2026-01-01T00:00:00+00:00','cases':cases,
            'generated_project':{'status':'passed','provenance':'passed','example':target['examples'][0],
                                 'origin_source_digest':source,'source_digest':'a'*64,'build_results':[cases[0]],'log':path,'log_sha256':digest(c.root/path)}}


def test_evidence_requires_all_native_cases_and_export_from_identical_sources():
    with fixture() as root:
        c = Catalog(root);tid = 'linux/reterminal'
        record = make_build_evidence(c,tid)
        validate_evidence(c,record,current=True)
        record['cases'].pop()
        rejected(lambda:validate_evidence(c,record,current=True),'every native case')
        record = make_build_evidence(c,tid)
        record['generated_project']['origin_source_digest'] = 'b'*64
        rejected(lambda:validate_evidence(c,record,current=True),'same sources')


def test_evidence_rejects_unsupported_versions_before_interpreting_observations():
    with fixture() as root:
        c = Catalog(root)
        record = make_build_evidence(c, 'linux/reterminal')
        for version in (1, 3, None):
            record['schema_version'] = version
            rejected(lambda: validate_evidence(c, record), 'Unsupported evidence schema')


def test_adapter_or_contract_changes_invalidate_evidence_but_log_additions_do_not():
    with fixture() as root:
        c = Catalog(root);tid = 'linux/reterminal'
        record = make_build_evidence(c,tid)
        directory = root/'devices/reterminal/tests/records'
        if directory.exists():shutil.rmtree(directory)
        directory.mkdir(parents=True)
        write_json(directory/'fixture.json',record)
        assert Catalog(root).support(tid)['level'] == 'build-verified'
        (root/'devices/reterminal/tests/logs/unrelated.log').write_text('another observation')
        assert Catalog(root).support(tid)['level'] == 'build-verified'
        path = root/'platforms/linux/adapter.py'
        path.write_text(path.read_text()+'\n# Changed actual adapter\n')
        assert Catalog(root).support(tid)['level'] == 'unknown'
        assert Catalog(root).support(tid)['stale_records']


def test_physical_verification_requires_revision_and_complete_named_cases():
    with fixture() as root:
        tid = 'linux/reterminal'
        edit(root,'devices/reterminal/device.json',lambda device:device.update(revision='synthetic-revision'))
        c=Catalog(root);record=make_build_evidence(c,tid)
        directory=root/'devices/reterminal/tests/records'
        if directory.exists():shutil.rmtree(directory)
        directory.mkdir(parents=True)
        write_json(directory/'build.json',record)
        record.update(kind='device',revision='synthetic-revision',cases=[{'name':'identity','status':'passed','observation':'synthetic identity only','procedure':'test fixture'}])
        write_json(directory/'physical.json',record)
        assert Catalog(root).support(tid)['level']=='build-verified'
        assert Catalog(root).support(tid)['device']=='not_run'
        acceptance=read_json(root/'devices/reterminal/tests/acceptance.json')
        record['cases']=[{'name':case['id'],'status':'passed','observation':'synthetic unit-test observation','procedure':'synthetic unit-test procedure'} for case in acceptance['cases']]
        write_json(directory/'physical.json',record)
        assert Catalog(root).support(tid)['level']=='device-verified'
        record['revision']='unknown'
        rejected(lambda:validate_evidence(c,record),'observed revision')


def test_cloud_provider_projection_exports_selected_standalone_skill():
    c=Catalog(ROOT)
    choice={'capability':'asr','provider':'asr/codecraft-cloud','configuration':{},
            'environment':{'network':True,'tls':True,'privacy_approved':True,'environment_refs':['CODECRAFT_API_ORIGIN'],'secret_refs':['CODECRAFT_DEVICE_FILE']},'limits':{}}
    with tempfile.TemporaryDirectory() as folder:
        output=Path(folder)/'project'
        generated=generate_project(c,'linux/reterminal','buttons_evdev',output,[choice])
        assert verify_project(output)['status']=='passed'
        assert read_json(output/'project.yaml')['capabilities']==[choice]
        assert (output/'capabilities/asr/providers/codecraft-cloud/provider.json').is_file()
        assert not (output/'capabilities/tts').exists()
        package=output/'skills/codecraft-asr'
        assert (package/'scripts/device_api.py').is_file()
        assert (package/'SKILL.md').is_file()
        assert not (package/'SKILL.zh_CN.md').exists()
        assert not (output/'skills/codecraft-tts').exists()
        lock=read_json(output/'codecraft.lock')
        assert 'capabilities/asr/providers/codecraft-cloud/provider.json' in lock['files']
        assert 'skills/codecraft-asr/scripts/device_api.py' in lock['files']
        assert all(not Path(path).is_absolute() for path in lock['files'])
        prepared=Catalog(output).cloud().prepare(choice,'linux/reterminal','transcribe',{'file':'/user/input.wav'})
        assert prepared['entrypoint']=={'skill':'codecraft-asr','path':'scripts/transcribe.py'}
        run=subprocess.run([sys.executable,str(package/'scripts/transcribe.py'),'--help'],cwd=output,capture_output=True,text=True)
        assert run.returncode==0 and '--file' in run.stdout
        (package/'scripts/device_api.py').write_text('# Unreviewed client edit\n')
        assert verify_project(output)['status']=='failed'


def test_repository_skill_mutations_and_missing_export_dependencies_are_rejected():
    with fixture() as root:
        path=root/'skills/codecraft-asr/scripts/transcribe.py'
        path.write_text(path.read_text()+'\n# Unreviewed runtime change\n')
        rejected(lambda:Catalog(root).cloud(),'repository Skill differs from pinned source')
    with fixture() as root:
        edit(root,'capabilities/asr/providers/codecraft-cloud/provider.json',lambda provider:provider['dependencies'].remove('skills/codecraft-asr'))
        rejected(lambda:Catalog(root).cloud(),'declared dependency')


def test_an_additional_provider_does_not_modify_core_resolver():
    with fixture() as root:
        provider=read_json(root/'capabilities/asr/providers/codecraft-cloud/provider.json')
        provider['id']='asr/fixture-provider'
        write_json(root/'capabilities/asr/providers/fixture-provider/provider.json',provider)
        c=Catalog(root).cloud()
        assert len(c.resolve('asr','linux/reterminal')['candidates'])==2
        assert c.resolve('asr','linux/reterminal')['needs_user_input']


def test_llm_requires_exactly_one_input_and_stream_handoff_keeps_done_semantics():
    c=Catalog(ROOT).cloud()
    choice={'capability':'llm','provider':'llm/codecraft-cloud','configuration':{'max_tokens':256},
            'environment':{'network':True,'tls':True,'privacy_approved':True,'environment_refs':['CODECRAFT_API_ORIGIN'],'secret_refs':['CODECRAFT_DEVICE_FILE']},'limits':{}}
    rejected(lambda:c.prepare(choice,'linux/reterminal','complete',{'prompt_file':'/a','messages_file':'/b'}),'exactly one')
    prepared=c.prepare(choice,'linux/reterminal','stream',{'prompt_file':'/a'})
    assert '--stream' in prepared['arguments'] and prepared['output_schema']['type']=='string'
    choice['configuration']['max_tokens']=0
    rejected(lambda:c.prepare(choice,'linux/reterminal','complete',{'prompt_file':'/a'}),'below minimum')


def test_private_environment_files_are_not_locked_or_packaged():
    with tempfile.TemporaryDirectory() as folder:
        output=Path(folder)/'app'
        generate_project(Catalog(ROOT),'linux/reterminal','buttons_evdev',output)
        (output/'.env').write_text('SYNTHETIC_TEST_PRIVATE_VALUE=not-a-credential\n')
        (output/'secrets').mkdir();(output/'secrets/device.json').write_text('{"synthetic":true}')
        lock=lock_project(output)
        assert '.env' not in lock['files'] and 'secrets/device.json' not in lock['files']
        package_project(output,Path(folder)/'package.zip')
        import zipfile
        with zipfile.ZipFile(Path(folder)/'package.zip') as archive:
            assert '.env' not in archive.namelist() and 'secrets/device.json' not in archive.namelist()


def cloud_choice():
    return {'capability': 'asr', 'provider': 'asr/codecraft-cloud', 'configuration': {},
            'environment': {'network': True, 'tls': True, 'privacy_approved': True,
                            'environment_refs': ['CODECRAFT_API_ORIGIN'], 'secret_refs': ['CODECRAFT_DEVICE_FILE']},
            'limits': {}}


def test_cloud_cli_needs_no_hardware_catalog_but_checks_explicit_targets():
    cloud = load_cloud(ROOT)
    choice = cloud_choice()
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)/'cloud-only'
        for relative in cloud.graph(choice['provider']).files:
            destination = root/relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT/relative, destination)
        assert not (root/'devices').exists() and not (root/'platforms').exists()
        requirements = Path(folder)/'requirements.json'
        selections = Path(folder)/'selection.json'
        inputs = Path(folder)/'input.json'
        write_json(requirements, {'environment': choice['environment']})
        write_json(selections, choice)
        write_json(inputs, {'file': '/user/recording.wav'})
        for args in [
            ['cloud-catalog'], ['check-cloud-skills'],
            ['resolve-capability', '--capability', 'asr', '--requirements', str(requirements)],
            ['prepare-capability', '--selection', str(selections), '--operation', 'transcribe', '--input', str(inputs)],
        ]:
            run = subprocess.run([sys.executable, str(ROOT/'codecraft.py'), '--root', str(root), *args],
                                 cwd=folder, capture_output=True, text=True, timeout=30)
            assert run.returncode == 0, run.stdout+run.stderr
            result = json.loads(run.stdout)
            assert result['ok']
            if args[0] in ('resolve-capability', 'prepare-capability'):
                assert result['data']['target'] is None
        assert load_cloud(root).resolve('asr', environment=choice['environment'])['candidates'][0]['status'] == 'eligible'
    rejected(lambda: cloud.resolve('asr', 'linux/nonexistent'), 'unknown Target')


def test_malformed_cloud_selections_are_not_silently_dropped():
    c = Catalog(ROOT)
    with tempfile.TemporaryDirectory() as folder:
        output = Path(folder)/'application'
        for invalid in ({}, False, '', [None]):
            rejected(lambda: generate_project(c, 'linux/reterminal', 'buttons_evdev', output, invalid), 'selection')
            assert not output.exists()
        selections = Path(folder)/'null-selection.json'
        write_json(selections, None)
        run = subprocess.run([sys.executable, str(ROOT/'codecraft.py'), 'new',
                              '--target', 'linux/reterminal', '--example', 'buttons_evdev',
                              '--output', str(output), '--capabilities', str(selections)],
                             capture_output=True, text=True, timeout=30)
        assert run.returncode != 0 and not output.exists()
        generate_project(c, 'linux/reterminal', 'buttons_evdev', output)
        edit(output, 'project.yaml', lambda data: data.update(capabilities={}))
        rejected(lambda: lock_project(output), 'selections must be a list')
    cloud = c.cloud()
    for invalid in ([], False, ''):
        rejected(lambda: cloud.resolve('asr', environment=invalid), 'must be objects')
        rejected(lambda: cloud.resolve('asr', limits=invalid), 'must be objects')


def test_pinned_skill_binary_assets_survive_context_export_lock_and_package():
    import zipfile
    with fixture() as root, tempfile.TemporaryDirectory() as folder:
        asset = 'skills/codecraft-asr/assets/vocabulary.bin'
        path = root/asset
        path.parent.mkdir(parents=True)
        path.write_bytes(b'\x00synthetic packaged vocabulary\xff')
        edit(root, 'capabilities/asr/providers/codecraft-cloud/provider.json',
             lambda provider: provider['skill']['files'].update({'assets/vocabulary.bin': digest(path)}))
        catalog = Catalog(root)
        assert asset in catalog.context('linux/reterminal', providers=['asr/codecraft-cloud'])['files']
        output = Path(folder)/'application'
        generate_project(catalog, 'linux/reterminal', 'buttons_evdev', output, [cloud_choice()])
        assert (output/asset).read_bytes() == path.read_bytes()
        assert read_json(output/'codecraft.lock')['files'][asset] == digest(path)
        assert verify_project(output)['status'] == 'passed'
        package = Path(folder)/'application.zip'
        package_project(output, package)
        with zipfile.ZipFile(package) as archive:
            assert archive.read(asset) == path.read_bytes()
        (output/asset).write_bytes(b'changed asset')
        assert asset in verify_project(output)['drift']


def test_provider_rejects_ambiguous_or_malformed_cli_mappings():
    cloud = load_cloud(ROOT)
    for fixed in ('--stream', ['--stream', '--stream'], [42]):
        provider = copy.deepcopy(cloud.providers['llm/codecraft-cloud'])
        provider['operations']['stream']['fixed_arguments'] = fixed
        rejected(lambda: cloud.schema.provider(ROOT, provider, cloud.capabilities['llm']), 'CLI' if isinstance(fixed, list) else 'fixed arguments')
    provider = copy.deepcopy(cloud.providers['llm/codecraft-cloud'])
    provider['operations']['complete']['options']['max_tokens'] = '--prompt-file'
    rejected(lambda: cloud.schema.provider(ROOT, provider, cloud.capabilities['llm']), 'duplicate CLI flag')
