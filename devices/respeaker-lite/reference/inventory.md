# Historical extraction inventory

Imported from the pre-migration docs/inventory.md. Status labels are historical observations, not current verification. The old cross-cutting table mentioned IDF 6.0.1 while board notes select 6.0.2; current builds follow the Target manifest. Preserve historical claims with their original scope.

## Seeed reSpeaker Lite (XIAO ESP32-S3)

| Capability | Fact | Source | Extraction status |
|---|---|---|---|
| SoC / memory | XIAO ESP32-S3, 8 MB flash (DIO 80 MHz), 8 MB octal PSRAM | `reference:esp32/devices/sdkconfig.seeed-respeaker-lite` | confirmed |
| Audio in | XMOS-processed microphone over 16 kHz I2S; XMOS must run Seeed **16 kHz I2S firmware v1.0.9** (USB-audio and 48 kHz images incompatible) | `reference:esp32/devices/seeed-respeaker-lite.md` + vendor example | **extracted** (`bsp_audio`) |
| Input | XIAO BOOT button, GPIO 0, active low | sdkconfig + doc above | **extracted** (`bsp_button`) |
| Status | single WS2812 on GPIO 1 (XIAO D0), no power switch | `reference:esp32/main/led_status.c` + vendor D-pin map | **extracted** (`bsp_led`) |
| USB | small XIAO board USB exposes USB Serial/JTAG console (`303a:1001`) | doc above | confirmed |
| RF | attach XIAO external antenna; 2.4 GHz Wi-Fi only | doc above | confirmed |
| IDF version | ESP-IDF v6.0.1 per reference doc; examples build clean on v6.0.2 | doc above + local build | confirmed |
