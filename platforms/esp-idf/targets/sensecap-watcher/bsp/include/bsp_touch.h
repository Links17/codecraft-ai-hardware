/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * SenseCAP Watcher touch: the SPD2010 panel's integrated capacitive
 * controller on the dedicated I2C1 bus (SDA GPIO39 / SCL GPIO38, 400 kHz,
 * addr 0x53). Its interrupt line is not a real GPIO — it is pin 5 of the
 * PCA9535 IO expander, so the driver is created without an interrupt GPIO
 * and apps either poll or watch the expander (bsp_io_expander).
 * Coordinates map 1:1 to the 412x412 display, no swap/mirror.
 */
#pragma once

#include "esp_err.h"
#include "esp_lcd_touch.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Task context only, serialized startup; use a single touch owner or application
 * mutex for handle operations. No ISR calls. Brings up I2C1 and configures
 * expander pin 5 as input. Init includes at most 25 boot polls with 20 ms
 * retry delays, in addition to boot waits and bounded I2C transactions; no
 * whole-call deadline is promised. All polls failing returns the last error.
 * Successful repeat calls return the same borrowed, process-lifetime handle;
 * never delete it or its I2C bus/IO. Output may be NULL and is cleared on
 * failure. Failed init rolls back owned resources, retaining shared LCD power.
 * Retry is supported after complete rollback; incomplete cleanup requires a
 * board reset and subsequent init returns ESP_ERR_INVALID_STATE.
 * Native polling buffers belong to the caller through each call. Serialize
 * read_data/get_data as one owner transaction, honor both results and do not
 * publish cached coordinates after an error. Use a worker task rather than
 * a non-blocking UI/input callback; LVGL still requires its separate lock. */
esp_err_t bsp_touch_init(esp_lcd_touch_handle_t *out_handle);

/* Returns a handle only after fully successful init; otherwise NULL. */
esp_lcd_touch_handle_t bsp_touch_get_handle(void);

#ifdef __cplusplus
}
#endif
