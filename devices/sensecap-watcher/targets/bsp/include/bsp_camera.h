/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * SenseCAP Watcher camera: a Himax WiseEye2 vision coprocessor that speaks
 * Seeed's SSCMA protocol over SPI2. Its power rail, sync line and reset all
 * sit on the PCA9535 expander, so bsp_camera_init() brings up I2C0 and the
 * expander first. The driver itself is the repository-shared sscma_client
 * component; this file only wires the board's lines into it.
 */
#pragma once

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Task-only, serialized startup: configure system power, camera power/sync/reset
 * lines and SD chip-select, then register the process-lifetime SSCMA backend.
 * Reset is an output, initially inactive; the backend manages its sourced
 * power/reset sequence. This function does not capture or prove camera readiness.
 * Registration is published only after every board operation succeeds. Repeated
 * success is a no-op; failure permits retry without switching off shared rails.
 *
 * Includes the existing 100 ms startup delay (tick-rounded), plus expander/GPIO
 * calls; there is no hard whole-call deadline. Do not call from ISR/UI callbacks.
 * Initialize shared peripherals serially and keep SD idle during camera traffic.
 * Subsequent frame/stream ownership and blocking rules are in camera.h and
 * camera_sscma.h; the BSP borrows the expander and retains system power. */
esp_err_t bsp_camera_init(void);

#ifdef __cplusplus
}
#endif
