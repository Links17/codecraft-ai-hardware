"""Reference production parses source and requires an attributable revision."""
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tools/codecraft'))
from io_utils import ContractError, package_inventory, write_json

PRODUCER = ROOT / 'tools/skill_packages/recamera/api_reference.py'
spec = importlib.util.spec_from_file_location('recamera_reference_tests', PRODUCER)
reference = importlib.util.module_from_spec(spec); spec.loader.exec_module(reference)


@contextmanager
def fixture():
    with tempfile.TemporaryDirectory(prefix='codecraft-recamera-reference-test-') as directory:
        base = Path(directory); root = base / 'repo'; sdk = base / 'sdk'
        sdk.mkdir()
        for name in reference.EXTRA_SOURCES:
            path = sdk / name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('Synthetic source fixture.\n' if path.suffix != '.py' else '# synthetic source fixture\n')
        for module in ('kit', 'sdk/python/recamera_ext'):
            path = sdk / module / '__init__.py'; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('"""Synthetic public module."""\n'
                            'raise RuntimeError("Reference production must never execute SDK code")\n'
                            'def ping(value: str = "ok") -> str:\n'
                            '    """Return the supplied value."""\n'
                            '    return value\n')
        git = ['git', '-c', 'user.name=SDK Fixture', '-c', 'user.email=fixture@example.invalid',
               '-c', 'commit.gpgsign=false', '-C', str(sdk)]
        for args in (['init', '--quiet'], ['add', '.'], ['commit', '--quiet', '-m', 'test: create synthetic SDK']):
            subprocess.run([*git, *args], check=True, capture_output=True)
        revision = subprocess.check_output([*git, 'rev-parse', 'HEAD'], text=True).strip()
        maintenance = root / 'tools/skill_packages/recamera'; maintenance.mkdir(parents=True)
        shutil.copyfile(PRODUCER, maintenance / 'api_reference.py')
        write_json(maintenance / 'api-notes.json', {
            'modules': {'kit': 'Synthetic Kit module.', 'recamera_ext': 'Synthetic binding module.'},
            'symbols': {}, 'common': {}})
        write_json(maintenance / 'api-http-notes.json', {})
        skill = root / 'skills' / reference.SKILL_ID
        write_json(skill / 'scripts/api-reference-lock.json', {'source_revision': revision, 'generated_files': {}})
        yield root, sdk, skill, revision


def test_reference_round_trip_does_not_execute_sdk_and_detects_source_and_page_drift():
    with fixture() as (root, sdk, skill, revision):
        written = reference.reference(root, sdk, write=True, revision=revision)
        assert written['status'] == 'passed' and written['modules'] == 2
        assert written['sdk_execution'] == 'not_run'
        before = package_inventory(root)
        assert reference.reference(root, sdk)['status'] == 'passed'
        assert package_inventory(root) == before
        page = skill / 'references/api/python/kit.md'
        page.write_text(page.read_text() + '\nManual edit.\n')
        check = reference.reference(root, sdk)
        assert check['status'] == 'failed' and 'python/kit.md' in check['changed_pages']
        (sdk / 'kit/__init__.py').write_text((sdk / 'kit/__init__.py').read_text().replace('value: str', 'value: int'))
        check = reference.reference(root, sdk)
        assert check['status'] == 'failed' and check['source_changes'] == ['kit/__init__.py']
        assert not check['repository_changed']


def test_reference_writes_reject_wrong_revision_dirty_checkout_and_implicit_pin():
    with fixture() as (root, sdk, _, revision):
        before = package_inventory(root)
        for selected in (None, '0' * 40):
            try:
                reference.reference(root, sdk, write=True, revision=selected)
            except ContractError:
                pass
            else:
                raise AssertionError('Unattributable reference write accepted')
        (sdk / 'unreviewed.txt').write_text('unreviewed source')
        try:
            reference.reference(root, sdk, write=True, revision=revision)
        except ContractError as error:
            assert 'clean SDK checkout' in str(error)
        else:
            raise AssertionError('Dirty SDK reference write accepted')
        assert package_inventory(root) == before


def test_public_reference_command_reports_drift_and_invalid_source_as_typed_results():
    with fixture() as (root, sdk, _, revision):
        reference.reference(root, sdk, write=True, revision=revision)
        args = [sys.executable, '-B', str(ROOT / 'tools/codecraft/maintenance.py'), '--root', str(root),
                'skill-reference', '--skill', reference.SKILL_ID, '--sdk-root', str(sdk), '--check']
        good = subprocess.run(args, cwd=sdk, capture_output=True, text=True, timeout=30)
        assert good.returncode == 0 and json.loads(good.stdout)['ok'], good.stdout + good.stderr
        (sdk / 'kit/__init__.py').write_text('this is not valid Python!\n')
        bad = subprocess.run(args, cwd=sdk, capture_output=True, text=True, timeout=30)
        result = json.loads(bad.stdout)
        assert bad.returncode == 1 and result['error']['type'] == 'contract'
        assert 'SDK source parsing failed' in result['error']['message'] and not bad.stderr
