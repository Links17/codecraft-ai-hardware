"""Execute shared camera ownership and lifecycle C code with narrow doubles."""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[5]
COMPONENT = ROOT/'platforms/esp-idf/components/sscma_client'


def run_cases(fixture, cases, *, pm=True):
    compiler=shutil.which('cc')
    assert compiler, 'Camera host tests require a C compiler (cc)'
    sources=[COMPONENT/'camera.c',COMPONENT/'tests'/fixture]
    flags=['-pthread']
    if fixture=='backend_cases.c':
        sources.append(COMPONENT/'camera_sscma.c')
        flags += ['-Dfree=test_free',f'-DCONFIG_PM_ENABLE={int(pm)}']
    with tempfile.TemporaryDirectory(prefix='codecraft-camera-host-') as folder:
        executable=str(Path(folder)/'camera-test')
        run=subprocess.run([compiler,'-std=c11','-Wall','-Wextra','-Werror',*flags,
            '-I'+str(COMPONENT/'tests/stubs'),'-I'+str(COMPONENT),
            *map(str,sources),'-o',executable],capture_output=True,text=True)
        assert run.returncode==0, run.stdout+run.stderr
        for args in cases:
            run=subprocess.run([executable,*args],capture_output=True,text=True,timeout=10)
            assert run.returncode==0, f'{args}, pm={pm}: {run.stdout}{run.stderr}'


def test_camera_frame_ownership_and_control_failures():
    names=('success','missing','invalid-driver','busy-frame','release','replace','null',
           'init-failure','capture-failure','invalid-frame','stream-failure','stream','concurrent')
    run_cases('core_cases.c',[[name] for name in names])


def test_sscma_resource_power_and_stream_failures():
    cases=[['invalid'],['configure-twice'],['0']]+[[str(n)] for n in (1,2,3,4,7,8,9,10,11,12,13,14,15,16,17,18,19,20,24)]
    cases += [['4',str(n)] for n in (5,6)]
    cases += [['stream'],['stream-slow']]+[['stream',str(n)] for n in (14,15,21,22)]
    run_cases('backend_cases.c',cases)


def test_sscma_lifecycle_without_power_management():
    cases=[['0'],['1'],['2'],['4'],['4','6'],['8'],['9'],['12'],['13'],['18'],['19'],['stream'],['stream','22']]
    run_cases('backend_cases.c',cases,pm=False)
