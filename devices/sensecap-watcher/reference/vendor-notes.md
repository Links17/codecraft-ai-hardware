# Vendor provenance

Primary links identify vendor sources; inspect the stated files and revisions before changing hardware facts.

| Board | Vendor source | Where to look |
| --- | --- | --- |
| SenseCAP Watcher | [Seeed-Studio/SenseCAP-Watcher-Firmware](https://github.com/Seeed-Studio/SenseCAP-Watcher-Firmware) | `components/sensecap-watcher/` is the vendor BSP. `include/sensecap-watcher.h` has the pins for the LCD, touch, knob, IO expander, audio, battery, SD card and the Himax camera chip (driven through `components/sscma_client/`). `examples/factory_firmware/` is the firmware it ships with. xiaozhi-esp32's [sensecap-watcher board](https://github.com/78/xiaozhi-esp32/tree/main/main/boards/sensecap-watcher) is a second reference. |
