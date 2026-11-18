# Recorded device observations

Source: repository commit f457d9d08f33844b99d2ed217824f02c6ec81cd7. These dated observations apply to the sketches and units stated in that source. They do not certify newly changed code; current source-bound acceptance is recorded separately in acceptance.json and records/.

## Wio Terminal (SAMD51, Arduino)

Required toolchain: `Seeeduino:samd@1.8.6` plus the exact libraries pinned in
`platforms/arduino/targets/wio-terminal/target.json`. Wi-Fi/BLE additionally require
compatible RTL8720DN eRPC firmware; it is not updated by an Arduino upload.

| # | Check | Example / how | Expected |
|---|-------|---------------|----------|
| 1 | Display + all inputs | `display_buttons` | landscape 320x240 UI; every A/B/C and five-way event appears on LCD and serial |
| 2 | Accelerometer | `accelerometer` | `0x18` probe succeeds; X/Y/Z change with tilt; still magnitude near 1 g |
| 3 | Light sensor | `light_sensor` | raw/mV changes when the sensor window is covered; direction recorded, not assumed |
| 4 | Analog microphone | `microphone_level` | peak-to-peak/RMS rise when speaking or whistling, return near baseline in silence |
| 5 | Passive buzzer | `buzzer_tones` | A gives 440 Hz/250 ms, B gives 4 kHz/120 ms, C stops the output |
| 6 | microSD | `sd_card_log` | FAT32 card ≤16 GB mounts; root lists; `/wio_terminal.log` receives a line |
| 7 | IR emitter | `ir_nec_sender` | a 38 kHz receiver decodes NEC address `0x00` and commands `0x45`/`0x10`/`0x02` |
| 8 | Grove I2C | `grove_i2c_scan` | a known 3.3 V J4 device's address appears; removing it yields no ACK |
| 9 | Wi-Fi | `wifi_scan` | RTL eRPC responds; nearby SSIDs/RSSI appear; record the firmware version; no association is attempted |
| 10 | BLE | `ble_scan` | RTL firmware verified; nearby BLE advertiser appears; no pairing/connection |

Run the Wi-Fi and BLE demos one at a time. The repository has no concurrent
wireless example.

Recorded results (2026-10-28):

- ✅ `display_buttons` — landscape LCD rendered the input map; A/B/C and
  five-way events appeared on LCD and serial; user confirmed.
- ✅ `accelerometer` — online at `0x18` (`WHO_AM_I` `0x33`); final mapping
  `displayX = -yg`, `displayY = xg`; dot rolled correctly with tilt; user
  confirmed.
- ✅ `light_sensor` — raw baseline approximately 14-20 counts under room
  light; user confirmed. Cover/uncover direction was not recorded.
- ✅ `microphone_level` — quiet peak-to-peak 162-666, RMS 37-129; speech or
  whistling reached peak-to-peak 3458 and RMS about 1578, then returned to
  baseline; user confirmed the LCD bar.
- ✅ `buzzer_tones` — 440 Hz and 4 kHz tones were audible, C stopped the
  output, and serial matched the A/B/C actions.
- ✅ `sd_card_log` — FAT32 card mounted, six root entries listed, and
  `/wio_terminal.log` grew from 98 to 147 bytes after a reset; LCD remained
  normal.
- ➖ `ir_nec_sender` — 940 nm emission observed on an iPhone camera at the
  back emitter; a 38 kHz receiver has not decoded the NEC frames.
- ➖ `grove_i2c_scan` — empty J4 reports zero devices after the `0x7F` prime
  fix; no external Grove device was available, so device detection remains
  pending.
- ✅ `wifi_scan` — the RTL8720DN eRPC firmware already installed on the test
  unit accepted the sketch; serial scans returned nearby 2.4 GHz and 5 GHz
  SSIDs with RSSI around -40 to -46 dBm, and the user confirmed the LCD.
  `rpc_system_version()` was not queried, so no RTL firmware version is
  recorded.
- ✅ `ble_scan` — coprocessor firmware 2.1.3 (`rpc_system_version()`); after
  an explicit `ble_start()` each five-second pass reported several hundred
  advertisements and listed nearby devices with names, addresses and RSSI; the
  user confirmed the LCD. The blocking `BLEScan::start` overload froze the UI
  on this unit, so the demo uses the non-blocking overload.

## accelerometer: source observation

Verified on 2026-10-28: the probe succeeded at `0x18` with `WHO_AM_I` `0x33`.
The final screen mapping was corrected on hardware to `displayX = -yg` and
`displayY = xg`; the dot then rolled in the correct downhill direction when
the board was tilted. The user confirmed the final behavior.

## ble_scan: source observation

Verified on a Wio Terminal with coprocessor firmware 2.1.3:

1. The scan reported several hundred advertisements per five-second pass and
   listed real nearby devices with names, addresses and negative RSSI values.
2. The local address displayed on line 3 is non-zero, which shows the BT stack
   is up.

## buzzer_tones: source observation

Verified on 2026-10-28: the board printed `tone 440 Hz for 250 ms`,
`tone 4000 Hz for 120 ms`, and `buzzer stopped` for repeated A/B/C presses.
The user confirmed that both tones were audible, the LCD action field followed
each press, and no tone continued after its finite duration or after C.

## display_buttons: source observation

Verified on 2026-10-28: the landscape LCD rendered the full input map, A/B/C
and five-way events appeared on both LCD and serial, and the user confirmed
the demo. No electrical timing measurement was made.

## grove_i2c_scan: source observation

Verified on 2026-10-28: after adding the `0x7F` prime fix, an empty J4 bus
reported zero devices and no serial address lines. A temporary probe found the
onboard IMU at `0x18` on `Wire1`, confirming the scanner logic. No external
Grove I2C device was available in this session, so device detection was not
performed and remains pending.

## ir_nec_sender: source observation

Verified on 2026-10-28: the user observed the 940 nm emission on an iPhone
camera after pointing it at the back emitter, left of the microSD slot. This
proves LED activity, not NEC protocol validity; decoding with a 38 kHz
receiver remains pending.

## light_sensor: source observation

Verified on 2026-10-28: raw counts around 14-20 were observed under room
light, and the user confirmed the LCD/serial demo. The cover/uncover
direction was not recorded in this run; measure it before setting a
threshold.

## microphone_level: source observation

Verified on 2026-10-28: with the room quiet, peak-to-peak was approximately
162-666 counts and RMS approximately 37-129 counts. During speech/whistling,
peak-to-peak reached 3458 counts and RMS reached approximately 1578 counts;
after the sound stopped, both returned to the quiet baseline. The user also
confirmed that the LCD level bar followed the sound.

## sd_card_log: source observation

Verified on 2026-10-28 with a FAT32 card already present: the board listed six
root files, appended `/wio_terminal.log`, and read back
`log_bytes=98 last_line=wio-terminal sd_card_log mounted at millis=3494`.
After a second reset the read-back grew to `log_bytes=147` with a new
`millis=3714` line, proving append behavior. The user confirmed the LCD result.

## wifi_scan: source observation

Recorded on 2026-10-28: the RTL8720DN eRPC firmware already installed on the
test unit accepted the sketch; serial scans returned nearby 2.4 GHz and
5 GHz SSIDs with RSSI around -40 to -46 dBm, and the user confirmed the LCD.
`rpc_system_version()` was not queried, so no firmware version is claimed.
