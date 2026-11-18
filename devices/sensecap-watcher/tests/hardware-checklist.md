# Hardware acceptance checklist

Imported from the pre-migration on-device checklist. These are procedures and expectations, not completed observations. Device writes require session authorization and verified physical identity. Use record-evidence for results; no automatic support promotion.

## SenseCAP Watcher (ESP32-S3)

| # | Check | Example / how | Expected |
|---|-------|---------------|----------|
| 1 | Camera | `camera_capture` | JPEG frame saved, plausible size |
| 2 | Display | `display_color_bars` | bars render, correct order/orientation |
| 3 | Touch | `touch_read` | coordinates track finger |
| 4 | Audio out | `audio_tone` | audible tone, no clipping |
| 5 | Mic | `mic_level` | level rises when speaking |
| 6 | Knob | `knob_input` | events follow rotation/press |
| 7 | Battery | `battery_status` | plausible mV, charging flag when USB in |
| 8 | microSD | `sdcard_test` | mount + write/read-back OK (FAT card) |
