"""Execute native display/audio contracts at their owning Target boundaries."""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
TESTS = Path(__file__).resolve().parent


def run_cases(board, suite, cases, original=None, variant=None):
    compiler=shutil.which('cc')
    assert compiler, 'Native I/O contract tests require a C compiler (cc)'
    target=ROOT/'devices'/board/'targets'
    tests=ROOT/'tests/devices'/board/'targets'
    sources={'epaper':'bsp_epd.c','microphone':'bsp_mic.c','display':'bsp_display.c','expander':'bsp_io_expander.c','audio':'bsp_audio.c'}
    source=original or target/'bsp/src'/sources[suite]
    stubs={'epaper':'epd','microphone':'pdm','display':'lcd','expander':'lcd','audio':'respeaker'}[suite]
    flags=['-pthread','-Dfree=test_free'] if suite=='epaper' else []
    if suite in ('expander','audio'): flags+=['-pthread']
    extra=[]
    if original: flags+=['-DTEST_ORIGINAL']
    if board=='sensecap-indicator' and suite=='display':
        assert variant in (None, 'gx', 'dx')
        flags += ['-DCODECRAFT_DISPLAY_GX='+('0' if variant=='dx' else '1')]
    if suite=='display' and board=='xiao-s3-147':
        extra=[str(target/'examples/display_hello/main/main.c')]
    outputs=[]
    with tempfile.TemporaryDirectory(prefix='codecraft-io-contract-') as folder:
        executable=str(Path(folder)/'io-test')
        run=subprocess.run([compiler,'-std=c11','-Wall','-Wextra','-Werror',*flags,
            '-I'+str(TESTS/'stubs'/stubs),'-I'+str(target/'bsp/include'),
            str(source),str(tests/suite/'failure_cases.c'),*extra,'-o',executable],capture_output=True,text=True)
        assert run.returncode==0, run.stdout+run.stderr
        for args in cases:
            run=subprocess.run([executable,*args],capture_output=True,text=True,timeout=10)
            assert run.returncode==0, f'{board}/{args}: {run.stdout}{run.stderr}'
            outputs.append(run.stdout)
    return outputs
