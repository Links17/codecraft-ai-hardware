# Sourced hardware variant selection snapshot

Executed on 2026-11-18 (Asia/Shanghai). This slice implements the software
portion of **OPT-06** using real Indicator GX/DX vendor definitions. It does
**not close OPT-06**: compatible PCB revisions and physical observations remain
unknown/not_run. No optimization items were added. Current instructions live
in [hardware variants](../development/hardware-variants.md).

## Sourced behavior and ownership

The [Device source record](../../devices/sensecap-indicator/reference/display-variants.md)
pins vendor commit 77edb8d2b9a92fc67965c1b2d4a838f0d09a1800 and source/license
hashes. GX uses the ST7701S register sequence; DX releases the vendor-specified
CS/reset outputs without that sequence. Existing pins, RGB timings, public
function declarations, Flash/PSRAM defaults and dependency locks are preserved.
The original GX wire trace still passes. No PCB revision or DX controller
identity was inferred from a product label.

Device variants own typed panel facts and explicit unknown revision mappings.
Target variants bind those identities to native CMake profiles. Generic context,
export, lock and adapter protocol code carries selection without stack- or
Provider-ID branches. The Indicator retains its documented GX repository build
default; exported Targets default to their explicitly recorded selection.
Unknown choices, missing inputs and profile/lock mismatches fail.

Variant-bearing Device/Target records use schema version 3. The pre-change
version 2 consumer was observed accepting variant fields while omitting native
profiles; the original Device/Target validators now reject version 3 explicitly.
Unmodified version 2 records remain accepted. Platform, adapter envelope,
project and lock versions are independent and unchanged. New regression cases
reject variant declarations under version 2 and empty version 3 declarations.

Native build cases and output directories distinguish GX/DX. After compiler
success, actual CMake selection and BSP compile definitions must match the
selected profile. Complete validation builds every declared variant and a
clean exported project for each; an aggregate project result retains both
child digests/results/logs. Build evidence cannot omit a variant's export.

Physical observations name variant and observed revision. Unknown compatibility
does not promote support; a known incompatible revision is rejected. Evidence
is aggregated per variant and one assembly cannot certify another. Synthetic
fixtures exercise these rules without changing real physical status.

## Coverage and complete gate

All **168 previous host cases retain identical function ASTs**. The original
**772 C scenarios** remain, with **20 additional DX failure/recovery scenarios**
for a total of **792**. The DX fixture rejects the prior GX-only source because
it performs register writes. Public header declarations and other boards'
native sources remain unchanged. Cloud Capability/Provider contracts,
standalone package bytes and import provenance are unchanged.

Nine added host cases cover selection/projection, source and lock drift,
malformed metadata/profiles, actual native compiler evidence, adapter routing,
variant/revision-scoped physical support, per-variant export requirements,
public CLI behavior and native DX failure paths. The full gate passed
**240/240**: **196 static/host results** (19 repository checks plus 177 host
cases), **36 native build/source results**, and **8 project-verification
results covering 9 clean exported projects**. None failed or skipped.

| Target | Native checks | Clean exports | Source-matched evidence |
| --- | --- | --- | --- |
| esp-idf/respeaker-lite | 3 passed | passed | [record](../../devices/respeaker-lite/tests/records/build-d4addd0e6e1d6319.json) |
| esp-idf/reterminal-e1001 | 4 passed | passed | [record](../../devices/reterminal-e1001/tests/records/build-5b05ee59da8995a8.json) |
| esp-idf/reterminal-e1002 | 4 passed | passed | [record](../../devices/reterminal-e1002/tests/records/build-29dbbc2ad7129c41.json) |
| esp-idf/reterminal-sticky | 3 passed | passed | [record](../../devices/reterminal-sticky/tests/records/build-7fb804dd17df29db.json) |
| esp-idf/sensecap-indicator | 6 passed | GX and DX passed | [record](../../devices/sensecap-indicator/tests/records/build-66660c5ff2b494f3.json) |
| esp-idf/sensecap-watcher | 8 passed | passed | [record](../../devices/sensecap-watcher/tests/records/build-6093fb498b5be47c.json) |
| esp-idf/xiao-s3-147 | 3 passed | passed | [record](../../devices/xiao-s3-147/tests/records/build-20a17d7d347b6a10.json) |
| linux/reterminal | 5 passed | passed | [record](../../devices/reterminal/tests/records/build-028fee7faf1a01ca.json) |

An additional DX display_color_bars export passed public build-project and
verify-project. A fresh direct ESP-IDF build in that same export, without a
variant command-line override, also selected DX and passed actual compile
definition verification. Its lock remained unchanged.

All Target digests match their retained records. ESP-IDF used v6.0.2-dirty,
GCC 15.2.0 and Python 3.14.6 with the unchanged pre-existing SDK modifications.
Linux used Python 3.14.6 and DTC 1.8.1. Arduino has no registered hardware Target.
Rules, Skills, generated views, README pairs and English engineering guidance
were updated together. Existing exports keep their original locked source;
rollback must restore selection, native profiles and evidence rules together.

The [retained variant receipt](../../devices/sensecap-indicator/tests/logs/20261117221133Z-opt10-variant-summary.json) contains source hashes,
coverage preservation, configuration comparisons, the negative original-source
experiment and additional export/native results. Logs remain with the Device.

## Open acceptance

The ledger remains **13 completed and 6 open**. OPT-06 still requires sourced
revision compatibility and corresponding physical observations. OPT-07 needs
identified hardware/workloads and measurements; OPT-10 needs a real additional
Provider contract; OPT-16 needs an authorized live task/environment; OPT-18
needs licensed revision-matched assets; OPT-19 needs actual maintainers and
test/storage decisions. No hardware write, physical observation, real cloud
API operation or publication occurred in this slice.
