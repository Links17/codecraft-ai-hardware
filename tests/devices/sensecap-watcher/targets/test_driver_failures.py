"""Run selected native BSP logic with narrow host doubles, without hardware."""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[4]


def run_cases(source, suite_name, cases):
    target = ROOT/'devices/sensecap-watcher/targets'
    tests = Path(__file__).resolve().parent
    suite = tests/suite_name
    stubs = tests/'stubs'
    compiler = shutil.which('cc')
    assert compiler, 'Native BSP host tests require a C compiler (cc)'
    with tempfile.TemporaryDirectory(prefix='codecraft-display-host-') as folder:
        executable = str(Path(folder)/'display-test')
        flags = []
        if source=='bsp_io_expander.c': flags += ['-pthread']
        if source=='bsp_sdcard.c': flags += ['-Dmalloc=test_malloc','-Dfree=test_free']
        run = subprocess.run([compiler,'-std=c11','-Wall','-Wextra','-Werror',*flags,
                              '-I'+str(stubs),'-I'+str(target/'bsp/include'),
                              '-I'+str(ROOT/'platforms/esp-idf/components/sscma_client'),
                              str(target/'bsp/src'/source),str(suite/'failure_cases.c'),
                              '-o',executable],capture_output=True,text=True)
        assert run.returncode==0, run.stdout+run.stderr
        for args in cases:
            run=subprocess.run([executable,*args],capture_output=True,text=True,timeout=10)
            assert run.returncode==0, f'{args}: {run.stdout}{run.stderr}'


def test_watcher_display_initialization_failure_and_retry():
    cases=[['retry'],['0']]+[[str(step)] for step in range(1,15)]
    cases += [['14',str(step)] for step in range(15,22)]
    run_cases('bsp_display.c','display',cases)


def test_watcher_expander_initialization_failure_and_retry():
    cases=[['retry'],['0']]+[[str(step)] for step in range(1,8)]
    cases += [['7',str(step)] for step in (8,9)]
    run_cases('bsp_io_expander.c','expander',cases)


def test_watcher_expander_write_error_resynchronizes_shadows():
    run_cases('bsp_io_expander.c','expander',
              [[name,str(applied)] for name in ('shadow-output','shadow-config') for applied in (0,1)])


def test_watcher_expander_concurrent_operations_and_mutex_failure():
    run_cases('bsp_io_expander.c','expander',[['concurrent'],['lock-timeout'],['10']])


def test_watcher_touch_device_ownership_boot_timeout_and_retry():
    cases=[['timeout'],['late-ready'],['0']]+[[str(step)] for step in range(1,9)]
    cases += [['8',str(step)] for step in (9,10,11)]
    run_cases('bsp_touch.c','touch',cases)


def test_watcher_knob_initialization_failure_and_retry():
    cases=[['retry'],['0']]+[[str(step)] for step in range(1,14)]
    cases += [['13',str(step)] for step in range(14,19)]
    run_cases('bsp_knob.c','knob',cases)


def test_watcher_battery_initialization_failure_and_retry():
    cases=[['retry'],['0'],['read-errors']]+[[str(step)] for step in range(1,8)]
    cases += [['7','8']]
    run_cases('bsp_battery.c','battery',cases)


def test_watcher_audio_initialization_failure_and_retry():
    cases=[['retry-ready'],['retry-channel'],['0'],['variant-e'],['controls']]
    cases += [[str(step)] for step in range(1,22) if step!=15]
    cases += [['21',str(step)] for step in range(22,32)]
    cases += [[str(step),'0','variant-e'] for step in (16,17,18)]
    run_cases('bsp_audio.c','audio',cases)


def test_watcher_storage_path_ownership_and_failure():
    cases=[[str(step)] for step in range(9)]
    cases += [[name] for name in ('wrong-path','unmount-late','unmount-early','absent','borrowed-bus')]
    run_cases('bsp_sdcard.c','storage',cases)


def test_watcher_camera_board_initialization_failure_and_retry():
    run_cases('bsp_camera.c','camera',[[str(step)] for step in range(10)]+[['registered']])
