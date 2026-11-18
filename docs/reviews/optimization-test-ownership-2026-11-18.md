# Test ownership and discovery optimization snapshot

Executed on 2026-11-18 (Asia/Shanghai). This slice closes **OPT-13** from the
existing 19-item ledger. No additional optimization items were introduced.
The [host testing guide](../development/testing.md) owns current instructions.

## Ownership and execution

Core graph/export/lock/evidence and cross-layer tests now live in
skills/_shared/tests. Cloud installation, protocol and release tests live in
skills/_cloud/tests. Validation entry, public CLI, language policy and discovery
tests remain with codecraft-validate. Capability tests retain their domain
ownership. Native Python runners now live with their component or Target beside
their C fixtures; platform-wide compiler helpers and SDK doubles remain shared.
Physical acceptance procedures and observations remain in devices and are not
part of automatic host execution.

The public `python3 codecraft.py test` entry lists or executes recursively
discovered owner-local tests. Plain functions and unittest methods share one
gate; imported tests and duplicate aliases are not executed as extra cases.
Empty/invalid selections and collection errors fail visibly. unittest fixture,
subtest, skip and expected-failure states retain their distinct outcomes.
Nested inventory collection does not replace an executing suite's fixture
globals. Focused commands and the full gate use the same implementation.

## Preserved coverage

The [migration mapping](../../skills/codecraft-validate/tests/migrations/opt-13.json)
accounts for all **133 previous host entries** as **156 explicit preserved
cases**. The old one-entry protocol wrapper is replaced by its nine unittest
methods. Native cross-board functions are split into their owning Targets:
**38 functions become 53, preserving exactly 772 scenario invocations**.
Captured case arguments before/after are identical. The other 94 function
bodies and the entire protocol unittest class have identical normalized ASTs.
All native C/header/overlay bytes and standalone Skill package bytes are
unchanged. These are coverage-preservation results, not new hardware evidence.

Six new discovery regressions cover recursive ownership, function/unittest
execution, module/class fixtures, failures/skips/subtests, malformed/empty
collection, focused CLI output/statuses and missing/duplicate migration IDs.
Focused validation passed those six functions, all nine protocol methods and
the SHT4x component's sixteen actual C scenarios.

The [retained host receipt](../../devices/sensecap-indicator/tests/logs/20261117205246Z-opt8-host-summary.json) records the full ID mapping
references, preserved workload arguments, source hashes and actual result rows.

## Complete gate

The final complete gate passed **222/222**: **181 static/host results** (19
repository checks and 162 host cases), **33 native build/source checks** and
**8 clean external-project builds**. No result was failed or skipped. Every
current Target source digest matches its retained build/project receipt.
Shared runner source is included in the dependency graph and exported locks.

| Target | Native checks | Clean external project | Source-matched record |
| --- | --- | --- | --- |
| esp-idf/respeaker-lite | 3 passed | passed | [record](../../devices/respeaker-lite/tests/records/build-ffaef15d90ff0fc0.json) |
| esp-idf/reterminal-e1001 | 4 passed | passed | [record](../../devices/reterminal-e1001/tests/records/build-0c3638ec342128d8.json) |
| esp-idf/reterminal-e1002 | 4 passed | passed | [record](../../devices/reterminal-e1002/tests/records/build-00030d3b5900215c.json) |
| esp-idf/reterminal-sticky | 3 passed | passed | [record](../../devices/reterminal-sticky/tests/records/build-e06a9b92f99ba2f6.json) |
| esp-idf/sensecap-indicator | 3 passed | passed | [record](../../devices/sensecap-indicator/tests/records/build-818ed75ceff2d23c.json) |
| esp-idf/sensecap-watcher | 8 passed | passed | [record](../../devices/sensecap-watcher/tests/records/build-accb87147f28f047.json) |
| esp-idf/xiao-s3-147 | 3 passed | passed | [record](../../devices/xiao-s3-147/tests/records/build-28199054741e5ad8.json) |
| linux/reterminal | 5 passed | passed | [record](../../devices/reterminal/tests/records/build-d522b7b1b97c68f2.json) |

ESP-IDF builds used v6.0.2-dirty, GCC 15.2.0 and Python 3.14.6, preserving the
existing SDK modifications. Linux source/overlay checks used Python 3.14.6 and
DTC 1.8.1. Actual SDK identity/change fingerprints and sanitized logs are
retained per Target. Arduino has no registered hardware Target.

Rules, Skills, README pairs, CI discovery and current links were updated in the
same migration. The former direct protocol-script command is replaced by the
public path-selecting runner; historical receipts retain their original IDs
and source hashes. Only README files retain bilingual copies.

## Remaining acceptance

On-device verification and real cloud API execution were **not_run**. No board
was flashed and no Skill was installed, published or uploaded. OPT-05/14 remain
open for native composition/layout work; revision, resource, second-Provider,
live-service, asset and governance prerequisites remain explicit. The ledger
now has **11 completed and 8 open** optimization items.
