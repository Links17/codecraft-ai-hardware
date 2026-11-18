# reTerminal Sticky

Generated from device.json. Edit typed facts and regenerate; never edit this view.

## Overview

Portrait e-paper, keys and temperature/humidity sensing.

Use the listed standalone examples as the supported development entry points.

unknown; revision-specific orientation and imagery have not been verified.

Revision: unknown

## Specs

### Controller

- Physical flash capacity: **unknown** — Historical sources claim 32 MB while the native configuration uses 16 MB; identify the actual chip.
- Controller: **ESP32-S3** — [documented](../../devices/reterminal-sticky/reference/hardware.md)
- PSRAM capacity: **8 MB** — [documented](../../devices/reterminal-sticky/reference/hardware.md)

### Connectivity

- Bus: **I2C1** — [documented](../../devices/reterminal-sticky/reference/hardware.md)

### Inputs

- Keys: **AI/Up/Down** — [documented](../../devices/reterminal-sticky/reference/hardware.md)
- Environmental sensor: **SHT4x** — [documented](../../devices/reterminal-sticky/reference/hardware.md)

### Outputs

- Display: **SSD1677** — [documented](../../devices/reterminal-sticky/reference/hardware.md)
- Native panel height: **480 px** — [documented](../../devices/reterminal-sticky/reference/hardware.md)
- Native panel width: **800 px** — [documented](../../devices/reterminal-sticky/reference/hardware.md)

### Power

- Power: **unknown** — No independently confirmed value is retained; consult the original reference for limitations.

### Accessories

- Accessories: **unknown** — No independently confirmed value is retained; consult the original reference for limitations.

## Targets

- [esp-idf/reterminal-sticky](../../platforms/esp-idf/targets/reterminal-sticky/README.md)

## Evidence

Build/project: build-verified. Device: not_run. Maintenance: unassigned. Maturity: experimental.

- Physical board revision and fresh on-device verification are not recorded.
- Read the original hardware reference for unsupported drivers, prerequisites and known limitations.

## Source conflicts

- Use vendor-supported physical facts; the native flash configuration is not a measurement. Sticky physical capacity remains unknown pending chip identification. [Source](../../devices/reterminal-sticky/reference/hardware.md)

## Assets

[Manifest](assets/manifest.json)

No verified redistributable image is registered.

## References

- [hardware.md](../../devices/reterminal-sticky/reference/hardware.md)
- [bsp_pins.h](../../platforms/esp-idf/targets/reterminal-sticky/bsp/include/bsp_pins.h)
- [vendor-notes.md](../../devices/reterminal-sticky/reference/vendor-notes.md)
- [build-d6802099ca960cf4.json](../../devices/reterminal-sticky/tests/records/build-d6802099ca960cf4.json)

## Vendor links

- [Source 1](https://www.seeedstudio.com/sticky/docs/en/device-guide/hardware-overview/)
