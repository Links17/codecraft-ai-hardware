# Submission validation snapshot

Executed at 2026-11-18 09:11:22 CST, before committing and pushing the feature branch.
This snapshot follows the hardware architecture migration and the 13 completed
optimization items. The six open items retain their existing acceptance criteria.

The submission cleanup corrects three BSP source paths in NOTICE and removes
terminal blank lines from 35 files. Python AST comparisons passed for the
formatted Python files. Native driver behavior is unchanged. Retained compiler
logs keep their original hashed bytes; .gitattributes excludes only those logs
from whitespace diagnostics because console output includes padding.

## Complete software gate

The final `python3 codecraft.py validate` run passed **240/240** results:
196 static/host checks (19 repository checks and 177 host cases), 36 native
build/source checks, and eight project results covering nine clean exported
projects. No result failed or skipped. The stored records identify the final
source digests and actual toolchains.

| Target | Native checks | Clean exports | Evidence |
| --- | --- | --- | --- |
| esp-idf/respeaker-lite | 3 passed | passed | [record](../../devices/respeaker-lite/tests/records/build-acf909779ca29888.json) |
| esp-idf/reterminal-e1001 | 4 passed | passed | [record](../../devices/reterminal-e1001/tests/records/build-1fd5c3aa5d7abacb.json) |
| esp-idf/reterminal-e1002 | 4 passed | passed | [record](../../devices/reterminal-e1002/tests/records/build-49316ecce2be3743.json) |
| esp-idf/reterminal-sticky | 3 passed | passed | [record](../../devices/reterminal-sticky/tests/records/build-6319c007a1fb0bdb.json) |
| esp-idf/sensecap-indicator | 6 passed | GX and DX passed | [record](../../devices/sensecap-indicator/tests/records/build-1ec617c5903c208c.json) |
| esp-idf/sensecap-watcher | 8 passed | passed | [record](../../devices/sensecap-watcher/tests/records/build-d5dd4242cc8c1f4c.json) |
| esp-idf/xiao-s3-147 | 3 passed | passed | [record](../../devices/xiao-s3-147/tests/records/build-1676d9399e0cfb9e.json) |
| linux/reterminal | 5 passed | passed | [record](../../devices/reterminal/tests/records/build-e606532c045e1983.json) |

ESP-IDF used v6.0.2-dirty, GCC 15.2.0 and Python 3.14.6, retaining the
pre-existing SDK modifications. Linux used Python 3.14.6 and DTC 1.8.1.
Arduino has no registered Target in this branch's verified catalog.

## Scope and remaining integration

The branch is `feat/v0.1/hardware-architecture-refactor`. Remote main at
9902601 includes later Wio Terminal, Grove Beginner Kit and Watcher merged-image
work that is not integrated into this branch. That work requires integration
with the new directory and metadata contracts before merging into main.

Only README files retain English/Chinese pairs. Other maintained engineering
documents use English, and imported original evidence retains its attribution.
OPT-06, OPT-07, OPT-10, OPT-16, OPT-18 and OPT-19 remain open in the
[optimization ledger](../development/optimization-plan.md).
Physical device verification and live cloud API acceptance are **not_run**.
No device write, live API request or firmware publication was performed.
