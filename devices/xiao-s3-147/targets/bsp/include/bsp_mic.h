/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Onboard PDM microphone (I2S0 PDM RX: CLK GPIO 1, DATA GPIO 2 — the only
 * PDM receiver on the ESP32-S3). Mono 16-bit PCM at the requested sample
 * rate; the board removes the PDM filter's DC offset in hardware.
 */
#pragma once

#include <stddef.h>
#include <stdint.h>

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Task context only. One owning task or an application mutex must serialize
 * init/read/deinit; never deinitialize during a read or use from an ISR or
 * non-blocking UI/button callback. The BSP owns the I2S0 RX channel.
 *
 * Start PDM RX at nonzero sample_rate_hz (typically 16000). Repeating the same
 * ready rate is a no-op; changing it requires a successful deinit. Failure
 * attempts channel cleanup; incomplete cleanup blocks init/read until deinit
 * succeeds or the device resets. Native init/cleanup has no BSP-imposed
 * whole-call deadline. SDK errors propagate. */
esp_err_t bsp_mic_init(uint32_t sample_rate_hz);

/* Read up to sample_count 16-bit mono samples into caller-owned storage, which
 * must remain valid for the call. NULL arguments, zero count or a byte count
 * exceeding the native int-length range return INVALID_ARG; unready state
 * returns INVALID_STATE. out_read is required and cleared before validation.
 *
 * timeout_ms is passed unchanged in milliseconds to the native I2S API. IDF
 * applies it separately to channel/DMA waits; multi-buffer reads and scheduling
 * can exceed it, so it is not a hard whole-call deadline. On native error
 * (including TIMEOUT), out_read reports complete samples already copied; the
 * remaining buffer is unspecified. */
esp_err_t bsp_mic_read(int16_t *samples, size_t sample_count, size_t *out_read,
                       uint32_t timeout_ms);

/* Stop/delete the channel. Success is idempotent. Failure invalidates readiness
 * but preserves ownership; retry deinit to finish before init. Never delete
 * BSP handles through SDK APIs. Native stop has no hard whole-call deadline. */
esp_err_t bsp_mic_deinit(void);

#ifdef __cplusplus
}
#endif
