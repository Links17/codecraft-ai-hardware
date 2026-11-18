# Historical extraction inventory

Imported from the pre-migration docs/inventory.md. Status labels are historical observations, not current verification. The old cross-cutting table mentioned IDF 6.0.1 while board notes select 6.0.2; current builds follow the Target manifest. Preserve historical claims with their original scope.

## SenseCAP Watcher

| Capability | Fact | Source | Extraction status |
|---|---|---|---|
| SoC / memory | ESP32-S3, 32 MB flash, octal PSRAM with XIP (`SPIRAM_XIP_FROM_PSRAM`) | `reference:esp32/devices/sdkconfig.sensecap-watcher` | confirmed |
| Display + touch | LCD, touch, knob, IO expander pins live in the vendor BSP | `vendor:SenseCAP-Watcher-Firmware components/sensecap-watcher/include/sensecap-watcher.h` | pending |
| Audio | codec pins in vendor BSP | same as above | pending |
| Camera | Himax chip via SSCMA protocol | `reference:esp32/components/camera/` (`camera_sscma.c`, `sscma_proto.c`) | pending |
| Battery / SD | pins in vendor BSP | same as display row | pending |
| Power profile | USB-free sweep methodology + findings | `reference:esp32/docs/power/sensecap-watcher*.md`, `ppk2.md` | docs only, carry over |
| IDF version | per reference default (verify against vendor firmware) | `reference:esp32/README.md` | verify |
