# Skill delivery and public entry optimization snapshot

Executed on 2026-11-18 (Asia/Shanghai). This slice closes **OPT-11** and
**OPT-12** from the existing 19-item ledger. No additional optimization items
were introduced. Current instructions are in the
[Skill release workflow](../development/skill-releases.md) and
[architecture guide](../architecture/overview.md).

## Reproducible, reviewed Skill releases

skills/_cloud/release.py provides prepare/check/apply. Preparation assembles all
registered repository packages from maintained sources, synchronizes the common
helper into candidate copies only, and emits complete file/version differences.
Candidates require explicit version increases for changed package/API inputs.
Documentation and runtime changes are classified separately; semantic/API
compatibility still requires review. Policy versions cannot decrease and
contract versions must match the reviewed Capability.

Application requires the exact reviewed candidate digest, verifies complete
candidate/source inventories and reruns isolated conformance. It changes only
affected package directories and Provider manifests. Transaction failures restore
completed changes; if restoration itself fails, original backup files remain for
recovery. Negative tests cover wrong digests, tampering, missing version changes,
invalid identities, source drift, CLI failures, write failures and failed backup
restoration. A distribution helper that differs from both its pin and the
maintained source is rejected before preparation, preserving the conflicting
local edit. Validation/application copy only pinned files and verify copied
bytes; ignored candidate caches cannot enter a distribution. Both documentation
and runtime candidates run actual isolated conformance before application in
temporary repositories. The retained receipt records the reproduced regressions. Original import provenance is never rewritten.

The actual repository public CLI produced two byte-identical candidates with
the same review digest. Candidate validation passed four package/CLI checks,
one nine-case offline protocol suite and twelve prepared-client functions:
**17 result rows**. This was a no-change candidate: current packages remain
1.0.1, API v1, Capability 2.0.0 and policy 1.0.0. The real application/version
change test uses a temporary copied repository; it does not release version
1.0.2 into the maintained repository or change an installed Skill.

The [retained candidate receipt](../../devices/sensecap-indicator/tests/logs/20261117203617Z-opt7-candidate-summary.json) records complete
candidate file hashes, the review digest and the actual offline check rows.

## Stable public entry and compatibility

python3 codecraft.py is the public repository and new-export entry. The root
file is a thin bootstrap; shared implementation and native platform ownership
remain unchanged. The former skills/_shared/codecraft.py entry retains the same
commands, JSON envelopes, errors and exit codes. Tests compare both entries from
another working directory.

New exported projects include the public entry in their dependency graph and
lock. verify-project, lock-project and build-project operate on the application's
existing source/toolchain lock; build.py and build.py --lock remain available.
Tests check equivalent public/legacy build results, retained initial import
provenance, public-entry source drift, unavailable-toolchain exit 2 and the
not_supported status for repository-only release maintenance in a plain export.
A separate missing-source regression now reports a contract failure for an
incomplete repository, rather than treating absent implementation as proof of
non-support. The retained receipt records the observed before/after statuses.
No global CLI installation is required. Existing exports retain their old bytes
and continue to use their bundled build.py until an explicit migration/new export.

README pairs, Agent rules, hardware workflow Skills, native platform guidance,
CI and generated project instructions now use the public entry. Historical
reports retain the commands that actually ran. Standalone cloud Skill packages
do not depend on this CLI and were not changed by this slice.

## Validation

The complete gate passed **193/193**: **152 static/host checks**, **33 native
build/source checks** and **8 clean external-project builds**. All 140 previous
static/host IDs were retained; twelve were added, with no duplicates or removals.
There were no failed or skipped results in the final run. Three earlier full-gate
attempts were intentionally interrupted for missing-source status, conflicting
distribution edits and pinned-file-only copying; only the final run certifies this source. All eight current Target digests matched
the complete-gate receipts before evidence was retained. The unchanged native
test sources still execute **38 C functions / 772 scenarios**; no native C/header
implementation changed in this slice.

The [retained host receipt](../../devices/sensecap-indicator/tests/logs/20261117203617Z-opt7-host-summary.json) records preserved/added test IDs,
implementation hashes, unchanged package provenance and native scenario inventory.

| Target | Native checks | Clean external project | Source-matched record |
| --- | --- | --- | --- |
| esp-idf/respeaker-lite | 3 passed | passed | [record](../../devices/respeaker-lite/tests/records/build-f9d87a6c1fa03fe5.json) |
| esp-idf/reterminal-e1001 | 4 passed | passed | [record](../../devices/reterminal-e1001/tests/records/build-03c074fdf6b89ddc.json) |
| esp-idf/reterminal-e1002 | 4 passed | passed | [record](../../devices/reterminal-e1002/tests/records/build-eae872804bbf9a66.json) |
| esp-idf/reterminal-sticky | 3 passed | passed | [record](../../devices/reterminal-sticky/tests/records/build-a4829075770d9233.json) |
| esp-idf/sensecap-indicator | 3 passed | passed | [record](../../devices/sensecap-indicator/tests/records/build-d338c96b525a70f0.json) |
| esp-idf/sensecap-watcher | 8 passed | passed | [record](../../devices/sensecap-watcher/tests/records/build-613a4ba1d17b24bd.json) |
| esp-idf/xiao-s3-147 | 3 passed | passed | [record](../../devices/xiao-s3-147/tests/records/build-5f4392c5dfeb6ca1.json) |
| linux/reterminal | 5 passed | passed | [record](../../devices/reterminal/tests/records/build-3a673ebeaddc4b3a.json) |

ESP-IDF builds used v6.0.2-dirty, GCC 15.2.0 and Python 3.14.6, preserving the
pre-existing SDK changes. Linux checks used Python 3.14.6 / DTC 1.8.1, including
overlay compilation; no hardware demo was run. Complete toolchain identities and
sanitized logs are retained per Target. Arduino has no registered hardware Target.
English-only engineering documents and paired maintained READMEs remain enforced.

## Remaining acceptance

Physical-device verification and real cloud API execution were **not_run**.
Nothing was flashed, installed globally, committed, published or uploaded.
No real second Provider, revision compatibility, resource budget or live billing
claim is established. Test-layout work remains open under OPT-13; these release
tests reside with their owner without claiming the earlier suites were migrated.
The ledger now has **10 completed and 9 open** optimization items.
