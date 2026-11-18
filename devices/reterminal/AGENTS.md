# reTerminal (CM4)

## Overview

Linux peripheral overlay and input, LED, buzzer, sensor and GPIO demos.

## Profile

| Field | Value |
| --- | --- |
| ID | reterminal |
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

Source for every row: Seeed-Studio/seeed-linux-dtoverlays
`overlays/rpi/reTerminal-overlay.dts` (file header MIT), pinned at commit
`1d53c3cf2c96` (2026-10-21). The overlay declares "reTerminal V1.9".

| Function | Interface | Address / pin | Notes |
|---|---|---|---|
| Buttons F1–F4 | MCP23008 IO expander, pins 0/2/1/3 (note the 1↔2 swap) | expander @ I2C1 0x38 | active low; KEY_A/S/D/F (codes 30/31/32/33); 5 ms debounce |
| Power button | GPIO13 (SoC) | — | active low, KEY_SLEEP (142), pull-up |
| User LEDs ×3 | MCP23008 pins 4/5/6 | — | active low, `usr_led0..2` |
| Buzzer | MCP23008 pin 7 | — | active **high**, exposed as `usr_buzzer` LED node |
| Expander IRQ | GPIO6 (SoC) | — | falling edge, pull-up |
| Light sensor | LTR-303ALS | I2C1 @0x29 | iio device `ltr303` |
| Accelerometer | LIS331DLH | I2C1 @0x19 | iio device `lis331dlh` |
| RTC | PCF8563 | I2C3 @0x51 | bus at 100 kHz |
| Display + touch | ILI9881x over DSI1, config @ I2C1 0x45 | — | needs Seeed's out-of-tree modules; see `overlays/README.md` |

Board I2C1 runs at 300 kHz per the vendor overlay.

### Source locations

Primary links identify vendor sources; inspect the stated files and revisions before changing hardware facts.

| Board | Vendor source | Where to look |
| --- | --- | --- |
| reTerminal (CM4) | [Seeed-Studio/seeed-linux-dtoverlays][vendor-2], pinned at commit `1d53c3cf2c96` | `overlays/rpi/reTerminal-overlay.dts` (file header MIT) has every peripheral fact: MCP23008 @I2C1 0x38 pin map (buttons 0/2/1/3, LEDs 4-6 active low, buzzer 7 active high), expander IRQ GPIO6, power key GPIO13, LTR-303 @0x29, LIS331DLH @0x19, PCF8563 @I2C3 0x51, I2C1 300 kHz. Display/touch need Seeed's out-of-tree modules (`modules/ili9881d`); the repo-level COPYING is GPLv2, so link rather than vendor it. |

Software configuration and examples belong to the [Target][readme].

## Implementation references

The [Linux Target][readme] provides the peripheral overlay and reference demos for buttons, LEDs, buzzer, sensors and header GPIO. Its [Target manifest][target] maps device interfaces to the native sources. Hardware signals and constraints are documented above; OS interfaces, overlay installation and runtime dependencies are owned by the Linux Target.

## Specifications

### Controller

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Controller (`mcu`) | string | CM4 | — | documented | [device-notes][device-notes] | reTerminal ({value}) |

### Connectivity

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| IO expander (`expander`) | string | MCP23008 | — | documented | [device-notes][device-notes] | &#124; Buttons F1–F4 &#124; {value} IO expander, |

### Inputs

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Accelerometer (`accelerometer`) | string | LIS331DLH | — | documented | [device-notes][device-notes] | Accelerometer &#124; {value} &#124; |
| Keys (`keys`) | string | Buttons F1–F4 | — | documented | [device-notes][device-notes] | &#124; {value} &#124; |
| Light sensor (`light_sensor`) | string | LTR-303ALS | — | documented | [device-notes][device-notes] | Light sensor &#124; {value} &#124; |

### Outputs

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Buzzer (`buzzer`) | string | Buzzer | — | documented | [device-notes][device-notes] | &#124; {value} &#124; |
| User lights (`leds`) | string | User LEDs ×3 | — | documented | [device-notes][device-notes] | &#124; {value} &#124; |

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

## Physical acceptance

### Preconditions

Identify the actual unit, revision, required peripherals and authorized write scope. Run one selected native example at a time. Record source digest, toolchain, stimuli, actual observations and recovery; a plan or build is not a physical pass. RTC time retention and display/touch using the full vendor overlay are separate checks: fit the RTC battery and compare timedatectl/hwclock across a power cycle; verify panel output and touch with the vendor drivers. They are outside the registered native interface acceptance below.

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

### buttons-evdev

- Interfaces: input
- Source: [target][target]

Run `buttons_evdev` under the confirmed write scope and observe the selected hardware.

Expected: F1/F2/F3/O events

### header-gpio-blink

- Interfaces: gpio
- Source: [target][target]

Run `header_gpio_blink` under the confirmed write scope and observe the selected hardware.

Expected: BCM4 toggles (scope or LED)

### leds-buzzer-sysfs

- Interfaces: audio, led
- Source: [target][target]

Run `leds_buzzer_sysfs` under the confirmed write scope and observe the selected hardware.

Expected: LEDs cycle, buzzer chirps

### sensors-sysfs

- Interfaces: environment
- Source: [target][target]

Run `sensors_sysfs` under the confirmed write scope and observe the selected hardware.

Expected: lux + accel readings plausible

## Sources

- [device-notes][device-notes]
- [reterminal-peripherals-overlay][reterminal-peripherals-overlay]
- [vendor][vendor]

[device-notes]: AGENTS.md#hardware-notes
[target]: targets/target.json
[reterminal-peripherals-overlay]: targets/overlays/reterminal-peripherals-overlay.dts
[vendor]: https://github.com/Seeed-Studio/seeed-linux-dtoverlays/tree/1d53c3cf2c96
[vendor-2]: https://github.com/Seeed-Studio/seeed-linux-dtoverlays
[readme]: targets/README.md
