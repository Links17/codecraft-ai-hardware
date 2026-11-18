# Native-driver optimization snapshot — 2026-11-18

This is the second execution slice of the [19-item ledger](../development/optimization-plan.md).
It continues OPT-01–OPT-04 and resolves the scope decision in OPT-17. It does
not add optimization IDs. The [first snapshot](optimization-progress-2026-11-18.md)
retains its historical source and validation results.

## Failure recovery and ownership

Watcher touch initialization previously returned success even when every boot
poll failed; an I2C-device creation failure also leaked its wrapper allocation.
It now publishes readiness only after a successful poll, returns the last poll
error on exhaustion, and rolls back touch → IO/device → I2C1. It preserves the
shared LCD/touch power rail. Incomplete cleanup retains handles and rejects
another initialization until reset.

Knob initialization now retains both PCNT channels, tracks enable state and
unwinds stop/disable → channel B → channel A → unit. It rejects operations
before readiness and refuses to overwrite resources after incomplete cleanup.
The local ESP-IDF v6.0.2 PCNT contract permits stop on an enabled unit, including
failure before its counter starts. Successful repeated initialization remains a
no-op. Task context, caller serialization and ownership are in public headers.

Expander writes no longer leave a trusted cache after a failed transfer. The
affected port is marked unknown; the next mutation must first read the hardware
register successfully. Tests cover both possibilities after a failed write:
the hardware received the value, or it did not. A failed readback issues no
write. Callers must still serialize expander operations as documented.

## Shared sensor protocols

[codecraft_sht4x](../../platforms/esp-idf/components/codecraft_sht4x/) and
[codecraft_pcf8563](../../platforms/esp-idf/components/codecraft_pcf8563/)
contain one maintained protocol implementation each, consumed by both E1001
and E1002. BSP entry signatures remain unchanged. Each BSP supplies its own
sourced bus/address/speed and retains its process-lifetime singleton. The I2C0
helper remains board-local because it owns pins and bus startup. Original
copyright, license and protocol-source comments are retained.

The SHT4x mutex covers command → conversion delay → receive on one sensor
handle. A second reader cannot interleave commands; unrelated bus devices can
progress while conversion waits. Each lock/transfer has a bounded timeout
policy, with scheduler timing explicitly outside a hard deadline. Conversion
adds one scheduler tick to the existing nominal 10 ms wait. CRC failure,
transfer failure and invalid state/input leave caller outputs unchanged.

RTC transfers retain the existing 2000–2099 interpretation and century-bit
convention. Invalid BCD/field ranges now return INVALID_RESPONSE; invalid
write fields and NULL buffers return INVALID_ARG. Previously accepted invalid
fields are intentionally rejected. Callers retain responsibility for date and
weekday consistency. Read failures do not partially update the caller's time.

Both Target manifests and all eight E1001/E1002 native projects declare the
shared components. Existing exported projects retain their locked source;
new exports carry these components through the same source graph. Reverting
this extraction requires reverting BSP wrappers, component dependencies,
CMake inputs and tests together, not only deleting the component directories.

## Executable coverage and remaining audit

Eight host test functions execute **124 C subprocess scenarios**: 23 display,
11 expander initialization, 4 expander write/resynchronization, 15 touch,
20 knob, 16 SHT4x component, 11 RTC component and 24 board-binding scenarios.
The expander write scenarios each exercise both ports. Component tests are
under their component; Watcher cases are under its Target; common runners and
narrow SDK doubles are under the ESP-IDF platform. No full SDK replacement or
physical simulator is introduced.

Before correction, actual C source failed the touch timeout, knob leaked-unit,
expander stale-shadow, repeated sensor/RTC initialization and interleaved
sensor-read assertions. Corrected code passes. The concurrency case uses
thread barriers and a contended device mutex, with an unrelated bus operation
completing before the first conversion is released; it does not depend on
arbitrary sleep timing.

OPT-01 and OPT-02 remain open. The neighboring source audit found Watcher
audio readiness inferred from allocated codec/channel handles before later
initialization completes, and battery ADC ownership retained after later
configuration failure. These remain within the existing initialization and
ownership scope; they have not yet been corrected or physically reproduced.
Camera/storage initialization and callback ownership also need completion of
that audit. Passing this slice does not close the complete BSP review.

## Validation

The complete software gate passed **137/137**: **96 static/host checks**,
**33 native build/source checks**, and **8 clean external-project builds**.
All 28 ESP-IDF examples used **ESP-IDF v6.0.2-dirty**; pre-existing SDK changes
were preserved and fingerprinted. Linux used Python 3.14.6 and DTC 1.8.1 for
four source checks and overlay compilation. No Linux device demo was run.

| Target | Native checks | Clean external project | Source-matched record |
| --- | --- | --- | --- |
| esp-idf/respeaker-lite | 3 passed | passed | [record](../../devices/respeaker-lite/tests/records/build-30ba0b5651bf10f7.json) |
| esp-idf/reterminal-e1001 | 4 passed | passed | [record](../../devices/reterminal-e1001/tests/records/build-ee95ad9c18bfcecd.json) |
| esp-idf/reterminal-e1002 | 4 passed | passed | [record](../../devices/reterminal-e1002/tests/records/build-aa9db6c56cff9056.json) |
| esp-idf/reterminal-sticky | 3 passed | passed | [record](../../devices/reterminal-sticky/tests/records/build-493f779c3c4a595a.json) |
| esp-idf/sensecap-indicator | 3 passed | passed | [record](../../devices/sensecap-indicator/tests/records/build-f7c75da53f672c9a.json) |
| esp-idf/sensecap-watcher | 8 passed | passed | [record](../../devices/sensecap-watcher/tests/records/build-1bb08ce808067eb2.json) |
| esp-idf/xiao-s3-147 | 3 passed | passed | [record](../../devices/xiao-s3-147/tests/records/build-e06c885435e52787.json) |
| linux/reterminal | 5 passed | passed | [record](../../devices/reterminal/tests/records/build-1440431a20b0f79b.json) |

Each retained record includes complete expected cases, actual toolchain, source
digest and sanitized logs. All eight source digests were compared to the tested
receipts before recording. Historical records remain; only matching records
establish build verification. Arduino's adapter contract passed, with no
registered Arduino hardware Target. This closes OPT-03 and OPT-04; the sourced
non-support decision closes OPT-17. OPT-01/02 and physical acceptance remain open.

Physical verification and live cloud execution remain **not_run**. The
[simulation scope decision](../architecture/simulation-scope.md) retains
explicit platform non-support, with sources and reopening criteria. Host
doubles do not establish physical timing, sensor accuracy or combined-load
resource bounds. No firmware was flashed, no live cloud operation was run, and no commit,
push or publication was performed.
