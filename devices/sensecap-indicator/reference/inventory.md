# Historical extraction inventory

Imported from the pre-migration docs/inventory.md. Status labels are historical observations, not current verification. The old cross-cutting table mentioned IDF 6.0.1 while board notes select 6.0.2; current builds follow the Target manifest. Preserve historical claims with their original scope.

## SenseCAP Indicator (D1 / D1S / D1Pro / D1L)

| Capability | Fact | Source | Extraction status |
|---|---|---|---|
| SoC / memory | ESP32-S3, 8 MB flash (QIO 80 MHz), 8 MB octal PSRAM | `reference:esp32/devices/sdkconfig.sensecap-indicator` | confirmed |
| Display | 4 inch 480x480 ST7701S RGB, 16-bit bus, PCLK 18 MHz; 450 KB framebuffer in octal PSRAM; register init over bit-banged 9-bit SPI (SCK=41, SDO=48, CS on TCA9535 IO4) | same + vendor `SenseCAP_Indicator_ESP32` | **extracted** (`bsp_display`) |
| Input | top button, active low, GPIO 38 | same + vendor board file | **extracted** (`bsp_button`) |
| Status indication | no status LED; display edge bars used instead | same | confirmed |
| Sensors | RP2040 co-processor handles sensors; unused in the reference profile | same | out of scope for v1 |
| USB | CH340 USB-UART bridge | same | confirmed |
| IDF version | vendor SDK targets ESP-IDF 5.1.1; this BSP builds clean on v6.0.2 | vendor sources + local build | confirmed |
| IO expander | TCA9535 @0x20 (fallback 0x39), I2C SDA=39/SCL=40; IO4 LCD CS, IO5 LCD RST, IO7 TP RST, IO8 RP2040 RST, IO10 BMP PWR | vendor board file | **extracted** (`bsp_io_expander`) |
| Touch | FT6336U @0x48/0x38 or GT911 @0x5D, reset on expander IO7 | vendor `indev_tp.c` | pending |
