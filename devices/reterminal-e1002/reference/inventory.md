# Historical extraction inventory

Imported from the pre-migration docs/inventory.md. Status labels are historical observations, not current verification. The old cross-cutting table mentioned IDF 6.0.1 while board notes select 6.0.2; current builds follow the Target manifest. Preserve historical claims with their original scope.

## reTerminal E1002 (7.3" Spectra 6 color e-ink)

Same mainboard as the E1001 (same pin map, 32 MB flash, SHT4x, RTC, charger,
battery sense, keys, LED); only the panel differs.

| Capability | Fact | Source | Extraction status |
|---|---|---|---|
| SoC / memory | as E1001: ESP32-S3R8, 32 MB flash | as E1001 | confirmed |
| Display | Spectra 6 (GDEP073E01) 800x480 six-color; 4 bpp, 2 px/byte, left pixel in high nibble; ink codes 0 black, 1 white, 2 yellow, 3 red, 4 blue, 5 green; full refresh only (~30 s, busy timeout 60 s) | `reference:esp32/main/epd_spectra6.c` + Zephyr dts color palette | **extracted** (`bsp_epd`) |
| Input / LED / sensors / battery / RTC / charger / mic / buzzer | identical to E1001 (shared `bsp_pins.h` values) | as E1001 | **extracted** (same drivers copied) |
| IDF version | BSP + examples build clean on ESP-IDF v6.0.2 | local build | confirmed |
