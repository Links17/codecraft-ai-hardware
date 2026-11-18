# Hardware acceptance checklist

Imported from the pre-migration on-device checklist. These are procedures and expectations, not completed observations. Device writes require session authorization and verified physical identity. Use record-evidence for results; no automatic support promotion.

## reTerminal E1001 / E1002 (ESP32-S3)

| # | Check | Example / how | Expected |
|---|-------|---------------|----------|
| 1 | EPD | `epd_hello` | pattern renders fully, no ghosting streaks; E1002 shows 6 colors |
| 2 | Keys/LED | `board_health` | all three keys register, LED toggles |
| 3 | SHT4x + battery | `sht4x_battery` | plausible temp/RH/mV |
| 4 | RTC | `board_health` | time sets and survives reboot |
| 5 | Charger | `board_health` | SY6974B part ID match, charge status on USB |
| 6 | Mic | `board_health` | PDM samples non-zero, level follows noise |
| 7 | Buzzer | `board_health` | audible beep |
| 8 | microSD | `sdcard_test` | mount + write/read-back OK; **also verify the panel still works after the SD bus init** (shared SPI2) |
