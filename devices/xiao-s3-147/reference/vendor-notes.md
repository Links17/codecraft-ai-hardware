# Vendor provenance

Primary links identify vendor sources; inspect the stated files and revisions before changing hardware facts.

| Board | Vendor source | Where to look |
| --- | --- | --- |
| XIAO ESP32-S3 1.47" Touch Display | [Seeed wiki](https://wiki.seeedstudio.com/getting_started_1.47_inch_touch_display_esp32s3/) + [Seeed-Studio/Seeed_GFX2](https://github.com/Seeed-Studio/Seeed_GFX2) (MIT) | Seeed_GFX2 has the JD9853A register sequence (`Driver_JD9853A.cpp`), the AXS5106L touch reports, and the `0519_DashBoard_147_ESP32` PDM example. reference's field-verified `reference:boards/board_seeed_xiao_s3_147.c` + `esp32/devices/seeed-xiao-s3-147.md` have the complete pin table and the USB-console constraint (UART0 pins taken by SD CS and touch INT). |
