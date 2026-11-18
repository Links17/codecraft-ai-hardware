"""Host discovery preserves ownership, test identity, fixtures and failure status."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/codecraft'))
from io_utils import ContractError
from testing import inventory, run_tests


def write(root, relative, text):
    path=root/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    return path


def register_target(root, device, platform):
    native=f'devices/{device}/targets'
    write(root,native+'/target.json',json.dumps({
        'id':f'{platform}/{device}','platform':platform,'device':device,'path':native}))


def test_nested_owners_and_suite_styles_are_collected_once_without_running_bodies():
    paths=['tests/tools/codecraft/test_core.py','tests/tools/skill_packages/deeper/test_client.py',
           'tests/platforms/esp-idf/test_adapter.py',
           'tests/platforms/esp-idf/components/chip/protocol/test_protocol.py',
           'tests/devices/board/targets/test_board.py',
           'tests/tools/codecraft/test_skill_contracts.py','tests/skills/codecraft-capabilities-asr/test_contract.py']
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder)
        register_target(root,'board','esp-idf')
        for path in paths:
            write(root,path,"def test_body():\n    raise AssertionError('collection executed a test')\n")
        write(root,'tests/tools/skill_packages/test_suite.py',
              'import unittest\nfrom unittest import TestCase as Imported\n'
              'class Cases(unittest.TestCase):\n'
              "    def test_case(self): raise AssertionError('collection executed unittest')\n")
        for path in ('tests/devices/board/targets/fixtures/test_ignored.py',
                     'tests/platforms/esp-idf/stubs/test_ignored.py',
                     'tests/tools/skill_packages/mocks/test_ignored.py',
                     'tests/tools/skill_packages/build-cache/test_ignored.py',
                     'tests/tools/skill_packages/.cache/test_ignored.py',
                     'skills/codecraft-capabilities-asr/scripts/test_client.py',
                     'tools/codecraft/test_client.py',
                     'tools/skill_packages/test_package.py'):
            write(root,path,"raise AssertionError('not a test owner')\n")
        data=inventory(root)
        ids=[entry['name'] for entry in data['tests']]
        assert not data['collection_errors'] and len(ids)==len(set(ids))==8
        assert all(path+'::test_body' in ids for path in paths)
        assert inventory(root,selection='tests/platforms/esp-idf/components')['tests']==[
            {'name':paths[3]+'::test_body','kind':'function'}]
        # No class or function imported from another module becomes a test here.
        write(root,'tests/tools/codecraft/test_imports.py',
              'from unittest import TestCase\nfrom shutil import copy as test_imported\n'
              'def test_local(): pass\n')
        assert len(inventory(root)['tests'])==9


def test_unittest_fixtures_and_plain_functions_execute_once():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder)
        write(root,'tests/tools/skill_packages/test_events.py',
              'from pathlib import Path\nimport unittest\nfrom testing import inventory\nready=False\n'
              "def event(value):\n    with Path(__file__).with_suffix('.events').open('a') as f: f.write(value+'\\n')\n"
              "def test_function(): event('function')\n"
              "def setUpModule():\n    global ready\n    ready=True\n    event('module-up')\n"
              "def tearDownModule():\n    assert ready, 'nested inventory replaced fixture globals'\n    event('module-down')\n"
              'class Cases(unittest.TestCase):\n'
              "    @classmethod\n    def setUpClass(cls): event('class-up')\n"
              "    @classmethod\n    def tearDownClass(cls): event('class-down')\n"
              "    def setUp(self): event('up')\n    def tearDown(self): event('down')\n"
              "    def test_a(self): event('a')\n"
              "    def test_b(self):\n        inventory(Path(__file__).parents[3])\n        event('b')\n")
        rows=run_tests(root)
        assert len(rows)==3 and all(row['status']=='passed' for row in rows)
        events=(root/'tests/tools/skill_packages/test_events.events').read_text().splitlines()
        assert events==['function','module-up','class-up','up','a','down','up','b','down','class-down','module-down']


def test_collection_failures_and_duplicate_aliases_cannot_silently_pass():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder)
        fixtures={'test_syntax.py':'def broken(\n','test_import.py':"raise ImportError('fixture')\n",
                  'test_empty.py':'value=1\n','test_exit.py':'raise SystemExit(0)\n',
                  'test_alias.py':'def test_a(): pass\ntest_duplicate=test_a\n',
                  'test_async.py':'async def test_async(): pass\n'}
        for name,body in fixtures.items():write(root,'tests/tools/codecraft/'+name,body)
        data=inventory(root);assert not data['tests'] and len(data['collection_errors'])==6
        rows=run_tests(root);assert len(rows)==6 and all(row['status']=='failed' for row in rows)
        for selection in ('missing','/tmp','../outside'):
            try:inventory(root,selection=selection)
            except ContractError:pass
            else:raise AssertionError('Invalid or empty selection accepted')
        target=root/'tests/tools/codecraft/test_syntax.py'
        target.with_name('test_alias_path.py').symlink_to(target)
        try:inventory(root)
        except ContractError as error:assert 'Symlink' in str(error)
        else:raise AssertionError('Symlink test path accepted')


def test_suite_failures_subtests_skips_and_unrun_cases_keep_distinct_statuses():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder)
        write(root,'tests/tools/skill_packages/test_states.py',
              'import unittest\n'
              "def test_skip(): raise unittest.SkipTest('fixture skip')\n"
              'def test_exit(): raise SystemExit(0)\n'
              'class Broken(unittest.TestCase):\n'
              "    @classmethod\n    def setUpClass(cls): raise RuntimeError('setup failed')\n"
              "    def test_never(self): raise AssertionError('never reached')\n"
              'class Cases(unittest.TestCase):\n'
              '    def test_subtest(self):\n'
              '        for n in (1,2):\n'
              '            with self.subTest(n=n): self.assertEqual(n,1)\n'
              "    @unittest.skip('fixture')\n    def test_skip(self): pass\n"
              '    @unittest.expectedFailure\n    def test_expected(self): self.fail()\n'
              '    @unittest.expectedFailure\n    def test_unexpected(self): pass\n')
        rows=run_tests(root);states={row['name'].split('::')[1]:row['status'] for row in rows}
        assert states['test_skip']=='skipped' and states['test_exit']=='failed'
        assert states['Broken.test_never']=='not_run'
        assert states['Cases.test_subtest']=='failed'
        assert states['Cases.test_skip']==states['Cases.test_expected']=='skipped'
        assert states['Cases.test_unexpected']=='failed'
        assert any('setup failed' in row['reason'] and row['status']=='failed' for row in rows)
        assert not any(row['status']=='passed' for row in rows)


def test_focused_public_cli_preserves_json_and_failure_or_skip_exit_codes():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder)
        register_target(root,'board','esp-idf')
        write(root,'tests/devices/board/targets/test_case.py',
              "def test_pass(): print('test output must not corrupt JSON')\n")
        write(root,'tests/tools/skill_packages/test_failure.py','def test_fail(): raise AssertionError("fixture")\n')
        write(root,'tests/tools/skill_packages/test_skip.py','import unittest\ndef test_skip(): raise unittest.SkipTest("fixture")\n')
        def call(*args):
            run=subprocess.run([sys.executable,str(ROOT/'codecraft.py'),'--root',str(root),'test',*args],
                               capture_output=True,text=True,timeout=20,cwd=folder)
            return run.returncode,json.loads(run.stdout)
        code,data=call('--list');assert code==0 and len(data['data']['tests'])==3
        code,data=call('--path','tests/devices');assert code==0 and len(data['data']['results'])==1
        code,data=call('--path','tests/tools/skill_packages/test_failure.py');assert code==1 and not data['ok']
        code,data=call('--path','tests/tools/skill_packages/test_skip.py');assert code==2 and not data['ok']
        code,data=call('--path','missing');assert code==1 and data['error']['type']=='contract'


def test_repository_host_cases_have_unique_owned_identities():
    current=inventory(ROOT)
    assert not current['collection_errors'],current['collection_errors']
    discovered=[entry['name'] for entry in current['tests']]
    assert discovered and len(discovered)==len(set(discovered))
    assert all(identity.startswith('tests/') for identity in discovered)


def test_device_test_platform_selection_uses_manifest_and_excludes_evidence():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder)
        for device,platform in (('board-a','esp-idf'),('board-b','arduino')):
            register_target(root,device,platform)
            write(root,f'tests/devices/{device}/targets/test_board.py','def test_body(): pass\n')
            write(root,f'tests/devices/{device}/logs/test_not_executable.py',
                  "raise AssertionError('evidence must not execute')\n")
        write(root,'tests/platforms/arduino/nested/test_adapter.py','def test_body(): pass\n')
        write(root,'tests/platforms/esp-idf/components/chip/test_driver.py','def test_body(): pass\n')
        write(root,'tests/tools/codecraft/test_common.py','def test_body(): pass\n')
        write(root,'tests/skills/codecraft-capabilities-asr/test_contract.py','def test_body(): pass\n')
        current=inventory(root,platform='arduino')
        assert not current['collection_errors']
        assert [row['name'] for row in current['tests']]==[
            'tests/devices/board-b/targets/test_board.py::test_body',
            'tests/platforms/arduino/nested/test_adapter.py::test_body',
            'tests/skills/codecraft-capabilities-asr/test_contract.py::test_body',
            'tests/tools/codecraft/test_common.py::test_body']
        assert {row['name'] for row in inventory(root,platform='esp-idf')['tests']}=={
            'tests/skills/codecraft-capabilities-asr/test_contract.py::test_body',
            'tests/devices/board-a/targets/test_board.py::test_body',
            'tests/platforms/esp-idf/components/chip/test_driver.py::test_body',
            'tests/tools/codecraft/test_common.py::test_body'}
        (root/'devices/board-b/targets/target.json').unlink()
        try:inventory(root)
        except ContractError:pass
        else:raise AssertionError('Orphan device tests were silently omitted')
