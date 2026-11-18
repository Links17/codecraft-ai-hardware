# Vendor provenance

Primary links identify vendor sources; inspect the stated files and revisions before changing hardware facts.

| Board | Vendor source | Where to look |
| --- | --- | --- |
| SenseCAP Indicator | [Seeed-Solution/SenseCAP_Indicator_ESP32](https://github.com/Seeed-Solution/SenseCAP_Indicator_ESP32) (Apache 2.0, ESP-IDF 5.1.1) | `components/bsp/src/boards/sensecap_indicator_board.c` has the full pin map and TCA9535 expander map; `lcd_panel_config.c` has the ST7701S register init and bit-bang SPI channel; `Kconfig.projbuild` has PCLK/timing defaults and the GX/DX screen variants. |
