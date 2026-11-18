/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * SenseCAP Watcher display: a 412x412 round SPD2010 panel on SPI3 in QSPI
 * mode (40 MHz, 32-bit commands, 8-bit params, SPI mode 3, no D/C line), its
 * power rail on the IO expander and a PWM backlight on GPIO8.
 * Raw esp_lcd only — no LVGL; apps that want a UI toolkit layer it on top.
 */
#pragma once

#include "esp_err.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_panel_io.h"

#ifdef __cplusplus
extern "C" {
#endif

#define BSP_LCD_H_RES 412
#define BSP_LCD_V_RES 412

/* Task context only; serialize init, brightness and raw panel operations from
 * one owning task or an application mutex. Never call from ISR callbacks.
 * Powers the shared LCD/touch rail, initializes QSPI and the panel, then sets
 * brightness to 100%. Init may block for driver operations and boot delays;
 * no end-to-end deadline is promised. Successful repeat calls are idempotent.
 * The BSP exclusively owns SPI3 and LEDC low-speed timer 0/channel 1. Returned
 * handles are borrowed for the process lifetime: callers must not delete them.
 * Either output may be NULL; supplied outputs are cleared on every failure.
 * Failed init rolls back owned resources while preserving shared touch power.
 * A retry is supported after successful rollback. Incomplete rollback keeps
 * resource ownership, rejects retries with ESP_ERR_INVALID_STATE and requires
 * a board reset. A non-NULL internal handle alone never implies readiness. */
esp_err_t bsp_display_init(esp_lcd_panel_handle_t *out_panel, esp_lcd_panel_io_handle_t *out_io);

/* Clamp to 0-100; returns ESP_ERR_INVALID_STATE until init fully succeeds.
 * Same serialized task context as init. The display keeps its last frame with
 * the backlight off. No asynchronous buffer ownership is transferred here. */
esp_err_t bsp_display_set_brightness(int percent);

#ifdef __cplusplus
}
#endif
