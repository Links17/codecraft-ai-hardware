# Optimization execution snapshot — 2026-11-18

This report records the first implementation slice of the [19-item optimization ledger](../development/optimization-plan.md). The ledger remains authoritative for open/closed status. No extra optimization scope was added. Physical device and live cloud verification were not performed.

## Documentation policy and OPT-15

Only maintained README files have English/Chinese counterparts. AGENTS, CLAUDE, Skills, API references, plans and reports use English. Removed 47 duplicate translations, repaired incoming links, supplied two missing maintained README translations and preserved original third-party documentation. Structured hardware values and upstream import provenance were not rewritten.

Current architecture moved from docs/development/architecture.md to [docs/architecture/overview.md](../architecture/overview.md). Capability and refactor reviews moved to this reviews/ directory, with their evidence links and snapshot semantics retained. The planning baseline and optimization ledger retain their original paths. Both [documentation indexes](../README.md) distinguish current guidance, planning and historical evidence.

Generated engineering views and exported application AGENTS use English; exported READMEs remain bilingual. The documentation gate rejects obsolete non-README translations, missing README counterparts and broken local routes. A paired-render request for an engineering document fails. Four standalone Skill packages changed from 1.0.0 to 1.0.1: two translated files were removed and language links were removed from two English documents in each package. All runtime/UI files retain their starting hashes. API/Capability versions are unchanged. Whole-directory replacement is required when upgrading an installed package; overlay copies retain obsolete files and fail exact inventory validation. Existing external projects retain their original locked imports.

## Partial OPT-01, OPT-02 and OPT-03

Actual Watcher BSP C code reproduced two false-ready bugs: display reset failure and expander probe failure both allowed subsequent initialization to succeed without a ready device. Both implementations now separate allocation from readiness, release owned resources after failure, clear output handles, and refuse to overwrite resources if cleanup failed. Successful repeated initialization remains supported. The display preserves the shared touch power rail; the expander bus is released only before its first successful publication and otherwise remains borrowed for process lifetime.

Public headers state task context, required caller serialization, ownership and blocking/failure behavior. Cleanup failure requires a board reset; no reset or flash was performed here. The C host harness covers 23 display scenarios and 11 expander scenarios, including every declared acquisition/initialization failure, cleanup failures, repeat calls and successful retries. The original source fails the ready-state regression; corrected source passes. These are two host test functions executing 34 C scenarios, not 34 physical observations.

The neighboring touch audit found incomplete cleanup and success even when all boot polls fail. Knob initialization also retains PCNT resources after later failures. Those fixes, the remaining initialization audit and sensor concurrency/CRC coverage remain open in the existing OPT-01–OPT-03 items. This slice does not mark them complete.

## Validation

The documentation slice passed 88 static/host checks. The completed combined gate passed **131/131**: **90 static/host checks**, **33 native build/source checks** and **8 clean external-project builds**. The 90-result subtotal includes the two C harness functions that execute 34 failure/retry scenarios. Original broken implementations failed their ready-state regression before the fixes.

| Target | Native checks | Clean external project | Current-source record |
| --- | --- | --- | --- |
| esp-idf/respeaker-lite | 3 passed | passed | [record](../../devices/respeaker-lite/tests/records/build-1c798ffd7c9cf567.json) |
| esp-idf/reterminal-e1001 | 4 passed | passed | [record](../../devices/reterminal-e1001/tests/records/build-a21f90116812dcac.json) |
| esp-idf/reterminal-e1002 | 4 passed | passed | [record](../../devices/reterminal-e1002/tests/records/build-9f168d4adcc36037.json) |
| esp-idf/reterminal-sticky | 3 passed | passed | [record](../../devices/reterminal-sticky/tests/records/build-6e73ae4c66963c20.json) |
| esp-idf/sensecap-indicator | 3 passed | passed | [record](../../devices/sensecap-indicator/tests/records/build-ffd1ae770ff35073.json) |
| esp-idf/sensecap-watcher | 8 passed | passed | [record](../../devices/sensecap-watcher/tests/records/build-c4d2367972ca6343.json) |
| esp-idf/xiao-s3-147 | 3 passed | passed | [record](../../devices/xiao-s3-147/tests/records/build-c44ac433f56119c4.json) |
| linux/reterminal | 5 passed | passed | [record](../../devices/reterminal/tests/records/build-3010756f763986ed.json) |

The records retain exact execution timestamps, source digests, actual toolchains and sanitized logs. All 28 ESP-IDF examples passed with **ESP-IDF v6.0.2-dirty**; pre-existing SDK changes were retained and fingerprinted. Linux checks cover four Python sources and DTS compilation; no device demo was executed. The Arduino adapter contract passed, with no registered Arduino hardware Target. Each native source digest was checked again before retaining evidence. Historical records remain available; only matching source records establish build-verified status.

Physical verification and real cloud execution remain **not_run**. Simulation remains **not_supported** by the registered adapters. These software results do not close touch/knob recovery, sensor concurrency or physical-acceptance TODOs, and do not establish readiness to merge the hardware changes without the required on-device evidence.

No commit, push, publication or device write was performed. Existing unrelated working-tree changes were retained.
