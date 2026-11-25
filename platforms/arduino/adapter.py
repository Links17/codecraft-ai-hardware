"""Native Arduino CLI operations with exact, source-sensitive toolchain locks."""
from pathlib import Path
import json
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools/codecraft'))
from io_utils import ContractError, digest, object_digest, require, result, safe_path
from runtime import command, main, selected


def validate_evidence_toolchain(target, actual, case=None):
    tc = target['toolchain']
    require(actual.get('cli') == tc['version'] and actual.get('fqbn') == tc['fqbn']
            and isinstance(actual.get('core'), dict)
            and actual['core'].get('version') == tc['core_version'],
            'Evidence toolchain differs from declared Arduino CLI/core/board')
    libraries = actual.get('libraries', {})
    require(isinstance(libraries, dict) and all(
        isinstance(libraries.get(name), dict) and libraries[name].get('version') == version
        for name, version in tc['libraries'].items()),
        'Evidence toolchain differs from declared Arduino libraries')
    if case is not None:
        require(case.get('toolchain') == actual,
                'Build case toolchain differs from its recorded probe')


def cases(root, target, example=None):
    return [target['id']+'/'+name for name in selected(target, example)]


def inspect_json(*arguments):
    run = subprocess.run(['arduino-cli', *arguments, '--format', 'json'], capture_output=True, text=True, timeout=60)
    require(run.returncode == 0, 'Arduino inspection failed: '+run.stderr.strip())
    data = json.loads(run.stdout)
    require(isinstance(data, dict), 'Arduino CLI must return an object')
    return data


def tree_fingerprint(path):
    path = Path(path).resolve()
    require(path.is_dir(), f'Missing Arduino dependency: {path}')
    return object_digest({str(p.relative_to(path)): digest(p) for p in sorted(path.rglob('*'))
                          if p.is_file() and not {'.git', '__pycache__'} & set(p.relative_to(path).parts)
                          and p.name != '.DS_Store'})


def probe(root, target):
    executable = shutil.which('arduino-cli')
    if not executable:
        return {'status': 'not_run', 'reason': 'arduino-cli is not installed.'}
    tc = target['toolchain']
    try:
        version = inspect_json('version')['VersionString']
        require(version == tc['version'], 'Arduino CLI version differs from Target requirement.')
        core_id = ':'.join(tc['fqbn'].split(':')[:2])
        cores = inspect_json('core', 'list')['platforms']
        require(any(item['id'] == core_id and item.get('installed_version') == tc['core_version'] for item in cores),
                f'Required core {core_id}@{tc["core_version"]} is not installed.')
        details = inspect_json('board', 'details', '--fqbn', tc['fqbn'])
        require(details['fqbn'] == tc['fqbn'] and details['version'] == tc['core_version'], 'Arduino board/core mismatch')
        properties = dict(item.split('=', 1) for item in details['build_properties'])
        core_path = Path(properties['runtime.platform.path']).resolve()
        installed = {item['library']['name']: item['library'] for item in inspect_json('lib', 'list')['installed_libraries']}
        libraries = {}
        for name, required in sorted(tc['libraries'].items()):
            library = installed.get(name, {})
            require(library.get('version') == required, f'Required library {name}@{required} is not installed.')
            path = Path(library['install_dir']).resolve()
            libraries[name] = {'version': required, 'path': str(path), 'source_digest': tree_fingerprint(path)}
        bundled = {}
        for directory in tc['bundled_libraries']:
            path = core_path/'libraries'/directory
            require(path.is_dir(), f'Missing bundled library: {directory}')
            bundled[directory] = str(path)
        native_tools = {}
        for item in details['tools_dependencies']:
            name, version = item['name'], item['version']
            path = properties[f'runtime.tools.{name}-{version}.path']
            native_tools[f'{item["packager"]}/{name}'] = {'version': version, 'source_digest': tree_fingerprint(path)}
        return {'status': 'passed', 'cli': tc['version'], 'cli_sha256': digest(executable), 'fqbn': tc['fqbn'],
                'core': {'id': core_id, 'version': tc['core_version'], 'path': str(core_path), 'source_digest': tree_fingerprint(core_path)},
                'libraries': libraries, 'bundled_libraries': bundled, 'tools': native_tools}
    except (ContractError, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        return {'status': 'not_run', 'reason': str(error)}


def build(root, target, example=None):
    actual = probe(root, target)
    if actual['status'] != 'passed':
        return [result(name, 'not_run', actual['reason'], toolchain=actual) for name in cases(root, target, example)]
    checks = []
    for name in selected(target, example):
        output = root/'.codecraft/builds'/target['platform']/target['device']/name
        output.mkdir(parents=True, exist_ok=True)
        argv = ['arduino-cli', 'compile', '--fqbn', target['toolchain']['fqbn'], '--build-path', str(output), '--jobs', '4']
        # Explicit paths give the pinned library precedence over unrelated user libraries.
        for path in [*(item['path'] for item in actual['libraries'].values()), *actual['bundled_libraries'].values()]:
            argv += ['--library', path]
        argv.append(str(safe_path(root, target['path'])/'examples'/name))
        checks.append(command(root, target['id']+'/'+name, argv, actual))
    return checks


def validate_target(root, target):
    tc = target['toolchain']
    require({'fqbn', 'core_version', 'libraries', 'board_manager_urls', 'bundled_libraries'} <= tc.keys(), 'Arduino requires FQBN, core, libraries and board-manager sources')
    require(re.fullmatch(r'[\w-]+:[\w-]+:[\w-]+', tc['fqbn']), 'Invalid Arduino FQBN')
    require(isinstance(tc['libraries'], dict) and isinstance(tc['bundled_libraries'], list), 'Invalid Arduino library declarations')
    require(all(isinstance(name, str) and name.strip() for name in tc['libraries']), 'Invalid Arduino library name')
    require(all(re.fullmatch(r'[\w-]+', name) for name in tc['bundled_libraries']), 'Invalid bundled library directory')
    require(isinstance(tc['board_manager_urls'], list) and all(url.startswith('https://') for url in tc['board_manager_urls']), 'Invalid board-manager URLs')
    require(all(isinstance(version, str) and re.fullmatch(r'\d+\.\d+\.\d+(?:[-+][a-zA-Z0-9.]+)?', version) for version in [tc['version'], tc['core_version'], *tc['libraries'].values()]), 'Unpinned Arduino toolchain')
    for name in target['examples']:
        sketch = f'{target["path"]}/examples/{name}/{name}.ino'
        safe_path(root, sketch)
        require(f'{target["path"]}/examples/{name}' in target['example_inputs'][name] or sketch in target['example_inputs'][name], f'{name}: Arduino sketch must belong to its example source closure')


if __name__ == '__main__':
    raise SystemExit(main('arduino'))
