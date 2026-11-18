"""Run the native scenarios owned by this Target or component."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tests'))
from host_peripheral import run_cases, run_example_cases


def test_touch_examples_do_not_publish_failed_samples():
    for board in ('sensecap-watcher',):
        run_example_cases(board, 'touch_read', [['0']])
