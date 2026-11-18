# Vendor provenance

Primary links identify vendor sources; inspect the stated files and revisions before changing hardware facts.

| Board | Vendor source | Where to look |
| --- | --- | --- |
| reTerminal (CM4) | [Seeed-Studio/seeed-linux-dtoverlays](https://github.com/Seeed-Studio/seeed-linux-dtoverlays), pinned at commit `1d53c3cf2c96` | `overlays/rpi/reTerminal-overlay.dts` (file header MIT) has every peripheral fact: MCP23008 @I2C1 0x38 pin map (buttons 0/2/1/3, LEDs 4-6 active low, buzzer 7 active high), expander IRQ GPIO6, power key GPIO13, LTR-303 @0x29, LIS331DLH @0x19, PCF8563 @I2C3 0x51, I2C1 300 kHz. Display/touch need Seeed's out-of-tree modules (`modules/ili9881d`); the repo-level COPYING is GPLv2, so link rather than vendor it. |
