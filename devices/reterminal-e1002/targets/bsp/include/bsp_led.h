/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Green status LED on GPIO 6, active low
 * (Zephyr boards/seeed/reterminal_e1001 dts, Apache 2.0).
 */
#pragma once

#include <stdbool.h>

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Serialized task context: one LED owner/application mutex for init/set;
 * no ISR calls. The pin is reserved for this BSP until reset. Init is ready
 * only after configuring and requesting off; native errors propagate and
 * allow retry. Repeated successful init preserves the requested LED state.
 * Native GPIO calls add no BSP delay and have no hard total deadline. */
esp_err_t bsp_led_init(void);
/* Returns INVALID_STATE before readiness and propagates GPIO write errors.
 * Physical state is uncertain after a failed write; the owner may retry. */
esp_err_t bsp_led_set(bool on);

#ifdef __cplusplus
}
#endif
