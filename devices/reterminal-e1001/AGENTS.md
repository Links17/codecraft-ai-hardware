# reTerminal E1001

## Overview

Monochrome e-paper with keys, environmental sensing, power, RTC and storage.

## Profile

| Field | Value |
| --- | --- |
| ID | reterminal-e1001 |
| Format | 5 |
| Revision | unknown |
| Maintenance | unassigned |
| Maturity | experimental |

## Usage

Use the listed standalone examples as the supported development entry points.

## Physical layout

unknown; revision-specific orientation and imagery have not been verified.

## Hardware notes

Battery-powered 800x480 monochrome e-paper terminal: ESP32-S3R8
(8 MB octal PSRAM), 32 MB flash, SHT4x temperature/humidity, PCF8563 RTC,
SY6974B charger for the 2000 mAh LiPo, buzzer, PDM mic, microSD, three top
keys and a green status LED.

### Source locations

Primary links identify vendor sources; inspect the stated files and revisions before changing hardware facts.

| Board | Vendor source | Where to look |
| --- | --- | --- |
| reTerminal E1001 / E1002 | [Zephyr board definitions][vendor] (`reterminal_e1001` / `reterminal_e1002`, Apache 2.0, vendor-contributed) + [E1001 V1.2 schematic][vendor-2] (CC BY-SA 4.0) | The dts + pinctrl dtsi are the cleanest facts: key/LED GPIOs and active levels, battery ADC divider + enable, I2C addresses (SHT4x 0x44, PCF8563 0x51, SY6974B 0x6B), buzzer PWM, 32 MB flash. The schematic confirms flash size and power topology. UC8179 (E1001) and Spectra 6 (E1002) refresh sequences came from reference `../../devices/reterminal-e1001/targets/bsp/include/bsp_pins.h` / `epd_spectra6.c`. PCF8563 RTC register handling follows `zephyr:drivers/rtc/rtc_pcf8563.c`; the SY6974B charger driver follows `zephyr:drivers/charger/charger_sy6974b.c` (register map, part-ID check, reset/watchdog init) with board defaults from the dts (1000 mA / 4208 mV). |

Native pin citations: [bsp_pins.h][bsp-pins]. Software configuration and examples belong to the [Target][readme].

## Implementation references

The [esp-idf/reterminal-e1001 Target][readme] provides the native reference implementation. Header and example names below are relative to that Target. Keep hardware behavior and implementation guidance here; the Target owns executable code, software-stack bindings and build configuration.

### Reference interfaces
| Header | Native interface |
|---|---|
| `bsp_epd.h` | UC8179 panel: 1 bpp framebuffer (MSB leftmost, 1 = white), full/fast refresh, panel deep-sleeps after each update |
| `bsp_button.h` | green / Left / Right keys (GPIO 3/4/5, active low, debounced) |
| `bsp_led.h` | green status LED (GPIO 6, active low) |
| `bsp_sht4x.h` | temperature/humidity, single-shot, CRC-checked |
| `bsp_battery.h` | battery millivolts (ADC1 CH0, 10k/10k divider, enable GPIO 21) |
| `bsp_rtc.h` | PCF8563 real-time clock on I2C0 |
| `bsp_charger.h` | SY6974B charger status/limit control on I2C1 |
| `bsp_buzzer.h` | buzzer tones (LEDC PWM, GPIO 45) |
| `bsp_mic.h` | PDM microphone capture (CLK 42 / DATA 41 / EN 38) |
| `bsp_sdcard.h` | microSD over SDSPI on SPI2 (shared with the panel), rail + card-detect |

Pin facts with sources: [bsp_pins.h][bsp-pins].

### Reference examples

- `epd_hello` — checkerboard + bars pattern, one full refresh; demonstrates
  the framebuffer format and the refresh cycle.
- `sht4x_battery` — 10 s sampling loop of sensor + battery, LED blink per
  sample, key press samples immediately.
- `board_health` — exercises every peripheral once and prints a summary.
- `sdcard_test` — mounts the microSD slot, writes and reads back a file;
  insert a FAT-formatted card first.

### Hardware behavior and limits

- Flash: 32 MB W25Q256JV (vendor schematic + Zephyr dts). the Target configuration uses the sourced capacity.
- The UC8179 has no partial-refresh waveform here: "fast" refresh is the
  reference/GxEPD2 GDEY075T7 sequence. Do not invent a partial refresh.
- Board heat warms the onboard SHT4x; apply an offset in the application
  only after measurements support it.

## Specifications

### Controller

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Flash capacity (`flash`) | integer | 32 | MB | documented | [device-notes][device-notes] | {value} MB flash |
| Controller (`mcu`) | string | ESP32-S3R8 | — | documented | [device-notes][device-notes] | terminal: {value} |
| PSRAM capacity (`psram`) | integer | 8 | MB | documented | [device-notes][device-notes] | {value} MB octal PSRAM |

### Connectivity

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Storage bus (`storage_bus`) | string | SDSPI on SPI2 | — | documented | [device-notes][device-notes] | microSD over {value} |

### Inputs

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Keys (`keys`) | string | three top keys | — | documented | [device-notes][device-notes] | microSD, {value} and |
| Environmental sensor (`sensor`) | string | SHT4x | — | documented | [device-notes][device-notes] | flash, {value} temperature/humidity |

### Outputs

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Display (`display`) | string | UC8179 | — | documented | [device-notes][device-notes] | &#124; bsp_epd.h &#124; {value} panel: |
| Native panel height (`display_height`) | integer | 480 | px | documented | [device-notes][device-notes] | 800x{value} |
| Native panel width (`display_width`) | integer | 800 | px | documented | [device-notes][device-notes] | {value}x480 |

### Power

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Battery (`battery`) | integer | 2000 | mAh | documented | [device-notes][device-notes] | the {value} mAh LiPo |
| Charger (`charger`) | string | SY6974B | — | documented | [device-notes][device-notes] | {value} charger for |

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
| [device-notes][device-notes] | E1001 uses the sourced 32 MB W25Q256JV capacity; the native configuration and partition table must remain within it. |

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

### board-health

- Interfaces: audio, environment, power, rtc
- Source: [target][target]

Run `board_health` under the confirmed write scope and observe the selected hardware.

Expected: all three keys register, LED toggles; time sets and survives reboot; SY6974B part ID match, charge status on USB; PDM samples non-zero, level follows noise; audible beep

### epd-hello

- Interfaces: display, led
- Source: [target][target]

Run `epd_hello` under the confirmed write scope and observe the selected hardware.

Expected: pattern renders fully, no ghosting streaks; E1002 shows 6 colors

### sdcard-test

- Interfaces: storage
- Source: [target][target]

Run `sdcard_test` under the confirmed write scope and observe the selected hardware.

Expected: mount + write/read-back OK; **also verify the panel still works after the SD bus init** (shared SPI2)

### sht4x-battery

- Interfaces: environment, input, led, power
- Source: [target][target]

Run `sht4x_battery` under the confirmed write scope and observe the selected hardware.

Expected: plausible temp/RH/mV

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
[vendor]: https://github.com/zephyrproject-rtos/zephyr/tree/main/boards/seeed/reterminal_e1001
[vendor-2]: https://files.seeedstudio.com/wiki/reterminal_e10xx/res/202004307_reTerminal_E1001_V1_2_SCH_251120.pdf
