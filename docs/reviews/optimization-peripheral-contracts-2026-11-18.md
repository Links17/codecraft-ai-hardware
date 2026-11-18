# BSP peripheral and caller contracts — 2026-11-18

Scope: the remaining **OPT-02** interfaces and their existing example callers,
using the **OPT-03** native test harness. This snapshot introduces no new TODO.
It follows the [I/O snapshot](optimization-io-contracts-2026-11-18.md) and the
[optimization ledger](../development/optimization-plan.md).

## Result and evidence

The complete gate passed **167/167**: **126 static/host checks**, **33 native
build/source checks**, and **8 clean external-project builds**. There were no
failed or skipped results. All eight current Target digests matched the
complete-gate receipts before evidence was recorded.

The [retained host receipt](../../devices/sensecap-indicator/tests/logs/20261117191822Z-opt5-host-summary.json) contains the case inventory,
passed host rows, test-source hashes, original failure observations, the
41-header contract inventory and hashes of inspected native implementations.

The full native test inventory is **38 host functions / 772 C scenarios**.
This slice adds **13 functions / 245 scenarios**: 233 BSP scenarios and 12
example scenarios. Native C is compiled with warnings treated as errors and
executed against narrow SDK-boundary doubles. Twenty-four selected scenarios
also fail at runtime against retained pre-change sources whose hashes match
the starting snapshot. These failures establish software regressions, not a
physical reproduction. The original-source compilation permits pre-existing
unused parameters; compilation errors are not counted as reproductions.

## Changes at the owning layer

| Area | Contract and implementation | Verification |
| --- | --- | --- |
| E1001/E1002 battery | One task/application lock owns ADC, calibration and divider. Init is ready only after checked setup; failed channel/calibration setup releases the ADC. Only `NOT_SUPPORTED` permits the existing approximate voltage conversion. Every read attempts divider-off, including after enable failure. A failed off must recover before another sample. Outputs remain unchanged on error. | Setup/read failures, calibration fallback, incomplete rollback, repeat init and power recovery; 32 cases across both BSPs. |
| E1001/E1002 charger | Serialized startup owns I2C1, device and mutex. Ready follows the complete original register sequence. A device mutex spans each register read or complete read-modify-write; it does not make a sequence of public calls atomic. Failed startup releases resources in reverse order; uncertain cleanup requires reset. | 50 cases cover all startup operations, part ID, cleanup, null/unready outputs, partial native reads, lock timeout, deterministic competing transactions and original register encodings. |
| E1001/E1002 SD | One storage owner serializes mount, file/card use and unmount. The BSP owns a mount-path copy and lends the card until any native unmount attempt. Another path is rejected. Failed unmount blocks reuse until reset because native code may already have freed the card. Shared SPI2 and rail ownership are retained. | 30 cases cover path mutation, wrong paths, allocation/mount errors, card absence, an existing bus, output preservation and early/late unmount failure. |
| E1001/E1002 buzzer and LED | A task/application lock owns each peripheral. Ready requires checked native setup. Repeat init preserves an active tone/LED state. Buzzer operations reject unready use and zero frequency; positive short beeps request a delay of at least one tick. The existing void LED setter cannot return an error and logs uncertain writes. | 26 buzzer and 12 GPIO LED scenarios, including failed setup, retries, native runtime errors and preserved state. |
| reSpeaker LED | One task/application lock owns one RMT strip for process lifetime. Repeat init reuses it. Pixel, refresh and clear errors propagate. Native constructor cleanup limitations and potentially indefinite refresh waits are explicit. | Seven cases verify allocation ownership, repeat behavior, unready use and errors. |
| Indicator touch | Serialized startup owns touch and panel IO while retaining the shared expander/bus. A failed touch constructor releases its owned IO. Output publication requires success. Display, when used, must start first because it also pulses touch reset. The caller owns complete polling transactions and buffers. | Sixteen cases cover reset/setup errors, all four candidate addresses, missing devices, constructor/IO cleanup, optional outputs and repeats. |
| Six button BSPs | One process-lifetime worker owns debounce. Same callback/context registration is idempotent; replacement is rejected. Callback/context storage remains valid until reset. Pressed samples are atomic; invalid keys return false. Callbacks may begin before init returns and must not block. | Sixty scenarios cover GPIO/task failure, retry, duplicate registration, polling-only use, early callbacks, debounce, tick wrap, cross-task reads and coarse tick conversion. |

Native implementation and test ownership remain under the corresponding
`platforms/esp-idf/targets/<board>/`. The shared test runner and SDK-boundary
types live under `platforms/esp-idf/tests/`; they are not firmware abstractions
or a replacement SDK.

## Caller corrections

The contract audit included the existing example calls, not only headers.

- E100x `sht4x_battery` previously sampled and delayed inside the input callback
  while the main task accessed the same battery and LED. It now initializes
  services first, queues key requests without waiting, and performs all samples
  in the main task. A bounded full queue drops an extra request; periodic
  sampling continues. Tests include a callback before init returns, a full
  queue and the existing battery-only mode.
- Indicator `button_backlight` notifies its display owner. XIAO `button_hello`
  queues events to its display owner. Neither callback calls display APIs.
  Tests inject presses during registration and check the owner receives them.
- reSpeaker `button_led` publishes color through an atomic variable and reads
  one snapshot per frame. RMT and logging stay in the main task.
- Indicator and Watcher `touch_read` check both native polling results. A
  failed sample produces neither a fresh press nor a false release; cached
  coordinates are not presented as new data. Tests cover read and decode
  failures followed by a real release.

## Completed BSP contract inventory

The current seven ESP-IDF Targets expose **41 public runtime BSP headers**.
Seven additional pin headers contain hardware constants, and the two E100x
internal I2C headers retain their serialized-startup/process-lifetime contract.
The retained receipt hashes every public runtime header reviewed across the
successive snapshots. The table accounts for the complete current BSP scope.

| Target | Runtime headers | Ownership coverage |
| --- | --- | --- |
| reSpeaker Lite | 3: audio, button, LED | RX/TX owners plus serialized audio controls; button worker; LED owner |
| E1001 | 10: battery, button, buzzer, charger, EPD, LED, microphone, RTC, SD, SHT4x | Device transaction locks, EPD exclusion and documented task owners |
| E1002 | Same 10 interfaces, separately compiled/tested BSP | Same policies with independent board bindings |
| Sticky | 3: button, EPD, SHT4x | Button worker, EPD exclusion, shared sensor component transaction lock |
| Indicator | 4: button, display, expander, touch | Button worker, display/touch owners, expander transaction lock |
| Watcher | 8: audio, battery, camera, display, expander, knob, SD, touch | Existing lifecycle/ownership contracts plus checked touch example sampling |
| XIAO S3 1.47 | 3: button, display, microphone | Button worker, display/DMA buffer owner, microphone owner |

This closes OPT-02's software contract scope. It does not close combined-load
physical validation, revision compatibility or resource measurements in the
other optimization items.

## Timing, compatibility and limits

- All seven pin headers are unchanged. Existing bus numbers, addresses,
  polarities, charger defaults and native build systems are preserved.
  The charger still requests 1000 mA, encoded as 960 mA in its existing
  60 mA steps; this change does not establish a new charging specification.
- Battery settling now includes one scheduler tick beyond the nominal 10 ms.
  Button polling and positive beeps use at least one tick; zero-duration beeps
  request tone then immediate stop. These are scheduling policies, not measured
  electrical/acoustic timing or hard whole-call deadlines.
- Charger mutex and each I2C operation use their documented 100 ms policy;
  compound operations may take longer. Other native waits can be indefinite.
  Applications must use worker tasks and their documented ownership rules.
- SDK constructors own their internal partial allocations. The pinned RMT
  constructor hides deletion errors; panel-IO deletion can abort on an I2C
  removal failure. Host doubles cannot prove graceful recovery where the
  SDK does not provide it. Native implementation hashes are retained.
- No new button unregister, peripheral shutdown or runtime bus-reconfiguration
  API is promised. Process-lifetime ownership is intentional. Replacing a
  registered button callback is now an explicit invalid-state error.
- The E100x LED setter keeps its existing void signature. Its runtime error
  can be logged but not returned; physical state after that error is unknown.
- Host thread barriers establish the tested serialization/order. They do not
  prove real RTOS latency, bus arbitration, GPIO levels, battery accuracy,
  audio/display behavior, resource budgets or physical recovery.

## Native and external-project gate

All 28 ESP-IDF examples used **ESP-IDF v6.0.2-dirty**, preserving pre-existing
SDK modifications. Linux checks used **Python 3.14.6 / DTC 1.8.1**, including
overlay compilation; no Linux hardware demo was executed.

| Target | Native checks | Clean external project | Source-matched record |
| --- | --- | --- | --- |
| esp-idf/respeaker-lite | 3 passed | passed | [record](../../devices/respeaker-lite/tests/records/build-effc7b0054a3c831.json) |
| esp-idf/reterminal-e1001 | 4 passed | passed | [record](../../devices/reterminal-e1001/tests/records/build-6118d6ff8939639c.json) |
| esp-idf/reterminal-e1002 | 4 passed | passed | [record](../../devices/reterminal-e1002/tests/records/build-183d176ec74c361d.json) |
| esp-idf/reterminal-sticky | 3 passed | passed | [record](../../devices/reterminal-sticky/tests/records/build-3297d24708578f48.json) |
| esp-idf/sensecap-indicator | 3 passed | passed | [record](../../devices/sensecap-indicator/tests/records/build-4ced47b70950ac4e.json) |
| esp-idf/sensecap-watcher | 8 passed | passed | [record](../../devices/sensecap-watcher/tests/records/build-d1a93280c8e25cfa.json) |
| esp-idf/xiao-s3-147 | 3 passed | passed | [record](../../devices/xiao-s3-147/tests/records/build-11bda72e4e00071b.json) |
| linux/reterminal | 5 passed | passed | [record](../../devices/reterminal/tests/records/build-185705b68b8f42c8.json) |

Arduino has no registered hardware Target. Simulator support remains absent
under the existing scope decision. README language/link and generated-view
checks passed; a successful build does not change physical acceptance.

**On-device verification: not_run. Cloud API execution: not_run.** No firmware
was flashed, physical action performed, live cloud call made or artifact
published. The working tree remains uncommitted; source digests identify the
tested state. All remaining TODOs stay within OPT-01 through OPT-19.
