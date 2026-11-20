"""Run the native scenarios owned by this Target or component."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'tests/platforms/esp-idf'))
from host_sensor import run_cases


def test_e100x_sensor_bindings_preserve_configuration_and_lifetime():
    for board in ('reterminal-e1002',):
        run_cases('sht4x',['before-init','init','concurrent','crc-temperature','crc-humidity','timeout-rx'],board)
        run_cases('pcf8563',['before-init','init','voltage-low','corrupt','invalid-args','timeout'],board)
