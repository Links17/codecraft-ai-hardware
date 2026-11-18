# Historical extraction inventory

Imported from the pre-migration docs/inventory.md. Status labels are historical observations, not current verification. The old cross-cutting table mentioned IDF 6.0.1 while board notes select 6.0.2; current builds follow the Target manifest. Preserve historical claims with their original scope.

## reTerminal Sticky (3.97" mono e-ink)

| Capability | Fact | Source | Extraction status |
|---|---|---|---|
| SoC / memory | ESP32-S3R8 (8 MB octal PSRAM); reference configures 16 MB flash (DIO 80 MHz); the 32 MB claim on the store page is unconfirmed | `reference:esp32/devices/sdkconfig.reterminal-sticky` | confirmed (16 MB), 32 MB unverified |
| Display | SSD1677 800x480 e-paper, used portrait 480x800; 1 bpp mono with full + fast refresh, plus a 4-gray image mode; SPI2 SCLK=13, MOSI=14, MISO=12, CS=15, DC=16, RST=17 (active low), BUSY=18 (high = busy), panel power EN=47, 20 MHz | `reference:esp32/main/epd_ssd1677.c` (MIT); protocol credited to Seeed `factory_fw` `ssd1677.c` (repo not publicly locatable, see vendor-sources.md) | **extracted** (`bsp_epd`) |
| Input | three keys: AI=GPIO 4, Up=5, Down=6, active low | `reference:boards/board_reterminal_sticky.c` | **extracted** (`bsp_button`) |
| Sensors | SHT4x temperature/humidity @0x44 on I2C1 (SDA=1, SCL=0), shared with the BQ27220 fuel gauge @0x55 | `reference:esp32/main/reterminal_sht4x.c` + `board_reterminal_sticky.c` | **extracted** (`bsp_sht4x`) |
| Audio in | PDM mic on I2S0: CLK=19, DATA=20, power EN=38 (active high) | `reference:board_reterminal_sticky.c` | pins extracted; driver not yet ported |
| Touch | GT911 capacitive touch on I2C0 (SDA=3, SCL=2), 0x5D (fallback 0x14), power EN=42, RST=41, INT=21; Y axis flipped in software | `reference:board_reterminal_sticky.c` | pins extracted; driver not yet ported |
| microSD | SDSPI on the panel's SPI2 bus: CS=8, power EN=10, card-detect=11 (low = inserted), MISO=12 | `reference:board_reterminal_sticky.c` | pins extracted; driver not yet ported |
| Charger | charger enable on GPIO 39; reference drives it low at boot but the active level is unconfirmed against `factory_fw` | `reference:board_reterminal_sticky.c` | unverified until measured |
| IDF version | BSP + examples build clean on ESP-IDF v6.0.2 | local build | confirmed |
