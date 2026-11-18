"""Run the native scenarios owned by this Target or component."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tests'))
from host_peripheral import run_cases, run_example_cases


def test_buttons_single_task_callback_lifetime_and_debounce():
    boards = ('xiao-s3-147',)
    cases = [[name] for name in ('0', '1', '2', 'repeat', 'replace', 'poll-only', 'samples', 'wrap', 'early-callback')]
    for board in boards:
        run_cases(board, 'button', cases)
        run_cases(board, 'button', [['min-tick']], tick_ms=50)



def test_xiao_example_queues_backlight_operations():
    run_example_cases('xiao-s3-147', 'button_hello', [['0'], ['queue-full']])
