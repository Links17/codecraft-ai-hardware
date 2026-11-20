# SenseCAP Watcher

## Overview

Display, touch, camera, audio, knob, battery and microSD reference implementations.

## Profile

| Field | Value |
| --- | --- |
| ID | sensecap-watcher |
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

- SoC: ESP32-S3, 32 MB flash, 8 MB octal PSRAM (80 MHz) with XIP
  (`SPIRAM_XIP_FROM_PSRAM`, fetch instructions + rodata).
  Source: reference `../../devices/sensecap-watcher/targets/sdkconfig.defaults`.
- Camera: Himax WiseEye2 vision coprocessor, Seeed SSCMA protocol over SPI2
  (12 MHz, mode 0), power/sync/reset on a PCA9535 IO expander (I2C0 @0x21).
  Driver: `platforms/esp-idf/components/sscma_client/` (from reference `components/camera/`,
  Apache 2.0, source attribution retained). Board glue: `bsp/src/bsp_camera.c`.
  The chip is reset by power-cycling its rail (reference-verified); the vendor's
  expander reset pin stays an input.
- LCD, touch, knob, IO expander, audio, battery and SD card pins live in the
  vendor BSP: `SenseCAP-Watcher-Firmware/components/sensecap-watcher/include/sensecap-watcher.h`
  and are transcribed with sources into `bsp/include/bsp_pins.h`.
- Power measurements require the actual board revision, supply and workload;
  no current source-bound power characterization is recorded.

### Vendor source

[Seeed-Studio/SenseCAP-Watcher-Firmware][vendor];
`examples/factory_firmware/` is the shipping firmware. xiaozhi-esp32's
sensecap-watcher board is a second reference.

### Source locations

Primary links identify vendor sources; inspect the stated files and revisions before changing hardware facts.

| Board | Vendor source | Where to look |
| --- | --- | --- |
| SenseCAP Watcher | [Seeed-Studio/SenseCAP-Watcher-Firmware][vendor] | `components/sensecap-watcher/` is the vendor BSP. `include/sensecap-watcher.h` has the pins for the LCD, touch, knob, IO expander, audio, battery, SD card and the Himax camera chip (driven through `components/sscma_client/`). `examples/factory_firmware/` is the firmware it ships with. xiaozhi-esp32's [sensecap-watcher board][vendor-2] is a second reference. |

Native pin citations: [bsp_pins.h][bsp-pins]. Software configuration and examples belong to the [Target][readme].

## Implementation references

The [esp-idf/sensecap-watcher Target][readme] provides the native reference implementation. Header and example names below are relative to that Target. Keep hardware behavior and implementation guidance here; the Target owns executable code, software-stack bindings and build configuration.

### Reference interfaces
| Header | Native interface |
|---|---|
| `bsp_camera.h` | Himax WiseEye2 over SSCMA/SPI2: rail power, boot, JPEG capture |
| `bsp_display.h` | SPD2010 QSPI panel (esp_lcd), backlight |
| `bsp_touch.h` | SPD2010 touch (I2C1, polled; IRQ is an expander pin) |
| `bsp_audio.h` | ES8311 DAC + ES7243 mic ADC via esp_codec_dev 1.6.2 (I2S0) |
| `bsp_knob.h` | quadrature wheel (PCNT) + push button |
| `bsp_battery.h` | presence + terminal voltage (gated divider, ADC1 CH2) |
| `bsp_sdcard.h` | microSD over SDSPI, shared SPI2 (CS=46, detect/rail on expander) |
| `bsp_io_expander.h` | PCA9535 IO expander |

Pin facts with sources: [bsp_pins.h][bsp-pins].

### Reference examples

- `camera_capture` — one JPEG over SSCMA: powers the Himax rail, boots the
  chip, samples at 640x480, logs size/dimensions, powers back off.
- `display_color_bars` — raw esp_lcd on the SPD2010: vertical color bands
  drawn one row at a time, then a backlight fade. No LVGL.
- `battery_status` — presence (expander BAT_DET) + terminal voltage every
  second (gated 62k/20k divider onto ADC1 channel 2).
- `knob_input` — quadrature wheel via PCNT (GPIO41/42) and the push on
  expander pin 3 (active low).
- `touch_read` — polls the SPD2010 touch controller (I2C1, SDA=GPIO39,
  SCL=GPIO38) and logs press coordinates; the interrupt line is expander
  pin 5, not a real GPIO, so the driver polls.
- `audio_tone` — 1 kHz sine on the ES8311 DAC + PA (I2S0), then a volume
  sweep; replays every 5 s.
- `mic_level` — RMS level meter from the ES7243/ES7243E mic ADC (variant
  auto-detected on I2C0), with a dBFS bar graph.
- `sdcard_test` — mounts the microSD slot (SDSPI, second device on the
  shared SPI2 bus next to the camera; CS=GPIO46, detect on expander pin 4,
  rail on pin 8), writes and reads back a file, unmounts.

## Specifications

### Controller

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Flash capacity (`flash`) | integer | 32 | MB | documented | [device-notes][device-notes] | {value} MB flash |
| Controller (`mcu`) | string | ESP32-S3 | — | documented | [device-notes][device-notes] | SoC: {value}, |
| PSRAM capacity (`psram`) | integer | 8 | MB | documented | [device-notes][device-notes] | {value} MB octal PSRAM |

### Connectivity

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Bus (`bus`) | string | SPI2 | — | documented | [device-notes][device-notes] | Seeed SSCMA protocol over {value} |

### Inputs

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Camera coprocessor (`camera`) | string | Himax WiseEye2 | — | documented | [device-notes][device-notes] | Camera: {value} vision coprocessor |
| Knob (`knob`) | string | quadrature wheel | — | documented | [device-notes][device-notes] | &#124; bsp_knob.h &#124; {value} (PCNT) |

### Outputs

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Display (`display`) | string | SPD2010 | — | documented | [device-notes][device-notes] | &#124; bsp_display.h &#124; {value} QSPI panel |

### Power

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Battery measurement (`battery_measurement`) | string | presence + terminal voltage | — | documented | [device-notes][device-notes] | &#124; bsp_battery.h &#124; {value} |

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

### audio-tone

- Interfaces: audio, gpio
- Source: [target][target]

Run `audio_tone` under the confirmed write scope and observe the selected hardware.

Expected: audible tone, no clipping

### battery-status

- Interfaces: gpio, power
- Source: [target][target]

Run `battery_status` under the confirmed write scope and observe the selected hardware.

Expected: plausible mV, charging flag when USB in

### camera-capture

- Interfaces: camera, gpio
- Source: [target][target]

Run `camera_capture` under the confirmed write scope and observe the selected hardware.

Expected: JPEG frame saved, plausible size

### display-color-bars

- Interfaces: display, gpio
- Source: [target][target]

Run `display_color_bars` under the confirmed write scope and observe the selected hardware.

Expected: bars render, correct order/orientation

### knob-input

- Interfaces: gpio, input
- Source: [target][target]

Run `knob_input` under the confirmed write scope and observe the selected hardware.

Expected: events follow rotation/press

### mic-level

- Interfaces: audio, gpio
- Source: [target][target]

Run `mic_level` under the confirmed write scope and observe the selected hardware.

Expected: level rises when speaking

### sdcard-test

- Interfaces: gpio, storage
- Source: [target][target]

Run `sdcard_test` under the confirmed write scope and observe the selected hardware.

Expected: mount + write/read-back OK (FAT card)

### touch-read

- Interfaces: display, gpio, touch
- Source: [target][target]

Run `touch_read` under the confirmed write scope and observe the selected hardware.

Expected: coordinates track finger

## Sources

- [device-notes][device-notes]
- [bsp-pins][bsp-pins]
- [readme][readme]
- [vendor][vendor]

[device-notes]: AGENTS.md#hardware-notes
[target]: targets/target.json
[bsp-pins]: targets/bsp/include/bsp_pins.h
[readme]: targets/README.md
[vendor]: https://github.com/Seeed-Studio/SenseCAP-Watcher-Firmware
[vendor-2]: https://github.com/78/xiaozhi-esp32/tree/main/main/boards/sensecap-watcher
