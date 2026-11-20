"""Run the native scenarios owned by this Target or component."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'tests/platforms/esp-idf'))
from host_io import run_cases


def test_xiao_microphone_lifetime_timeout_and_partial_reads():
    cases=[['0'],['rate'],['invalid-read'],['timeout-units'],['partial-read']]
    cases += [[str(n)] for n in (3,4,5)]+[['4','8']]
    cases += [['deinit',str(n)] for n in (7,8)]+[['disable-applied','7']]
    run_cases('xiao-s3-147','microphone',cases)



def test_xiao_display_readiness_rollback_and_dma_buffer_lifetime():
    cases=[[name] for name in ('0','unready','borrowed','drain','wait-error','draw-error','example')]
    cases += [[str(n)] for n in range(1,31)]
    cases += [['30',str(n)] for n in (40,41)]
    run_cases('xiao-s3-147','display',cases)
    # GPIO/register/delay trace captured from the retained pre-fix driver.
    assert run_cases('xiao-s3-147','display',[['wire']])==['17490358664246970766\n']
