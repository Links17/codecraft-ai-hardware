/* Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0 */
#pragma once

#include <time.h>
#include "driver/i2c_master.h"
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct codecraft_pcf8563 *codecraft_pcf8563_handle_t;

/* Task context only. Exclusive create/delete before/after concurrent readers.
 * The caller owns the synchronous bus and supplies address/speed in config;
 * the component owns only the attached I2C device and handle. No board pin,
 * power, reset or bus configuration is changed. Positive per-call timeout_ms;
 * *out must be NULL and stays NULL on failure. Probe failure => NOT_FOUND. */
esp_err_t codecraft_pcf8563_create(i2c_master_bus_handle_t bus,
                                  const i2c_device_config_t *config,
                                  int timeout_ms, codecraft_pcf8563_handle_t *out);

/* Exclusive access, no outstanding reads/writes. On removal error keep *rtc
 * for retry; success frees the handle and clears it. Never deletes the bus. */
esp_err_t codecraft_pcf8563_delete(codecraft_pcf8563_handle_t *rtc);

/* Task-only synchronous I2C operations, each with the configured timeout.
 * ESP-IDF serializes individual transfers; read/write ordering across tasks is
 * unspecified. Callers needing a read-modify-write must serialize that sequence.
 * Buffers belong to the caller; outputs are unchanged on failure. NULL handle
 * => INVALID_STATE, NULL buffer => INVALID_ARG, SDK transfer errors propagate.
 * get: VL => INVALID_STATE; invalid BCD/field range => INVALID_RESPONSE.
 * Calendar convention retained from the BSP: tm_year=100..199 (2000..2099),
 * tm_mon=0..11, tm_wday=0..6; the century bit is ignored on read/clear on write.
 * set rejects out-of-range fields; calendar/day-of-week consistency is the
 * caller's responsibility. This is not a hard realtime deadline. */
esp_err_t codecraft_pcf8563_get_time(codecraft_pcf8563_handle_t rtc, struct tm *out);
esp_err_t codecraft_pcf8563_set_time(codecraft_pcf8563_handle_t rtc, const struct tm *time);

#ifdef __cplusplus
}
#endif
