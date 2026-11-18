# Hardware acceptance checklist

These procedures define expected physical observations. Device writes require session authorization and verified physical identity. Use record-evidence for results; no automatic support promotion.

## SenseCAP Indicator (ESP32-S3)

| # | Check | Example / how | Expected |
|---|-------|---------------|----------|
| 1 | Display | `display_color_bars` | ST7701S RGB bars render |
| 2 | Button | `button_backlight` | press toggles backlight |
| 3 | Touch | `touch_read` | FT6336U or GT911 probed, coordinates sane |
