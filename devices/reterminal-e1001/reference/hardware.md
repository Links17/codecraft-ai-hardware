# reTerminal E1001 (7.5" mono e-ink)


Battery-powered 800x480 monochrome e-paper terminal: ESP32-S3R8
(8 MB octal PSRAM), 32 MB flash, SHT4x temperature/humidity, PCF8563 RTC,
SY6974B charger for the 2000 mAh LiPo, buzzer, PDM mic, microSD, three top
keys and a green status LED.

## BSP

| Header | Native interface |
|---|---|
| `bsp_epd.h` | UC8179 panel: 1 bpp framebuffer (MSB leftmost, 1 = white), full/fast refresh, panel deep-sleeps after each update |
| `bsp_button.h` | green / Left / Right keys (GPIO 3/4/5, active low, debounced) |
| `bsp_led.h` | green status LED (GPIO 6, active low) |
| `bsp_sht4x.h` | temperature/humidity, single-shot, CRC-checked |
| `bsp_battery.h` | battery millivolts (ADC1 CH0, 10k/10k divider, enable GPIO 21) |
| `bsp_rtc.h` | PCF8563 real-time clock on I2C0 |
| `bsp_charger.h` | SY6974B charger status/limit control on I2C1 |
| `bsp_buzzer.h` | buzzer tones (LEDC PWM, GPIO 45) |
| `bsp_mic.h` | PDM microphone capture (CLK 42 / DATA 41 / EN 38) |
| `bsp_sdcard.h` | microSD over SDSPI on SPI2 (shared with the panel), rail + card-detect |

Pin facts with sources: [bsp_pins.h](../../../platforms/esp-idf/targets/reterminal-e1001/bsp/include/bsp_pins.h).

## Examples

- `epd_hello` — checkerboard + bars pattern, one full refresh; demonstrates
  the framebuffer format and the refresh cycle.
- `sht4x_battery` — 10 s sampling loop of sensor + battery, LED blink per
  sample, key press samples immediately.
- `board_health` — exercises every peripheral once and prints a summary.
- `sdcard_test` — mounts the microSD slot, writes and reads back a file;
  insert a FAT-formatted card first.


## Notes for agents

- Flash: 32 MB W25Q256JV (vendor schematic + Zephyr dts). the Target configuration uses the sourced capacity.
- The 48 KB framebuffer belongs in octal PSRAM (`MALLOC_CAP_SPIRAM`); the
  examples fall back to internal RAM.
- The UC8179 has no partial-refresh waveform here: "fast" refresh is the
  reference/GxEPD2 GDEY075T7 sequence. Do not invent a partial refresh.
- Board heat warms the onboard SHT4x; apply an offset in the application
  only after measurements support it.

## Current commands and verification

Run `python3 codecraft.py validate --target esp-idf/reterminal-e1001 --projects` from the repository root. The [Target manifest](../../../platforms/esp-idf/targets/reterminal-e1001/target.json) declares exact toolchain, examples and native interface scope. The [Device acceptance plan](../tests/acceptance.json) defines physical checks. Build receipts and physical observations are separate; an exported project carries no hardware-verification claim. Hardware writes require a selected unit and explicit authorization.
