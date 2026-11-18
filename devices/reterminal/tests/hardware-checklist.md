# Hardware acceptance checklist

Imported from the pre-migration on-device checklist. These are procedures and expectations, not completed observations. Device writes require session authorization and verified physical identity. Use record-evidence for results; no automatic support promotion.

## reTerminal (CM4, Linux)

| # | Check | Demo / how | Expected |
|---|-------|------------|----------|
| 1 | Buttons | `buttons_evdev.py` | F1/F2/F3/O events |
| 2 | LEDs + buzzer | `leds_buzzer_sysfs.py` | LEDs cycle, buzzer chirps |
| 3 | Sensors | `sensors_sysfs.py` | lux + accel readings plausible |
| 4 | RTC | `timedatectl` / `hwclock -r` | PCF8563 keeps time across power cycle (battery fitted) |
| 5 | Header GPIO | `header_gpio_blink.py` | BCM4 toggles (scope or LED) |
| 6 | Display + touch | vendor overlay | desktop/console on panel, touch tracks |
