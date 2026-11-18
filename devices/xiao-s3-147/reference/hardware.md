# Seeed XIAO ESP32-S3 1.47" Touch Display


## Hardware facts

- Controller: XIAO ESP32-S3 Plus (ESP32-S3, dual-core 240 MHz), 16 MB
  flash (DIO 80 MHz), 8 MB octal PSRAM (80 MHz).
  Sources: reference `esp32/devices/sdkconfig.seeed-xiao-s3-147`,
  `esp32/devices/seeed-xiao-s3-147.md`.
- Display: 1.47" 172x320 IPS LCD, JD9853A on SPI2, driven with the
  ST7789-compatible esp_lcd driver plus Seeed's register sequence:
  MADCTL 0x48 (MX+BGR), X offset 34, Y offset 0, inversion off.
  CS=3, DC=4, SCLK=7, MOSI=9, RST=13 (shared with touch), BL=12
  (active high).
  Sources: Seeed_GFX2 (MIT) via reference
  `reference:boards/board_seeed_xiao_s3_147.c`.
- Buttons: USR1=GPIO 11, USR2=GPIO 42, active low.
  Source: reference `board_seeed_xiao_s3_147.c`.
- PDM microphone on I2S0: CLK=1, DATA=2.
  Sources: Seeed_GFX2 `0519_DashBoard_147_ESP32` example, reference board file.
- Console: native USB Serial/JTAG (`303a:1001`); UART0's GPIO43/44 carry
  the SD chip-select and the touch interrupt.
  Source: reference `devices/seeed-xiao-s3-147.md`.

## Hardware outside registered native interfaces

- AXS5106L capacitive touch @0x63 (SDA=5, SCL=6, INT=44); the reset line
  is shared with the LCD and pulsed once at boot. Touch X is mirrored to
  match the panel orientation. Protocol reference: reference
  `reference:boards/xiao_147_touch.h`.
- microSD slot (CS=43, held high when unused); LSM6DS3 IMU; battery
  input. All present on the board, outside the registered interfaces.

## Vendor source

[Seeed wiki](https://wiki.seeedstudio.com/getting_started_1.47_inch_touch_display_esp32s3/)
and [Seeed_GFX2](https://github.com/Seeed-Studio/Seeed_GFX2) (MIT) —
JD9853A register sequence, AXS5106L reports, PDM example.

## BSP

| Header | Native interface |
|---|---|
| `bsp_display.h` | JD9853A panel via esp_lcd ST7789 + vendor sequence, backlight |
| `bsp_button.h` | USR1/USR2 keys with debounce task |
| `bsp_mic.h` | PDM microphone, mono 16-bit PCM |

Pin facts with sources: [bsp_pins.h](../../../platforms/esp-idf/targets/xiao-s3-147/bsp/include/bsp_pins.h).

## Examples

- `display_hello` — red/green/blue bands on the panel.
- `button_hello` — USR1 logs, USR2 toggles the backlight.
- `mic_level` — PDM mic RMS level bar on the console.

Each is a standalone IDF project sharing the board `sdkconfig.defaults`
via symlink. Native code paths below are relative to the Target directory.

Build (ESP-IDF v6.0.2):

```bash
source ~/esp/esp-idf-v6.0.2/export.sh
python3 codecraft.py validate --target esp-idf/xiao-s3-147
```

## Current commands and verification

Run `python3 codecraft.py validate --target esp-idf/xiao-s3-147 --projects` from the repository root. The [Target manifest](../../../platforms/esp-idf/targets/xiao-s3-147/target.json) declares exact toolchain, examples and native interface scope. The [Device acceptance plan](../tests/acceptance.json) defines physical checks. Build receipts and physical observations are separate; an exported project carries no hardware-verification claim. Hardware writes require a selected unit and explicit authorization.
