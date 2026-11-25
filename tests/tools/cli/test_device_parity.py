"""Compare the new parser against repository conformance data, without hardware."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/codecraft'))
from model import Catalog


def test_rust_device_parser_preserves_all_typed_values_and_procedure_order():
    suffix = '.exe' if os.name == 'nt' else ''
    candidates = [os.environ.get('CODECRAFT_TEST_CLI')]
    candidates += [str(ROOT / path / ('codecraft' + suffix)) for path in
                   ('.codecraft/bin', '.codecraft/cargo/debug', '.codecraft/cargo/release')]
    candidates.append(shutil.which('codecraft'))
    executable = next((p for p in candidates if p and Path(p).is_file()), None)
    if not executable:
        raise unittest.SkipTest('Install/build the Rust CLI or set CODECRAFT_TEST_CLI for parser parity')
    run = subprocess.run([executable, '--root', str(ROOT), 'catalog'],
                         capture_output=True, text=True, timeout=60)
    assert run.returncode == 0, run.stdout + run.stderr
    data = json.loads(run.stdout)['data']
    assert data['schema_version'] == 4
    assert data['devices'] == Catalog(ROOT).devices
