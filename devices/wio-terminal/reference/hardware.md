# Wio Terminal hardware reference

## Hardware facts

- MCU: Microchip ATSAMD51P19A, Arm Cortex-M4F, 512 KB program flash and
  192 KB RAM. The Arduino core uses the standard 120 MHz clock.
  Source: [Wio Terminal schematic v1.2](https://files.seeedstudio.com/wiki/Wio-Terminal/res/Wio-Terminal-SCH-v1.2.pdf)
  sheet 02 (MCU and memory), the
  [product page](https://wiki.seeedstudio.com/Wio-Terminal-Getting-Started/),
  and `Seeeduino:samd@1.8.6` `boards.txt` (`seeed_wio_terminal`).
- External flash: W25Q32JVZPIM, 32 Mbit / 4 MB, on the QSPI bus. Source:
  schematic sheet 02. No example in this directory uses it yet.
- LCD: 2.4-inch 320x240 ILI9341 panel on SPI3. The core pin map gives SCK
  68, MOSI 67, MISO 66, CS 69, DC 70, reset 71 and backlight 72. The
  `TFT_eSPI` / `Seeed_Arduino_LCD` library bundled with the core selects the
  ILI9341 driver and these pins. Examples call `setRotation(3)` for a
  320-pixel-wide landscape view. Source: schematic sheet 07, core
  `variants/wio_terminal/variant.h`, and
  `libraries/Seeed_Arduino_LCD/User_Setup.h`.
- Top buttons: `WIO_KEY_A`, `WIO_KEY_B`, `WIO_KEY_C` on GPIO 28, 29 and 30;
  active low with external pull-ups. Source: schematic sheet 05 and core
  `variant.h`.
- Five-way switch: `WIO_5S_UP`, `WIO_5S_LEFT`, `WIO_5S_RIGHT`,
  `WIO_5S_DOWN`, `WIO_5S_PRESS` on GPIO 31, 32, 33, 34 and 35; active low.
  Source: schematic sheet 04 and core `variant.h`.
- IMU: ST LIS3DHTR on the internal `Wire1` bus, SDA 78, SCL 77, 7-bit
  address `0x18`; INT1 is GPIO 79. Source: schematic sheet 07 and core
  `variant.h` (`WIO_LIS3DH_SDA`, `WIO_LIS3DH_SCL`, `WIO_LIS3DH_INT`) for the
  bus and pins; the address comes from Seeed_Arduino_LIS3DHTR's
  `LIS3DHTR_DEFAULT_ADDRESS` (`0x19` is the library's alternate
  `LIS3DHTR_ADDRESS_UPDATED`). The variant macro `WIO_LIS3DH_WiRE` contains
  a vendor typo; use `Wire1`.
- Light sensor: photodiode output on `WIO_LIGHT`, GPIO 27 / ADC channel 15.
  The product lists a 400-1050 nm response. Source: schematic sheet 05 and
  core `variant.h`; spectrum range from the product page.
- Microphone: analog electret microphone and LMV358 gain stage, with the
  conditioned signal on `WIO_MIC`, GPIO 39 / ADC channel 12. Source:
  schematic sheet 04 and core `variant.h`. This is an analog level path, not
  a digital I2S microphone.
- Buzzer: passive buzzer B4013AM422-042 driven through Q4 from
  `WIO_BUZZER`, GPIO 12. It needs an AC/PWM waveform; the example uses the
  core `tone()` API. Source: schematic sheet 04 and core `variant.h`.
- microSD: dedicated SPI2 bus, SCK 63, MOSI 62, MISO 61, CS 64, card-detect
  65. The product page specifies cards up to 16 GB. Source: schematic sheet
  02, core `variant.h` (`SDCARD_*`), and the product page.
- Infrared emitter: 940 nm LED D10 driven through Q13 from `WIO_IR`, GPIO
  14; `IR_CTL` is active high. It is on the back of the enclosure, to the
  left of the microSD slot. This is a transmitter, not a receiver. Source:
  schematic sheet 05, core `variant.h`, the product page, and the Seeed wiki
  Getting Started with Infrared Emitter page.
- Grove connectors: the left J4 is I2C on `Wire`, SDA 46 / SCL 45, with a
  3.3 V supply. J4 has no onboard I2C pull-ups; a Grove module normally
  supplies them (schematic sheet 05 shows only the connector, decoupling and
  DNP SWD links). The right J5 exposes A0/D0 and A1/D1. Source: schematic
  sheet 05 and core `variant.h` (`PIN_WIRE_SDA`, `PIN_WIRE_SCL`). Only J4
  I2C has a maintained example here.
- Wireless: Realtek RTL8720DN, dual-band 2.4/5 GHz 802.11 a/b/g/n and BLE
  5.0. The SAMD51 connects to it over SPI1/UART and controls it with
  CHIP_PU GPIO 80 and IRQ0 GPIO 11. Source: schematic sheet 06, core
  `variant.h`, and the product page.
- Expansion: 40-pin Raspberry Pi-compatible header, a 20-pin FPC connector,
  USB Type-C power/OTG, I2S and DAC pins. These are present on the product
  but are not covered by the current examples; do not infer their use from
  this directory.

## Not provided

The vendor feature list and schematic v1.2 do not include a touch controller,
an onboard battery/charger, a speaker or audio codec, or a camera. Treat the
LCD as display-only, power the board from USB-C or the documented power pins,
and use the passive buzzer for audible output. Do not add libraries or pin
assignments for hardware that is not present.

## Known constraints

- **RTL8720 firmware is separate.** Uploading an Arduino sketch only writes
  the ATSAMD51. Wi-Fi and BLE need compatible eRPC firmware on the
  RTL8720DN. Follow Seeed's
  [Wi-Fi firmware update guide](https://wiki.seeedstudio.com/Wio-Terminal-Network-Overview/)
  and verify the RTL firmware with `rpc_system_version()` before debugging
  sketch code. The repository does not pin a binary firmware release.
- `wifi_scan` completed on-device on 2026-10-28 using the RTL8720DN eRPC
  firmware already installed on the test unit. Serial scans returned nearby
  2.4 GHz and 5 GHz SSIDs with RSSI around -40 to -46 dBm, and the user
  confirmed the LCD. `rpc_system_version()` was not queried, so no RTL
  firmware version is claimed.
- `ble_scan` completed on-device on 2026-10-29 with the official RTL8720DN
  eRPC firmware 2.1.3 (`rpc_system_version()` returns `2.1.3`). Each
  five-second pass reported several hundred advertisements and listed nearby
  devices with names, addresses and RSSI, and the user confirmed the LCD.
  Two coprocessor behaviours are required for that result and are recorded in
  `../../../platforms/arduino/targets/wio-terminal/examples/ble_scan/AGENTS.md`: call `ble_start()` once after
  `BLEDevice::init()`, because without it the BT stack stays down and
  `BD_ADDR` reads all zeros; and use the non-blocking `BLEScan::start`
  overload, because the blocking one waits on a semaphore with no timeout and
  froze the LCD on this unit.
- `wifi_scan` and `ble_scan` each initialize and own the RTL8720DN. Run them
  as separate sketches; concurrent Wi-Fi/BLE operation is not exercised by
  this repository even though the vendor eRPC firmware is documented as
  supporting both.
- `rpcBLE@1.0.0` conflicts with the Arduino `min`/`max` macros. `ble_scan`
  undefines both before including the rpcBLE headers. Keep that include
  order when extending the sketch.
- The light sensor demo reports raw ADC and an estimated millivolt value; it
  is not calibrated to lux. The direction of the raw change is not asserted;
  observe it on the target unit before choosing a threshold.
- The microphone demo measures an analog AC envelope. It is not calibrated
  dB SPL and cannot record digital audio without additional sampling logic.
- `sd_card_log` expects a FAT32 card of at most 16 GB and mounts once. It
  does not implement hot-swap/remount handling. Card-detect GPIO 65 is
  documented but not used by the sketch. It uses Seeed Arduino FS 2.1.5 with
  an explicit SPI2 bus and CS 64; the standard Arduino `SD` library defaults
  to `SS` GPIO 50 and is not a valid substitute.
- `ir_nec_sender` is a blocking, bit-banged NEC transmitter. It has no
  receiver and no protocol decoder.
- `grove_i2c_scan` limits its scan to `0x08`-`0x77` and primes the bus with a
  reserved `0x7F` transaction. J4 has no onboard I2C pull-ups; a Grove module
  normally supplies them. Without a module, the first `Wire` transaction after
  idle can false-ACK the first address; this was measured and worked around.
- `ir_nec_sender` has only been observed with a camera so far; a 38 kHz
  receiver has not decoded the NEC frames.
