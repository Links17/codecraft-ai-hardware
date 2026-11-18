# Grove Beginner Kit for Arduino hardware reference

## Hardware facts

- MCU: Microchip ATmega328P-MU, 16 MHz, 32 KB flash (32,256-byte sketch
  maximum), 2 KB SRAM and 1 KB EEPROM, 5 V logic. Seeeduino Lotus v1.0 uses
  a CH340 USB bridge; v1.1 uses CP2102N. Source:
  [Seeeduino Lotus wiki](https://wiki.seeedstudio.com/Seeeduino_Lotus/) and
  [v1.1 schematic](https://files.seeedstudio.com/wiki/Seeeduino_Lotus/res/Seeeduino%20Lotus%20v1.1%20SCH.pdf).
- Build identity: `arduino:avr:uno` uses the ATmega328P, standard variant,
  16 MHz, AVR_UNO and 32,256-byte sketch limit. This matches the Lotus v1.1
  board configuration. Source: Seeeduino AVR 1.2.1 boards.txt and
  [ArduinoCore-avr 1.8.8](https://github.com/arduino/ArduinoCore-avr/tree/1.8.8).
  Only the declared core is supported by this Target.
- Hardware I2C: A4 is SDA (PC4, Arduino pin 18), A5 is SCL (PC5, pin 19), and
  the Grove connectors are 5 V logic. Source: Seeeduino Lotus v1.1
  schematic and the core's `standard` variant.
- Kit LED: Grove LED on D4, active high, with a board trimpot for brightness.
  D4 is not a PWM pin on this core. Source: kit wiki default-pin table and
  Lesson 1.
- Button: Grove Button on D6. The vendor example configures `INPUT` and reads
  pressed as `HIGH`, so the module provides its own pull-down. Source: kit
  wiki Lesson 2.
- Rotary potentiometer: Grove Rotary Potentiometer on A0; `analogRead()`
  returns 0-1023 using the 5 V reference. Source: kit wiki Lesson 3.
- Buzzer: Grove passive piezo buzzer on D5; it needs a square wave such as
  `tone()`, not a static DC level. Source: kit wiki Lesson 4.
- Light sensor: Grove Light on A6; the vendor example turns the LED on below
  raw 200. This is an uncalibrated analog level, not lux. Source: kit wiki
  Lesson 5.
- Sound sensor: Grove Sound on A2; the vendor example uses raw > 400 to
  indicate a sound peak. The output is an analog envelope, not calibrated
  dB SPL and not recorded audio. Source: kit wiki Lesson 6.
- OLED: 0.96-inch 128x64 SSD1306/SSD1315-compatible display on I2C. The kit
  wiki gives 0x78 as the 8-bit write address, which is 0x3C in 7-bit form;
  0x3D is accepted as an alternate in the demo. Source: kit wiki default-pin
  table and [OLED wiki](https://wiki.seeedstudio.com/Grove-OLED-Display-0.96-SSD1315/).
- Temperature/humidity: the supported post-October-2025 kit uses DHT20 on
  I2C. The current vendor example calls `Wire.begin()`, the Grove DHT library
  uses fixed I2C address 0x38, and the wiki says a black
  humidity/temperature detector identifies this revision. Source: current kit
  wiki DHT20 section and
  [Grove_Temperature_And_Humidity_Sensor](https://github.com/Seeed-Studio/Grove_Temperature_And_Humidity_Sensor).
- Air pressure: the supported post-October-2025 kit uses SPA06-003 on I2C at
  0x77 by default, 0x76 optional. The SPA06 library verifies device ID 0x11.
  Source:
  [SPA06-003 wiki](https://wiki.seeedstudio.com/grove_barometer_sensor_spa06_003/).
- Accelerometer: ST LIS3DHTR on I2C at 0x19. Source: kit wiki default-pin
  table and Lesson 10.

Most unchanged board connections above come from the
[Grove Beginner Kit wiki](https://wiki.seeedstudio.com/Grove-Beginner-Kit-For-Arduino/)
and the kit's
[schematic/PCB archive](https://files.seeedstudio.com/wiki/Grove-Beginner-Kit-For-Arduino/res/Grove-Beginner-Kit-for-Arduino-SCH-PCB.zip)
(the published schematic is dated 2020, revision v1.4). That schematic
predates the DHT20/SPA06-003 revision and does not document their sensor
routing. The current wiki and an `i2c_scan` of the target unit are the
authority for 0x38 and the SPA06-003 address.

## Not provided

The kit contains no Wi-Fi/BLE radio, motor driver, relay, battery/charger,
camera, or digital audio recorder. The "sound sensor" is an analog envelope
output. Do not add network, pairing, account, telemetry, or cloud code: this
repository is a local hardware reference only.

## Known constraints and source conflicts

- **Only the post-October-2025 revision is supported.** Run `i2c_scan` and
  require DHT20 at 0x38. If it is absent, stop and confirm the hardware
  revision; do not add a DHT11 fallback or apply the 2020 D3 wiring.
- **The published schematic predates the current sensors.** It does not
  document DHT20 or SPA06-003 routing. Treat 0x38 as the DHT20 probe result
  and require the SPA06 library's device-ID 0x11 check before claiming the
  pressure sensor is supported.
- **D4 has no PWM.** The LED demo is on/off only. PWM dimming needs the LED
  module broken out and reconnected to D3.
- **The button module has an external pull-down.** Use `INPUT`; `INPUT_PULLUP`
  would make an idle button read pressed.
- **I2C is shared and 5 V.** Address 0x19/0x3C-or-0x3D/0x38/0x77 may all be
  present on one board. Do not drive 3.3 V-only external devices from this
  bus without level shifting.
- **SRAM is 2 KB.** Use U8x8 text mode or stream readings; do not add a full
  framebuffer or large global buffers without checking the build size.
- **Raw analog values are not engineering units.** The potentiometer, light,
  and sound examples report ADC counts and estimated millivolts only. Lux and
  dB SPL require calibration that this repository has not performed.

