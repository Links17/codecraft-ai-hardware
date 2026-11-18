# Historical extraction inventory

Imported from the pre-migration docs/inventory.md. Status labels are historical observations, not current verification. The old cross-cutting table mentioned IDF 6.0.1 while board notes select 6.0.2; current builds follow the Target manifest. Preserve historical claims with their original scope.

## XIAO ESP32-S3 1.47" Touch Display

| Capability | Fact | Source | Extraction status |
|---|---|---|---|
| SoC / memory | XIAO ESP32-S3R8, 16 MB flash (DIO 80 MHz), 8 MB octal PSRAM | `reference:esp32/devices/sdkconfig.seeed-xiao-s3-147` | confirmed |
| Display | 1.47" JD9853A (ST7789-compatible) 172x320 LCD, SPI CS=3 (D2), DC=4 (D3), SCLK=7 (D8), MOSI=9 (D10), RST=13 (D17), BL=12 (D18); mirror X, gap 34; JD9853A init sequence from Seeed_GFX2 (MIT) | `reference:boards/board_seeed_xiao_s3_147.c` + `Seeed-Studio/Seeed_GFX2` `Driver_JD9853A.cpp` | **extracted** (`bsp_display`) |
| Touch | AXS5106L capacitive touch @0x63 on I2C (SDA=5/D4, SCL=6/D5), INT=44 (D7) | `reference:board_seeed_xiao_s3_147.c` + Seeed_GFX2 | pins extracted; driver not yet ported |
| Input | USR1=GPIO 11 (D19), USR2=GPIO 42 (D15), active low | `reference:board_seeed_xiao_s3_147.c` | **extracted** (`bsp_button`) |
| Audio in | PDM mic on I2S0: CLK=1 (D0), DATA=2 (D1) | `reference:board_seeed_xiao_s3_147.c` + Seeed_GFX2 `0519_DashBoard_147_ESP32` | **extracted** (`bsp_mic`) — build-verified, levels need on-device validation |
| microSD | CS=43 (D6) on the LCD SPI bus | `reference:board_seeed_xiao_s3_147.c` | pins extracted; driver not yet ported |
| USB | USB-Serial/JTAG console; UART0 pins are taken by SD CS and touch INT, so no UART console fallback | `reference:esp32/devices/seeed-xiao-s3-147.md` | confirmed |
| IDF version | BSP + examples build clean on ESP-IDF v6.0.2 | local build | confirmed |
