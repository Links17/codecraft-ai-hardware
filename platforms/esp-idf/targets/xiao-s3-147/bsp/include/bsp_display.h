/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * 1.47" 172x320 IPS LCD, JD9853A driven with the ST7789-compatible
 * esp_lcd driver plus Seeed's vendor register sequence (Seeed_GFX2, MIT).
 * Portrait: the panel is mirrored on X with a column gap of 34.
 */
#pragma once

#include <stdbool.h>

#include "esp_err.h"
#include "esp_lcd_types.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Task context only. One display-owning task or application mutex must
 * serialize initialization, BSP calls and all calls on the borrowed panel.
 * Do not call from an ISR or a non-blocking UI/button callback. Application
 * LVGL calls still require its LVGL lock; this BSP does not provide one.
 *
 * Initialize before any consumer of the shared LCD/touch reset starts.
 * SPI2 is board-owned for the process lifetime. An existing bus must have
 * matching pins/configuration; INVALID_STATE alone does not verify that.
 * The BSP owns the panel and IO for the process lifetime: do not delete or
 * independently reset them. out_panel is required and cleared on failure.
 * Repeated successful init returns the same handle without resetting touch.
 * Failed init releases owned panel/IO; complete cleanup permits retry before
 * other reset consumers start. Incomplete cleanup blocks init until reset.
 * GPIO/reset/backlight state after an error is not promised to be restored.
 * Native SPI waits may be indefinite; init also has vendor fixed delays.
 * There is no hard total deadline or physical recovery guarantee.
 *
 * esp_lcd_panel_draw_bitmap() queues DMA: its caller-owned RGB565 buffer
 * must remain alive and unchanged until bsp_display_wait_idle() succeeds,
 * including after a draw error that may have queued a partial transfer. */
esp_err_t bsp_display_init(esp_lcd_panel_handle_t *out_panel);

/* Drain queued pixel transfers without sending a panel command. Requires
 * ready state and the same owner/lock as drawing. Native portMAX_DELAY waits
 * can block indefinitely. On error keep outstanding buffers alive/unchanged
 * and retry draining; do not reuse them based on elapsed time. This confirms
 * transfer completion, not visible pixels or tear-free presentation. */
esp_err_t bsp_display_wait_idle(void);

/* Backlight on/off (BSP_PIN_LCD_BL, active high); requires ready state.
 * GPIO errors propagate; physical backlight state is then uncertain. */
esp_err_t bsp_display_backlight(bool on);

#ifdef __cplusplus
}
#endif
