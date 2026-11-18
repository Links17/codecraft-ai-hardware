"""Run the native scenarios owned by this Target or component."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'tests/platforms/esp-idf'))
from host_peripheral import run_cases, run_example_cases


def test_buttons_single_task_callback_lifetime_and_debounce():
    boards = ('reterminal-sticky',)
    cases = [[name] for name in ('0', '1', '2', 'repeat', 'replace', 'poll-only', 'samples', 'wrap', 'early-callback')]
    for board in boards:
        run_cases(board, 'button', cases)
        run_cases(board, 'button', [['min-tick']], tick_ms=50)
