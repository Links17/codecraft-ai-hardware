/* Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0 */
#pragma once

#include "driver/i2c_master.h"
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct codecraft_sht4x *codecraft_sht4x_handle_t;

/* Task context only. Create/delete require exclusive access; initialize before
 * starting reader tasks. The caller owns the synchronous I2C bus; the component
 * owns its device, mutex and handle. No bus, pin or power configuration changes.
 * config supplies the board's address and bus speed. timeout_ms must be positive.
 * *out must be NULL; failure leaves it NULL and releases acquired resources.
 * A failed probe returns ESP_ERR_NOT_FOUND. Other SDK errors are propagated. */
esp_err_t codecraft_sht4x_create(i2c_master_bus_handle_t bus,
                                const i2c_device_config_t *config,
                                int timeout_ms, codecraft_sht4x_handle_t *out);

/* Exclusive task access, with no readers outstanding. On removal failure retain
 * *sensor for retry; on success free owned resources and set *sensor to NULL.
 * The caller's shared bus is never deleted. */
esp_err_t codecraft_sht4x_delete(codecraft_sht4x_handle_t *sensor);

/* Concurrent task reads on one handle are serialized across command, conversion
 * and receive. Unrelated I2C devices remain usable during conversion. Never use
 * from an ISR or while holding a callback lock that forbids blocking.
 * The mutex wait and each of two I2C calls use timeout_ms; conversion delays
 * nominally 10 ms plus a scheduler tick. Tick rounding/scheduling means this is
 * a blocking policy, not a hard total deadline. No output is written on error.
 * NULL handle => INVALID_STATE; NULL outputs => INVALID_ARG; lock/I2C timeout
 * => TIMEOUT; corrupt temperature or humidity word => INVALID_CRC.
 * Output buffers belong to the caller and must not be shared across readers. */
esp_err_t codecraft_sht4x_read(codecraft_sht4x_handle_t sensor,
                              float *temp_c, float *rh_pct);

#ifdef __cplusplus
}
#endif
