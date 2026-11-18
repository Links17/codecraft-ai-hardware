"""Native linux adapter. No other platform owns these operations."""
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
    return [target['id']+'/'+name for name in selected(target, example)] + [target['id']+'/overlay/'+p.stem for p in sorted((root/target['path']/'overlays').glob('*.dts'))]


def build(root, target, example=None):
    path = safe_path(root, target['path'])
    examples = selected(target, example)
    checks = []
    for ex in examples:
        try:
            ast.parse((path/'demos'/f'{ex}.py').read_text())
            checks.append(result(target['id']+'/'+ex, 'passed', 'Python syntax checked; device behavior not executed.', toolchain=sys.version.split()[0]))
        except (SyntaxError, OSError) as exc:
            checks.append(result(target['id']+'/'+ex, 'failed', str(exc)))
    dtc_version = subprocess.run(['dtc','--version'],capture_output=True,text=True).stdout.strip() if shutil.which('dtc') else 'unavailable'
    for overlay in path.glob('overlays/*.dts'):
        output = root/'.codecraft/builds'/target['device']/(overlay.stem+'.dtbo')
        output.parent.mkdir(parents=True, exist_ok=True)
        checks.append(command(root, target['id']+'/overlay/'+overlay.stem, ['dtc', '-@', '-I', 'dts', '-O', 'dtb', '-o', str(output), str(overlay)], dtc_version))
    return checks


def probe(root, target):
    if not shutil.which('dtc'):
        return {'status': 'not_run', 'reason': 'dtc is not installed.'}
    run = subprocess.run(['dtc', '--version'], capture_output=True, text=True)
    require(run.returncode == 0, 'Cannot inspect dtc version')
    return {'status': 'passed', 'python': sys.version.split()[0], 'dtc': run.stdout.strip(), 'scope': 'host syntax and overlay compilation; device OS/kernel not verified'}


def validate_target(root, target):
    path = root/target['path']
    for name in target['examples']:
        ast.parse((path/'demos'/f'{name}.py').read_text())
    require(list((path/'overlays').glob('*.dts')), 'Linux overlay source required')
    require(target['toolchain'].get('runtime_requirements'), 'Linux runtime prerequisites must be explicit')


if __name__ == '__main__':
    raise SystemExit(main('linux'))
