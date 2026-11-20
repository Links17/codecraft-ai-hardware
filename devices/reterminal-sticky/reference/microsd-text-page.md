# Read MicroSD text without disrupting the display

Source: Seeed's [ESP-IDF Pages and Peripherals](https://www.seeedstudio.com/sticky/docs/en/device-guide/esp-pages/). This describes the official Note page and its Device APIs.

## Required operation order

The e-paper panel and MicroSD share **SPI2**, with separate chip selects. Finish the complete SD transaction before refreshing the panel:

```text
Detect card
-> enable MicroSD power
-> mount FAT filesystem
-> read file
-> unmount filesystem
-> release the SD device's shared-SPI2 access
-> render the page
-> refresh e-paper
```

Do not release or deinitialize the entire SPI2 bus after an SD read; the display owns and reuses that bus. When initializing `spi_bus_config_t`, set every unused data pin to `-1`—a default `0` can incorrectly claim GPIO0, which belongs to the sensor I2C1 bus.

## Demo data path

```text
MicroSD /TEST.TXT
-> sticky_sdcard_read_text()
-> AppState.note
-> Note Page Renderer
```

`update_note()` calls the Device API and stores `valid` and `error`. The App invokes it before `render_current_page()` can refresh the display. Opening the Note page or short-pressing AI / OK / Power button on that page reads the file again.

The demo stores up to **256 bytes** and draws up to **6 lines**, with at most **52 single-byte characters per line**. Its byte-oriented Renderer is intended for short ASCII text; these limits are demo choices, not hardware limits.

## Failure behavior

Keep file access out of the Page Renderer. If the card is absent, mounting fails, or `TEST.TXT` is missing, mark the note invalid and show an error state while leaving other pages usable. A failed read must not proceed directly into a display operation while SD still owns shared SPI2 access.
