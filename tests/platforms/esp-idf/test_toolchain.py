"""Release identity is shared by build preflight, probes and offline evidence."""
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools/codecraft'))
from model import Catalog
from runtime import load_adapter
from io_utils import ContractError


def test_release_identity_and_build_probe_agree():
    c = Catalog(ROOT)
    target = c.target('esp-idf/reterminal-e1001')
    adapter = load_adapter(ROOT, c.platforms['esp-idf'])
    required = target['toolchain']['version']
    for suffix in ('', '-dirty', '-rc1', '.1', '-99-gabcdef', '-rc1-dirty'):
        actual = 'ESP-IDF v'+required+suffix
        accepted = suffix in ('', '-dirty')
        assert adapter.matches_version(actual, required) == accepted
        try:
            adapter.validate_evidence_toolchain(target, {'version':actual})
        except ContractError:
            assert not accepted
        else:
            assert accepted
        if accepted:
            probe_record = {'status':'passed','version':actual,'python':'3.14.6'}
            adapter.validate_evidence_toolchain(target, probe_record, {'toolchain':actual})
            try:
                adapter.validate_evidence_toolchain(target, probe_record, {'toolchain':'3.14.6'})
            except ContractError:
                pass
            else:
                raise AssertionError('ESP-IDF case accepted a Python version as its SDK')
        def run(argv, **kwargs):
            output = actual if argv[0] == 'idf.py' else ('compiler fixture' if argv[0].endswith('gcc') else 'fixture')
            return subprocess.CompletedProcess(argv, 0, output, '')
        with patch.object(adapter.shutil, 'which', return_value='/fixture/tool'), \
             patch.object(adapter.subprocess, 'run', side_effect=run), \
             patch.dict(adapter.os.environ, {'IDF_PATH':'/fixture/sdk'}), \
             patch.object(adapter, 'command', return_value={'status':'failed','reason':'synthetic build'}) as command:
            probe = adapter.probe(ROOT, target)
            checks = adapter.build(ROOT, target, target['examples'][0])
            assert (probe['status'] == 'passed') == accepted
            assert command.called == accepted
            if not accepted:
                assert all(item['status'] == 'not_run' for item in checks)
