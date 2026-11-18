"""Run the native scenarios owned by this Target or component."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tests'))
from host_sensor import run_cases


def test_sht4x_protocol_failures_and_concurrent_reads():
    run_cases('sht4x',['before-init','invalid-create','1','2','3','4','init',
                     'invalid-read','crc-temperature','crc-humidity','timeout-tx',
                     'timeout-rx','timeout-lock','limits','concurrent','delete-failure'])
