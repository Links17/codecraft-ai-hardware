/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * SenseCAP Watcher knob: a quadrature wheel on GPIO41/42 decoded by the
 * pulse counter, with its push button on IO expander pin 3 (active low).
 */
#pragma once

#include <stdbool.h>

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Task context only; serialize startup and reads from one owning task or an
 * application mutex. Never call from an ISR. Sets up the PCNT decoder with a
 * 1 us glitch filter and the button line. Init may wait on expander I2C (100 ms
 * per transfer); no whole-call deadline is promised. Successful repeat calls
 * are idempotent. PCNT resources remain BSP-owned for the process lifetime.
 * Failed init rolls them back; retry is supported after complete cleanup.
 * Incomplete rollback retains ownership and rejects init until a board reset. */
esp_err_t bsp_knob_init(void);

/* Encoder counts since the last call, signed (positive = one way, negative =
 * the other; clockwise polarity requires measurement on the actual unit). The raw count advances
 * several steps per detent — divide by the encoder's steps-per-detent if you
 * want detents. Output is written only on success. Returns INVALID_STATE
 * before successful init and INVALID_ARG for a NULL output after init.
 * The get/clear sequence requires a single serialized consumer. */
esp_err_t bsp_knob_get_delta(int *out_delta);

/* True while pushed after successful init; false if not ready or on I2C error.
 * Task context; uses the expander's bounded read and shares its serialization. */
bool bsp_knob_button_pressed(void);

#ifdef __cplusplus
}
#endif
