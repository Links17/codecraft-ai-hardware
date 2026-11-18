/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Onboard Sensirion SHT4x temperature/humidity sensor on I2C1
 * (address 0x44, shared with the BQ27220 fuel gauge). Single-shot,
 * high-precision measurements using the shared codecraft_sht4x component.
 */
#pragma once

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Serialized task-context startup only, before reader tasks; no ISR or
 * non-blocking callbacks. Successful repeat init is a no-op. I2C1 is owned
 * for the process lifetime and retained if sensor creation fails; retry
 * reuses that bus. The component releases failed device/mutex allocations.
 * Successful bus/device handles remain BSP-owned until reset. Do not reset
 * the bus or modify sensor registers externally while reads are active.
 * Returns ESP_ERR_NOT_FOUND on probe failure; other SDK errors propagate. */
esp_err_t bsp_sht4x_init(void);

/* Concurrent task reads serialize the entire command/conversion/receive
 * sequence, without holding the bus during conversion. Each caller owns
 * distinct output storage through the call. Both outputs are required and
 * preserved on error. Not initialized => INVALID_STATE; NULL output =>
 * INVALID_ARG; corrupt temperature/humidity => INVALID_CRC.
 * Mutex wait and each of two native I2C transactions use 100 ms; conversion
 * waits nominally 10 ms plus one tick to avoid tick truncation. Scheduling
 * and SDK overhead are additional: no hard whole-call deadline is promised. */
esp_err_t bsp_sht4x_read(float *temp_c, float *rh_pct);

#ifdef __cplusplus
}
#endif
