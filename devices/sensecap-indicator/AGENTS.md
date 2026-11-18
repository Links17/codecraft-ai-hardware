# SenseCAP Indicator

Generated from device.json. Edit typed facts and regenerate; never edit this view.

## Overview

RGB display, touch and a case button through native examples; sensor co-processor interfaces are outside the registered Target scope.

Use the listed standalone examples as the supported development entry points.

unknown; revision-specific orientation and imagery have not been verified.

Revision: unknown

## Specs

### Controller

- Flash capacity: **8 MB** — [documented](../../devices/sensecap-indicator/reference/hardware.md)
- Controller: **ESP32-S3** — [documented](../../devices/sensecap-indicator/reference/hardware.md)
- PSRAM capacity: **8 MB** — [documented](../../devices/sensecap-indicator/reference/hardware.md)

### Connectivity

- USB bridge: **CH340** — [documented](../../devices/sensecap-indicator/reference/hardware.md)

### Inputs

- Button: **top case button** — [documented](../../devices/sensecap-indicator/reference/hardware.md)
- Touch controller: **FT6336U** — [documented](../../devices/sensecap-indicator/reference/hardware.md)

### Outputs

- Display: **RGB** — [documented](../../devices/sensecap-indicator/reference/display-variants.md)
- Native panel height: **480 px** — [documented](../../devices/sensecap-indicator/reference/hardware.md)
- Native panel width: **480 px** — [documented](../../devices/sensecap-indicator/reference/hardware.md)

### Power

- Power: **unknown** — No independently confirmed value is retained; consult the original reference for limitations.

### Accessories

- Accessories: **unknown** — No independently confirmed value is retained; consult the original reference for limitations.

## Hardware variants

Panel/assembly choices do not identify a physical PCB revision.

### dx: DX display assembly

[Source](../../devices/sensecap-indicator/reference/display-variants.md)

- Compatible PCB revisions: **unknown** — No attributable mapping from this panel assembly to physical PCB revisions is recorded.
- Display register controller: **unknown** — The cited vendor source does not identify the DX controller.
- Initialization interface: **RGB-only** — [documented](../../devices/sensecap-indicator/reference/display-variants.md)
- Panel supplier: **DaXian** — [documented](../../devices/sensecap-indicator/reference/display-variants.md)

### gx: GX display assembly

[Source](../../devices/sensecap-indicator/reference/display-variants.md)

- Compatible PCB revisions: **unknown** — No attributable mapping from this panel assembly to physical PCB revisions is recorded.
- Display register controller: **ST7701S** — [documented](../../devices/sensecap-indicator/reference/display-variants.md)
- Initialization interface: **SPI+RGB** — [documented](../../devices/sensecap-indicator/reference/display-variants.md)
- Panel supplier: **GuanXian** — [documented](../../devices/sensecap-indicator/reference/display-variants.md)

## Targets

- [esp-idf/sensecap-indicator](../../platforms/esp-idf/targets/sensecap-indicator/README.md)

## Evidence

Build/project: build-verified. Device: not_run. Maintenance: unassigned. Maturity: experimental.

- Physical board revision and fresh on-device verification are not recorded.
- Read the original hardware reference for unsupported drivers, prerequisites and known limitations.
- GX/DX build selection does not identify the actual panel or PCB revision; physical compatibility remains unknown.

## Source conflicts

No additional resolved conflict recorded.

## Assets

[Manifest](assets/manifest.json)

No verified redistributable image is registered.

## References

- [hardware.md](../../devices/sensecap-indicator/reference/hardware.md)
- [bsp_pins.h](../../platforms/esp-idf/targets/sensecap-indicator/bsp/include/bsp_pins.h)
- [vendor-notes.md](../../devices/sensecap-indicator/reference/vendor-notes.md)
- [hardware-checklist.md](../../devices/sensecap-indicator/tests/hardware-checklist.md)
- [display-variants.md](../../devices/sensecap-indicator/reference/display-variants.md)
- [build-4fa2274e2e872ff2.json](../../devices/sensecap-indicator/tests/records/build-4fa2274e2e872ff2.json)

## Vendor links

- [Source 1](https://github.com/Seeed-Solution/SenseCAP_Indicator_ESP32)
