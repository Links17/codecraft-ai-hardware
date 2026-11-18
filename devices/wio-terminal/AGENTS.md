# Wio Terminal

Generated from device.json. Edit typed facts and regenerate; never edit this view.

## Overview

SAMD51 terminal with LCD, buttons, sensors, microSD and separate Wi-Fi/BLE scan examples.

Use the standalone native sketches and their explicit physical test procedures.

See the cited vendor schematic and hardware reference; revision-specific imagery is not registered.

Revision: unknown; source schematic v1.2 does not identify a connected board

## Specs

### Controller

- MCU: **ATSAMD51P19A** — [documented](../../devices/wio-terminal/reference/hardware.md)
- RAM: **192 KB** — [documented](../../devices/wio-terminal/reference/hardware.md)

### Connectivity

- Wireless coprocessor: **RTL8720DN** — [documented](../../devices/wio-terminal/reference/hardware.md)

### Inputs

- Accelerometer: **LIS3DHTR** — [documented](../../devices/wio-terminal/reference/hardware.md)

### Outputs

- Buzzer pin: **12 GPIO** — [documented](../../devices/wio-terminal/reference/hardware.md)
- Display: **ILI9341** — [documented](../../devices/wio-terminal/reference/hardware.md)

### Power

- Power limits: **unknown** — No source-bound qualification is recorded for the actual connected assembly.

### Accessories

- Accessory qualification: **unknown** — No source-bound qualification is recorded for the actual connected assembly.

## Targets

- [arduino/wio-terminal](../../platforms/arduino/targets/wio-terminal/README.md)

## Evidence

Build/project: build-verified. Device: not_run. Maintenance: unassigned. Maturity: experimental.

- Current source-bound on-device acceptance has not been performed. Recorded observations do not certify new source bytes.

## Source conflicts

No additional resolved conflict recorded.

## Assets

[Manifest](assets/manifest.json)

No verified redistributable image is registered.

## References

- [hardware.md](../../devices/wio-terminal/reference/hardware.md)
- [toolchain.md](../../devices/wio-terminal/reference/toolchain.md)
- [hardware-checklist.md](../../devices/wio-terminal/tests/hardware-checklist.md)
- [observations.md](../../devices/wio-terminal/tests/observations.md)
- [build-b27b9742df9a333a.json](../../devices/wio-terminal/tests/records/build-b27b9742df9a333a.json)

## Vendor links

- [Source 1](https://files.seeedstudio.com/wiki/Wio-Terminal/res/Wio-Terminal-SCH-v1.2.pdf)
- [Source 2](https://wiki.seeedstudio.com/Wio-Terminal-Getting-Started/)
