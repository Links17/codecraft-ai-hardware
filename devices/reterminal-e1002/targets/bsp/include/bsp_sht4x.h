/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Onboard Sensirion SHT4x temperature/humidity sensor on I2C0
 * (address 0x44). Single-shot, high-precision measurements; each read
 * takes about 10 ms. The enclosure warms the sensor slightly — apply a
 * calibration offset in the application if absolute temperature matters.
 */
#pragma once

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Task-only, serialized startup before readers. Attach once to shared I2C0;
 * successful repeated init is a no-op. Bus and sensor are BSP-owned for the
 * process lifetime; no caller may delete them. Returns NOT_FOUND for a failed
 * probe. Failed attachment releases its resources and may be retried. */
esp_err_t bsp_sht4x_init(void);

/* Task-only; concurrent readers are serialized across command/conversion/read.
 * No ISR or non-blocking callback use. The per-device mutex waits up to 100 ms
 * (tick rounded), each I2C operation up to 100 ms, and conversion nominally
 * 10 ms plus one tick. Scheduler delays mean no hard total deadline is promised.
 * Other bus devices are not locked during conversion. Outputs are caller-owned
 * and unchanged on failure. NULL output => INVALID_ARG, uninitialized =>
 * INVALID_STATE, lock/transfer timeout => TIMEOUT, bad CRC => INVALID_CRC. */
esp_err_t bsp_sht4x_read(float *temp_c, float *rh_pct);

#ifdef __cplusplus
}
#endif
