"""Run the native scenarios owned by this Target or component."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tests'))
from host_io import run_cases


def test_e100x_microphone_lifetime_timeout_and_partial_reads():
    cases=[['0'],['rate'],['invalid-read'],['timeout-units'],['partial-read']]
    cases += [[str(n)] for n in range(1,6)]
    cases += [['4','8'],['4','9'],['2','9']]
    cases += [['deinit',str(n)] for n in (7,8,9)]+[['disable-applied','7']]
    for board in ('reterminal-e1001',):
        run_cases(board,'microphone',cases)



def test_e100x_epaper_ownership_busy_errors_and_retry():
    cases=[[name] for name in ('0','unready','borrowed','null','full-null','concurrent-init','concurrent-update')]
    cases += [[str(n)] for n in (1,2,4,5,6,7)]
    cases += [['runtime',str(n)] for n in (11,12,13,14,15)]
    for board,waits in (('reterminal-e1001',4),):
        run_cases(board,'epaper',cases+[['busy',str(n)] for n in range(1,waits+1)])
