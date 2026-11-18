"""Cloud maintenance and native application graphs remain independently usable."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/codecraft'))
from model import Catalog
from project import generate_project, verify_project
from cli import check_documentation
from io_utils import read_json


def selection(sid):
    return {'skill':sid,'configuration':{},'limits':{},
            'environment':{'network':True,'tls':True,'privacy_approved':True,
                           'environment_refs':['CODECRAFT_API_ORIGIN'],'secret_refs':['CODECRAFT_DEVICE_FILE']}}


def test_skill_contracts_never_import_hardware_or_read_credentials():
    program='''
import importlib.abc, pathlib, sys
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'tools/codecraft'))
class NoHardware(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname=='model':raise AssertionError('Skill checks imported hardware')
sys.meta_path.insert(0,NoHardware())
from skill_contracts import registrations, load_package, prerequisites
for sid in registrations(root):
    record,contract=load_package(root,sid)
    assert prerequisites(contract)['status']=='unknown'
assert 'model' not in sys.modules
'''
    run=subprocess.run([sys.executable,'-I','-B','-c',program,str(ROOT)],capture_output=True,text=True,timeout=30)
    assert run.returncode==0,run.stdout+run.stderr


def test_application_dispatch_uses_explicit_path_without_reference_catalog():
    import cli
    with tempfile.TemporaryDirectory() as folder:
        app=Path(folder)/'app'
        generate_project(Catalog(ROOT),'linux/reterminal','buttons_evdev',app)
        # Invalid --root must not be consulted for an explicit application operation.
        run=subprocess.run([sys.executable,'-B',str(ROOT/'codecraft.py'),'--root',folder,'verify-project',str(app)],
                           capture_output=True,text=True,timeout=30)
        assert run.returncode==0,run.stdout+run.stderr
        assert json.loads(run.stdout)['data']['status']=='passed'
        selected=Path(folder)/'selected'
        generate_project(Catalog(ROOT),'linux/reterminal','buttons_evdev',selected,[selection('codecraft-capabilities-asr')])
        (selected/'tools/codecraft/skill_contracts.py').unlink()
        run=subprocess.run([sys.executable,'-B',str(selected/'codecraft.py'),'check-cloud-skills'],
                           cwd=selected,capture_output=True,text=True,timeout=30)
        assert run.returncode==1 and not run.stderr
        assert json.loads(run.stdout)['error']['type']=='contract'


def test_all_target_variant_exports_preserve_context_and_selected_skill_closure():
    c=Catalog(ROOT)
    ids=['codecraft-capabilities-asr','codecraft-capabilities-llm','codecraft-capabilities-tts','codecraft-capabilities-image-generation']
    for tid,target in c.targets.items():
        for variant in target.get('variants') or [None]:
            for chosen in ([],[selection(sid) for sid in ids]):
                with tempfile.TemporaryDirectory() as folder:
                    app=Path(folder)/'app'
                    generate_project(c,tid,target['examples'][0],app,chosen,variant=variant)
                    assert verify_project(app)['status']=='passed'
                    check_documentation(app)
                    lock=read_json(app/'codecraft.lock')
                    assert lock['schema_version']==read_json(app/'project.yaml')['schema_version']==3
                    assert 'docs/development/application-workflow.md' in lock['files']
                    assert f'platforms/{target["platform"]}/AGENTS.md' in lock['dependency_graph']['files']
                    assert ('tools/codecraft/skill_contracts.py' in lock['files'])==bool(chosen)
                    assert (app/'tools/skill_packages').exists()==bool(chosen)
                    program='''
import importlib.abc, pathlib, sys
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'tools/codecraft'))
if sys.argv[3]=='native':
    class NoCloud(importlib.abc.MetaPathFinder):
        def find_spec(self,fullname,path=None,target=None):
            if fullname=='skill_contracts':raise AssertionError('Native context imported cloud checks')
    sys.meta_path.insert(0,NoCloud())
from model import Catalog
c=Catalog(root)
for task in ('ideate','develop','setup','build','debug','device-test','discover','validate'):
    value=c.context(sys.argv[2],task=task)
    assert set(value['guidance'])<=set(value['files'])
    assert all((root/path).is_file() for path in value['files'])
'''
                    run=subprocess.run([sys.executable,'-I','-B','-c',program,str(app),tid,'selected' if chosen else 'native'],
                                       cwd=folder,capture_output=True,text=True,timeout=90)
                    assert run.returncode==0,(tid,variant,run.stdout,run.stderr)
