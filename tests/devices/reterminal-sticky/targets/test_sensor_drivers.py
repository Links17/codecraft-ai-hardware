"""Run the native scenarios owned by this Target or component."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'tests/platforms/esp-idf'))
from host_sensor import run_cases


def test_sticky_sensor_binding_preserves_i2c1_and_serializes_reads():
    run_cases('sht4x',['before-init','init','concurrent','crc-temperature','crc-humidity',
                     'timeout-rx','timeout-tx','timeout-lock','limits','invalid-read',
                     '1','2','3','4','bus-failure'],'reterminal-sticky')
