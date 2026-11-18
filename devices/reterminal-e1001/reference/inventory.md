# Historical extraction inventory

Imported from the pre-migration docs/inventory.md. Status labels are historical observations, not current verification. The old cross-cutting table mentioned IDF 6.0.1 while board notes select 6.0.2; current builds follow the Target manifest. Preserve historical claims with their original scope.

## reTerminal E1001 (7.5" mono e-ink)

| Capability | Fact | Source | Extraction status |
|---|---|---|---|
| SoC / memory | ESP32-S3R8 (8 MB octal PSRAM), **32 MB flash** (W25Q256JV, DIO 80 MHz). reference configures 16 MB; the schematic + Zephyr dts confirm 32 MB | vendor schematic E1001 V1.2 + `zephyr:boards/seeed/reterminal_e1001` + `reference:esp32/devices/sdkconfig.reterminal-e1001` | confirmed |
| Display | UC8179 800x480 mono, SPI2 (SCLK=7, MOSI=9, CS=10, DC=11, RST=12, BUSY=13 low=busy), 10 MHz; 1 bpp MSB-leftmost 1=white; full + fast refresh, no partial waveform | `reference:esp32/main/epd_uc8179.c` + Zephyr dts | **extracted** (`bsp_epd`) |
| Input | three top keys: green/Refresh=GPIO 3, Left=4, Right=5; active low with internal pull-up | Zephyr dts + reference sdkconfig | **extracted** (`bsp_button`) |
| Status LED | green, GPIO 6, active low | Zephyr dts | **extracted** (`bsp_led`) |
| Sensors | SHT4x @0x44 on I2C0 (SDA=19, SCL=20) | `reference:esp32/main/reterminal_sht4x.c` + Zephyr dts | **extracted** (`bsp_sht4x`) |
| Battery | ADC1_CH0 (GPIO 1), 10k/10k divider (VBAT = 2x ADC), enable GPIO 21 active high, 10 ms settle | Zephyr dts | **extracted** (`bsp_battery`) |
| RTC | PCF8563 @0x51 on I2C0 (shares the bus with SHT4x via `bsp_i2c0_internal`) | Zephyr dts + `zephyr:drivers/rtc/rtc_pcf8563.c` | **extracted** (`bsp_rtc`) |
| Charger | SY6974B @0x6B on I2C1 (SDA=39, SCL=40); board defaults 1000 mA / 4208 mV from Zephyr dts; part-ID verified at init | `zephyr:drivers/charger/charger_sy6974b.c` + Zephyr dts | **extracted** (`bsp_charger`) |
| Audio / buzzer | PDM mic CLK=42 DATA=41 EN=38; buzzer LEDC GPIO 45 | Zephyr dts + schematic | **extracted** (`bsp_mic`, `bsp_buzzer`) — build-verified, mic levels need on-device validation |
| microSD | SDSPI on SPI2 shared with the panel: SCLK=7, MOSI=9, MISO=8, CS=14; TF_CARD_PWR rail via TPS22916 load switch, EN=16 active high; card-detect switch GPIO 15, low = inserted | vendor schematic E1001 V1.2 sheet 06 Peripherals (J5 ST-TF-003J, U13 TPS22916) | **extracted** (`bsp_sdcard`) — E1002 identical (shared mainboard) |
| IDF version | BSP + examples build clean on ESP-IDF v6.0.2 | local build | confirmed |
