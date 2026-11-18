# Grove Beginner Kit for Arduino toolchain

The Target manifest is the executable version declaration. Use Arduino CLI 1.5.0 with these exact native dependencies. Library versions are copied from the board-maintained dependency declarations; bundled drivers come from the pinned core.

```sh
arduino-cli core update-index
arduino-cli core install arduino:avr@1.8.8
arduino-cli lib install --no-deps "U8g2@2.36.19"
arduino-cli lib install --no-deps "Grove Temperature And Humidity Sensor@2.0.2"
arduino-cli lib install --no-deps "Seeed Arduino SPA06@1.0.1"
arduino-cli lib install --no-deps "Grove-3-Axis-Digital-Accelerometer-2g-to-16g-LIS3DHTR@1.2.4"
```

Use ARDUINO_DIRECTORIES_DATA, ARDUINO_DIRECTORIES_DOWNLOADS and ARDUINO_DIRECTORIES_USER for an isolated installation. The adapter fingerprints the selected core, native tools and pinned libraries, and passes explicit library paths to the compiler. Unrelated installed cores are not part of the lock. Builds write under .codecraft/builds/arduino/.

Source: https://github.com/arduino/ArduinoCore-avr/tree/1.8.8
