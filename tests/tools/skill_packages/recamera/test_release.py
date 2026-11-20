"""Development candidates preserve provenance and execute isolated SDK acceptance."""
from contextlib import contextmanager, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tools/codecraft'))
from io_utils import ContractError, package_inventory, read_json, write_json

spec = importlib.util.spec_from_file_location('recamera_release_tests', ROOT / 'tools/skill_packages/recamera/release.py')
release = importlib.util.module_from_spec(spec); spec.loader.exec_module(release)


@contextmanager
def workspace():
    with tempfile.TemporaryDirectory(prefix='codecraft-recamera-release-test-') as directory:
        base = Path(directory); root = base / 'repo'; root.mkdir()
        sources, _, _ = release.inputs(ROOT)
        release.copy_files(ROOT, root, sources['files'])
        # A synthetic already-reviewed baseline for each isolated transaction.
        baseline = release.record(root)
        baseline['files'] = package_inventory(root / release.PACKAGE)
        write_json(root / release.RECORD, baseline)
        yield root, base


def reject(operation, message):
    try:
        operation()
    except ContractError as error:
        assert message in str(error), str(error)
        return
    raise AssertionError('Invalid SDK candidate was accepted')


def next_release(root):
    major, minor, patch_version = release.version(release.record(root)['version'])
    return {release.SKILL: {'skill_version': f'{major}.{minor}.{patch_version + 1}'}}


def changed_candidate(root, base):
    entry = root / release.PACKAGE / 'SKILL.md'
    entry.write_text(entry.read_text() + '\nA local candidate fixture.\n')
    return release.prepare(root, base / 'candidate', next_release(root))


def test_reviewed_worktree_package_has_a_complete_inventory():
    assert release.check_package(ROOT)['status'] == 'passed'


def test_sdk_candidates_are_reproducible_without_repository_mutation():
    with workspace() as (root, base):
        before = package_inventory(root)
        first = release.prepare(root, base / 'first')
        second = release.prepare(root, base / 'second')
        assert first['review_sha256'] == second['review_sha256']
        assert package_inventory(base / 'first') == package_inventory(base / 'second')
        assert package_inventory(root) == before
        assert not first['changes']
        manifest, _ = release.inspect(root, base / 'first')
        assert manifest['proposed']['source'] == release.record(root)['source']
        assert not any(name.startswith('skills/codecraft-capabilities-') for name in manifest['sources']['files'])


def test_sdk_candidate_apply_runs_real_isolated_package_checks():
    with workspace() as (root, base):
        source = (root / 'docs/recamera-skill-import.json').read_bytes()
        prepared = changed_candidate(root, base)
        outcome = release.apply(root, base / 'candidate', prepared['review_sha256'])
        assert outcome['status'] == 'passed' and len(outcome['checks']) >= 5
        assert all(row['status'] == 'passed' for row in outcome['checks'])
        assert outcome['repository_changed'] and not outcome['published']
        assert outcome['device_verification'] == 'not_run'
        assert release.check_package(root)['status'] == 'passed'
        assert (root / 'docs/recamera-skill-import.json').read_bytes() == source
        assert not (root / '.codecraft/skill-release.lock').exists()


def test_wrong_digest_candidate_drift_and_source_drift_fail_before_execution():
    with workspace() as (root, base):
        prepared = release.prepare(root, base / 'candidate')
        with patch.object(release.subprocess, 'run', side_effect=AssertionError('Unreviewed code executed')):
            reject(lambda: release.apply(root, base / 'candidate', '0' * 64), 'reviewed digest')
            candidate = base / 'candidate' / release.PACKAGE / 'SKILL.md'
            content = candidate.read_bytes(); candidate.write_bytes(content + b'\ndrift\n')
            reject(lambda: release.validate(root, base / 'candidate'), 'Candidate files drifted')
            candidate.write_bytes(content)
            source = root / release.PACKAGE / 'SKILL.md'
            source.write_bytes(source.read_bytes() + b'\nsource drift\n')
            reject(lambda: release.validate(root, base / 'candidate', prepared['review_sha256']), 'Maintained sources changed')
        assert not (root / '.codecraft/skill-release.lock').exists()


def test_changed_package_needs_version_review_and_rejects_private_or_linked_files():
    with workspace() as (root, base):
        source = root / release.PACKAGE / 'SKILL.md'
        source.write_bytes(source.read_bytes() + b'\nchanged\n')
        reject(lambda: release.prepare(root, base / 'unversioned'), 'higher Skill version')
        assert not (base / 'unversioned').exists()
        reject(lambda: release.prepare(root, base / 'cloud-fields', {release.SKILL: {'api_version': 'v2'}}), 'only skill_version')
        private = root / release.PACKAGE / '.env'; private.write_text('SYNTHETIC=fixture')
        reject(lambda: release.prepare(root, base / 'private', next_release(root)), 'Private file')
        private.unlink()
        link = root / release.PACKAGE / 'linked'; link.symlink_to(source)
        reject(lambda: release.prepare(root, base / 'linked', next_release(root)), 'symlinks')


def test_empty_successful_checker_output_cannot_accept_a_candidate():
    with workspace() as (root, base):
        release.prepare(root, base / 'candidate')
        empty = subprocess.CompletedProcess([], 0, json.dumps({'ok': True, 'data': {'results': []}}), '')
        with patch.object(release.subprocess, 'run', return_value=empty):
            reject(lambda: release.validate(root, base / 'candidate'), 'incomplete')


def test_release_identity_cannot_rewrite_the_original_import():
    with workspace() as (root, base):
        value = release.record(root)
        value['source']['commit'] = '0' * 40
        write_json(root / release.RECORD, value)
        reject(lambda: release.prepare(root, base / 'candidate'), 'immutable import')
        assert not (base / 'candidate').exists()


def test_failed_apply_restores_release_record_and_preserves_the_worktree():
    with workspace() as (root, base):
        prepared = changed_candidate(root, base)
        before = (root / release.RECORD).read_bytes()
        package_before = package_inventory(root / release.PACKAGE)
        original = release.check_package
        def fail_final_check(path):
            if Path(path).resolve() == root.resolve():
                raise ContractError('injected final check failure')
            return original(path)
        with patch.object(release, 'check_package', side_effect=fail_final_check):
            reject(lambda: release.apply(root, base / 'candidate', prepared['review_sha256']), 'injected final check')
        assert (root / release.RECORD).read_bytes() == before
        assert package_inventory(root / release.PACKAGE) == package_before
        assert not (root / '.codecraft/skill-release.lock').exists()
        assert not list((root / 'skills').glob('.release-recamera-*'))


def test_public_sdk_release_command_does_not_construct_a_hardware_catalog():
    spec = importlib.util.spec_from_file_location('sdk_public_entry', ROOT / 'codecraft.py')
    public = importlib.util.module_from_spec(spec); spec.loader.exec_module(public)
    with workspace() as (root, base):
        output = io.StringIO()
        with patch('model.Catalog', side_effect=AssertionError('SDK release loaded hardware')), redirect_stdout(output):
            code = public.main(['--root', str(root), 'skill-release', 'prepare', '--skill', release.SKILL,
                                '--output', str(base / 'candidate')])
        assert code == 0, output.getvalue()
        assert json.loads(output.getvalue())['data']['review_sha256'] == release.inspect(root, base / 'candidate')[1]
