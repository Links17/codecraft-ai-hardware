"""Offline behavior of the independently installed reCamera SDK Skill."""
from contextlib import contextmanager
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / 'skills/codecraft-development-recamera-pysdk'
FIXTURES = Path(__file__).parent / 'fixtures'


@contextmanager
def installation():
    with tempfile.TemporaryDirectory(prefix='codecraft-recamera-skill-') as folder:
        root = Path(folder)
        skill = root / SKILL.name
        shutil.copytree(SKILL, skill, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        app = root / 'app'
        shutil.copytree(FIXTURES, app)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        for key in ('PYTHONPATH', 'RECAMERA_SDK_ROOT', 'RECAMERA_EXT_API_ROOT'):
            env.pop(key, None)
        yield root, skill, app, env


def invoke(script, arguments, cwd, env):
    return subprocess.run([sys.executable, str(script), *map(str, arguments)],
                          cwd=cwd, env=env, capture_output=True, text=True, timeout=45)


def package(root, skill, app, env, output='dist'):
    run = invoke(skill / 'scripts/package_app.py', ['--app-dir', app, '--out', root / output], root, env)
    assert run.returncode == 0, run.stdout + run.stderr
    archives = list((root / output).glob('*.tar.gz'))
    assert len(archives) == 1
    return archives[0]


def inspect(archive, root, skill, env):
    code = ('import sys; from pathlib import Path; '
            'sys.path.insert(0, sys.argv[1]); '
            'from package_app import inspect_archive; '
            'inspect_archive(Path(sys.argv[2]))')
    return subprocess.run([sys.executable, '-c', code, str(skill / 'scripts'), str(archive)],
                          cwd=root, env=env, capture_output=True, text=True, timeout=30)


def test_isolated_validation_and_deterministic_package_do_not_execute_app():
    with installation() as (root, skill, app, env):
        run = invoke(skill / 'scripts/validate_app.py', ['--app-dir', app, '--mode', 'package'], root, env)
        assert run.returncode == 0, run.stdout + run.stderr
        report = json.loads(run.stdout)
        assert report['valid'] and not report['device_connected']
        assert report['runtime_preconditions_unverified']
        first = package(root, skill, app, env)
        second = package(root, skill, app, env, 'second')
        assert first.read_bytes() == second.read_bytes()
        assert inspect(first, root, skill, env).returncode == 0
        with tarfile.open(first) as archive:
            assert {'manifest.json', 'app.py', 'files.sha256', 'release.lock.json'} <= set(archive.getnames())
            manifest = json.load(archive.extractfile('manifest.json'))
            assert manifest['python']['wheels'] == []
            assert archive.extractfile('app.py').read() == (app / 'app.py').read_bytes()
        build_report = json.loads(next((root / 'dist').glob('*-build-report.json')).read_text())
        assert build_report['sha256'] == hashlib.sha256(first.read_bytes()).hexdigest()
        assert build_report['builder']['mode'] == 'bundled'
        assert not build_report['signature']['performed_by_skill']


def test_invalid_platform_and_entry_contracts_are_rejected_offline():
    with installation() as (root, skill, app, env):
        path = app / 'manifest.json'
        original = path.read_text()
        mutations = (('compatibility', 'arch', 'x86_64'), (None, 'entry', '../outside.py'))
        for parent, field, value in mutations:
            manifest = json.loads(original)
            (manifest[parent] if parent else manifest)[field] = value
            path.write_text(json.dumps(manifest))
            run = invoke(skill / 'scripts/validate_app.py', ['--app-dir', app, '--mode', 'package'], root, env)
            report = json.loads(run.stdout)
            assert run.returncode != 0 and not report['valid'] and report['errors']
            assert not report['device_connected']
        path.write_text(original)
        (app / 'app.py').write_text('from kit.app import App\nclass InvalidApp(App):\n    owns_loop = True\n    def run(self, frame):\n        return frame\n')
        run = invoke(skill / 'scripts/validate_app.py', ['--app-dir', app, '--mode', 'package'], root, env)
        assert run.returncode != 0 and json.loads(run.stdout)['errors']


def test_modified_payload_is_rejected_by_final_archive_verification():
    with installation() as (root, skill, app, env):
        original = package(root, skill, app, env)
        changed = root / 'tampered.tar.gz'
        with tarfile.open(original, 'r:gz') as source, tarfile.open(changed, 'w:gz') as target:
            for entry in source.getmembers():
                payload = source.extractfile(entry).read() if entry.isfile() else None
                if entry.name == 'app.py':
                    payload += b'\n# modified after packaging\n'
                    entry.size = len(payload)
                target.addfile(entry, io.BytesIO(payload) if payload is not None else None)
        assert inspect(original, root, skill, env).returncode == 0
        rejected = inspect(changed, root, skill, env)
        assert rejected.returncode != 0 and 'PackagingError' in rejected.stderr


def test_bundled_builder_drift_blocks_packaging():
    with installation() as (root, skill, app, env):
        manifest = skill / 'scripts/sdk-builder/market/appmgr/manifest.py'
        manifest.write_bytes(manifest.read_bytes() + b'\n# drift\n')
        run = invoke(skill / 'scripts/package_app.py', ['--app-dir', app, '--out', root / 'dist'], root, env)
        assert run.returncode != 0 and 'bundled SDK builder hash mismatch' in run.stderr
        assert not list((root / 'dist').glob('*.tar.gz'))


def test_imported_api_reference_and_builder_match_recorded_snapshots():
    api = json.loads((SKILL / 'scripts/api-reference-lock.json').read_text())
    builder = json.loads((SKILL / 'scripts/sdk-contract-lock.json').read_text())
    assert api['source_revision'] == builder['commit']
    for relative, digest in api['generated_files'].items():
        assert hashlib.sha256((SKILL / 'references/api' / relative).read_bytes()).hexdigest() == digest, relative
    for relative, digest in builder['bundled_files'].items():
        assert hashlib.sha256((SKILL / 'scripts/sdk-builder' / relative).read_bytes()).hexdigest() == digest, relative
