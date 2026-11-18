"""The public entry preserves old CLI behavior and builds locked exported apps."""
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


def command(entry,arguments,cwd,environment=None):
    return subprocess.run([sys.executable,'-B',str(entry),*arguments],cwd=cwd,
                          env=environment,capture_output=True,text=True,timeout=120)


def test_public_and_legacy_cli_preserve_json_errors_help_and_working_directory_independence():
    with tempfile.TemporaryDirectory() as folder:
        for args in (['catalog'],['cloud-catalog'],['--help'],['not-a-command'],
                     ['resolve-capability','--capability','missing'],['skill-release','--help']):
            public=command(ROOT/'codecraft.py',args,folder)
            legacy=command(ROOT/'skills/_shared/codecraft.py',args,folder)
            assert (public.returncode,public.stdout,public.stderr)==(legacy.returncode,legacy.stdout,legacy.stderr),args
        assert command(ROOT/'codecraft.py',['catalog'],folder).returncode==0
        assert command(ROOT/'codecraft.py',['resolve-capability','--capability','missing'],folder).returncode==1
        assert command(ROOT/'codecraft.py',['not-a-command'],folder).returncode==2


def test_exported_public_entry_builds_with_the_same_lock_and_keeps_legacy_build_entry():
    with tempfile.TemporaryDirectory() as folder:
        output=Path(folder)/'app';generate_project(Catalog(ROOT),'linux/reterminal','buttons_evdev',output)
        assert (output/'codecraft.py').read_bytes()==(ROOT/'codecraft.py').read_bytes()
        lock=json.loads((output/'codecraft.lock').read_text())
        assert 'codecraft.py' in lock['files'] and 'codecraft.py' in lock['dependency_graph']['files']
        verify=command(output/'codecraft.py',['verify-project','.'],output)
        assert verify.returncode==0 and json.loads(verify.stdout)['data']['status']=='passed'
        public=command(output/'codecraft.py',['build-project','.'],output)
        legacy=command(output/'build.py',[],output)
        assert public.returncode==legacy.returncode==0,(public.stdout,legacy.stdout)
        assert json.loads(public.stdout)['data']==json.loads(legacy.stdout)
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
