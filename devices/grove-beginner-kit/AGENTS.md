# Grove Beginner Kit for Arduino

## Overview

ATmega328P kit with ten Grove modules and standalone bus diagnostics.

## Profile

| Field | Value |
| --- | --- |
| ID | grove-beginner-kit |
| Format | 5 |
| Revision | post-October-2025 DHT20/SPA06-003 kit; identify the actual Lotus PCB revision |
| Maintenance | unassigned |
| Maturity | experimental |

## Usage

Use the standalone native sketches and their explicit physical test procedures.

## Physical layout

See the cited vendor schematic and hardware reference; revision-specific imagery is not registered.

## Hardware notes

### Hardware facts

- MCU: Microchip ATmega328P-MU, 16 MHz, 32 KB flash (32,256-byte sketch
  maximum), 2 KB SRAM and 1 KB EEPROM, 5 V logic. Seeeduino Lotus v1.0 uses
  a CH340 USB bridge; v1.1 uses CP2102N. Source:
  [Seeeduino Lotus wiki][vendor-7] and
  [v1.1 schematic][vendor-2].
- Hardware I2C: A4 is SDA (PC4, Arduino pin 18), A5 is SCL (PC5, pin 19), and
  the Grove connectors are 5 V logic. Source: Seeeduino Lotus v1.1
  schematic and the core's `standard` variant.
- Kit LED: Grove LED on D4, active high, with a board trimpot for brightness.
  D4 is not a PWM pin on this core. Source: kit wiki default-pin table and
  Lesson 1.
- Button: Grove Button on D6. The vendor example configures `INPUT` and reads
  pressed as `HIGH`, so the module provides its own pull-down. Source: kit
  wiki Lesson 2.
- Rotary potentiometer: Grove Rotary Potentiometer on A0; `analogRead()`
  returns 0-1023 using the 5 V reference. Source: kit wiki Lesson 3.
- Buzzer: Grove passive piezo buzzer on D5; it needs a square wave such as
  `tone()`, not a static DC level. Source: kit wiki Lesson 4.
- Light sensor: Grove Light on A6; the vendor example turns the LED on below
  raw 200. This is an uncalibrated analog level, not lux. Source: kit wiki
  Lesson 5.
- Sound sensor: Grove Sound on A2; the vendor example uses raw > 400 to
  indicate a sound peak. The output is an analog envelope, not calibrated
  dB SPL and not recorded audio. Source: kit wiki Lesson 6.
- OLED: 0.96-inch 128x64 SSD1306/SSD1315-compatible display on I2C. The kit
  wiki gives 0x78 as the 8-bit write address, which is 0x3C in 7-bit form;
  0x3D is accepted as an alternate in the demo. Source: kit wiki default-pin
  table and [OLED wiki][vendor-6].
- Temperature/humidity: the supported post-October-2025 kit uses DHT20 on
  I2C. The current vendor example calls `Wire.begin()`, the Grove DHT library
  uses fixed I2C address 0x38, and the wiki says a black
  humidity/temperature detector identifies this revision. Source: current kit
  wiki DHT20 section and
  [Grove_Temperature_And_Humidity_Sensor][vendor-3].
- Air pressure: the supported post-October-2025 kit uses SPA06-003 on I2C at
  0x77 by default, 0x76 optional. The SPA06 library verifies device ID 0x11.
  Source:
  [SPA06-003 wiki][vendor-8].
- Accelerometer: ST LIS3DHTR on I2C at 0x19. Source: kit wiki default-pin
  table and Lesson 10.

Most unchanged board connections above come from the
[Grove Beginner Kit wiki][vendor-5]
and the kit's
[schematic/PCB archive][vendor]
(the published schematic is dated 2020, revision v1.4). That schematic
predates the DHT20/SPA06-003 revision and does not document their sensor
routing. The current wiki and an `i2c_scan` of the target unit are the
authority for 0x38 and the SPA06-003 address.

### Not provided

The kit contains no Wi-Fi/BLE radio, motor driver, relay, battery/charger,
camera, or digital audio recorder. The "sound sensor" is an analog envelope
output. Do not add network, pairing, account, telemetry, or cloud code: this
repository is a local hardware reference only.

### Known constraints and source conflicts

- **Only the post-October-2025 revision is supported.** Run `i2c_scan` and
  require DHT20 at 0x38. If it is absent, stop and confirm the hardware
  revision; do not add a DHT11 fallback or apply the 2020 D3 wiring.
- **The published schematic predates the current sensors.** It does not
  document DHT20 or SPA06-003 routing. Treat 0x38 as the DHT20 probe result
  and require the SPA06 library's device-ID 0x11 check before claiming the
  pressure sensor is supported.
- **D4 has no PWM.** The LED demo is on/off only. PWM dimming needs the LED
  module broken out and reconnected to D3.
- **The button module has an external pull-down.** Use `INPUT`; `INPUT_PULLUP`
  would make an idle button read pressed.
- **I2C is shared and 5 V.** Address 0x19/0x3C-or-0x3D/0x38/0x77 may all be
  present on one board. Do not drive 3.3 V-only external devices from this
  bus without level shifting.
- **SRAM is 2 KB.** Use U8x8 text mode or stream readings; do not add a full
  framebuffer or large global buffers without checking the build size.
- **Raw analog values are not engineering units.** The potentiometer, light,
  and sound examples report ADC counts and estimated millivolts only. Lux and
  dB SPL require calibration that this repository has not performed.

Software configuration and examples belong to the [Target][readme].

## Implementation references

The [Arduino Target][readme] provides standalone sketches for the onboard modules and I2C diagnostics. Its [Target manifest][target] maps native interfaces to their implementing examples. Use the hardware notes above for wiring, assembly constraints and sourced module behavior, and the acceptance section below for the per-example procedures.

## Specifications

### Controller

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| MCU (`mcu`) | string | ATmega328P-MU | — | documented | [device-notes][device-notes] | MCU: Microchip {value}, |
| SRAM (`sram`) | integer | 2 | KB | documented | [device-notes][device-notes] | {value} KB SRAM |

### Connectivity

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| I2C SDA (`i2c_sda`) | string | A4 | — | documented | [device-notes][device-notes] | Hardware I2C: {value} is SDA |

### Inputs

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Button (`button`) | string | D6 | — | documented | [device-notes][device-notes] | Grove Button on {value}. |
| Pressure (`pressure`) | string | SPA06-003 | — | documented | [device-notes][device-notes] | kit uses {value} on I2C |
| Temperature and humidity (`temperature`) | string | DHT20 | — | documented | [device-notes][device-notes] | kit uses {value} on I2C. |

### Outputs

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| LED (`led`) | string | D4 | — | documented | [device-notes][device-notes] | Grove LED on {value}, active high |

### Power

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Power limits (`power`) | string | — | — | unknown | — | No source-bound qualification is recorded for the actual connected assembly. |

### Accessories

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Accessory qualification (`accessories`) | string | — | — | unknown | — | No source-bound qualification is recorded for the actual connected assembly. |

## Limitations

- Current source-bound on-device acceptance has not been performed. Recorded observations do not certify new source bytes.

## Physical acceptance

### Preconditions

Identify the actual unit, revision, required peripherals and authorized device-write scope before running these steps. Build and test one selected sketch at a time. Record source digest, toolchain, stimuli, actual results and recovery. These procedures are not validation results.

After testing, power-cycle and repeat the selected startup checks. Existing dated results are in [recorded observations][observations]; they do not certify current source bytes.

### identity

- Interfaces: none
- Source: [target][target]

Record board identity, observed revision, selected port and authorized write scope.

Expected: The observed assembly matches the documented pin map and supported sensors.

### recovery

- Interfaces: none
- Source: [target][target]

Power-cycle and rerun the selected sketch; record the startup state and any required peripherals.

Expected: The unit returns to the documented working state.

### accelerometer

- Interfaces: motion
- Source: [target][target]

1. Run `i2c_scan` and confirm 0x19.
2. Open the 9600-baud monitor and confirm the magnitude is near 1 g at rest.
3. Tilt the kit slowly; record which axis changes and in which direction.
4. Tap or shake gently; confirm the LED flashes `ACTIVE` and returns to
   `REST` when motion stops.

Expected: Record the actual stimulus and output against the selected native interface contract; note deviations and recovery.

### air-pressure-spa06

- Interfaces: environment
- Source: [target][target]

1. Run `i2c_scan` and record whether 0x77 or 0x76 is present.
2. Open the 9600-baud monitor and confirm the detected address.
3. Confirm lines repeat without blocking; the configured rate is 4 Hz but
   serial printing dominates the loop.
4. Carry the kit up or down a stair flight and compare the pressure and
   altitude trend after several samples.

Expected: Record the actual stimulus and output against the selected native interface contract; note deviations and recovery.

### button-led

- Interfaces: input, led
- Source: [target][target]

1. Open the 9600-baud monitor and confirm the initial released line.
2. Press and hold the button; confirm the LED follows immediately and the
   pressed line appears once.
3. Release; confirm the LED turns off and the released line appears once.

Expected: Record the actual stimulus and output against the selected native interface contract; note deviations and recovery.

### buzzer-tones

- Interfaces: audio
- Source: [target][target]

1. Open the 9600-baud monitor and listen.
2. Confirm four distinct ascending tones and the silent gap.
3. If no sound, verify D5 and the passive buzzer module; do not replace
   `tone()` with a static `digitalWrite(HIGH)`.

Expected: Record the actual stimulus and output against the selected native interface contract; note deviations and recovery.

### i2c-scan

- Interfaces: gpio
- Source: [target][target]

1. Power the intact kit over USB and open the 9600-baud monitor.
2. Confirm 0x19, 0x38, 0x3C or 0x3D, and 0x77 or 0x76 on an intact supported
   kit. The exact OLED and pressure addresses can differ as documented.
3. If modules are broken out, disconnect one known device and confirm its
   address disappears on the next scan.

Expected: Record the actual stimulus and output against the selected native interface contract; note deviations and recovery.

### led-blink

- Interfaces: led
- Source: [target][target]

1. Power the kit and open the 9600-baud monitor.
2. Confirm a steady 1 Hz blink.
3. If visible but dim, adjust the trimpot on the LED module; do not change
   the GPIO drive in software.

Expected: Record the actual stimulus and output against the selected native interface contract; note deviations and recovery.

### light-sensor

- Interfaces: environment
- Source: [target][target]

1. Open the 9600-baud monitor in room light and record the raw value.
2. Cover the sensor with your hand; confirm the raw value moves toward the
   dark threshold and the LED turns on.
3. Remove your hand; confirm the LED turns off above the upper threshold.

Expected: Record the actual stimulus and output against the selected native interface contract; note deviations and recovery.

### oled-status

- Interfaces: display
- Source: [target][target]

1. Run `i2c_scan` and record whether 0x3C or 0x3D is present.
2. Open the 9600-baud monitor and confirm the four text rows appear.
3. Watch for at least three counter updates and confirm the panel and serial
   agree.
4. If the text is upside down, the panel is mounted opposite to the
   `setFlipMode(1)` assumption; set it to 0 and re-check. Do not change the
   I2C address to work around orientation.

Expected: Record the actual stimulus and output against the selected native interface contract; note deviations and recovery.

### potentiometer

- Interfaces: input
- Source: [target][target]

1. Open the 9600-baud monitor.
2. Rotate the potentiometer from stop to stop and record the raw range.
3. Confirm the LED switches near the middle. Do not assume clockwise means
   increasing until observed on the unit.

Expected: Record the actual stimulus and output against the selected native interface contract; note deviations and recovery.

### sound-sensor

- Interfaces: input
- Source: [target][target]

1. Open the 9600-baud monitor or plotter in a quiet room.
2. Clap or speak near the sound sensor; confirm the printed peak rises and
   the LED turns on.
3. Let the room settle; confirm the LED returns off after the hold time.

Expected: Record the actual stimulus and output against the selected native interface contract; note deviations and recovery.

### temperature-humidity-dht20

- Interfaces: environment
- Source: [target][target]

1. Run `i2c_scan` and confirm 0x38. If it is missing, this is not the
   supported revision or the sensor is not connected. This Target requires the documented DHT20 assembly.
2. Open the 9600-baud monitor and confirm `DHT20 on I2C 0x38`.
3. Breathe gently near the sensor and wait several samples; humidity should
   move before temperature.
4. Confirm readings update about once per second.

Expected: Record the actual stimulus and output against the selected native interface contract; note deviations and recovery.

## Sources

- [device-notes][device-notes]
- [readme][readme]
- [observations][observations]
- [vendor][vendor]
- [vendor-2][vendor-2]
- [vendor-3][vendor-3]
- [vendor-4][vendor-4]
- [vendor-5][vendor-5]
- [vendor-6][vendor-6]
- [vendor-7][vendor-7]
- [vendor-8][vendor-8]

[device-notes]: AGENTS.md#hardware-notes
[target]: targets/target.json
[readme]: targets/README.md
[observations]: ../../tests/devices/grove-beginner-kit/observations.md
[vendor]: https://files.seeedstudio.com/wiki/Grove-Beginner-Kit-For-Arduino/res/Grove-Beginner-Kit-for-Arduino-SCH-PCB.zip
[vendor-2]: https://files.seeedstudio.com/wiki/Seeeduino_Lotus/res/Seeeduino%20Lotus%20v1.1%20SCH.pdf
[vendor-3]: https://github.com/Seeed-Studio/Grove_Temperature_And_Humidity_Sensor
[vendor-4]: https://github.com/arduino/ArduinoCore-avr/tree/1.8.8
[vendor-5]: https://wiki.seeedstudio.com/Grove-Beginner-Kit-For-Arduino/
[vendor-6]: https://wiki.seeedstudio.com/Grove-OLED-Display-0.96-SSD1315/
[vendor-7]: https://wiki.seeedstudio.com/Seeeduino_Lotus/
[vendor-8]: https://wiki.seeedstudio.com/grove_barometer_sensor_spa06_003/
