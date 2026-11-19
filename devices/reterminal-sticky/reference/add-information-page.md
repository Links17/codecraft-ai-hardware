# Add an ESP-IDF information page

Source: Seeed's [ESP-IDF Development Basics](https://www.seeedstudio.com/sticky/docs/en/device-guide/esp-basics/). The names below belong to the official `Sticky_dashboard_demo`; they are not current repository BSP APIs.

## Keep the data path unidirectional

```text
Device -> app_data -> AppState -> Page Renderer -> Canvas -> Display
```

- `board/`: initialize shared power and buses once.
- `devices/`: access hardware; do not draw UI.
- `app_data`: read Device APIs and update data, validity, and error state.
- `pages/`: read `AppState` and draw to `Canvas`; do not access hardware or refresh the panel.
- App layer: select the page, update its data, render it, and call the display refresh flow.

For shared I2C1 devices, reuse `board_sensor_i2c_bus()` instead of creating another bus on GPIO0/GPIO1.

## Add a page

1. Create `main/pages/<name>_page.h` and `.cpp` with a Renderer accepting `Canvas &` and `const AppState &`.
2. If the page needs hardware data, add a state structure containing the values plus `valid` and `error`; update it in `app_data` through a Device API.
3. Add the page to `PageId`, `page_name()`, and `render_current_page()`.
4. Add both forward and reverse navigation in `select_next_page()` and `select_previous_page()`.
5. Add the new `.cpp` to `main/CMakeLists.txt`.
6. Build and verify page entry, both navigation directions, valid data, and the read-failure state.

A missing CMake entry commonly causes an undefined-reference error. A page that builds but cannot be opened usually lacks a Renderer registration or one of the navigation transitions.

## Rendering contract

- Use **800 × 480 landscape logical coordinates**, origin at the top-left. The Display layer handles the physical 180° rotation; do not rotate page coordinates again.
- Use only `GrayLevel::Black` and `GrayLevel::White` on monochrome pages. Add a page to `page_uses_gray4()` only when it needs four-level grayscale.
- Let the App layer call `refresh_current_page()` after rendering. See [Display refresh implementations](display-refresh.md).
- The built-in bitmap font supports printable ASCII; unsupported glyphs appear as `?` unless the font is extended.

## Build and verify

The official demo baseline is **ESP-IDF v5.4**.

```sh
idf.py set-target esp32s3
idf.py build
idf.py -p PORT flash monitor
```

Run `set-target` only when configuring the project for ESP32-S3. Replace `PORT` with the Sticky serial port.
