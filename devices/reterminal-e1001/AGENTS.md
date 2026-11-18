# reTerminal E1001

Generated from device.json. Edit typed facts and regenerate; never edit this view.

## Overview

Monochrome e-paper with keys, environmental sensing, power, RTC and storage.

Use the listed standalone examples as the supported development entry points.

unknown; revision-specific orientation and imagery have not been verified.

Revision: unknown

## Specs

### Controller

- Flash capacity: **32 MB** — [documented](../../devices/reterminal-e1001/reference/hardware.md)
- Controller: **ESP32-S3R8** — [documented](../../devices/reterminal-e1001/reference/hardware.md)
- PSRAM capacity: **8 MB** — [documented](../../devices/reterminal-e1001/reference/hardware.md)

### Connectivity

- Storage bus: **SDSPI on SPI2** — [documented](../../devices/reterminal-e1001/reference/hardware.md)

### Inputs

- Keys: **three top keys** — [documented](../../devices/reterminal-e1001/reference/hardware.md)
- Environmental sensor: **SHT4x** — [documented](../../devices/reterminal-e1001/reference/hardware.md)

### Outputs

- Display: **UC8179** — [documented](../../devices/reterminal-e1001/reference/hardware.md)
- Native panel height: **480 px** — [documented](../../devices/reterminal-e1001/reference/hardware.md)
- Native panel width: **800 px** — [documented](../../devices/reterminal-e1001/reference/hardware.md)

### Power

- Battery: **2000 mAh** — [documented](../../devices/reterminal-e1001/reference/hardware.md)
- Charger: **SY6974B** — [documented](../../devices/reterminal-e1001/reference/hardware.md)

### Accessories

- Accessories: **unknown** — No independently confirmed value is retained; consult the original reference for limitations.

## Targets

- [esp-idf/reterminal-e1001](../../platforms/esp-idf/targets/reterminal-e1001/README.md)

## Evidence

Build/project: build-verified. Device: not_run. Maintenance: unassigned. Maturity: experimental.

- Physical board revision and fresh on-device verification are not recorded.
- Read the original hardware reference for unsupported drivers, prerequisites and known limitations.

## Source conflicts

- E1001 uses the sourced 32 MB W25Q256JV capacity; the native configuration and partition table must remain within it. [Source](../../devices/reterminal-e1001/reference/hardware.md)

## Assets

[Manifest](assets/manifest.json)

No verified redistributable image is registered.

## References

- [hardware.md](../../devices/reterminal-e1001/reference/hardware.md)
- [bsp_pins.h](../../platforms/esp-idf/targets/reterminal-e1001/bsp/include/bsp_pins.h)
- [vendor-notes.md](../../devices/reterminal-e1001/reference/vendor-notes.md)
- [hardware-checklist.md](../../devices/reterminal-e1001/tests/hardware-checklist.md)
- [build-965dea5578207f5c.json](../../devices/reterminal-e1001/tests/records/build-965dea5578207f5c.json)

## Vendor links

- [Source 1](https://github.com/zephyrproject-rtos/zephyr/tree/main/boards/seeed/reterminal_e1001)
- [Source 2](https://files.seeedstudio.com/wiki/reterminal_e10xx/res/202004307_reTerminal_E1001_V1_2_SCH_251120.pdf)
