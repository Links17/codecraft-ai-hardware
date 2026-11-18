/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * reTerminal Sticky e-paper panel: 3.97" SSD1677, native 800x480, used in
 * portrait at 480x800.
 *
 * Mono framebuffer: 1 bit per pixel, 8 pixels per byte, MSB is the
 * leftmost pixel of the logical row, 1 = white, 0 = black.
 * Gray4 framebuffer: 2 bits per pixel packed MSB first (four pixels per
 * byte), 0 = black ... 3 = white.
 *
 * The panel power rail (BSP_PIN_EPD_EN) stays on between updates; the
 * driver holds refresh state so fast updates can follow full ones.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"

#define BSP_EPD_WIDTH            480
#define BSP_EPD_HEIGHT           800
#define BSP_EPD_ROW_BYTES        (BSP_EPD_WIDTH / 8)
#define BSP_EPD_FRAME_BYTES      (BSP_EPD_ROW_BYTES * BSP_EPD_HEIGHT)
#define BSP_EPD_GRAY4_ROW_BYTES  (BSP_EPD_WIDTH / 4)
#define BSP_EPD_GRAY4_FRAME_BYTES (BSP_EPD_GRAY4_ROW_BYTES * BSP_EPD_HEIGHT)

#ifdef __cplusplus
extern "C" {
#endif

/* Task context only; never use from ISR or a non-blocking UI/button callback.
 * Init/mono/gray4 updates share a non-waiting guard: concurrent/reentrant use
 * returns INVALID_STATE before touching shared state. Schedule from an owning
 * display task; retain the LVGL lock for any separate LVGL operations.
 *
 * Configure GPIOs and attach to board-configured SPI2. Repeated successful init
 * is a no-op. Failure frees the DMA allocation and permits retry, retaining the
 * shared bus and existing rail state. Existing SPI2 must match this board's
 * pins and transfer requirements. BSP owns its device/DMA buffer for process
 * lifetime; no shutdown API exists. Readiness establishes transport setup,
 * not image content. Native setup has no hard whole-call deadline. */
esp_err_t bsp_epd_init(void);

/* Show `frame`. `prev` is what the panel currently shows (pass NULL on the
 * first update after boot or after a failed update; it forces a full
 * refresh). `full` selects a full (slow, clean) refresh over a fast one.
 * Caller owns frame/prev, each containing BSP_EPD_FRAME_BYTES, and keeps them
 * valid and immutable until return. The driver retains neither buffer.
 * Before readiness returns INVALID_STATE; NULL frame returns INVALID_ARG.
 * GPIO/SPI errors and busy timeout propagate. A failed attempted refresh makes
 * the next mono update full; panel content/power state remains uncertain.
 *
 * Each busy-poll window is 30 s plus polling/scheduler granularity. Multiple
 * windows, synchronous SPI and native bus waits mean there is no hard total
 * deadline. Keep this work off non-blocking callbacks. */
esp_err_t bsp_epd_update(const uint8_t *frame, const uint8_t *prev, bool full);

/* Show BSP_EPD_GRAY4_FRAME_BYTES of caller-owned 2 bpp data. Same context,
 * lifetime, argument/state and blocking contract as mono update. Always a full
 * grayscale refresh; the next mono update is full after success or an attempted
 * refresh failure. Invalid input or rejected concurrent calls do not change
 * the in-progress refresh state. */
esp_err_t bsp_epd_update_gray4(const uint8_t *frame);

#ifdef __cplusplus
}
#endif
