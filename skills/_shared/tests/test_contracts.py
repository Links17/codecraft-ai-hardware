"""Behavioral regression tests for discovery, generation and validation."""
from contextlib import contextmanager
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import struct
import zlib
from unittest.mock import patch
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/_shared'))
from model import Catalog
from io_utils import ContractError, read_json, safe_path, source_files
from project import generate_project, verify_project, package_project
from render import generate, paired, views
from cli import record_evidence, check_documentation
from runtime import command, run_target, load_adapter
from evidence import validate_evidence
from io_utils import digest


@contextmanager
def fixture():
    with tempfile.TemporaryDirectory(prefix='codecraft-contract-') as folder:
        root=Path(folder)/'repo';root.mkdir()
        for p in source_files(ROOT):
            out=root/p.relative_to(ROOT);out.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,out,follow_symlinks=True)
        yield root


def rejected(fn, contains):
    try:fn()
    except ContractError as exc:assert contains in str(exc),(contains,str(exc))
    else:raise AssertionError('Expected contract rejection')


def change(root,path,fn):
    p=root/path;data=json.loads(p.read_text());fn(data);p.write_text(json.dumps(data))


def test_discovery_keeps_unknowns_and_rejects_unavailable_combinations():
    c=Catalog(ROOT)
    found=c.resolve(['display','environment'],'esp-idf')
    assert any(x['target']=='esp-idf/reterminal-e1001' for x in found['candidates'])
    assert all(x['verification'] in ('unknown','build-verified','device-verified') and 'compatible' not in x for x in found['candidates'])
    assert c.resolve(['camera'],'linux')['status']=='unsupported'
    rejected(lambda:c.resolve(['invented-capability']),'unknown requested native interface')


def test_context_contains_native_sources_and_only_selected_workflow():
    context=Catalog(ROOT).context('esp-idf/sensecap-watcher')
    assert any(p.endswith('bsp_pins.h') for p in context['files'])
    assert 'skills/codecraft-develop/SKILL.md' in context['files']
    assert 'skills/codecraft-device-test/SKILL.md' not in context['files']
    assert context['unknowns'] and context['support']['device']=='not_run'


def test_source_paths_cannot_escape_the_repository():
    rejected(lambda:safe_path(ROOT,'../outside'),'escapes repository')
    rejected(lambda:safe_path(ROOT,'/etc/passwd'),'invalid relative path')


def test_duplicate_json_keys_and_unknown_schema_versions_are_rejected():
    with tempfile.TemporaryDirectory() as folder:
        p=Path(folder)/'bad.json';p.write_text('{"schema_version":1,"schema_version":2}')
        rejected(lambda:read_json(p),'duplicate key')
    with fixture() as root:
        change(root,'devices/reterminal-e1001/device.json',lambda d:d.update(schema_version=99))
        rejected(lambda:Catalog(root),'unsupported device schema_version')


def test_orphan_native_targets_are_not_silently_omitted():
    with fixture() as root:
        (root/'platforms/esp-idf/targets/unregistered').mkdir()
        rejected(lambda:Catalog(root),'unregistered Target')


def test_missing_reference_and_nonreciprocal_binding_fail():
    with fixture() as root:
        change(root,'devices/reterminal-e1001/device.json',lambda d:d['references'].append('missing-source.md'))
        rejected(lambda:Catalog(root),'missing reference')
    with fixture() as root:
        change(root,'platforms/esp-idf/targets/reterminal-e1001/target.json',lambda d:d.update(device='reterminal'))
        rejected(lambda:Catalog(root),'identity/path mismatch')


def test_verified_claim_cannot_be_inserted_into_capability_manifest():
    with fixture() as root:
        change(root,'platforms/esp-idf/targets/reterminal-e1001/target.json',lambda d:d['interfaces'][0].update(verification='device-verified'))
        rejected(lambda:Catalog(root),'verification is derived')


def test_generation_is_stable_and_detects_metadata_changes():
    with fixture() as root:
        c=Catalog(root);generate(c)
        assert generate(c,check=True)==[]
        change(root,'devices/reterminal/device.json',lambda d:d['overview'].update(en='A changed description.'))
        c=Catalog(root)
        assert 'devices/reterminal/AGENTS.md' in generate(c,check=True)
        generate(c)
        assert generate(c,check=True)==[]


def test_generation_cannot_reintroduce_translated_engineering_documents():
    rejected(lambda:paired('AGENTS.md','# Rules\n','# Rules\n'),'Only README.md')
    generated=views(Catalog(ROOT))
    assert not any(name.endswith('.zh_CN.md') for name in generated)
    assert all('.zh_CN.md' not in value.replace('README.zh_CN.md','') for name,value in generated.items() if name.endswith('.md'))


def test_project_is_portable_reproducible_and_refuses_overwrite():
    c=Catalog(ROOT)
    with tempfile.TemporaryDirectory(prefix='codecraft-project-test-') as folder:
        a=Path(folder)/'a';b=Path(folder)/'b'
        first=generate_project(c,'esp-idf/reterminal-e1001','epd_hello',a)
        second=generate_project(c,'esp-idf/reterminal-e1001','epd_hello',b)
        assert first['source_digest']==second['source_digest']
        assert verify_project(a)['status']=='passed'
        assert not any(p.is_symlink() for p in a.rglob('*'))
        rejected(lambda:generate_project(c,'esp-idf/reterminal-e1001','epd_hello',a),'Output must be a new directory')
        assert (a/'project.yaml').is_file() and (a/'codecraft.lock').is_file()
        assert (a/'README.zh_CN.md').is_file() and (a/'AGENTS.md').is_file()
        assert not [p for p in a.rglob('*.zh_CN.md') if p.name!='README.zh_CN.md']
        (a/'codecraft.py').write_text('# deliberately modified\n')
        assert verify_project(a)['drift']==['codecraft.py']
        rejected(lambda:package_project(a,Path(folder)/'bad.zip'),'differs from its current lock')


def test_exported_documentation_resolves_without_the_reference_checkout():
    catalog=Catalog(ROOT)
    with tempfile.TemporaryDirectory(prefix='codecraft-export-docs-') as folder:
        for tid,target in catalog.targets.items():
            native=load_adapter(ROOT,catalog.platforms[target['platform']])
            adapter=SimpleNamespace(validate_target=native.validate_target,
                                    probe=lambda root,target: {'status':'not_run','reason':'Documentation test only'})
            output=Path(folder)/target['device']
            with patch('project.load_adapter',return_value=adapter):
                generate_project(catalog,tid,target['examples'][0],output)
            check_documentation(output)
            assert verify_project(output)['status']=='passed'


def test_missing_executable_is_not_a_success_or_unsupported_hardware():
    with tempfile.TemporaryDirectory() as folder:
        outcome=command(Path(folder),'test',['codecraft-test-executable-does-not-exist'])
        assert outcome['status']=='not_run'


def test_adapter_exit_and_result_must_agree():
    c=Catalog(ROOT)
    payload={'ok':True,'results':[{'name':'build','status':'not_run'}]}
    with patch('runtime.subprocess.run',return_value=subprocess.CompletedProcess([],0,json.dumps(payload),'')):
        outcomes=run_target(c,'linux/reterminal')
    assert outcomes[0]['status']=='failed'
    assert 'protocol' in outcomes[0]['reason'].lower()


def test_incomplete_physical_evidence_is_rejected():
    with tempfile.TemporaryDirectory() as folder:
        p=Path(folder)/'evidence.json';p.write_text('{"result":"passed"}')
        rejected(lambda:record_evidence(Catalog(ROOT),p),'Incomplete evidence')


def test_package_refuses_unlocked_source_files():
    with tempfile.TemporaryDirectory() as folder:
        output=Path(folder)/'project'
        generate_project(Catalog(ROOT),'linux/reterminal','buttons_evdev',output)
        (output/'unreviewed.txt').write_text('not part of the imported source')
        assert verify_project(output)['drift']==['unreviewed.txt']
        rejected(lambda:package_project(output,Path(folder)/'source.zip'),'differs from its current lock')


def test_unsupported_operation_returns_typed_status_and_no_device_write():
    run=subprocess.run([sys.executable,str(ROOT/'platforms/esp-idf/adapter.py'),'flash','--root',str(ROOT),'--target','esp-idf/reterminal-e1001'],capture_output=True,text=True)
    assert run.returncode==2
    payload=json.loads(run.stdout)
    assert payload['schema_version']==2 and payload['results'][0]['status']=='not_supported'


def test_asset_manifest_cannot_claim_false_dimensions_or_alpha():
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
    with fixture() as root:
        image=root/'devices/reterminal/assets/fixture.png'
        image.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b'\x00\x00\x00\x00\x00'))+chunk(b'IEND',b''))
        change(root,'devices/reterminal/device.json',lambda d:d.update(revision='test-fixture'))
        asset={'path':str(image.relative_to(root)),'source':'unit-test fixture','license':'CC0-1.0','sha256':digest(image),'revision':'test-fixture','width':1,'height':1,'alpha':True}
        change(root,'devices/reterminal/assets/manifest.json',lambda d:d.update(assets=[asset]))
        Catalog(root)
        change(root,'devices/reterminal/assets/manifest.json',lambda d:d['assets'][0].update(width=99))
        rejected(lambda:Catalog(root),'dimensions mismatch')
        change(root,'devices/reterminal/assets/manifest.json',lambda d:d['assets'][0].update(width=1,alpha=False))
        rejected(lambda:Catalog(root),'alpha claim mismatch')
