# SenseCAP Watcher

Generated from device.json. Edit typed facts and regenerate; never edit this view.

## Overview

Display, touch, camera, audio, knob, battery and microSD reference implementations.

Use the listed standalone examples as the supported development entry points.

unknown; revision-specific orientation and imagery have not been verified.

Revision: unknown

## Specs

### Controller

- Flash capacity: **32 MB** — [documented](../../devices/sensecap-watcher/reference/hardware.md)
- Controller: **ESP32-S3** — [documented](../../devices/sensecap-watcher/reference/hardware.md)
- PSRAM capacity: **8 MB** — [documented](../../devices/sensecap-watcher/reference/hardware.md)

### Connectivity

- Bus: **SPI2** — [documented](../../devices/sensecap-watcher/reference/hardware.md)

### Inputs

- Camera coprocessor: **Himax WiseEye2** — [documented](../../devices/sensecap-watcher/reference/hardware.md)
- Knob: **quadrature wheel** — [documented](../../devices/sensecap-watcher/reference/hardware.md)

### Outputs

- Display: **SPD2010** — [documented](../../devices/sensecap-watcher/reference/hardware.md)

### Power

- Battery measurement: **presence + terminal voltage** — [documented](../../devices/sensecap-watcher/reference/hardware.md)

### Accessories

- Accessories: **unknown** — No independently confirmed value is retained; consult the original reference for limitations.

## Targets

- [esp-idf/sensecap-watcher](../../platforms/esp-idf/targets/sensecap-watcher/README.md)

## Evidence

Build/project: unknown. Device: not_run. Maintenance: unassigned. Maturity: experimental.

- Physical board revision and fresh on-device verification are not recorded.
- Read the original hardware reference for unsupported drivers, prerequisites and known limitations.

## Source conflicts

No additional resolved conflict recorded.

## Assets

[Manifest](assets/manifest.json)

No verified redistributable image is registered.

## References

- [hardware.md](../../devices/sensecap-watcher/reference/hardware.md)
- [bsp_pins.h](../../platforms/esp-idf/targets/sensecap-watcher/bsp/include/bsp_pins.h)
- [vendor-notes.md](../../devices/sensecap-watcher/reference/vendor-notes.md)
- [hardware-checklist.md](../../devices/sensecap-watcher/tests/hardware-checklist.md)

## Vendor links

- [Source 1](https://github.com/Seeed-Studio/SenseCAP-Watcher-Firmware)
