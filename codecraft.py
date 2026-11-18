#!/usr/bin/env python3
"""Stable repository and exported-project entry; implementation stays in skills/."""
from pathlib import Path
import runpy
import sys


def main(argv=None):
    shared=Path(__file__).resolve().parent/'skills/_shared'
    sys.path.insert(0,str(shared))
    implementation=runpy.run_path(str(shared/'codecraft.py'),run_name='codecraft_cli')
    return implementation['main'](argv)


if __name__=='__main__':
    raise SystemExit(main())
