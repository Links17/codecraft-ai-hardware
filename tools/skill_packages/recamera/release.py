"""Review one standalone SDK Skill without a cloud contract or hardware catalog."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from graph import SourceGraph
from io_utils import ContractError, digest, object_digest, package_inventory, read_json, require, safe_path, write_json

SKILL = 'codecraft-development-recamera-pysdk'
PACKAGE = 'skills/' + SKILL
RECORD = 'tools/skill_packages/recamera/release.json'
CONFORMANCE = 'tests/skills/' + SKILL


def version(value):
    require(isinstance(value, str) and re.fullmatch(r'\d+\.\d+\.\d+', value),
            'Skill version must be major.minor.patch')
    return tuple(map(int, value.split('.')))


def record(root):
    value = read_json(Path(root) / RECORD)
    require(set(value) == {'schema_version', 'id', 'version', 'source', 'files'}
            and type(value['schema_version']) is int and value['schema_version'] == 1
            and value['id'] == SKILL, 'Invalid SDK Skill release record')
    version(value['version'])
    require(isinstance(value['files'], dict) and 'SKILL.md' in value['files'], 'Missing SDK package inventory')
    source = value['source']
    require(isinstance(source, dict) and set(source) == {
        'repository', 'commit', 'path', 'import_manifest', 'import_sha256'
    } and source.get('import_manifest') == 'docs/recamera-skill-import.json',
            'Missing immutable SDK import identity')
    require(digest(safe_path(root, source['import_manifest'])) == source.get('import_sha256'),
            'Original SDK import provenance changed')
    imported = read_json(safe_path(root, source['import_manifest']))
    require(imported.get('installed_skill') == SKILL and all(
        source[field] == imported.get('source_' + field)
        for field in ('repository', 'commit', 'path')
    ), 'SDK release metadata differs from its immutable import')
    return value


def check_package(root):
    previous = record(root)
    require(package_inventory(Path(root) / PACKAGE) == previous['files'],
            'SDK Skill differs from its reviewed release; use the candidate workflow')
    return {'status': 'passed', 'skill': SKILL, 'version': previous['version']}


def inputs(root):
    previous = record(root)
    inventory = package_inventory(Path(root) / PACKAGE)
    graph = SourceGraph(root)
    graph.resolve(['tools/codecraft/resource.json', 'tools/codecraft/skill_contracts.py',
                   'tools/skill_packages/release.py',
                   'tools/skill_packages/recamera', 'docs/development/recamera-sdk-maintenance.md',
                   previous['source']['import_manifest'], CONFORMANCE,
                   *[PACKAGE + '/' + name for name in inventory]])
    return graph.snapshot(), inventory, previous


def copy_files(source, destination, files):
    for relative, checksum in sorted(files.items()):
        target = safe_path(destination, relative, exists=False)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(safe_path(source, relative).read_bytes())
        require(digest(target) == checksum, 'A reviewed file changed while being copied: ' + relative)


def changes(before, after):
    return [{'path': name, 'before': before.get(name), 'after': after.get(name)}
            for name in sorted(before.keys() | after.keys()) if before.get(name) != after.get(name)]


def proposal(previous, proposed):
    expected = copy.deepcopy(previous)
    expected.update(version=proposed['version'], files=proposed['files'])
    require(expected == proposed, 'Release cannot rewrite the package identity or original provenance')
    diff = changes(previous['files'], proposed['files'])
    require(version(proposed['version']) >= version(previous['version']), 'Skill version cannot decrease')
    require(not diff or version(proposed['version']) > version(previous['version']),
            'Changed package bytes require an explicit higher Skill version')
    return diff


def prepare(root, output, releases=None):
    root = Path(root).resolve(); output = Path(output).expanduser().resolve()
    require(not output.exists() and not output.is_relative_to(root),
            'Candidate output must be a new directory outside the repository')
    releases = {} if releases is None else releases
    require(isinstance(releases, dict) and set(releases) <= {SKILL}, 'Unknown SDK release selection')
    override = releases.get(SKILL, {})
    require(isinstance(override, dict) and set(override) <= {'skill_version'},
            'SDK releases accept only skill_version; API/builder pins are reviewed source files')
    sources, inventory, previous = inputs(root)
    proposed = copy.deepcopy(previous)
    proposed.update(files=inventory, version=override.get('skill_version', previous['version']))
    diff = proposal(previous, proposed)
    output.mkdir(parents=True)
    try:
        copy_files(root / PACKAGE, output / PACKAGE, inventory)
        write_json(output / RECORD, proposed)
        files = {PACKAGE + '/' + name: checksum for name, checksum in inventory.items()}
        files[RECORD] = digest(output / RECORD)
        manifest = {'schema_version': 1, 'kind': 'sdk-skill-candidate', 'skill': SKILL,
                    'sources': sources, 'baseline_files': inventory, 'previous': previous,
                    'proposed': proposed, 'changes': diff, 'files': files}
        write_json(output / 'manifest.json', manifest)
        return {'path': str(output), 'review_sha256': object_digest(manifest), 'changes': diff,
                'repository_changed': False, 'published': False, 'device_verification': 'not_run'}
    except Exception:
        shutil.rmtree(output)
        raise


def inspect(root, candidate, reviewed=None):
    root = Path(root).resolve(); candidate = Path(candidate).resolve()
    require(not candidate.is_relative_to(root), 'Candidate must be outside the repository')
    manifest = read_json(candidate / 'manifest.json')
    require(isinstance(manifest, dict) and set(manifest) == {
        'schema_version', 'kind', 'skill', 'sources', 'baseline_files', 'previous', 'proposed', 'changes', 'files'
    } and type(manifest['schema_version']) is int and manifest['schema_version'] == 1
        and manifest['kind'] == 'sdk-skill-candidate' and manifest['skill'] == SKILL, 'Invalid SDK candidate')
    checksum = object_digest(manifest)
    if reviewed is not None:
        require(reviewed == checksum, 'Candidate differs from the explicitly reviewed digest')
    require(package_inventory(candidate) == {**manifest['files'], 'manifest.json': digest(candidate / 'manifest.json')},
            'Candidate files drifted')
    sources, inventory, previous = inputs(root)
    require(sources == manifest['sources'] and inventory == manifest['baseline_files']
            and previous == manifest['previous'], 'Maintained sources changed after candidate preparation')
    proposed = manifest['proposed']
    require(proposal(previous, proposed) == manifest['changes'], 'Candidate change summary differs from its bytes')
    require(read_json(candidate / RECORD) == proposed, 'Candidate release record differs')
    expected = {PACKAGE + '/' + name: checksum for name, checksum in proposed['files'].items()}
    expected[RECORD] = digest(candidate / RECORD)
    require(manifest['files'] == expected and package_inventory(candidate / PACKAGE) == proposed['files'],
            'Candidate package differs from its proposed inventory')
    return manifest, checksum


def validate(root, candidate, reviewed=None):
    root = Path(root).resolve(); candidate = Path(candidate).resolve()
    manifest, checksum = inspect(root, candidate, reviewed)
    with tempfile.TemporaryDirectory(prefix='codecraft-recamera-check-') as folder:
        staged = Path(folder)
        copy_files(root, staged, manifest['sources']['files'])
        shutil.rmtree(staged / PACKAGE)
        copy_files(candidate, staged, manifest['files'])
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        for name in ('PYTHONPATH', 'RECAMERA_SDK_ROOT', 'RECAMERA_EXT_API_ROOT'):
            environment.pop(name, None)
        run = subprocess.run([sys.executable, '-I', '-B', str(staged / 'tools/codecraft/maintenance.py'),
                              'test', '--path', CONFORMANCE], cwd=staged, env=environment,
                             capture_output=True, text=True, timeout=180)
        require(run.returncode == 0, 'SDK candidate offline checks failed: ' + run.stdout + run.stderr)
        payload = json.loads(run.stdout)
        checks = payload.get('data', {}).get('results', [])
        require(payload.get('ok') is True and checks and all(row['status'] == 'passed' for row in checks),
                'SDK candidate checks were incomplete')
        check_package(staged)
    inspect(root, candidate, checksum)
    return {'status': 'passed', 'review_sha256': checksum, 'checks': checks,
            'repository_changed': False, 'published': False, 'device_verification': 'not_run'}


def apply(root, candidate, reviewed):
    root = Path(root).resolve(); candidate = Path(candidate).resolve()
    require(isinstance(reviewed, str) and re.fullmatch(r'[0-9a-f]{64}', reviewed),
            'Apply requires an explicitly reviewed candidate digest')
    lock = root / '.codecraft/skill-release.lock'; lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        handle = lock.open('x')
    except FileExistsError as exc:
        raise ContractError('Another release owns .codecraft/skill-release.lock') from exc
    try:
        with handle:
            handle.write(reviewed + '\n')
        checked = validate(root, candidate, reviewed)
        manifest, _ = inspect(root, candidate, reviewed)
        previous_bytes = (root / RECORD).read_bytes()
        stage = Path(tempfile.mkdtemp(prefix='.release-recamera-', dir=root / 'skills'))
        destination = root / PACKAGE; backup = stage / 'previous'
        moved = False; complete = False
        changed = []
        try:
            try:
                if manifest['baseline_files'] != manifest['proposed']['files']:
                    ready = stage / 'next'
                    copy_files(candidate / PACKAGE, ready, manifest['proposed']['files'])
                    destination.rename(backup); moved = True
                    ready.rename(destination); changed.append(PACKAGE)
                if manifest['previous'] != manifest['proposed']:
                    copy_files(candidate, stage, {RECORD: manifest['files'][RECORD]})
                    os.replace(stage / RECORD, root / RECORD); changed.append(RECORD)
                check_package(root)
            except Exception:
                try:
                    (root / RECORD).write_bytes(previous_bytes)
                    if moved:
                        if destination.exists():
                            shutil.rmtree(destination)
                        backup.rename(destination)
                except Exception as exc:
                    raise ContractError(f'Rollback incomplete; recovery files retained at {stage}') from exc
                complete = True
                raise
            complete = True
        finally:
            if complete:
                shutil.rmtree(stage)
        return {**checked, 'repository_changed': bool(changed), 'changed': changed}
    finally:
        lock.unlink()


def dispatch(root, args):
    if args.command == 'prepare':
        return prepare(root, args.output, read_json(args.versions) if args.versions else None)
    if args.command == 'check':
        return validate(root, args.candidate)
    return apply(root, args.candidate, args.review_sha256)
