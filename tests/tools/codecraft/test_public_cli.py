"""The canonical public entry exposes typed results and builds locked exports."""
from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/codecraft'))
from model import Catalog
from project import generate_project
from io_utils import ContractError, digest
from cli import validate_project
from types import SimpleNamespace


def command(entry,arguments,cwd,environment=None):
    return subprocess.run([sys.executable,'-B',str(entry),*arguments],cwd=cwd,
                          env=environment,capture_output=True,text=True,timeout=120)


def test_public_cli_emits_typed_results_and_errors_from_any_working_directory():
    with tempfile.TemporaryDirectory() as folder:
        for args in (['catalog'],['check-cloud-skills'],['--help'],['not-a-command'],
                     ['context','--target','linux/missing'],['skill-release','--help']):
            public=command(ROOT/'codecraft.py',args,folder)
            if args[-1]=='--help':
                assert public.returncode==0 and 'usage:' in public.stdout
            elif args[0]=='not-a-command':
                assert public.returncode==2 and 'invalid choice' in public.stderr
            else:
                payload=json.loads(public.stdout)
                assert payload['schema_version']==2 and type(payload['ok']) is bool
                assert payload['ok']==(public.returncode==0)
                assert ('data' in payload) if payload['ok'] else payload['error']['type']=='contract'
        assert command(ROOT/'codecraft.py',['catalog'],folder).returncode==0
        assert command(ROOT/'codecraft.py',['context','--target','linux/missing'],folder).returncode==1
        assert command(ROOT/'codecraft.py',['not-a-command'],folder).returncode==2


def test_exported_public_entry_builds_and_relocks_with_one_command_contract():
    with tempfile.TemporaryDirectory() as folder:
        output=Path(folder)/'app';generate_project(Catalog(ROOT),'linux/reterminal','buttons_evdev',output)
        assert (output/'codecraft.py').read_bytes()==(ROOT/'codecraft.py').read_bytes()
        lock=json.loads((output/'codecraft.lock').read_text())
        assert 'codecraft.py' in lock['files'] and 'codecraft.py' in lock['dependency_graph']['files']
        verify=command(output/'codecraft.py',['verify-project','.'],output)
        assert verify.returncode==0 and json.loads(verify.stdout)['data']['status']=='passed'
        public=command(output/'codecraft.py',['build-project','.'],output)
        assert public.returncode==0,public.stdout
        assert json.loads(public.stdout)['data']['ok']
        assert not (output/'build.py').exists()
        assert 'tools/codecraft/cli.py' in lock['files']
        relock=command(output/'codecraft.py',['lock-project','.'],output)
        assert relock.returncode==0
        assert json.loads((output/'codecraft.lock').read_text())['origin']==lock['origin']
        (output/'codecraft.py').write_text((output/'codecraft.py').read_text()+'\n# unreviewed change\n')
        verify=command(output/'codecraft.py',['verify-project','.'],output)
        assert verify.returncode==1 and 'codecraft.py' in json.loads(verify.stdout)['data']['drift']


def test_exported_public_entry_preserves_not_run_and_not_supported_exit_statuses():
    with tempfile.TemporaryDirectory() as folder:
        output=Path(folder)/'app';generate_project(Catalog(ROOT),'linux/reterminal','buttons_evdev',output)
        env={**os.environ,'PATH':''}
        missing=command(output/'codecraft.py',['build-project','.'],output,env)
        payload=json.loads(missing.stdout)
        assert missing.returncode==2 and not payload['ok']
        assert all(row['status']=='not_run' for row in payload['data']['results'])
        release=command(output/'codecraft.py',['skill-release','prepare','--output',str(Path(folder)/'release')],output)
        assert release.returncode==2 and json.loads(release.stdout)['data']['status']=='not_supported'
        assert not (Path(folder)/'release').exists()
        for args in (['check-cloud-skills'],['generate'],
                     ['skill-reference','--skill','codecraft-development-recamera-pysdk',
                      '--sdk-root',folder,'--check']):
            unavailable=command(output/'codecraft.py',args,output)
            assert unavailable.returncode==2 and not unavailable.stderr,unavailable.stdout+unavailable.stderr
            assert json.loads(unavailable.stdout)['data']['status']=='not_supported'
        incomplete=Path(folder)/'incomplete';incomplete.mkdir()
        missing_source=command(ROOT/'codecraft.py',['--root',str(incomplete),'skill-release','prepare','--output',str(Path(folder)/'missing-release')],folder)
        assert missing_source.returncode==1
        assert json.loads(missing_source.stdout)['error']['type']=='contract'
        assert not (Path(folder)/'missing-release').exists()


def test_public_entry_routes_candidate_preparation_without_loading_a_hardware_catalog():
    spec=importlib.util.spec_from_file_location('release_source',ROOT/'tools/skill_packages/release.py')
    release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)
    spec=importlib.util.spec_from_file_location('public_entry',ROOT/'codecraft.py')
    public=importlib.util.module_from_spec(spec);spec.loader.exec_module(public)
    with tempfile.TemporaryDirectory() as folder:
        output=Path(folder)/'candidate'
        stdout=io.StringIO()
        with patch('model.Catalog',side_effect=AssertionError('Release loaded hardware orchestration')),redirect_stdout(stdout):
            result=public.main(['skill-release','prepare','--output',str(output)])
        assert result==0,stdout.getvalue()
        assert release.inspect(ROOT,output)[1]==json.loads(stdout.getvalue())['data']['review_sha256']


def test_export_failure_returns_a_gate_result_and_retained_diagnostic():
    with tempfile.TemporaryDirectory() as folder:
        catalog=SimpleNamespace(root=Path(folder),target=lambda tid: {'examples':['fixture']})
        with patch('cli.generate_project',side_effect=ContractError('missing fixture acceptance source')):
            row=validate_project(catalog,'arduino/fixture')
        assert row['status']=='failed' and row['name']=='arduino/fixture/generated-project'
        log=catalog.root/row['log']
        assert 'missing fixture acceptance source' in log.read_text()
        assert row['log_sha256']==digest(log)


def test_requested_example_reaches_the_clean_export_and_native_build():
    run=command(ROOT/'codecraft.py',['validate','--target','linux/reterminal',
                                   '--example','sensors_sysfs','--projects'],ROOT)
    payload=json.loads(run.stdout)
    assert run.returncode==0,run.stdout
    project=next(row for row in payload['data']['results'] if row['name'].endswith('/generated-project'))
    assert project['example']=='sensors_sysfs'
    assert {row['name'] for row in project['build_results']}=={
        'linux/reterminal/sensors_sysfs','linux/reterminal/overlay/reterminal-peripherals-overlay'}
    assert 'sensors_sysfs' in project['log']


def test_requested_example_is_preserved_for_every_variant_export():
    with tempfile.TemporaryDirectory() as folder:
        target={'examples':['first','requested'],'variants':{'gx':{},'dx':{}},'default_variant':'gx'}
        catalog=SimpleNamespace(root=Path(folder),target=lambda tid:target,
                                graph=lambda tid:SimpleNamespace(fingerprint=lambda:'fixture'))
        with patch('cli.generate_project',side_effect=ContractError('controlled export stop')) as generate:
            row=validate_project(catalog,'esp-idf/fixture',example='requested')
        assert row['status']=='failed' and row['example']=='requested'
        assert [(call.args[2],call.kwargs['variant']) for call in generate.call_args_list]==[
            ('requested','gx'),('requested','dx')]


def test_no_public_build_route_bypasses_application_source_lock():
    with tempfile.TemporaryDirectory() as folder:
        output=Path(folder)/'app';generate_project(Catalog(ROOT),'linux/reterminal','buttons_evdev',output)
        native=output/'devices/reterminal/targets/demos/buttons_evdev.py'
        native.write_text(native.read_text()+'\n# Unreviewed application edit\n')
        adapter=output/'platforms/linux/adapter.py'
        routes=[(output/'codecraft.py',['build-project','.'],'Source changed'),
                (output/'codecraft.py',['validate','--target','linux/reterminal','--projects'],'build-project'),
                (ROOT/'codecraft.py',['--root',str(output),'validate','--target','linux/reterminal'],'build-project'),
                (adapter,['build','--root',str(output),'--target','linux/reterminal'],'Source changed')]
        for entry,args,message in routes:
            run=command(entry,args,output)
            assert run.returncode==1,run.stdout
            assert message in json.loads(run.stdout)['error']['message']
            assert not (output/'.codecraft/builds').exists()
        assert command(output/'codecraft.py',['lock-project','.'],output).returncode==0
        allowed=command(adapter,['build','--root',str(output),'--target','linux/reterminal'],output)
        assert allowed.returncode==0 and json.loads(allowed.stdout)['ok'],allowed.stdout


def test_direct_adapter_build_checks_locked_toolchain_and_requires_the_lock():
    with tempfile.TemporaryDirectory() as folder:
        output=Path(folder)/'app';generate_project(Catalog(ROOT),'linux/reterminal','buttons_evdev',output)
        lock_path=output/'codecraft.lock';lock=json.loads(lock_path.read_text())
        lock['resolved_toolchain']={'status':'passed','python':'different'}
        lock_path.write_text(json.dumps(lock))
        adapter=output/'platforms/linux/adapter.py'
        args=['build','--root',str(output),'--target','linux/reterminal']
        run=command(adapter,args,output)
        payload=json.loads(run.stdout)
        assert run.returncode==2 and all(row['status']=='not_run' for row in payload['results']),run.stdout
        assert not (output/'.codecraft/builds').exists()
        lock_path.unlink()
        run=command(adapter,args,output)
        assert run.returncode==1 and json.loads(run.stdout)['error']['type']=='contract'
        assert not (output/'.codecraft/builds').exists()
