/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * reTerminal E1002 e-paper panel: 7.3" 800x480 E Ink Spectra 6
 * (GDEP073E01), six inks, full refreshes only (~30 s).
 *
 * Framebuffer format: 4 bits per pixel, 2 pixels per byte, the left pixel
 * in the high nibble (the controller's order).
 *
 * The panel enters deep sleep after a successful update. Transport resources
 * remain owned by the BSP for the process lifetime.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"

#define BSP_EPD_WIDTH       800
#define BSP_EPD_HEIGHT      480
#define BSP_EPD_ROW_BYTES   (BSP_EPD_WIDTH / 2)
#define BSP_EPD_FRAME_BYTES (BSP_EPD_ROW_BYTES * BSP_EPD_HEIGHT)

/* Spectra 6 ink codes (reference epaper_status.c; Zephyr color-palette agrees). */
typedef enum {
    BSP_EPD_INK_BLACK  = 0,
    BSP_EPD_INK_WHITE  = 1,
    BSP_EPD_INK_YELLOW = 2,
    BSP_EPD_INK_RED    = 3,
    BSP_EPD_INK_BLUE   = 4,
    BSP_EPD_INK_GREEN  = 5,
} bsp_epd_ink_t;

#ifdef __cplusplus
extern "C" {
#endif

/* Task context only; never use from ISR or a non-blocking UI/button callback.
 * Init/update share a non-waiting guard: a concurrent/reentrant call returns
 * INVALID_STATE without touching the transport. Use an owning display task to
 * schedule refreshes. Retain the LVGL lock for any separate LVGL operations.
 *
 * Configure GPIOs and attach to the board's SPI2 bus. Successful repeated init
 * is a no-op; failure frees its DMA allocation and permits retry. The shared
 * bus remains available. An already-configured bus must match this board's
 * pins and transfer requirements; its settings are not inferred or replaced.
 * BSP owns its device/DMA buffer for process lifetime; no shutdown API exists.
 * Transport readiness does not establish panel content or physical validation.
 * Native setup has no BSP-imposed hard whole-call deadline. */
esp_err_t bsp_epd_init(void);

/* Show `frame`. The panel supports full refreshes only; `prev` and `full`
 * are accepted for interface parity with the mono panel and ignored.
 * Caller owns frame (BSP_EPD_FRAME_BYTES) and keeps it valid and immutable until
 * return; it is not retained. NULL frame returns INVALID_ARG; before readiness
 * returns INVALID_STATE. GPIO/SPI errors and busy timeout propagate.
 *
 * Each busy-poll window is 60 s plus polling/scheduler granularity. Several
 * windows and synchronous SPI transfers occur per refresh; native bus waits
 * mean this is not a hard whole-call deadline. On success the panel sleeps;
 * on failure its content/power state is uncertain. A retry performs the normal
 * reset/full-refresh sequence; physical recovery is not verified by software. */
esp_err_t bsp_epd_update(const uint8_t *frame, const uint8_t *prev, bool full);

/* Set one caller-owned pixel. Preconditions: fb contains BSP_EPD_FRAME_BYTES,
 * x/y are in bounds and ink is a declared code. Never mutate a frame while an
 * update is reading it; the caller schedules rendering and refresh ownership. */
static inline void bsp_epd_set_pixel(uint8_t *fb, int x, int y, bsp_epd_ink_t ink)
{
    uint8_t *byte = fb + (size_t)y * BSP_EPD_ROW_BYTES + x / 2;
    if (x & 1) *byte = (uint8_t)((*byte & 0xF0) | (uint8_t)ink);
    else       *byte = (uint8_t)((*byte & 0x0F) | ((uint8_t)ink << 4));
}

#ifdef __cplusplus
}
#endif
