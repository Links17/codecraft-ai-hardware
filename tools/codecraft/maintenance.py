"""Repository conformance backend. User authoring uses the Rust codecraft binary.

This module is retained for repository audits and native reference fixtures;
it is not included by Platform.application_inputs in creator exports.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cli import main

if __name__ == '__main__':
    raise SystemExit(main())
