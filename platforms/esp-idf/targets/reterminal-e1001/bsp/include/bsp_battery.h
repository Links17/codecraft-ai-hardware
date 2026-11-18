/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Battery voltage sense: divider on GPIO 1 (ADC1 channel 0), enabled by
 * driving GPIO 21 high. Divider is 10k/10k, so VBAT = 2x the ADC voltage
 * (Zephyr boards/seeed/reterminal_e1001 dts voltage-divider node,
 * Apache 2.0). Battery: 2000 mAh LiPo charged by a SY6974B on I2C1.
 */
#pragma once

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Task context only. One battery-owning task or application mutex must
 * serialize init/read; no ISR or non-blocking callback use. The BSP owns
 * ADC1, channel 0, calibration and the divider GPIO until reset. Do not
 * reconfigure/delete them through SDK calls. Repeated successful init is a
 * no-op. Failed setup releases the ADC; complete cleanup allows retry,
 * failed deletion blocks init until reset. Missing calibration eFuse data
 * preserves the legacy uncalibrated estimate; other calibration errors fail.
 * Native allocation/ADC/cleanup has no BSP-imposed total deadline. */
esp_err_t bsp_battery_init(void);

/* Requires readiness and non-NULL output, preserved on any error. Enable,
 * settle nominally 10 ms plus one tick, sample, then disable the divider.
 * No hard whole-call deadline; scheduling/native waits are additional.
 * Always attempts disable even after enable/read failure. A failed disable
 * leaves physical state uncertain; the next read must first turn it off
 * successfully before sampling again. Returns calibrated millivolts when
 * available; otherwise the existing raw*3100/4095*2 estimate is approximate,
 * not a measured accuracy guarantee. Caller owns output through the call. */
esp_err_t bsp_battery_read_mv(int *mv);

#ifdef __cplusplus
}
#endif
