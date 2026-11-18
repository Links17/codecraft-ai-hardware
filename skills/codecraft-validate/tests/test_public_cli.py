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
sys.path.insert(0,str(ROOT/'skills/_shared'))
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
        for args in (['catalog'],['cloud-catalog'],['--help'],['not-a-command'],
                     ['resolve-capability','--capability','missing'],['skill-release','--help']):
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
        assert command(ROOT/'codecraft.py',['resolve-capability','--capability','missing'],folder).returncode==1
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
        assert 'skills/_shared/cli.py' in lock['files']
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
        incomplete=Path(folder)/'incomplete';incomplete.mkdir()
        missing_source=command(ROOT/'codecraft.py',['--root',str(incomplete),'skill-release','prepare','--output',str(Path(folder)/'missing-release')],folder)
        assert missing_source.returncode==1
        assert json.loads(missing_source.stdout)['error']['type']=='contract'
        assert not (Path(folder)/'missing-release').exists()


def test_public_entry_routes_candidate_preparation_without_loading_a_hardware_catalog():
    spec=importlib.util.spec_from_file_location('release_source',ROOT/'skills/_cloud/release.py')
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
