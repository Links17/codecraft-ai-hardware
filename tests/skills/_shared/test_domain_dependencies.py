"""Cloud domains stay below hardware orchestration; exports keep their loaders."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'skills/_shared'))
from io_utils import ContractError
from model import Catalog, load_cloud
from project import generate_project, verify_project


def domain_catalog():
    spec = importlib.util.spec_from_file_location('standalone_cloud_domain', ROOT/'capabilities/catalog.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CapabilityCatalog


def test_cloud_domain_import_and_discovery_do_not_import_hardware_catalog():
    program = '''
import importlib.abc, importlib.util, json, pathlib, sys
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'skills/_shared'))
class NoHardware(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname=='model':raise AssertionError('cloud imported hardware orchestration')
sys.meta_path.insert(0,NoHardware())
spec=importlib.util.spec_from_file_location('cloud_domain',root/'capabilities/catalog.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
cloud=module.CapabilityCatalog(root)
assert 'model' not in sys.modules
assert cloud.resolve('asr')['status']=='candidates'
assert len(cloud.describe()['capabilities'])==4
print(json.dumps({'loaded_hardware':False}))
'''
    result = subprocess.run([sys.executable, '-I', '-B', '-c', program, str(ROOT)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout+result.stderr
    assert json.loads(result.stdout) == {'loaded_hardware': False}


def test_target_lookup_is_injected_and_public_composition_stays_lazy():
    cloud_type = domain_catalog()
    cloud = cloud_type(ROOT)
    try:
        cloud.resolve('asr', 'linux/reterminal')
    except ContractError as error:
        assert 'caller-supplied Target resolver' in str(error)
    else:
        raise AssertionError('Domain accepted unvalidated Target context')
    looked_up = []
    def resolve_target(tid):
        looked_up.append(tid)
        if tid != 'linux/reterminal':
            raise ContractError('Unknown injected Target')
    cloud = cloud_type(ROOT, target_lookup=resolve_target)
    cloud.resolve('asr');assert looked_up == []
    cloud.resolve('asr', 'linux/reterminal');assert looked_up == ['linux/reterminal']
    try:cloud.resolve('asr', 'linux/missing')
    except ContractError:pass
    else:raise AssertionError('Unknown explicit Target was accepted')
    with patch('model.Catalog', side_effect=AssertionError('eager hardware lookup')):
        assert load_cloud(ROOT).resolve('asr')['status'] == 'candidates'
    assert load_cloud(ROOT).resolve('asr', 'linux/reterminal')['target'] == 'linux/reterminal'
    try:load_cloud(ROOT).resolve('asr', 'linux/missing')
    except ContractError:pass
    else:raise AssertionError('Public composition accepted an unknown Target')


def test_registry_is_in_cloud_native_and_export_source_closures():
    c = Catalog(ROOT)
    required = {'skills/_shared/registry.py','skills/_shared/graph.py','skills/_shared/io_utils.py'}
    assert required <= c.cloud().graph('asr/codecraft-cloud').files
    assert 'skills/_shared/registry.py' in c.context('linux/reterminal')['files']
    with tempfile.TemporaryDirectory() as folder:
        output = Path(folder)/'app'
        generate_project(c, 'linux/reterminal', 'buttons_evdev', output)
        assert (output/'skills/_shared/registry.py').read_bytes() == (ROOT/'skills/_shared/registry.py').read_bytes()
        assert verify_project(output)['status'] == 'passed'
        (output/'skills/_shared/registry.py').write_text('# changed neutral loader\n')
        assert verify_project(output)['status'] == 'failed'
