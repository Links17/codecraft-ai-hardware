# Wio Terminal

## Overview

SAMD51 terminal with LCD, buttons, sensors, microSD and separate Wi-Fi/BLE scan examples.

## Profile

| Field | Value |
| --- | --- |
| ID | wio-terminal |
| Format | 5 |
| Revision | unknown; source schematic v1.2 does not identify a connected board |
| Maintenance | unassigned |
| Maturity | experimental |

## Usage

Use the standalone native sketches and their explicit physical test procedures.

## Physical layout

See the cited vendor schematic and hardware reference; revision-specific imagery is not registered.

## Hardware notes

### Hardware facts

- MCU: Microchip ATSAMD51P19A, Arm Cortex-M4F, 512 KB program flash and
  192 KB RAM. The Arduino core uses the standard 120 MHz clock.
  Source: [Wio Terminal schematic v1.2][vendor]
  sheet 02 (MCU and memory), the
  [product page][vendor-2],
  and `Seeeduino:samd@1.8.6` `boards.txt` (`seeed_wio_terminal`).
- External flash: W25Q32JVZPIM, 32 Mbit / 4 MB, on the QSPI bus. Source:
  schematic sheet 02. No example in this directory uses it yet.
- LCD: 2.4-inch 320x240 ILI9341 panel on SPI3. The core pin map gives SCK
  68, MOSI 67, MISO 66, CS 69, DC 70, reset 71 and backlight 72. The
  `TFT_eSPI` / `Seeed_Arduino_LCD` library bundled with the core selects the
  ILI9341 driver and these pins. Examples call `setRotation(3)` for a
  320-pixel-wide landscape view. Source: schematic sheet 07, core
  `variants/wio_terminal/variant.h`, and
  `libraries/Seeed_Arduino_LCD/User_Setup.h`.
- Top buttons: `WIO_KEY_A`, `WIO_KEY_B`, `WIO_KEY_C` on GPIO 28, 29 and 30;
  active low with external pull-ups. Source: schematic sheet 05 and core
  `variant.h`.
- Five-way switch: `WIO_5S_UP`, `WIO_5S_LEFT`, `WIO_5S_RIGHT`,
  `WIO_5S_DOWN`, `WIO_5S_PRESS` on GPIO 31, 32, 33, 34 and 35; active low.
  Source: schematic sheet 04 and core `variant.h`.
- IMU: ST LIS3DHTR on the internal `Wire1` bus, SDA 78, SCL 77, 7-bit
  address `0x18`; INT1 is GPIO 79. Source: schematic sheet 07 and core
  `variant.h` (`WIO_LIS3DH_SDA`, `WIO_LIS3DH_SCL`, `WIO_LIS3DH_INT`) for the
  bus and pins; the address comes from Seeed_Arduino_LIS3DHTR's
  `LIS3DHTR_DEFAULT_ADDRESS` (`0x19` is the library's alternate
  `LIS3DHTR_ADDRESS_UPDATED`). The variant macro `WIO_LIS3DH_WiRE` contains
  a vendor typo; use `Wire1`.
- Light sensor: photodiode output on `WIO_LIGHT`, GPIO 27 / ADC channel 15.
  The product lists a 400-1050 nm response. Source: schematic sheet 05 and
  core `variant.h`; spectrum range from the product page.
- Microphone: analog electret microphone and LMV358 gain stage, with the
  conditioned signal on `WIO_MIC`, GPIO 39 / ADC channel 12. Source:
  schematic sheet 04 and core `variant.h`. This is an analog level path, not
  a digital I2S microphone.
- Buzzer: passive buzzer B4013AM422-042 driven through Q4 from
  `WIO_BUZZER`, GPIO 12. It needs an AC/PWM waveform; the example uses the
  core `tone()` API. Source: schematic sheet 04 and core `variant.h`.
- microSD: dedicated SPI2 bus, SCK 63, MOSI 62, MISO 61, CS 64, card-detect
  65. The product page specifies cards up to 16 GB. Source: schematic sheet
  02, core `variant.h` (`SDCARD_*`), and the product page.
- Infrared emitter: 940 nm LED D10 driven through Q13 from `WIO_IR`, GPIO
  14; `IR_CTL` is active high. It is on the back of the enclosure, to the
  left of the microSD slot. This is a transmitter, not a receiver. Source:
  schematic sheet 05, core `variant.h`, the product page, and the Seeed wiki
  Getting Started with Infrared Emitter page.
- Grove connectors: the left J4 is I2C on `Wire`, SDA 46 / SCL 45, with a
  3.3 V supply. J4 has no onboard I2C pull-ups; a Grove module normally
  supplies them (schematic sheet 05 shows only the connector, decoupling and
  DNP SWD links). The right J5 exposes A0/D0 and A1/D1. Source: schematic
  sheet 05 and core `variant.h` (`PIN_WIRE_SDA`, `PIN_WIRE_SCL`). Only J4
  I2C has a maintained example here.
- Wireless: Realtek RTL8720DN, dual-band 2.4/5 GHz 802.11 a/b/g/n and BLE
  5.0. The SAMD51 connects to it over SPI1/UART and controls it with
  CHIP_PU GPIO 80 and IRQ0 GPIO 11. Source: schematic sheet 06, core
  `variant.h`, and the product page.
- Expansion: 40-pin Raspberry Pi-compatible header, a 20-pin FPC connector,
  USB Type-C power/OTG, I2S and DAC pins. These are present on the product
  but are not covered by the current examples; do not infer their use from
  this directory.

### Not provided

The vendor feature list and schematic v1.2 do not include a touch controller,
an onboard battery/charger, a speaker or audio codec, or a camera. Treat the
LCD as display-only, power the board from USB-C or the documented power pins,
and use the passive buzzer for audible output. Do not add libraries or pin
assignments for hardware that is not present.

Software configuration and examples belong to the [Target][readme].

## Implementation references

The [Arduino Target][readme] contains the native sketches and software integration settings. These hardware behaviors and implementation references apply to the stated examples.

- **RTL8720 firmware is separate.** Uploading an Arduino sketch only writes
  the ATSAMD51. Wi-Fi and BLE need compatible eRPC firmware on the
  RTL8720DN. Follow Seeed's
  [Wi-Fi firmware update guide][vendor-3]
  and verify the RTL firmware with `rpc_system_version()` before debugging
  sketch code. The repository does not pin a binary firmware release.
- The light sensor demo reports raw ADC and an estimated millivolt value; it
  is not calibrated to lux. The direction of the raw change is not asserted;
  observe it on the target unit before choosing a threshold.
- The microphone demo measures an analog AC envelope. It is not calibrated
  dB SPL and cannot record digital audio without additional sampling logic.
- `ir_nec_sender` is a blocking, bit-banged NEC transmitter. It has no
  receiver and no protocol decoder.
- `grove_i2c_scan` limits its scan to `0x08`-`0x77` and primes the bus with a
  reserved `0x7F` transaction. J4 has no onboard I2C pull-ups; a Grove module
  normally supplies them. Without a module, the first `Wire` transaction after
  idle can false-ACK the first address; this was measured and worked around.

Dated [physical observations][observations] identify the tested source and unit; they do not certify current code.

## Specifications

### Controller

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| MCU (`mcu`) | string | ATSAMD51P19A | — | documented | [device-notes][device-notes] | MCU: Microchip {value}, |
| RAM (`sram`) | integer | 192 | KB | documented | [device-notes][device-notes] | {value} KB RAM |

### Connectivity

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Wireless coprocessor (`wireless`) | string | RTL8720DN | — | documented | [device-notes][device-notes] | Wireless: Realtek {value}, |

### Inputs

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Accelerometer (`imu`) | string | LIS3DHTR | — | documented | [device-notes][device-notes] | IMU: ST {value} on |

### Outputs

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Buzzer pin (`buzzer`) | integer | 12 | GPIO | documented | [device-notes][device-notes] | WIO_BUZZER, GPIO {value}. |
| Display (`display`) | string | ILI9341 | — | documented | [device-notes][device-notes] | 320x240 {value} panel |

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

1. Build and upload with explicit authorization; open serial at 115200 baud.
2. Keep the board flat and still. Confirm the online message and a stable
   magnitude near 1 g.
3. Tilt once around each axis. Confirm the dot moves in the downhill
   direction with the measured mapping `displayX = -yg`, `displayY = xg`.
4. If the probe repeats `NOT FOUND at 0x18`, check `Wire1` and the address;
   do not switch to Grove `Wire` (GPIO 46/45).

Expected: Record the actual stimulus and output against the selected native interface contract; note deviations and recovery.

### ble-scan

- Interfaces: wireless
- Source: [target][target]

1. Confirm the coprocessor firmware with `rpc_system_version()`; a Wi-Fi-only
   or mismatched image changes the failure mode before any scan logic runs.
2. Build and upload with explicit authorization.
3. Place a known BLE advertiser nearby (a phone, beacon or another board).
4. Confirm its name or address appears and its RSSI changes plausibly with
   distance.
5. Run only this wireless demo while testing. Do not run the Wi-Fi sketch in
   parallel or assume combined behaviour from this repository.

Expected: Record the actual stimulus and output against the selected native interface contract; note deviations and recovery.

### buzzer-tones

- Interfaces: audio
- Source: [target][target]

1. Build and upload with explicit authorization; open serial at 115200 baud.
2. Press A and confirm a short, audible 440 Hz tone and the serial line.
3. Press B and confirm a higher-pitched, shorter beep.
4. Press A or B and then C; confirm the output stops and GPIO 12 is low.
5. Check that no tone continues indefinitely after a button action.

Expected: Record the actual stimulus and output against the selected native interface contract; note deviations and recovery.

### display-buttons

- Interfaces: display, input
- Source: [target][target]

1. Build and upload with explicit authorization.
2. Open the serial monitor at 115200 baud.
3. Press and release each of the eight inputs once.
4. Confirm exactly one press line and one release line per action, with the
   matching LCD box changing state.
5. Confirm the display is landscape and all labels fit without clipping.

Expected: Record the actual stimulus and output against the selected native interface contract; note deviations and recovery.

### grove-i2c-scan

- Interfaces: gpio
- Source: [target][target]

1. Build and upload with explicit authorization; open serial at 115200 baud.
2. Power down and connect one known 3.3 V Grove I2C device to the left J4.
3. Power up and confirm the device's documented address appears on the LCD and
   serial monitor within three seconds.
4. Disconnect the device and confirm the next scan reports `no ACK on Wire`.
5. Record the address and the external module part number; do not assume a
   generic address from another Grove product.

Expected: Record the actual stimulus and output against the selected native interface contract; note deviations and recovery.

### ir-nec-sender

- Interfaces: ir
- Source: [target][target]

1. Build and upload with explicit authorization; open serial at 115200 baud.
2. Point the **back** of the board (emitter left of the microSD slot)
   directly at a known 38 kHz demodulating receiver. A phone camera may show
   only a faint pulse and is not proof of a valid NEC frame; iPhone rear
   cameras often filter 940 nm. Use a TV remote as a camera control.
3. Press A, B and C one at a time and confirm the receiver decodes address
   `0x00` and commands `0x45`, `0x10`, `0x02` respectively.
4. Confirm the receiver does not decode a frame when no button is pressed.
5. If no frame is decoded, check line of sight, receiver supply and the GPIO
   14 drive before changing the NEC timings.

Expected: Record the actual stimulus and output against the selected native interface contract; note deviations and recovery.

### light-sensor

- Interfaces: input
- Source: [target][target]

1. Build and upload with explicit authorization; open serial at 115200 baud.
2. Record the raw value under normal room light.
3. Fully cover the sensor window and record the new value after it settles.
4. Uncover it and confirm the value returns in the opposite direction.
5. Use the observed direction and range to choose an application threshold;
   do not reuse a threshold from another unit without checking.

Expected: Record the actual stimulus and output against the selected native interface contract; note deviations and recovery.

### microphone-level

- Interfaces: audio
- Source: [target][target]

1. Build and upload with explicit authorization; open serial at 115200 baud.
2. With the room quiet, record a short baseline for mean, peak-to-peak and
   RMS.
3. Speak or whistle at a normal distance. Confirm all three values rise and
   fall with the sound.
4. Stop making noise and confirm the values return near the baseline.
5. If the signal is stuck at 0 or 4095, inspect the microphone path and the
   analog reference before changing the sketch.

Expected: Record the actual stimulus and output against the selected native interface contract; note deviations and recovery.

### sd-card-log

- Interfaces: storage
- Source: [target][target]

1. Format a card of 16 GB or less as FAT32 and insert it before power-up.
2. Build and upload with explicit authorization; open serial at 115200 baud.
3. Confirm `SD mounted`, root entries, `appended /wio_terminal.log`, and the
   read-back `log_bytes=` / `last_line=` values.
4. Remove the card, read it on a computer, and confirm
   `/wio_terminal.log` contains the mount line.
5. Reset and confirm `log_bytes` grows while `last_line` names the new mount;
   verify the LCD still renders normally and no LCD pin is disturbed.

Expected: Record the actual stimulus and output against the selected native interface contract; note deviations and recovery.

### wifi-scan

- Interfaces: wireless
- Source: [target][target]

1. Follow the vendor Wi-Fi firmware guide to install/verify compatible
   RTL8720DN eRPC firmware. Do not upload the sketch as a substitute for this
   step.
2. Build and upload with explicit authorization; open serial at 115200 baud.
3. Confirm the status progresses to `ready` and a scan reports networks that
   are actually present nearby.
4. Compare the strongest SSIDs/RSSI values with a known local access point;
   record the observed result rather than assuming 5 GHz coverage.
5. Run only this wireless demo while testing. Do not load the BLE sketch in
   parallel or expect concurrent Wi-Fi/BLE behavior from this repository.

Expected: Record the actual stimulus and output against the selected native interface contract; note deviations and recovery.

## Sources

- [device-notes][device-notes]
- [readme][readme]
- [observations][observations]
- [vendor][vendor]
- [vendor-2][vendor-2]

[device-notes]: AGENTS.md#hardware-notes
[target]: targets/target.json
[readme]: targets/README.md
[observations]: ../../tests/devices/wio-terminal/observations.md
[vendor]: https://files.seeedstudio.com/wiki/Wio-Terminal/res/Wio-Terminal-SCH-v1.2.pdf
[vendor-2]: https://wiki.seeedstudio.com/Wio-Terminal-Getting-Started/
[vendor-3]: https://wiki.seeedstudio.com/Wio-Terminal-Network-Overview/
