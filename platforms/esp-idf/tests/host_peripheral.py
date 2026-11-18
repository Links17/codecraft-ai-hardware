"""Execute Target-owned power, storage, touch and GPIO contract scenarios."""
from pathlib import Path
import shutil
import subprocess
import tempfile

PLATFORM = Path(__file__).resolve().parents[1]


def run_cases(board, suite, cases, original=None, tick_ms=10):
    compiler = shutil.which('cc')
    assert compiler, 'Peripheral contract tests require a C compiler (cc)'
    target = PLATFORM/'targets'/board
    source = original or target/'bsp/src'/f'bsp_{suite}.c'
    flags = ['-pthread', f'-DTEST_TICK_MS={tick_ms}']
    if original:
        flags += ['-Wno-unused-parameter']
    if suite == 'sdcard':
        flags += ['-Dmalloc=test_malloc', '-Dfree=test_free']
    with tempfile.TemporaryDirectory(prefix='codecraft-peripheral-') as folder:
        executable = str(Path(folder)/'contract-test')
        command = [compiler, '-std=c11', '-Wall', '-Wextra', '-Werror', *flags,
                   '-I'+str(PLATFORM/'tests/stubs/peripheral'),
                   '-I'+str(PLATFORM/'tests/fixtures'),
                   '-I'+str(target/'bsp/include'), str(source),
                   str(target/'tests'/suite/'failure_cases.c'), '-o', executable]
        run = subprocess.run(command, capture_output=True, text=True)
        assert run.returncode == 0, run.stdout+run.stderr
        for args in cases:
            run = subprocess.run([executable, *args], capture_output=True, text=True, timeout=10)
            assert run.returncode == 0, f'{board}/{suite}/{args}: {run.stdout}{run.stderr}'



def run_example_cases(board, example, cases, original=None):
    compiler = shutil.which('cc')
    assert compiler, 'Example contract tests require a C compiler (cc)'
    target = PLATFORM/'targets'/board
    source = original or target/'examples'/example/'main/main.c'
    flags = ['-DTEST_CAPTURE_LOG'] if example == 'touch_read' else []
    if original:
        flags += ['-Wno-unused-parameter']
    with tempfile.TemporaryDirectory(prefix='codecraft-example-') as folder:
        executable = str(Path(folder)/'example-test')
        run = subprocess.run([compiler, '-std=c11', '-Wall', '-Wextra', '-Werror', *flags,
                              '-I'+str(PLATFORM/'tests/stubs/peripheral'),
                              '-I'+str(PLATFORM/'tests/fixtures'),
                              '-I'+str(target/'bsp/include'), str(source),
                              str(target/'tests/examples'/(example+'.c')),
                              '-o', executable], capture_output=True, text=True)
        assert run.returncode == 0, run.stdout+run.stderr
        for args in cases:
            run = subprocess.run([executable, *args], capture_output=True, text=True, timeout=10)
            assert run.returncode == 0, f'{board}/{example}/{args}: {run.stdout}{run.stderr}'
