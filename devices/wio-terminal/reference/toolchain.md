# Wio Terminal toolchain

The Target manifest is the executable version declaration. Use Arduino CLI 1.5.0 with these exact native dependencies. Library versions are copied from the board-maintained dependency declarations; bundled drivers come from the pinned core.

```sh
arduino-cli core update-index --additional-urls https://files.seeedstudio.com/arduino/package_seeeduino_boards_index.json
arduino-cli core install Seeeduino:samd@1.8.6 --additional-urls https://files.seeedstudio.com/arduino/package_seeeduino_boards_index.json
arduino-cli lib install --no-deps "Seeed Arduino rpcUnified@2.1.4"
arduino-cli lib install --no-deps "Seeed_Arduino_mbedtls@3.0.2"
arduino-cli lib install --no-deps "Seeed Arduino FS@2.1.5"
arduino-cli lib install --no-deps "Seeed Arduino SFUD@2.0.2"
arduino-cli lib install --no-deps "Seeed Arduino rpcWiFi@1.1.0"
arduino-cli lib install --no-deps "Seeed Arduino rpcBLE@1.0.0"
```

Use ARDUINO_DIRECTORIES_DATA, ARDUINO_DIRECTORIES_DOWNLOADS and ARDUINO_DIRECTORIES_USER for an isolated installation. The adapter fingerprints the selected core, native tools and pinned libraries, and passes explicit library paths to the compiler. Unrelated installed cores are not part of the lock. Builds write under .codecraft/builds/arduino/.

Source: https://github.com/Seeed-Studio/ArduinoCore-samd/tree/1.8.6
