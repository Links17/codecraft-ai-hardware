# Recorded device observations

Source: repository commit f457d9d08f33844b99d2ed217824f02c6ec81cd7. These dated observations apply to the sketches and units stated in that source. They do not certify newly changed code; current acceptance procedures are in [Device AGENTS.md](../../../devices/grove-beginner-kit/AGENTS.md#physical-acceptance) and source-bound results remain in records/.

## Grove Beginner Kit for Arduino (ATmega328P, Arduino)

Required toolchain: `arduino:avr@1.8.8` with FQBN `arduino:avr:uno`, plus the
exact libraries pinned in `platforms/arduino/targets/grove-beginner-kit/target.json`.
Target hardware: **post-October-2025 kit revision only**. Run `i2c_scan`
first and require DHT20 at 0x38 plus an SPA06-003 ACK at 0x77/0x76; the
SPA06 sketch additionally verifies device ID 0x11. The 2020 DHT11/BMP280
revision is out of scope and has no sketch in this directory.

| # | Check | Example / how | Expected |
|---|-------|---------------|----------|
| 1 | I2C inventory | `i2c_scan` | 0x19, 0x38, 0x3C/0x3D and 0x77/0x76 appear; record the exact addresses |
| 2 | LED | `led_blink` | steady 1 Hz on/off; serial prints both phases |
| 3 | Button | `button_led` | LED follows D6; one line per debounced transition |
| 4 | Potentiometer | `potentiometer` | raw range spans a useful part of 0-1023; LED switches near midpoint with hysteresis |
| 5 | Passive buzzer | `buzzer_tones` | four ascending tones (440/880/1760/2000 Hz) and a silent gap |
| 6 | Light sensor | `light_sensor` | raw value falls when covered and the LED turns on below the dark threshold |
| 7 | Sound sensor | `sound_sensor` | clap/speech raises the 50 ms peak; LED lights above raw 400 and releases after the hold |
| 8 | OLED | `oled_status` | four text rows and a once-per-second uptime counter; note orientation |
| 9 | DHT20 | `temperature_humidity_dht20` | `DHT20 on I2C 0x38`; plausible readings every second |
| 10 | SPA06-003 | `air_pressure_spa06` | detection at 0x77 or 0x76; pressure/temperature/altitude lines repeat |
| 11 | Accelerometer | `accelerometer` | `LIS3DHTR on I2C 0x19`; still magnitude near 1 g; axes change with tilt; LED indicates motion |

Record the USB bridge (CH340 on Lotus v1.0, CP2102N on v1.1), the power
source, and the `arduino:avr` core version. The board revision must still be
confirmed by the 0x38 I2C result. A compile is not an on-device pass.

When reporting results, note: board revision, power source, and the relevant
toolchain version (Arduino core, ESP-IDF `idf.py --version`, or OS/kernel
`uname -a`).

Recorded results (2026-10-29, Seeeduino Lotus v1.1, CP2102N, USB-powered,
`arduino:avr@1.8.8`):

- ✅ `i2c_scan` — 9600-baud serial reported 0x19 LIS3DHTR, 0x38 DHT20,
  0x3C OLED and 0x77 SPA06-003, repeated across scans. This confirms the
  post-October-2025 revision and the expected four-device I2C inventory.
- ✅ `led_blink` — serial repeatedly printed `LED=ON` and `LED=OFF` at the
  500 ms half-period after reset. LED emission itself was not captured by an
  instrument.
- ✅ `button_led` — boot state was `Button=RELEASED LED=OFF`; four physical
  press/release cycles produced matching `Button=PRESSED LED=ON` and
  `Button=RELEASED LED=OFF` lines.
- ✅ `potentiometer` — turning A0 through its full travel swept `raw` from 0
  to 1023 (0-100 %, 0-5000 mV). The LED switched on above the 532 threshold
  and off below 492, and held its state at `raw=503` and `526`, inside the
  hysteresis band.
- ✅ `buzzer_tones` — serial continuously cycled `440`, `880`, `1760` and
  `2000 Hz` followed by `silence 1500 ms`. Audible output was not captured by
  an instrument.
- ✅ `light_sensor` — ambient light read `raw=776-781` (`3.8 V`) with
  `LED=OFF`. Covering the photoresistor drove `raw` to 0-26 and printed
  `LED=ON`; removing the hand returned to `raw=779` and `LED=OFF`. The pass
  through `raw=21-26` stayed `LED=ON`, confirming the 200/260 hysteresis. The
  user confirmed the LED lit and went out. A first covering attempt produced
  no change because the wrong module was covered; a six-pin analog probe then
  showed A6 responding (777 to 0) while A7 tracked it down to about 80.
- ✅ `sound_sensor` — ambient 50 ms peaks stayed at 100-170 with `LED=OFF`.
  Two hand claps next to the module produced `peak=561 LED=ON` and later
  `peak=686 LED=ON`; the next sample held `LED=ON` at `peak=162`/`282` and
  then released to `LED=OFF`, confirming the 100 ms hold. The user confirmed
  the LED effect.
- ✅ `oled_status` — serial printed monotonically increasing `uptime` values
  from 2 s onward after the OLED initialized. The user confirmed that the
  panel displayed correctly on 2026-10-29.
- ✅ `temperature_humidity_dht20` — initialized at 0x38 and reported
  43.8–44.0 %RH at 26.2 C with about one sample per second.
- ✅ `air_pressure_spa06` — the library accepted SPA06-003 (device ID 0x11)
  at 0x77 and reported approximately 101170 Pa, 27.4 C and 12.8 m
  barometric altitude.
- ✅ `accelerometer` — initialized at 0x19 and rested at `X≈-0.01`,
  `Y≈0.14`, `Z≈0.98`, `|a|≈1.00 g`, `LED=REST`. Tilting and shaking drove
  the axes through X -0.82 to +1.16 g, Z 0.05 to 1.40 g and |a| 0.14 to
  1.60 g, and every sample during the motion printed `LED=ACTIVE`; the board
  returned to `LED=REST` once still. The rest offset shifted slightly after
  the shake (X -0.03 g, Y 0.12 g), consistent with the LIS3DHTR offset.

## accelerometer: Measured on 2026-10-29

Seeeduino Lotus v1.1 sitting flat: `X≈-0.01 g`, `Y≈0.14 g`, `Z≈0.98 g`,
`|a|≈1.00 g`, `LED=REST`. The ~0.14 g Y bias is the part offset, not tilt.

The kit board lying flat therefore reads roughly Y/Z, not X/Z. Tilting and
shaking moved X over -0.82 to +1.16 g, Z over 0.05 to 1.40 g and |a| over
0.14 to 1.60 g; every sample during the motion reported `LED=ACTIVE` and the
board returned to `LED=REST` when still. After the shake the rest offset
moved to `X≈-0.03 g`, `Y≈0.12 g`. Source: measured result.

## light_sensor: Measured on 2026-10-29

Seeeduino Lotus v1.1, indoor room light: A6 reads raw 776-781 (3.8 V) with
`LED=OFF`. A hand fully covering the photoresistor drives A6 to 0-26 and the
LED turns on; a brief partial cover gave raw 76-118, which also lit the LED.
Removing the hand restores raw 779 and `LED=OFF`. Source: measured result.

Two traps worth knowing when repeating this:

- Covering the wrong module leaves A6 unchanged at about 777. The
  photoresistor is the small disc with a zigzag pattern.
- A6 and A7 both respond to the same photoresistor; A7 falls only to about
  raw 80. Use A6, which is the documented pin.

## sound_sensor: Measured on 2026-10-29

Seeeduino Lotus v1.1, quiet room: 50 ms peaks stay at 100-170 with
`LED=OFF`. Two hand claps about 20 cm from the microphone produced
`peak=561` and `peak=686`, each followed by `LED=ON`; the next samples held
`LED=ON` at `peak=162` and `282` before returning to `LED=OFF`. Source:
measured result.

The 400 threshold therefore has roughly 2x headroom over room noise and the
clap envelope reaches well above it. A clap from across the room does not
reliably trigger; bring the hand close to the microphone capsule.
