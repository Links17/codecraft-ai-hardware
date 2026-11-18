"""Arduino CLI 1.5 JSON, exact dependencies and source-sensitive native builds."""
from contextlib import contextmanager
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/_shared'))
from io_utils import ContractError, read_json
from runtime import load_adapter
adapter=load_adapter(ROOT,read_json(ROOT/'platforms/arduino/platform.json'))


@contextmanager
def environment():
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory).resolve()
        for name in ('native/examples/blink','core/libraries/LCD','library','compiler'):
            (root/name).mkdir(parents=True)
        for name in ('core/board.txt','library/driver.h','compiler/cc','arduino-cli','native/examples/blink/blink.ino'):
            (root/name).write_text('fixture')
        target={'id':'arduino/test-fixture','device':'test-fixture','platform':'arduino',
                'path':'native','examples':['blink'],'example_inputs':{'blink':['native/examples/blink']},
                'toolchain':{'version':'1.5.0','fqbn':'fixture:arch:board','core_version':'1.0.0',
                             'libraries':{'Fixture Library':'2.0.0'},'board_manager_urls':[], 'bundled_libraries':['LCD']}}
        responses={
          'version':{'VersionString':'1.5.0'},
          'core':{'platforms':[{'id':'fixture:arch','installed_version':'1.0.0'}]},
          'lib':{'installed_libraries':[{'library':{'name':'Fixture Library','version':'2.0.0','install_dir':str(root/'library')}}]},
          'board':{'fqbn':'fixture:arch:board','version':'1.0.0','build_properties':[
                   'runtime.platform.path='+str(root/'core'),'runtime.tools.compiler-1.0.0.path='+str(root/'compiler')],
                   'tools_dependencies':[{'packager':'fixture','name':'compiler','version':'1.0.0'}]},
        }
        def run(argv,**kwargs):
            return subprocess.CompletedProcess(argv,0,json.dumps(responses[argv[1]]),'')
        with patch.object(adapter.shutil,'which',return_value=str(root/'arduino-cli')),patch.object(adapter.subprocess,'run',side_effect=run):
            yield root,target,responses


def test_native_compile_uses_exact_fqbn_output_and_selected_library_paths():
    with environment() as (root,target,_):
        adapter.validate_target(root,target)
        with patch.object(adapter,'command',return_value={'status':'passed'}) as call:
            assert adapter.build(root,target)==[{'status':'passed'}]
        argv=call.call_args.args[2]
        assert argv[:4]==['arduino-cli','compile','--fqbn','fixture:arch:board']
        assert argv[-1]==str(root/'native/examples/blink')
        assert str(root/'library') in argv and str(root/'core/libraries/LCD') in argv
        assert '--build-path' in argv and call.call_args.args[3]['status']=='passed'


def test_missing_mismatched_or_malformed_dependencies_never_compile():
    for mutation in ('cli','core','library','response','tool'):
        with environment() as (root,target,responses):
            if mutation=='cli':responses['version']['VersionString']='9.0.0'
            elif mutation=='core':responses['core']['platforms'][0]['installed_version']='9.0.0'
            elif mutation=='library':responses['lib']['installed_libraries']=[]
            elif mutation=='response':responses['core']=[]
            else:(root/'compiler').rename(root/'removed-compiler')
            assert adapter.probe(root,target)['status']=='not_run'
            with patch.object(adapter,'command',side_effect=AssertionError('unqualified build')):
                assert adapter.build(root,target)[0]['status']=='not_run'


def test_probe_tracks_selected_source_bytes_and_ignores_unrelated_packages():
    with environment() as (root,target,responses):
        first=adapter.probe(root,target);assert first['status']=='passed'
        responses['core']['platforms'].append({'id':'other:arch','installed_version':'9.0.0'})
        responses['lib']['installed_libraries'].append({'library':{'name':'Unrelated','version':'9.0.0'}})
        assert adapter.probe(root,target)==first
        for path in ('library/driver.h','core/board.txt','compiler/cc'):
            source=root/path;source.write_text('changed')
            assert adapter.probe(root,target)!=first
            source.write_text('fixture')
        assert adapter.probe(root,target)==first


def test_target_requires_exact_sketch_and_source_closure():
    with environment() as (root,target,_):
        target['example_inputs']['blink']=[]
        try:adapter.validate_target(root,target)
        except ContractError as error:assert 'source closure' in str(error)
        else:raise AssertionError('Undeclared sketch accepted')


def test_each_sketch_exports_with_device_acceptance_and_without_other_sketches():
    from model import Catalog
    from project import generate_project, verify_project
    from cli import check_documentation
    catalog=Catalog(ROOT)
    isolated=SimpleNamespace(validate_target=adapter.validate_target,
                             probe=lambda root,target: {'status':'not_run','reason':'No native tools in this export test.'})
    with tempfile.TemporaryDirectory(prefix='codecraft-arduino-export-') as folder, patch('project.load_adapter',return_value=isolated):
        for tid,target in catalog.targets.items():
            if target['platform']!='arduino':continue
            for example in target['examples']:
                output=Path(folder)/target['device']/example
                generate_project(catalog,tid,example,output)
                check_documentation(output)
                assert verify_project(output)['status']=='passed'
                exported=Catalog(output)
                assert exported.target(tid)['examples']==[example]
                assert {p.stem for p in output.rglob('*.ino')}=={example}
                acceptance=exported.devices[target['device']]['acceptance']
                assert all((output/case['source']).is_file() for case in acceptance['cases'])
