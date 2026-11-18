# Vendor provenance

Primary links identify vendor sources; inspect the stated files and revisions before changing hardware facts.

| Board | Vendor source | Where to look |
| --- | --- | --- |
| reTerminal Sticky | [Sticky hardware overview](https://www.seeedstudio.com/sticky/docs/en/device-guide/hardware-overview/) + the imported hardware reference (Apache 2.0, field-verified) | reference's `reference:boards/board_reterminal_sticky.c` has the button/I2C/touch/mic/SD facts; `esp32/main/reterminal_sht4x.c` puts SHT4x on I2C1; `esp32/main/epd_ssd1677.c` (MIT) carries the SSD1677 panel pins and refresh sequence. reference's headers credit `Seeed-reTerminal-E10xx-Firmware` `factory_fw` (`main/boards/reterminal_e1005/`, `components/seeed_epaper/driver/ssd1677.c`, MIT, JoJang2u) as the original source, but that repo could not be located publicly at the time of writing, so reference's field-verified files are the citable source. |
