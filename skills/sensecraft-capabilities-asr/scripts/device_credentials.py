#!/usr/bin/env python3
"""Workstation onboarding helpers. Never create devices or print credentials."""
import argparse
import sys
import json
from pathlib import Path
import re

# Keep the installed skill directory free of Python bytecode caches.
sys.dont_write_bytecode = True

from device_api import DeviceAPI, SkillError, decode_json, new_output, read_bytes, run


def import_cli_credentials(source, output):
    data = decode_json(read_bytes(source, 16384))
    eui, key = data.get('eui'), data.get('device_key')
    if (not isinstance(eui, str) or not re.fullmatch(r'[0-9a-fA-F]{16}', eui)
            or not isinstance(key, str) or not re.fullmatch(r'[0-9a-fA-F]{32}', key)):
        raise SkillError('Expected SenseCraft CLI JSON with eui (16 hex characters) and device_key (32 hex characters). No credentials imported.')
    # Discard account credentials, MQTT tokens, and all unrelated response fields.
    with new_output(output) as out:
        out.write((json.dumps({'eui': eui, 'deviceKey': key}) + '\n').encode())
    print(json.dumps({'file': str(Path(output).expanduser().resolve()), 'format': 'device-credentials'}))


def check_device():
    api = DeviceAPI()
    result = decode_json(api.request('/deviceapi/device-management/v1/device', maximum=16384))
    data = result.get('data')
    if result.get('code') != 200 or not isinstance(data, dict):
        raise SkillError('Device access check failed; an HTTP success alone does not confirm authentication.')
    if not isinstance(data.get('eui'), str) or data['eui'].upper() != api.eui.upper():
        raise SkillError('Device access check returned a different identity.')
    initial = data.get('initial_quota')
    if type(initial) is not int or initial < 0:
        raise SkillError('Device access check returned an invalid profile.')
    print(json.dumps({'authenticated': True, 'identity_matches': True, 'initial_quota': initial,
                      'initial_quota_is_remaining_balance': False}))


def write_curl_config(output):
    api = DeviceAPI()
    # Authorization consists only of the fixed scheme and validated base64 text.
    with new_output(output) as out:
        out.write(('header = "Authorization: ' + api.authorization + '"\n').encode())
    print(json.dumps({'file': str(Path(output).expanduser().resolve()), 'format': 'private-curl-config'}))


def main():
    parser = argparse.ArgumentParser(description='Import existing device credentials, check access, or prepare a private curl configuration. Never creates a device.')
    sub = parser.add_subparsers(dest='command', required=True)
    ingest = sub.add_parser('import', help='Convert an existing private SenseCraft CLI response; no network calls.')
    ingest.add_argument('--input', required=True)
    ingest.add_argument('--output', required=True, help='New private file; existing files are never overwritten.')
    sub.add_parser('check', help='Check device access without invoking a model; first access may initialize its quota allocation.')
    curl = sub.add_parser('curl-config', help='Write a new private header file for native Linux curl; no network calls.')
    curl.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.command == 'import':
        import_cli_credentials(args.input, args.output)
    elif args.command == 'check':
        check_device()
    else:
        write_curl_config(args.output)


if __name__ == '__main__':
    run(main)
