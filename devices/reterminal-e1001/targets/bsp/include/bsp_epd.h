/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * reTerminal E1001 e-paper panel: 7.5" 800x480 monochrome, GDEY075T7
 * with a UC8179 controller.
 *
 * Framebuffer format: 1 bit per pixel, 8 pixels per byte, MSB is the
 * leftmost pixel, 1 = white, 0 = black (the controller's order).
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
#define BSP_EPD_ROW_BYTES   (BSP_EPD_WIDTH / 8)
#define BSP_EPD_FRAME_BYTES (BSP_EPD_ROW_BYTES * BSP_EPD_HEIGHT)

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

/* Show `frame`. `prev` is what the panel currently shows (pass NULL on the
 * first update after boot or after any failed refresh, forcing full refresh).
 * `full` selects full over fast refresh. Caller owns frame/prev, each containing
 * BSP_EPD_FRAME_BYTES, and must keep them valid and immutable until return;
 * neither buffer is retained. No mutation, including a UI renderer, may race
 * this call. NULL frame returns INVALID_ARG; before readiness returns
 * INVALID_STATE. GPIO/SPI errors and busy timeout propagate.
 *
 * Each busy-poll window is 10 s plus polling/scheduler granularity. Several
 * windows and synchronous SPI transfers occur per refresh; native bus waits
 * mean this is not a hard whole-call deadline. On success the panel sleeps;
 * on failure its content/power state is uncertain. Discard prev and request a
 * full refresh on retry. No image or physical-recovery claim follows an error. */
esp_err_t bsp_epd_update(const uint8_t *frame, const uint8_t *prev, bool full);

#ifdef __cplusplus
}
#endif
