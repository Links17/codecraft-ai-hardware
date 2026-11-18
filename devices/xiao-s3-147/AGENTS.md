# XIAO ESP32-S3 1.47-inch Touch Display

## Overview

Small LCD, two buttons and PDM microphone; touch and storage are outside the registered Target interface scope.

## Profile

| Field | Value |
| --- | --- |
| ID | xiao-s3-147 |
| Format | 5 |
| Revision | unknown |
| Maintenance | unassigned |
| Maturity | experimental |

## Usage

Use the listed standalone examples as the supported development entry points.

## Physical layout

unknown; revision-specific orientation and imagery have not been verified.

## Hardware notes

### Hardware facts

- Controller: XIAO ESP32-S3 Plus (ESP32-S3, dual-core 240 MHz), 16 MB
  flash (DIO 80 MHz), 8 MB octal PSRAM (80 MHz).
  Sources: reference `../../devices/xiao-s3-147/targets/sdkconfig.defaults`,
  `../../devices/xiao-s3-147/targets/bsp/include/bsp_pins.h`.
- Display: 1.47" 172x320 IPS LCD, JD9853A on SPI2, driven with the
  ST7789-compatible esp_lcd driver plus Seeed's register sequence:
  MADCTL 0x48 (MX+BGR), X offset 34, Y offset 0, inversion off.
  CS=3, DC=4, SCLK=7, MOSI=9, RST=13 (shared with touch), BL=12
  (active high).
  Sources: Seeed_GFX2 (MIT) via reference
  `../../devices/xiao-s3-147/targets/bsp/include/bsp_pins.h`.
- Buttons: USR1=GPIO 11, USR2=GPIO 42, active low.
  Source: reference `board_seeed_xiao_s3_147.c`.
- PDM microphone on I2S0: CLK=1, DATA=2.
  Sources: Seeed_GFX2 `0519_DashBoard_147_ESP32` example, reference board file.
- Console: native USB Serial/JTAG (`303a:1001`); UART0's GPIO43/44 carry
  the SD chip-select and the touch interrupt.
  Source: reference `../../devices/xiao-s3-147/targets/bsp/include/bsp_pins.h`.

### Hardware outside registered native interfaces

- AXS5106L capacitive touch @0x63 (SDA=5, SCL=6, INT=44); the reset line
  is shared with the LCD and pulsed once at boot. Touch X is mirrored to
  match the panel orientation. Protocol reference: reference
  `../../devices/xiao-s3-147/targets/bsp/include/bsp_pins.h`.
- microSD slot (CS=43, held high when unused); LSM6DS3 IMU; battery
  input. All present on the board, outside the registered interfaces.

### Vendor source

[Seeed wiki][vendor]
and [Seeed_GFX2][vendor-2] (MIT) —
JD9853A register sequence, AXS5106L reports, PDM example.

### Source locations

Primary links identify vendor sources; inspect the stated files and revisions before changing hardware facts.

| Board | Vendor source | Where to look |
| --- | --- | --- |
| XIAO ESP32-S3 1.47" Touch Display | [Seeed wiki][vendor] + [Seeed-Studio/Seeed_GFX2][vendor-2] (MIT) | Seeed_GFX2 has the JD9853A register sequence (`Driver_JD9853A.cpp`), the AXS5106L touch reports, and the `0519_DashBoard_147_ESP32` PDM example. reference's field-verified `../../devices/xiao-s3-147/targets/bsp/include/bsp_pins.h` + `../../devices/xiao-s3-147/targets/bsp/include/bsp_pins.h` have the complete pin table and the USB-console constraint (UART0 pins taken by SD CS and touch INT). |

Native pin citations: [bsp_pins.h][bsp-pins]. Software configuration and examples belong to the [Target][readme].

## Implementation references

The [esp-idf/xiao-s3-147 Target][readme] provides the native reference implementation. Header and example names below are relative to that Target. Keep hardware behavior and implementation guidance here; the Target owns executable code, software-stack bindings and build configuration.

### Reference interfaces
| Header | Native interface |
|---|---|
| `bsp_display.h` | JD9853A panel via esp_lcd ST7789 + vendor sequence, backlight |
| `bsp_button.h` | USR1/USR2 keys with debounce task |
| `bsp_mic.h` | PDM microphone, mono 16-bit PCM |

Pin facts with sources: [bsp_pins.h][bsp-pins].

### Reference examples

- `display_hello` — red/green/blue bands on the panel.
- `button_hello` — USR1 logs, USR2 toggles the backlight.
- `mic_level` — PDM mic RMS level bar on the console.

## Specifications

### Controller

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Flash capacity (`flash`) | integer | 16 | MB | documented | [device-notes][device-notes] | {value} MB flash |
| Controller (`mcu`) | string | XIAO ESP32-S3 Plus | — | documented | [device-notes][device-notes] | Controller: {value} |
| PSRAM capacity (`psram`) | integer | 8 | MB | documented | [device-notes][device-notes] | {value} MB octal PSRAM |

### Connectivity

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Console connection (`console`) | string | native USB Serial/JTAG | — | documented | [device-notes][device-notes] | Console: {value} |

### Inputs

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Keys (`keys`) | string | USR1/USR2 | — | documented | [device-notes][device-notes] | &#124; bsp_button.h &#124; {value} keys |
| Microphone (`mic`) | string | PDM microphone | — | documented | [device-notes][device-notes] | - {value} on I2S0: |

### Outputs

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Display (`display`) | string | JD9853A | — | documented | [device-notes][device-notes] | 172x320 IPS LCD, {value} on SPI2 |
| Native panel height (`display_height`) | integer | 320 | px | documented | [device-notes][device-notes] | 172x{value} |
| Native panel width (`display_width`) | integer | 172 | px | documented | [device-notes][device-notes] | {value}x320 |

### Power

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Battery (`battery`) | string | battery input | — | documented | [device-notes][device-notes] | LSM6DS3 IMU; {value}. |

### Accessories

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Accessories (`accessories_details`) | string | — | — | unknown | — | No independently confirmed value is retained; consult the original reference for limitations. |

## Limitations

- Physical board revision and fresh on-device verification are not recorded.
- Read the original hardware reference for unsupported drivers, prerequisites and known limitations.

## Physical acceptance

### Preconditions

Identify the actual unit, revision, required peripherals and authorized write scope. Run one selected native example at a time. Record source digest, toolchain, stimuli, actual observations and recovery; a plan or build is not a physical pass.

### identity

- Interfaces: none
- Source: [target][target]

Record board identity, observed revision, connected port/drive and approved write scope.

Expected: Identity and revision are unambiguous and match this Device.

### recovery

- Interfaces: none
- Source: [target][target]

After the functional cases, power-cycle/restart using the documented normal procedure.

Expected: Device returns to the documented working state; record failures and recovery steps.

### button-hello

- Interfaces: display, input
- Source: [target][target]

Run `button_hello` under the confirmed write scope and observe the selected hardware.

Expected: USR1 logs, USR2 toggles the backlight.

### display-hello

- Interfaces: display
- Source: [target][target]

Run `display_hello` under the confirmed write scope and observe the selected hardware.

Expected: red/green/blue bands on the panel.

### mic-level

- Interfaces: audio
- Source: [target][target]

Run `mic_level` under the confirmed write scope and observe the selected hardware.

Expected: PDM mic RMS level bar on the console.

## Sources

- [device-notes][device-notes]
- [bsp-pins][bsp-pins]
- [readme][readme]
- [vendor][vendor]
- [vendor-2][vendor-2]

[device-notes]: AGENTS.md#hardware-notes
[target]: targets/target.json
[bsp-pins]: targets/bsp/include/bsp_pins.h
[readme]: targets/README.md
[vendor]: https://wiki.seeedstudio.com/getting_started_1.47_inch_touch_display_esp32s3/
[vendor-2]: https://github.com/Seeed-Studio/Seeed_GFX2
