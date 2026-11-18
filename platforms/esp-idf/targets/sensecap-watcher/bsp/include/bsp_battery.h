/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * SenseCAP Watcher battery: a 62k/20k divider from the battery onto ADC1
 * channel 2 (GPIO3), gated by the PWR_BAT_ADC rail on the IO expander, and a
 * battery-present detect line next to it.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Task context only, with serialized startup and one owning task (or an
 * application mutex) for reads. No ISR use. Powers the divider rail and sets
 * up ADC1 channel 2 with curve-fitting calibration. Repeated success is a no-op.
 * The BSP owns ADC/calibration for process lifetime. Failure releases acquired
 * ADC resources; retry requires complete cleanup, otherwise reset is required.
 * Failure retains the existing divider-rail state. Expander operations use
 * their documented lock/I2C timeouts; ADC setup has no whole-call deadline. */
esp_err_t bsp_battery_init(void);

/* Battery terminal voltage in millivolts. Caller-owned output is unchanged on
 * error. INVALID_STATE before successful init; INVALID_ARG for NULL; native
 * ADC/calibration errors propagate, including a busy ADC timeout. The native
 * read has no caller-configurable deadline; this is not a hard realtime API. */
esp_err_t bsp_battery_get_voltage_mv(uint16_t *out_mv);

/* Expander BAT_DET line: true when present; false before init or on read error.
 * Task-only, using the expander's bounded lock/transfer policy. */
bool bsp_battery_is_present(void);

#ifdef __cplusplus
}
#endif
