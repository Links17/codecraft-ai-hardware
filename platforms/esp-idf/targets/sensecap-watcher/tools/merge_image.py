#!/usr/bin/env python3
"""Create one Watcher image from a validated native build directory; never flash."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

# Watcher target.json/sdkconfig.defaults and partitions.csv use a single app:
# ESP32-S3 bootloader 0x0, partition table 0x8000, factory app 0x10000.
EXPECTED_OFFSETS = {0x0, 0x8000, 0x10000}
OUTPUT_NAME = 'merged-binary.bin'


def layout(build):
    build = Path(build).resolve()
    data = json.loads((build/'flasher_args.json').read_text())
    if data['extra_esptool_args']['chip'] != 'esp32s3':
        raise ValueError('Watcher image requires chip esp32s3')
    files = data['flash_files']
    if not isinstance(files, dict) or len(files) != 3:
        raise ValueError('Watcher image requires exactly three build outputs')
    parts = []
    for offset, relative in files.items():
        address = int(offset, 16)
        path = (build/relative).resolve()
        if not path.is_relative_to(build) or not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f'Missing, empty or escaping build output: {relative}')
        parts.append((address, path))
    parts.sort()
    if {offset for offset, _ in parts} != EXPECTED_OFFSETS:
        raise ValueError('Watcher image requires flash offsets 0x0, 0x8000, and 0x10000')
    for (offset, path), (next_offset, _) in zip(parts, parts[1:]):
        if offset + path.stat().st_size > next_offset:
            raise ValueError('Overlapping flash outputs')
    settings = data['flash_settings']
    if set(settings) != {'flash_mode', 'flash_freq', 'flash_size'}:
        raise ValueError('Incomplete native flash settings')
    return build, parts, settings


def merge(build, output=None, check_only=False):
    build, parts, settings = layout(build)
    output = Path(output).resolve() if output else build/OUTPUT_NAME
    if output.exists():
        raise ValueError(f'Output already exists: {output}')
    if check_only:
        return {'status': 'passed', 'operation': 'layout-check', 'output': str(output)}
    output.parent.mkdir(parents=True, exist_ok=True)
    # Use the checked flasher_args.json entries, not a second flash_args manifest.
    # Keep incomplete output private until esptool succeeds and size is checked.
    with tempfile.TemporaryDirectory(prefix='watcher-image-', dir=output.parent) as directory:
        staged = Path(directory)/OUTPUT_NAME
        argv = [sys.executable, '-m', 'esptool', '--chip', 'esp32s3', 'merge-bin', '-o', str(staged)]
        for name, value in sorted(settings.items()):
            argv += ['--'+name.replace('_', '-'), str(value)]
        for offset, path in parts:
            argv += [hex(offset), str(path)]
        subprocess.run(argv, cwd=build, check=True, stdout=sys.stderr)
        expected = max(offset+path.stat().st_size for offset, path in parts)
        if not staged.is_file() or staged.stat().st_size != expected:
            raise ValueError('Merged image size does not match the checked build outputs')
        # Same-directory hard linking publishes complete bytes atomically and
        # refuses to replace a destination created meanwhile.
        output.hardlink_to(staged)
    return {'status': 'passed', 'operation': 'merge', 'output': str(output), 'bytes': expected, 'flashed': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path, help='Native IDF build directory containing flasher_args.json')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args(argv)
    try:
        print(json.dumps(merge(args.build, args.output, args.check_only)))
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(json.dumps({'status': 'failed', 'reason': str(error)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
