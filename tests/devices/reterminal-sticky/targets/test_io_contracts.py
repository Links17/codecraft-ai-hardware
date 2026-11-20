"""Run the native scenarios owned by this Target or component."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'tests/platforms/esp-idf'))
from host_io import run_cases


def test_sticky_epaper_ownership_gray4_and_full_recovery():
    cases=[[name] for name in ('0','unready','borrowed','null','full-null','concurrent-init','concurrent-update','gray','recover-full')]
    cases += [[str(n)] for n in range(1,8)]
    cases += [['runtime',str(n)] for n in range(10,16)]
    cases += [['gray',str(n)] for n in range(10,16)]
    cases += [[mode,str(n)] for mode in ('busy','gray-busy') for n in range(1,5)]
    run_cases('reterminal-sticky','epaper',cases)
