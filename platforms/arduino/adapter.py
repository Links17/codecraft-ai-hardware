"""Native arduino adapter. No other platform owns these operations."""
from pathlib import Path
import ast
import json
import os
import re
import shutil
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'skills/_shared'))
from io_utils import digest, object_digest, read_json, require, result, safe_path
from runtime import command, main, selected


def cases(root, target, example=None):
    return [target['id']+'/'+name for name in selected(target, example)]


def build(root, target, example=None):
    path = safe_path(root, target['path'])
    examples = selected(target, example)
    checks = []
    require('fqbn' in target['toolchain'] and 'core_version' in target['toolchain'], 'Arduino target needs pinned fqbn/core_version')
    if not shutil.which('arduino-cli'):
        return [result(name, 'not_run', 'arduino-cli is not installed.') for name in cases(root, target, example)]
    version=subprocess.run(['arduino-cli','version','--format','json'],capture_output=True,text=True)
    if version.returncode or json.loads(version.stdout).get('VersionString')!=target['toolchain']['version']:
        return [result(name, 'not_run', 'The installed arduino-cli version differs from the Target lock.') for name in cases(root, target, example)]
    cores = subprocess.run(['arduino-cli', 'core', 'list', '--format', 'json'], capture_output=True, text=True)
    if cores.returncode:
        return [result(name, 'not_run', 'Could not inspect installed Arduino cores.') for name in cases(root, target, example)]
    core = ':'.join(target['toolchain']['fqbn'].split(':')[:2])
    installed = json.loads(cores.stdout)
    platforms = installed.get('platforms', []) if isinstance(installed, dict) else installed
    if not any(x.get('id') == core and x.get('installed_version', x.get('installed')) == target['toolchain']['core_version'] for x in platforms):
        return [result(name, 'not_run', f'Required core {core}@{target["toolchain"]["core_version"]} is not installed.') for name in cases(root, target, example)]
    libraries=target['toolchain'].get('libraries',{})
    if libraries:
        inventory=subprocess.run(['arduino-cli','lib','list','--format','json'],capture_output=True,text=True)
        if inventory.returncode:
            return [result(name, 'not_run', 'Could not inspect installed Arduino libraries.') for name in cases(root, target, example)]
        installed={item['library']['name']:item['library']['version'] for item in json.loads(inventory.stdout).get('installed_libraries',[])}
        if any(installed.get(name)!=version for name,version in libraries.items()):
            return [result(name, 'not_run', 'Required pinned Arduino libraries are not installed.') for name in cases(root, target, example)]
    for ex in examples:
        checks.append(command(root, target['id']+'/'+ex, ['arduino-cli', 'compile', '--fqbn', target['toolchain']['fqbn'], str(path/'examples'/ex)], target['toolchain']))
    return checks


def probe(root, target):
    if not shutil.which('arduino-cli'):
        return {'status': 'not_run', 'reason': 'arduino-cli is not installed.'}
    version = json.loads(subprocess.check_output(['arduino-cli', 'version', '--format', 'json'], text=True))['VersionString']
    if version != target['toolchain']['version']:
        return {'status': 'not_run', 'reason': 'Arduino CLI version differs from Target requirement.'}
    return {'status': 'passed', 'cli': version,
            'cores': json.loads(subprocess.check_output(['arduino-cli', 'core', 'list', '--format', 'json'], text=True)),
            'libraries': json.loads(subprocess.check_output(['arduino-cli', 'lib', 'list', '--format', 'json'], text=True))}


def validate_target(root, target):
    tc = target['toolchain']
    require({'fqbn', 'core_version', 'libraries'} <= tc.keys() and isinstance(tc['libraries'], dict), 'Arduino requires FQBN and pinned core/libraries')
    require(all(re.fullmatch(r'\d+\.\d+\.\d+(?:[-+][a-zA-Z0-9.]+)?', version) for version in [tc['version'], tc['core_version'], *tc['libraries'].values()]), 'Unpinned Arduino toolchain')
    for name in target['examples']:
        require(list((root/target['path']/'examples'/name).glob('*.ino')), f'{name}: Arduino sketch required')


if __name__ == '__main__':
    raise SystemExit(main('arduino'))
