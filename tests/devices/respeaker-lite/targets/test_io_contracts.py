"""Run the native scenarios owned by this Target or component."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'tests/platforms/esp-idf'))
from host_io import run_cases


def test_respeaker_audio_lifetime_duplex_controls_and_timeouts():
    cases=[[name] for name in ('0','unready','timeout-units','duplex','concurrent-control','partial','stop-failure','stop-applied','controls')]
    cases += [[str(n)] for n in range(1,21)]
    cases += [['20',str(n)] for n in range(21,27)]
    run_cases('respeaker-lite','audio',cases)
