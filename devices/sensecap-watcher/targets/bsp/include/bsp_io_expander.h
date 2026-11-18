/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * SenseCAP Watcher PCA9535 16-bit IO expander (I2C0 @0x21, INT on GPIO2).
 * Carries the board's power rails, the camera sync/reset lines, card detect,
 * charge status, the knob's push and the touch interrupt.
 * All functions are idempotent-safe to call after bsp_io_expander_init().
 */
#pragma once

#include "esp_err.h"
#include "driver/i2c_master.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Task context only, with serialized startup before concurrent use. Register
 * operations use an internal mutex, including camera-task callbacks; one
 * read-modify-write cannot overlap another. No ISR use or non-blocking callback
 * context. Initialization includes probe and all four
 * shadow-register reads; an allocated device alone is not ready. Each I2C
 * operation has a 100 ms timeout, with no whole-call deadline promised.
 * Successful repeat init is idempotent. A failed init rolls back resources
 * acquired before publication; retry is supported after complete cleanup.
 * Failed cleanup retains handles and rejects init until a board reset. */
esp_err_t bsp_io_expander_init(void);

/* Returns a borrowed, process-lifetime I2C0 bus shared with the audio codecs,
 * after successful init. Never delete this bus or the expander device.
 * A non-NULL output pointer is required and is cleared on failure. */
esp_err_t bsp_i2c0_get_bus(i2c_master_bus_handle_t *out_bus);

/* pin: 0-15. direction: 1 = output, 0 = input. Each operation waits up to 100 ms
 * (tick-rounded) for the internal mutex, then applies its I2C timeout(s).
 * Applications must still serialize multi-call power/reset sequences involving
 * the same pins. A failed write invalidates that port's shadow;
 * the next setter first reads it back, or fails without writing if readback
 * fails. Therefore a setter uses one or two I2C calls (100 ms each). Failure
 * does not promise that the previous electrical value was preserved. */
esp_err_t bsp_io_expander_set_direction(int pin, int output);

/* pin: 0-15, must be configured as output. */
esp_err_t bsp_io_expander_set_level(int pin, int level);

/* pin: 0-15. Reads the input register regardless of direction. The caller owns
 * level; it is unchanged on lock/transfer error. Lock timeout => TIMEOUT. */
esp_err_t bsp_io_expander_get_level(int pin, int *level);

#ifdef __cplusplus
}
#endif
