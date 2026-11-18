"""Execute shared chip protocols and native board bindings with narrow SDK doubles."""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
PLATFORM = ROOT/'platforms/esp-idf'


def run_cases(chip, cases, board=None, original=None):
    compiler = shutil.which('cc')
    assert compiler, 'Sensor host tests require a C compiler (cc)'
    component = PLATFORM/'components'/('codecraft_'+chip)
    stubs = PLATFORM/'tests/stubs'
    includes = [stubs, component/'include']
    sources = [component/'src'/('codecraft_'+chip+'.c')]
    flags = []
    if board:
        bsp = PLATFORM/'targets'/board/'bsp'
        includes += [bsp/'include', bsp/'src']
        name = 'bsp_sht4x.c' if chip=='sht4x' else 'bsp_rtc.c'
        sources += [original or bsp/'src'/name]
        flags.append('-DTEST_BSP')
        if board=='reterminal-sticky': flags.append('-DTEST_STICKY')
    if original:
        sources = [original]
    with tempfile.TemporaryDirectory(prefix='codecraft-sensor-host-') as folder:
        executable = str(Path(folder)/'sensor-test')
        command = [compiler,'-std=c11','-Wall','-Wextra','-Werror','-pthread',
                   '-Dcalloc=test_calloc','-Dfree=test_free',*flags,
                   *['-I'+str(p) for p in includes],*[str(p) for p in sources],
                   str(component/'tests/failure_cases.c'),str(stubs/'sensor_doubles.c'),'-lm','-o',executable]
        run = subprocess.run(command,capture_output=True,text=True)
        assert run.returncode==0, run.stdout+run.stderr
        for case in cases:
            run = subprocess.run([executable,case],capture_output=True,text=True,timeout=10)
            assert run.returncode==0, f'{chip}/{board}/{case}: {run.stdout}{run.stderr}'
