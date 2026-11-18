# Native composition and BSP layout optimization snapshot

Executed on 2026-11-18 (Asia/Shanghai). This slice closes **OPT-05** and
**OPT-14** in the existing 19-item ledger. The [native composition guide](../development/native-compositions.md)
owns current instructions; this report records the tested migration.

## Changes and compatibility

All 28 ESP-IDF examples explicitly select BSP sources and native requirements
in bsp.cmake. Optional managed packages now belong to each example's main
manifest. Minimal native builds retain their required system components,
including PSRAM and Wi-Fi where configured. Target common/example inputs,
dependency scopes and native-interface bindings match each selected composition.
Shared component resource manifests export runtime sources and attribution;
their owner-local host fixtures remain in the repository.

Across seven BSPs, 45 implementation/private-header files moved into src/ with
identical bytes. Public headers, native example/driver logic, pins and SDK
defaults are unchanged. Retained managed packages keep their prior resolved
versions. Before/after actual Flash, PSRAM, CPU-frequency and partition settings
match for every example. Existing external projects keep their locked source;
new exports contain only their declared native composition. Direct source-path
consumers must adopt bsp/src/ and include the required native resources before
explicitly reviewing/relocking application changes.

Rollback must restore BSP paths, native CMake/manifests/locks, Target scopes,
runtime resource manifests, adapter checks, host paths and generated views
together. Revalidate source digests after rollback; retained historical build
receipts must not be relabeled as evidence for different source.

Native component registration remains in each BSP's CMakeLists.txt. A pre-gate
attempt to register from the shared helper failed because ESP-IDF resolved
include paths relative to that helper. The retained diagnostic identifies the
failure; moving registration back to the component root corrected it.

## Build graph and coverage

The adapter checks actual project_description.json BSP sources and requirements
after compilation. Six new regression functions cover profile syntax,
omitted/broad source dependencies, missing local components, exported-lock drift
and successful compiler metadata with an incorrect composition. All 28 examples
have closure/export/lock coverage. The previous 162 host test IDs remain; all
53 native test functions retain exactly 772 scenario arguments and unchanged C
fixtures. Capability/Provider contracts, standalone package bytes and original
import provenance are unchanged.

| Example | BSP source units before → after | Native components before → after |
| --- | --- | --- |
| esp-idf/sensecap-watcher/knob_input | 8 → 2 | 146 → 57 |
| esp-idf/sensecap-watcher/touch_read | 8 → 3 | 146 → 70 |
| esp-idf/reterminal-e1001/epd_hello | 11 → 2 | 141 → 53 |
| esp-idf/reterminal-sticky/button_hello | 3 → 1 | 140 → 52 |

These are actual registered source/component counts, not linker-size,
build-time or runtime-resource measurements. Minimal examples retain shared
board resources: Watcher knob includes its expander; touch includes display
and expander support. The full comparison retains every example's component
lists, protected configuration values and dependency versions.

## Complete gate

The complete gate passed **228/228**: **187 static/host results** (19 repository
checks plus 168 host cases), **33 native build/source checks**, and **8 clean
external-project builds**. No failed or skipped results remain. Two additional
clean Watcher exports, knob_input and touch_read, passed public new,
build-project and verify-project commands. This does not claim that all 28
exported examples were separately compiled from clean directories.

| Target | Native checks | Default clean export | Source-matched evidence |
| --- | --- | --- | --- |
| esp-idf/respeaker-lite | 3 passed | passed | [record](../../devices/respeaker-lite/tests/records/build-787ee2cf9da8ba46.json) |
| esp-idf/reterminal-e1001 | 4 passed | passed | [record](../../devices/reterminal-e1001/tests/records/build-6f691f913c4fed68.json) |
| esp-idf/reterminal-e1002 | 4 passed | passed | [record](../../devices/reterminal-e1002/tests/records/build-f6e6a39b1eef1db4.json) |
| esp-idf/reterminal-sticky | 3 passed | passed | [record](../../devices/reterminal-sticky/tests/records/build-9ae202031ab86583.json) |
| esp-idf/sensecap-indicator | 3 passed | passed | [record](../../devices/sensecap-indicator/tests/records/build-0e63f9745729061e.json) |
| esp-idf/sensecap-watcher | 8 passed | passed | [record](../../devices/sensecap-watcher/tests/records/build-7b19984812cd7cb5.json) |
| esp-idf/xiao-s3-147 | 3 passed | passed | [record](../../devices/xiao-s3-147/tests/records/build-bd082c6c03f13ee9.json) |
| linux/reterminal | 5 passed | passed | [record](../../devices/reterminal/tests/records/build-3a4175a0949f454d.json) |

Every Target digest matches its retained evidence. ESP-IDF used v6.0.2-dirty,
GCC 15.2.0 and Python 3.14.6 with the same pre-existing SDK modifications as
the prior gate. Linux used Python 3.14.6 and DTC 1.8.1. Arduino has no registered
hardware Target. Rules, Skills, metadata, generators, host compilation paths and
README pairs were updated together; engineering documents remain English only.

The [retained composition receipt](../../devices/sensecap-watcher/tests/logs/20261117212738Z-opt9-composition-summary.json) includes source hashes,
all before/after graphs, preserved workloads, extra-export results and the
diagnosed pre-gate failure. Native logs are retained beside each Target record.

## Remaining acceptance

No device writes, physical measurements or live cloud API calls ran. On-device
verification remains **not_run**. The ledger has **13 completed and 6 open**:
revision evidence (OPT-06), measured combined workloads (OPT-07), a second real
Provider (OPT-10), live-service acceptance (OPT-16), authorized assets (OPT-18)
and identified maintenance owners (OPT-19). These external prerequisites remain
explicit; software checks do not close them.
