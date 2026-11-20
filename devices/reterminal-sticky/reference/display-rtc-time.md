# Partially refresh the RTC status-bar time

Source: Seeed's [ESP-IDF Refresh and Low Power](https://www.seeedstudio.com/sticky/docs/en/device-guide/esp-refresh/). APIs below belong to `Sticky_dashboard_demo`.

## Event-driven update sequence

Use this only on **monochrome pages that display the status-bar time**. The grayscale Home page skips this path.

```text
RTC minute timer
-> post ClockMinuteTick
-> App event loop reads the physical RTC
-> update AppState.date_time
-> redraw only the time area in Canvas
-> sticky_display_refresh_partial()
```

Start `app_clock_start()` after the initial page and RTC read. If the RTC is valid, use its seconds value to align the first event with the next minute boundary. The timer callback only posts `ClockMinuteTick`; it must not read the RTC or access the display.

## Refresh only when the displayed value changes

On each event, save the previous validity, hour, and minute, then call `update_date_time()`. Continue only if validity changed or a valid hour/minute value changed. Return without redrawing when the value is unchanged, and skip partial refresh when `page_uses_gray4()` is true.

`status_bar_render_time()` must first fill the old time rectangle with white and then draw the new `HH:MM`. Drawing new digits over old ones leaves overlapping pixels in Canvas.

## What “partial” means in this demo

The Page layer changes only the small time area, but the SSD1677 Display layer still submits a **complete monochrome comparison frame**. The controller compares previous and current frames and leaves identical pixels unchanged. Do not mistake this for an arbitrary-rectangle BSP API.

Use the page's assigned full refresh after complete page changes or grayscale updates. A short press of AI / OK / Power button redraws the current page with its full-refresh mode and provides a cleanup opportunity after repeated partial updates.

See [Display refresh implementations](display-refresh.md) for method selection and the current repository BSP mapping.
