<p align="right"><strong>English</strong> · <a href="README.zh_CN.md">简体中文</a></p>

# Shared ESP32 Components

Components placed here must be used by at least two boards. Single-board
drivers belong in the board's own `bsp/` directory.

Landed:

- `codecraft_sht4x/` — SHT4x protocol, CRC and conversion decoding shared by
  E1001/E1002. Each sensor serializes its complete read transaction; it leaves
  the shared bus available during conversion. BSPs supply bus/address/speed.
- `codecraft_pcf8563/` — PCF8563 time/date protocol shared by E1001/E1002,
  preserving the existing 2000–2099 convention. BSPs retain board wiring and
  process-lifetime ownership; the component validates fields and response BCD.
- `sscma_client/` — generic still-camera abstraction plus the SSCMA-over-SPI
  backend (Seeed Himax WiseEye2 on the SenseCAP Watcher; also fits a Grove
  Vision AI V2). Extracted from the imported hardware reference `esp32/components/camera/`
  (Apache 2.0, Meta copyright headers retained, modifications marked).

The extracted sensor protocols retain their original source/license comments.
The board-local I2C0 helper stays in each BSP: it owns that board's bus/pins,
requires serialized startup and does not establish cross-board compatibility.
Sensor public contracts are in each component's `include/`; implementation and
executable C cases are in `src/` and `tests/`. The host runner at
`codecraft_sht4x/tests/test_sensor_drivers.py` and
`codecraft_pcf8563/tests/test_sensor_drivers.py` uses narrow I2C/task doubles and runs through
`python3 codecraft.py validate --static` from the repository root.
These checks establish software behavior, not physical timing or sensor accuracy.
