# BSP lifecycle optimization snapshot — 2026-11-18

This third execution slice closes OPT-01 and advances OPT-02 in the
[19-item ledger](../development/optimization-plan.md). It completes the
Watcher neighboring-initializer audit begun in the
[second snapshot](optimization-drivers-2026-11-18.md). It adds no optimization
IDs. README files remain bilingual; engineering documents have one English
version.

## Readiness and failure recovery

Audio readiness now requires both codec devices to be opened and input gain
setup to succeed. The BSP owns every allocated interface, device and I2S
channel, unwinds them after failure, and publishes borrowed handles only when
ready. Retrying after complete cleanup is supported. The pinned codec SDK's
interface deletion functions free their wrappers even when a close callback
reports an error; the BSP clears those pointers and blocks reuse until reset.
Native channels that could not be deleted remain owned. Shared I2C0 and the
existing codec rail are preserved.

Battery initialization releases its ADC unit when channel configuration or
calibration creation fails. Successful repeated initialization is a no-op;
failed deletion retains ownership and requires reset. Presence reads before
readiness return false, and voltage errors leave the caller's output unchanged.
The divider configuration, calibration method and voltage conversion remain
unchanged.

Camera board initialization now checks SD chip-select deassertion before
publishing registration. Existing registration/configuration is rejected;
registration is a startup operation, not evidence that a capture will succeed.
The shared SSCMA backend cleans failed device/PM setup, checks power/reset and
PM acquisition errors, and frees transient buffers on failure. Incomplete
shutdown faults the backend until reset. The board-configured shared SPI bus
remains available for storage. No sourced pins or power/reset delays changed.

SD mounting now owns its mount-path copy and accepts a repeated mount only at
that path. Failed mount clears the output and releases the path copy. Unmount
rejects a different path before touching the SDK. ESP-IDF v6.0.2 can release
the card/context before returning a later VFS error, so any attempted unmount
invalidates borrowed card handles; failure blocks mount/unmount until reset.
It never retries with a possibly freed card. Formatting remains disabled, and
the shared SPI bus and existing rail remain available.

The lifecycle audit covers all eight Watcher BSP units:

| Unit | Readiness / ownership decision | Executable coverage |
| --- | --- | --- |
| Display | Publish after complete setup; reverse cleanup; preserve shared rail | 23 cases retained from earlier slices |
| Expander | Publish after probe/shadow reads; unwind mutex/device/bus | 18 initialization, shadow and mutex cases |
| Touch | Require successful boot poll; release wrapper/device/IO/bus | 15 cases retained from the second slice |
| Knob | Track unit, both channels and enable state until fully started | 20 cases retained from the second slice |
| Audio | Explicit ready state; own codecs/interfaces/native channels | 38 cases, including both supported codec branches |
| Battery | Release failed ADC attachment; publish after calibration | 11 cases |
| Camera | Board setup before registration; lazy backend readiness | 11 board cases and 56 shared core/backend cases |
| Storage | Owned mount path; borrowed card lifetime; uncertain unmount recovery | 14 cases |

The earlier E1001/E1002 sensor/RTC initialization fixes and their 51 component
and binding cases also pass. This closes the recorded OPT-01 software recovery
scope. It is not a claim that SDK internals or physical failure recovery have
been exhaustively tested.

## Concurrency, ownership and compatibility

Expander operations now hold an internal mutex across shadow recovery and
read-modify-write. Camera worker callbacks and ordinary task callers cannot
overwrite each other's shadow updates. A lock timeout performs no bus write;
read outputs remain unchanged. Multi-call sequences affecting the same power
or reset lines still require application-level ownership. A deterministic
thread-barrier test proves two pin updates survive contention.

The camera wrapper preserves outputs on failure, including an attempted second
capture into the still-held frame. Only the original output object owns a
captured frame; foreign copies and duplicate releases do not free it or unlock
another operation. NULL outputs/callbacks fail before starting the backend.
Registration cannot replace an active process-lifetime backend. The stream
stop flag is atomic; shutdown completes buffer cleanup before releasing the
operation gate. Stream frames are borrowed only for the callback, and callback
context must survive until stop returns.

Public Watcher and shared camera headers specify task context, caller or
internal serialization, handle/buffer lifetime, failure state and blocking
policy. Capture/stream shutdown has no hard total deadline: native SPI calls,
callback duration and scheduling are outside the polling windows. Stop warns
after five seconds and continues waiting for the worker; it must never run
inside the frame callback. Audio uses an owning task or application mutex;
native codec/I2S timeouts do not establish a whole-operation deadline. Storage
requires all file/card operations to finish before unmount.

Public function signatures remain unchanged. Stricter behavior is intentional:
invalid audio volume is rejected, an unready battery cannot report presence,
alternate SD paths and repeated camera configuration are rejected, and camera
failure no longer clears a previously held frame. Callers must release the
exact captured frame object and must not independently close BSP-owned codec,
card or bus handles. Existing exported projects retain their locked imports;
new exports carry the corrected sources. A source rollback must keep the
driver, public contract and regression tests together; retained historical
evidence does not verify a changed source digest.

OPT-02 remains open. E1001/E1002 and Sticky display APIs, Indicator/XIAO display
APIs, and non-Watcher audio/microphone APIs still need the same ownership,
blocking and failure-contract review. No physical deadline, combined-load or
resource-bound claim is inferred from this slice.

## Validation and retained evidence

The complete gate passed **145/145**: **104 static/host checks**, **33 native
build/source checks** and **8 clean external-project builds**. The host gate
includes **16 native C test functions / 257 subprocess scenarios**. Six
retained original-source regressions fail the expected assertions before the
fixes: audio readiness, ADC ownership, camera frame retention, camera backend
rollback, camera board GPIO error handling and SD mount-path identity.

The [host receipt and case inventory](../../devices/sensecap-watcher/tests/logs/20261117180417Z-opt3-host-summary.json)
retain passed host results, test-source hashes, original-source failure
observations and coverage limits. Narrow SDK/transport/JSON doubles do not
simulate a camera or physical bus. Backend streaming tests execute the worker
deterministically when joining; they do not measure real RTOS scheduling.
Reported SDK errors are tested at the BSP boundary; errors hidden by vendor
cleanup implementations are not established by these doubles.

All 28 ESP-IDF examples used **ESP-IDF v6.0.2-dirty**, preserving and recording
pre-existing SDK modifications. Linux used **Python 3.14.6 / DTC 1.8.1** for
four source checks and overlay compilation. No Linux device demo was executed.

| Target | Native checks | Clean external project | Source-matched record |
| --- | --- | --- | --- |
| esp-idf/respeaker-lite | 3 passed | passed | [record](../../devices/respeaker-lite/tests/records/build-6c85d4c35c3710a2.json) |
| esp-idf/reterminal-e1001 | 4 passed | passed | [record](../../devices/reterminal-e1001/tests/records/build-959b8506c4ab6672.json) |
| esp-idf/reterminal-e1002 | 4 passed | passed | [record](../../devices/reterminal-e1002/tests/records/build-45ae94e2bc119444.json) |
| esp-idf/reterminal-sticky | 3 passed | passed | [record](../../devices/reterminal-sticky/tests/records/build-0f354f7eeb88f055.json) |
| esp-idf/sensecap-indicator | 3 passed | passed | [record](../../devices/sensecap-indicator/tests/records/build-6ba9e2247d013425.json) |
| esp-idf/sensecap-watcher | 8 passed | passed | [record](../../devices/sensecap-watcher/tests/records/build-660a7654abcf113c.json) |
| esp-idf/xiao-s3-147 | 3 passed | passed | [record](../../devices/xiao-s3-147/tests/records/build-fea43c1cb0a6d7a6.json) |
| linux/reterminal | 5 passed | passed | [record](../../devices/reterminal/tests/records/build-ecd337c0530a1810.json) |

All eight Target source digests matched the complete-gate receipts before
recording. Documentation-language/link checks and generated-view checks passed.
There were no failed or skipped checks in this gate. Arduino remains without
a registered hardware Target, and simulator support remains explicitly absent
under the existing scope decision.

Physical verification and live cloud execution remain **not_run**. No device
was flashed, no API operation was executed, and no commit, push or publication
was performed. OPT-06/07/10/16/18/19 retain their external evidence requirements;
the remaining software items also stay open until their own acceptance criteria
are met.
