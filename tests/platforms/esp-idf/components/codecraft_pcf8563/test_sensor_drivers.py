"""Run the native scenarios owned by this Target or component."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from host_sensor import run_cases


def test_pcf8563_protocol_failures_and_calendar_contract():
    run_cases('pcf8563',['before-init','invalid-create','1','3','4','init',
                       'voltage-low','corrupt','invalid-args','timeout','delete-failure'])
