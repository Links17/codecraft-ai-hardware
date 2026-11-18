# Imported vendor provenance

Source rows preserved from the pre-migration vendor index; primary links and source locations remain applicable.

| Board | Vendor source | Where to look |
| --- | --- | --- |
| reTerminal E1001 / E1002 | [Zephyr board definitions](https://github.com/zephyrproject-rtos/zephyr/tree/main/boards/seeed/reterminal_e1001) (`reterminal_e1001` / `reterminal_e1002`, Apache 2.0, vendor-contributed) + [E1001 V1.2 schematic](https://files.seeedstudio.com/wiki/reterminal_e10xx/res/202004307_reTerminal_E1001_V1_2_SCH_251120.pdf) (CC BY-SA 4.0) | The dts + pinctrl dtsi are the cleanest facts: key/LED GPIOs and active levels, battery ADC divider + enable, I2C addresses (SHT4x 0x44, PCF8563 0x51, SY6974B 0x6B), buzzer PWM, 32 MB flash. The schematic confirms flash size and power topology. UC8179 (E1001) and Spectra 6 (E1002) refresh sequences came from reference `esp32/main/epd_uc8179.c` / `epd_spectra6.c`. PCF8563 RTC register handling follows `zephyr:drivers/rtc/rtc_pcf8563.c`; the SY6974B charger driver follows `zephyr:drivers/charger/charger_sy6974b.c` (register map, part-ID check, reset/watchdog init) with board defaults from the dts (1000 mA / 4208 mV). |
