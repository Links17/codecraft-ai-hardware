/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Onboard NXP PCF8563 real-time clock on I2C0 (address 0x51). The RTC is
 * battery-backed: time survives deep sleep and main-power loss, which makes
 * it the right clock for wake scheduling on an e-paper device.
 */
#pragma once

#include <time.h>

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Task-only, serialized startup before access. Attach once to shared I2C0;
 * successful repeated init is a no-op. The BSP owns the device and shared bus
 * for the process lifetime. Failed attachment releases its resources and can
 * be retried; a failed probe returns NOT_FOUND. */
esp_err_t bsp_rtc_init(void);

/* Task-only synchronous read/write: one I2C transfer per call, timeout 100 ms.
 * No ISR use. Transfers serialize in the native driver; cross-task ordering is
 * unspecified. Applications must serialize any compound read-modify-write.
 * Buffers are caller-owned. NULL buffer => INVALID_ARG, not initialized =>
 * INVALID_STATE, transfer errors propagate. No hard total deadline is promised.
 *
 * Read the current time into out_time (struct tm; tm_year is years since
 * 1900, tm_mon is 0-11). Returns ESP_ERR_INVALID_STATE when the oscillator
 * integrity flag (VL) says the time was lost, e.g. after a full battery
 * drain — call bsp_rtc_set_time() before trusting the value. Invalid BCD/field
 * ranges return INVALID_RESPONSE. Outputs remain unchanged on every error. */
esp_err_t bsp_rtc_get_time(struct tm *out_time);

/* Set the time. 24-hour mode; tm_year counts from 1900 and must be within
 * 2000-2099 (the century bit is managed for you). tm_wday is written
 * through (0 = Sunday). Out-of-range fields return INVALID_ARG; consistency
 * between date, month length and weekday remains the caller's responsibility. */
esp_err_t bsp_rtc_set_time(const struct tm *time);

#ifdef __cplusplus
}
#endif
