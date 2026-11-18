# Native I/O contract optimization snapshot — 2026-11-18

This fourth execution slice advances OPT-02 and completes the remaining Sticky
SHT4x binding under OPT-04 in the [19-item ledger](../development/optimization-plan.md).
It adds no TODO IDs. README files remain bilingual; all other maintained
engineering documents use English. OPT-02 remains open for the interfaces
listed below; this report does not claim whole-catalog contract completion.

## Changes and compatibility

The E1001, E1002 and XIAO PDM microphone BSPs pass milliseconds directly to the
native I2S API. They report complete samples copied before a later timeout,
reject invalid buffer/count/rate requests and define one owning task or an
application mutex for init/read/deinit. Repeated init at the same rate is a
no-op; changing the rate requires deinit. Failed channel/rail cleanup retains
ownership for a later deinit retry, without overwriting the retained handle.
E100x dedicated microphone rails are released only after channel cleanup.

E1001/E1002/Sticky e-paper entry points use a non-waiting atomic operation guard
covering initialization and refresh. Concurrent/reentrant calls return
INVALID_STATE without touching hardware. Readiness requires complete setup;
failed allocation/attachment releases the DMA buffer and keeps the shared
board SPI bus. GPIO and SPI failures propagate. Caller frames remain borrowed
and immutable through the call. BUSY polling limits apply separately to each
wait (10/60/30 seconds respectively), with scheduler overhead and native SPI
blocking outside those budgets. They are not whole-refresh deadlines. A NULL
previous E1001 image now forces the already-documented full refresh. Sticky
errors and grayscale refresh invalidate its partial-refresh baseline. Protocol
register tables, formats, wiring, clocks and original refresh delays remain.

XIAO LCD initialization now owns panel/IO allocations, publishes only complete
readiness and returns the same borrowed handle on repeated success without
pulsing the shared LCD/touch reset. Complete rollback permits startup retry;
incomplete cleanup requires reset. New `bsp_display_wait_idle()` drains queued
SPI color transfers through the native no-command parameter barrier. Callers
keep buffers alive and unchanged until it succeeds, including after a partial
draw error. The display example waits before reusing its color-band buffer.
Native waits can be indefinite; the interface promises no hard total deadline.

Indicator RGB initialization checks every register-channel GPIO/expander
operation, cleans failed panel allocation and rejects reuse after incomplete
cleanup. Its public contract defines serialized startup before shared-reset
consumers, a borrowed process-lifetime panel/framebuffer, and single display
task/application locking. Native RGB copies an external draw buffer into its
framebuffer synchronously in the configured IDF implementation; direct RGB
framebuffer pointers remain DMA-owned. This does not guarantee tear-free or
visible frame completion. Backlight getters report the last successful request,
not measured hardware state.

The Indicator TCA9535 driver probes before allocating a device handle, requires
all shadow reads before readiness and rolls back failed startup. Pin operations
serialize read-modify-write and shadow recovery with a device mutex. A timed-out
write may have reached the chip; the affected shadow is reread before the next
update. Lock timeout performs no bus operation, and read errors preserve caller
outputs. Multi-call reset/bit-bang sequences still require a single pin owner.

reSpeaker Lite readiness requires checked reset operations, TX enable and the
initial codec gain sequence. Failed startup unwinds channels, devices, bus and
mutex; uncertain cleanup blocks reinitialization until reset. The RX owner
serializes mic start/read/stop, while a separate TX owner can write concurrently.
The control mutex spans each complete XMOS request/response or codec sequence.
Failed microphone stop retains ownership and blocks read/start until stop is
retried successfully. Native read/write timeouts receive milliseconds unchanged
and preserve partial complete-frame counts. The legacy size_t/void signatures
remain: zero conflates no-progress/state/input errors, and stop logs failures.
A readable XMOS version alone does not establish the required firmware variant.

Sticky now uses the existing `codecraft_sht4x` component, retaining its own
sourced I2C1 pins, address and speed. Device-level serialization spans command,
conversion and receive while allowing other I2C devices to operate during the
conversion wait. Its initialized bus has explicit process-lifetime ownership,
including after a failed sensor attachment; retry reuses it. The shared
component supplies CRC checks, atomic output publication and conversion delay
rounding. This adds one scheduler tick to the nominal 10 ms wait. Target
metadata, all three native project CMake files and export dependencies include
the component; narrower per-example BSP composition remains OPT-05.

Existing public signatures are retained; the XIAO wait function is additive.
Existing locked external projects retain their imported source. Updating an
application requires reviewing its source/lock change; native build evidence
must match the updated digest. Keep driver, contract, dependencies, examples
and regression tests together when reverting a slice. No new cloud behavior,
MCU cloud runtime, simulator or hardware configuration variant is introduced.

## Verification scope

The complete gate passed **154/154**: **113 static/host checks**, **33 native
build/source checks**, and **8 clean external-project builds**. There were no
failed or skipped results. All eight current Target digests matched the
complete-gate receipts before evidence was recorded.

The native C inventory contains 25 test functions and 527 subprocess scenarios,
including 270 additional cases in this slice. The new coverage comprises:

| Boundary | Cases | Covered behavior |
| --- | --- | --- |
| E1001/E1002/XIAO PDM | 46 | Readiness, rate changes, partial reads, timeout units, cleanup/deinit retry |
| E1001/E1002/Sticky e-paper | 82 | Concurrent init/refresh rejection, allocation/GPIO/SPI errors, BUSY timeouts, full/grayscale recovery |
| XIAO LCD | 40 | 30 startup stages, reverse cleanup, ready state, DMA lifetime and normal wire trace |
| Indicator LCD | 34 | Startup and early/later/idle bit-bang failures, RGB ownership and normal wire trace |
| Indicator expander | 18 | Probe fallback, rollback, shadow resynchronization, lock timeout and concurrent pin updates |
| reSpeaker audio | 35 | 20 startup stages, six cleanup stages, full duplex, control ordering, partial transfers and stop recovery |
| Sticky sensor binding | 15 | I2C1 configuration, retained bus retry, CRC/output errors and concurrent measurement |

Eleven original-source cases fail their expected assertions: three microphone
timeout conversions, three unready e-paper calls, repeated XIAO LCD allocation,
ignored Indicator bit-bang failure, ignored reSpeaker initial gain failure,
reSpeaker timeout conversion, and premature XIAO example buffer reuse. Original
and corrected LCD GPIO/register/delay traces match for normal initialization.

The [retained host receipt](../../devices/sensecap-indicator/tests/logs/20261117184609Z-opt4-host-summary.json) contains the case inventory,
passed host rows, test-source hashes, original failure observations, normal LCD
wire traces and hashes of the four inspected native SDK implementations.

These doubles execute actual BSP/component C at SDK boundaries. Thread barriers
exercise supported concurrency without arbitrary sleeps. They do not simulate
panels, microphones, I2C/SPI signals or RTOS scheduling, and do not establish
physical timing or resource limits. SDK-internal errors hidden by native
cleanup implementations are outside the host proof. Source policy, native
compilation, exported-project compilation and physical behavior remain separate.

All 28 ESP-IDF examples used **ESP-IDF v6.0.2-dirty**, preserving pre-existing
SDK modifications. Linux checks used **Python 3.14.6 / DTC 1.8.1**, including
overlay compilation; no Linux hardware demo was executed.

| Target | Native checks | Clean external project | Source-matched record |
| --- | --- | --- | --- |
| esp-idf/respeaker-lite | 3 passed | passed | [record](../../devices/respeaker-lite/tests/records/build-323a916bee5df31e.json) |
| esp-idf/reterminal-e1001 | 4 passed | passed | [record](../../devices/reterminal-e1001/tests/records/build-f083d3815aa168d8.json) |
| esp-idf/reterminal-e1002 | 4 passed | passed | [record](../../devices/reterminal-e1002/tests/records/build-e18cd82dff7b09d7.json) |
| esp-idf/reterminal-sticky | 3 passed | passed | [record](../../devices/reterminal-sticky/tests/records/build-b781c5915f6f1158.json) |
| esp-idf/sensecap-indicator | 3 passed | passed | [record](../../devices/sensecap-indicator/tests/records/build-f5001098d6efd765.json) |
| esp-idf/sensecap-watcher | 8 passed | passed | [record](../../devices/sensecap-watcher/tests/records/build-8b35b1d39ee78887.json) |
| esp-idf/xiao-s3-147 | 3 passed | passed | [record](../../devices/xiao-s3-147/tests/records/build-871d89d0293c4d12.json) |
| linux/reterminal | 5 passed | passed | [record](../../devices/reterminal/tests/records/build-06e7c41d10aed6d7.json) |

Arduino has no registered hardware Target. Simulator support remains absent
under the existing scope decision. README language/link and generated-view
checks passed; a successful build does not change physical acceptance.

## Remaining acceptance

OPT-02 stays open. E100x storage, battery/charger and buzzer APIs, Indicator touch,
and remaining GPIO/LED/button contracts still require the same public-state,
ownership, context and blocking review with executable cases for actual risks.
The old narrow header comments are not proof that these interfaces satisfy the
full item. The other open TODOs retain their original scope and prerequisites.

Physical verification and live cloud API execution remain **not_run**. Hardware
revisions and measured combined-load/resource bounds remain unknown. No board
was flashed, no live API operation was executed, and no commit, push or
publication was performed. The SDK's pre-existing local changes were preserved.
