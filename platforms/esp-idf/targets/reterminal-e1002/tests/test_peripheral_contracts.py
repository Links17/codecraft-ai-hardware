"""Run the native scenarios owned by this Target or component."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tests'))
from host_peripheral import run_cases, run_example_cases


def test_e100x_battery_readiness_calibration_and_power_recovery():
    cases = [[str(n)] for n in range(6)]
    cases += [[name] for name in ('repeat', 'unready', 'null', 'uncalibrated', 'cleanup')]
    cases += [['read', str(n)] for n in range(1, 5)] + [['off-recovery']]
    for board in ('reterminal-e1002',):
        run_cases(board, 'battery', cases)



def test_e100x_charger_lifetime_outputs_and_transaction_serialization():
    cases = [[str(n)] for n in range(14)]
    cases += [[name] for name in ('unready', 'null', 'repeat', 'part-id', 'lock-timeout', 'registers', 'concurrent')]
    cases += [['cleanup', str(n)] for n in (1, 2)]
    cases += [['runtime', str(n)] for n in (1, 2)]
    for board in ('reterminal-e1002',):
        run_cases(board, 'charger', cases)



def test_e100x_storage_owns_paths_and_invalidates_uncertain_unmounts():
    cases = [[str(n)] for n in range(7)]
    cases += [[name] for name in ('null', 'path', 'absent', 'borrowed-bus', 'allocation', 'detect', 'unmount-early', 'unmount-late')]
    for board in ('reterminal-e1002',):
        run_cases(board, 'sdcard', cases)



def test_e100x_buzzer_readiness_timing_and_errors():
    cases = [[name] for name in ('0', '1', '2', 'unready', 'repeat', 'zero-frequency', 'short-beep', 'zero-beep')]
    cases += [['tone', str(n)] for n in (1, 2, 3)] + [['stop', str(n)] for n in (1, 2)]
    for board in ('reterminal-e1002',):
        run_cases(board, 'buzzer', cases)



def test_e100x_led_readiness_and_idempotence():
    for board in ('reterminal-e1002',):
        run_cases(board, 'led', [[name] for name in ('0', '1', '2', 'unready', 'repeat', 'write-error')])



def test_buttons_single_task_callback_lifetime_and_debounce():
    boards = ('reterminal-e1002',)
    cases = [[name] for name in ('0', '1', '2', 'repeat', 'replace', 'poll-only', 'samples', 'wrap', 'early-callback')]
    for board in boards:
        run_cases(board, 'button', cases)
        run_cases(board, 'button', [['min-tick']], tick_ms=50)



def test_e100x_example_keeps_sampling_in_one_owner_task():
    for board in ('reterminal-e1002',):
        run_example_cases(board, 'sht4x_battery', [[name] for name in ('0', 'queue-full', 'sensor-absent')])
