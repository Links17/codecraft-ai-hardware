# reTerminal Sticky

## Overview

Portrait e-paper, keys and temperature/humidity sensing.

## Profile

| Field | Value |
| --- | --- |
| ID | reterminal-sticky |
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

- SoC/memory: ESP32-S3, 8 MB octal PSRAM (80 MHz). Flash: the retained factory/reference notes claim 32 MB, while the Target
  configuration uses 16 MB. The installed capacity remains unverified. This Target uses a 16 MB address range until the flash chip is confirmed on hardware. This is a configured
  address range, not proof of the installed capacity.
  Sources: reference `../../devices/reterminal-sticky/targets/bsp/include/bsp_pins.h`
  header, `../../devices/reterminal-sticky/targets/sdkconfig.defaults`.
- Display: 3.97" SSD1677 e-paper, native 800x480, used portrait 480x800;
  1 bpp mono with full + fast refresh, plus a 4-gray image mode. SPI2:
  SCLK=13, MOSI=14, MISO=12, CS=15, DC=16, RST=17 (active low), BUSY=18
  (high = busy), panel power EN=47, 20 MHz.
  Source: the native pins header records the panel provenance from
  Seeed-reTerminal-E10xx-Firmware `factory_fw` and the MIT panel reference.
  The local pins header itself is Apache-2.0.
- Keys: AI=GPIO 4, Up=GPIO 5, Down=GPIO 6, active low.
  Source: reference `board_reterminal_sticky.c`.
- SHT4x temperature/humidity @0x44 on I2C1 (SDA=1, SCL=0), shared with
  the BQ27220 fuel gauge @0x55.
  Sources: reference `../../devices/reterminal-sticky/targets/bsp/include/bsp_pins.h` (Sticky bus pins),
  `board_reterminal_sticky.c` (gauge).
- PDM microphone on I2S0: CLK=19, DATA=20, power EN=38 (active high).
  Source: reference `board_reterminal_sticky.c`.

### Hardware outside registered native interfaces

- GT911 capacitive touch on I2C0 (SDA=3, SCL=2), address 0x5D (fallback
  0x14), power EN=42, RST=41, INT=21; the digitizer counts Y from the
  bottom, so Y is flipped in software.
- microSD over SDSPI on the panel's SPI2 bus: CS=8, power EN=10,
  card-detect=11 (low = inserted), MISO=12.
- Charger enable on GPIO 39: the reference board file drives it low at boot,
  but the active level is unconfirmed against factory_fw — treat as
  unverified until measured.

### Vendor source

The imported hardware reference headers credit Seeed's
`Seeed-reTerminal-E10xx-Firmware` `factory_fw`
(`main/boards/reterminal_e1005/`, MIT, JoJang2u) as the original board
source, but that repo could not be located publicly at the time of
writing, so reference's field-verified files are the citable source here.
Board-level reference:
[reTerminal Sticky hardware overview][vendor].

### Source locations

Primary links identify vendor sources; inspect the stated files and revisions before changing hardware facts.

| Board | Vendor source | Where to look |
| --- | --- | --- |
| reTerminal Sticky | [Sticky hardware overview][vendor] + the imported hardware reference (Apache 2.0, field-verified) | reference's `../../devices/reterminal-sticky/targets/bsp/include/bsp_pins.h` has the button/I2C/touch/mic/SD facts; `../../devices/reterminal-sticky/targets/bsp/include/bsp_pins.h` puts SHT4x on I2C1; `../../devices/reterminal-sticky/targets/bsp/include/bsp_pins.h` (MIT) carries the SSD1677 panel pins and refresh sequence. reference's headers credit `Seeed-reTerminal-E10xx-Firmware` `factory_fw` (`main/boards/reterminal_e1005/`, `components/seeed_epaper/driver/ssd1677.c`, MIT, JoJang2u) as the original source, but that repo could not be located publicly at the time of writing, so reference's field-verified files are the citable source. |

Native pin citations: [bsp_pins.h][bsp-pins]. Software configuration and examples belong to the [Target][readme].

## Implementation references

The [esp-idf/reterminal-sticky Target][readme] provides the native reference implementation. Header and example names below are relative to that Target. Keep hardware behavior and implementation guidance here; the Target owns executable code, software-stack bindings and build configuration.

### Reference interfaces
| Header | Native interface |
|---|---|
| `bsp_epd.h` | SSD1677 panel, 480x800 portrait: mono full/fast refresh + 4-gray mode |
| `bsp_button.h` | AI/Up/Down keys with debounce task |
| `bsp_sht4x.h` | SHT4x temperature/humidity on I2C1 |

Pin facts with sources: [bsp_pins.h][bsp-pins].

### Reference examples

- `epd_hello` — test pattern, full refresh, then an inverted fast refresh.
- `sht4x` — temperature/humidity log once a second.
- `button_hello` — log AI/Up/Down presses.

## Specifications

### Controller

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Physical flash capacity (`flash`) | integer | — | MB | unknown | — | Historical sources claim 32 MB while the native configuration uses 16 MB; identify the actual chip. |
| Controller (`mcu`) | string | ESP32-S3 | — | documented | [device-notes][device-notes] | SoC/memory: {value}, |
| PSRAM capacity (`psram`) | integer | 8 | MB | documented | [device-notes][device-notes] | {value} MB octal PSRAM |

### Connectivity

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Bus (`bus`) | string | I2C1 | — | documented | [device-notes][device-notes] | temperature/humidity @0x44 on {value} |

### Inputs

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Keys (`keys`) | string | AI/Up/Down | — | documented | [device-notes][device-notes] | &#124; bsp_button.h &#124; {value} keys |
| Environmental sensor (`sensor`) | string | SHT4x | — | documented | [device-notes][device-notes] | - {value} temperature/humidity |

### Outputs

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Display (`display`) | string | SSD1677 | — | documented | [device-notes][device-notes] | Display: 3.97" {value} e-paper |
| Native panel height (`display_height`) | integer | 480 | px | documented | [device-notes][device-notes] | 800x{value} |
| Native panel width (`display_width`) | integer | 800 | px | documented | [device-notes][device-notes] | {value}x480 |

### Power

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Power (`power_details`) | string | — | — | unknown | — | No independently confirmed value is retained; consult the original reference for limitations. |

### Accessories

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Accessories (`accessories_details`) | string | — | — | unknown | — | No independently confirmed value is retained; consult the original reference for limitations. |

## Limitations

- Physical board revision and fresh on-device verification are not recorded.
- Read the original hardware reference for unsupported drivers, prerequisites and known limitations.

## Source conflicts

| Source | Resolution |
| --- | --- |
| [device-notes][device-notes] | Use vendor-supported physical facts; the native flash configuration is not a measurement. Sticky physical capacity remains unknown pending chip identification. |

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

- Interfaces: input
- Source: [target][target]

Run `button_hello` under the confirmed write scope and observe the selected hardware.

Expected: log AI/Up/Down presses.

### epd-hello

- Interfaces: display
- Source: [target][target]

Run `epd_hello` under the confirmed write scope and observe the selected hardware.

Expected: test pattern, full refresh, then an inverted fast refresh.

### sht4x

- Interfaces: environment
- Source: [target][target]

Run `sht4x` under the confirmed write scope and observe the selected hardware.

Expected: temperature/humidity log once a second.

## Sources

- [device-notes][device-notes]
- [bsp-pins][bsp-pins]
- [readme][readme]
- [vendor][vendor]

[device-notes]: AGENTS.md#hardware-notes
[target]: targets/target.json
[bsp-pins]: targets/bsp/include/bsp_pins.h
[readme]: targets/README.md
[vendor]: https://www.seeedstudio.com/sticky/docs/en/device-guide/hardware-overview/
