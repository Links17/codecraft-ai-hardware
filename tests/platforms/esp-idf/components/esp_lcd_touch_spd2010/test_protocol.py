"""Execute the actual SPD2010 driver with bounded raw I2C packets and faults."""
from pathlib import Path
import shutil
import subprocess
import tempfile


def test_native_i2c_frames_errors_and_borrowed_device_lifetime():
    tests=Path(__file__).resolve().parent
    component=Path(__file__).resolve().parents[5]/'platforms/esp-idf/components/esp_lcd_touch_spd2010'
    compiler=shutil.which('cc');assert compiler
    with tempfile.TemporaryDirectory() as folder:
        executable=Path(folder)/'protocol'
        run=subprocess.run([compiler,'-std=c11','-Wall','-Wextra','-Werror','-Dcalloc=test_calloc','-Dfree=test_free',
                            '-I'+str(tests/'stubs'),'-I'+str(component/'include'),
                            str(component/'esp_lcd_touch_spd2010.c'),str(tests/'protocol_cases.c'),'-o',str(executable)],capture_output=True,text=True)
        assert run.returncode==0,run.stdout+run.stderr
        for case in ('invalid','alloc','init-write','init-read','success','poll-empty','gesture','mixed-gesture','wire-error','oversize',
                     'short-point','short-gesture','unaligned','remain-oversize','remain-empty','chunk-timeout','bad-status'):
            run=subprocess.run([str(executable),case],capture_output=True,text=True,timeout=5)
            assert run.returncode==0,case+': '+run.stdout+run.stderr
