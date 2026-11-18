# Seeed reSpeaker Lite (XIAO ESP32-S3)


## Hardware facts

- Module: XIAO ESP32-S3, 8 MB flash (DIO 80 MHz), 8 MB octal PSRAM (80 MHz).
  Source: reference `esp32/devices/sdkconfig.seeed-respeaker-lite`.
- Button: XIAO BOOT button on GPIO 0. Source: same.
- Audio: XMOS-processed microphone over 16 kHz I2S. The XMOS must run
  Seeed's **16 kHz I2S firmware v1.0.9**; the USB-audio and 48 kHz I2S
  images do not work. Flash the XMOS through the larger board's USB port
  per Seeed's instructions — flashing the ESP32 does not update the XMOS.
  Source: reference `esp32/devices/seeed-respeaker-lite.md`.
- Status: RGB status LED. Source: same.
- USB console: connect to the **small XIAO board**; it exposes the ESP32's
  USB Serial/JTAG console (`303a:1001`). Source: same.
- RF: attach the XIAO's external antenna; 2.4 GHz Wi-Fi only. Source: same.
- ESP-IDF: **v6.0.1**. Source: same.

## Vendor source

[respeaker/reSpeaker_Lite](https://github.com/respeaker/reSpeaker_Lite):
`doc/images/pinout.png`, I2C examples, `xmos_firmwares/`.

## BSP

| Header | Native interface |
|---|---|
| `bsp_audio.h` | XMOS + AIC3204 over I2C, 16 kHz I2S slave capture/playback |
| `bsp_led.h` | WS2812 RGB LED |
| `bsp_button.h` | BOOT button with debounce task |

Pin facts with sources: [bsp_pins.h](../../../platforms/esp-idf/targets/respeaker-lite/bsp/include/bsp_pins.h).

## Layout

- `bsp/include/bsp_pins.h` — authoritative pin map with per-fact citations.
- `bsp/` — `bsp_audio` (XMOS + AIC3204 over I2C, 16 kHz I2S slave),
  `bsp_led` (WS2812), `bsp_button` (BOOT with debounce task).
- `examples/` — `audio_meter`, `button_led`, `wifi_scan`. Each is a
  standalone IDF project sharing the board `sdkconfig.defaults` via symlink. Native code paths below are relative to the Target directory.

## Examples

- `audio_meter` — XMOS mic RMS level, mirrored on the WS2812 (needs the
  16 kHz I2S XMOS firmware v1.0.9, see Verified facts).
- `button_led` — hold XIAO BOOT to cycle the WS2812 through red/green/blue.
- `wifi_scan` — 2.4 GHz AP scan, blinks the LED green each round (attach
  the external antenna).

Each is a standalone IDF project sharing the board `sdkconfig.defaults`
via symlink. Native code paths below are relative to the Target directory.

## Pin map (verified, see `bsp/include/bsp_pins.h` for citations)

| Function | GPIO | XIAO pin |
|---|---|---|
| WS2812 data | 1 | D0 |
| XMOS reset | 2 | D1 |
| I2C SDA | 5 | D4 |
| I2C SCL | 6 | D5 |
| I2S WS | 7 | D8 |
| I2S BCLK | 8 | D9 |
| I2S DOUT (to AIC3204 DAC) | 43 | D6 |
| I2S DIN (from XMOS mic) | 44 | D7 |
| BOOT button (active low) | 0 | — |

I2C devices: XMOS `0x42`, AIC3204 codec `0x18`.

## Current commands and verification

Run `python3 codecraft.py validate --target esp-idf/respeaker-lite --projects` from the repository root. The [Target manifest](../../../platforms/esp-idf/targets/respeaker-lite/target.json) declares exact toolchain, examples and native interface scope. The [Device acceptance plan](../tests/acceptance.json) defines physical checks. Build receipts and physical observations are separate; an exported project carries no hardware-verification claim. Hardware writes require a selected unit and explicit authorization.
