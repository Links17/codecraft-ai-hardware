/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * SenseCAP Watcher audio: an ES8311 DAC (I2C0 @0x30) driving the speaker
 * and an ES7243/ES7243E ADC (I2C0 @0x13/@0x14, variant auto-detected) for
 * the microphone, both on I2S0 (16 kHz / 16-bit / mono, MCLK=GPIO10,
 * BCLK=GPIO11, WS=GPIO12, DOUT=GPIO16, DIN=GPIO15). The codec+amplifier
 * power rail is IO expander pin 12.
 * Uses esp_codec_dev; the returned handles are opened and ready for
 * esp_codec_dev_read()/esp_codec_dev_write().
 */
#pragma once

#include "esp_err.h"
#include "esp_codec_dev.h"

#ifdef __cplusplus
extern "C" {
#endif

#define BSP_AUDIO_SAMPLE_RATE 16000
#define BSP_AUDIO_SAMPLE_BITS 16
#define BSP_AUDIO_CHANNELS    1
#define BSP_AUDIO_MIC_GAIN_DB 27.0f /* vendor DRV_AUDIO_MIC_GAIN */

/* Powers the codec rail, brings up I2S0 duplex and opens both codec
 * devices (speaker out, mic in, gain BSP_AUDIO_MIC_GAIN_DB).
 * Task-only, serialized startup; no ISR or non-blocking callback use.
 * Readiness requires both opened devices and successful input-gain setup;
 * successful repeated init is a no-op. Failure rolls back owned allocations.
 * Complete cleanup permits retry; reported cleanup failure requires reset.
 * The shared I2C bus and existing codec rail remain board-owned.
 * Expander and codec I2C calls have 100 ms transfer timeouts; initialization
 * includes multiple native operations/delays and has no hard total deadline. */
esp_err_t bsp_audio_init(void);

/* Borrowed, opened handles only after successful init; NULL otherwise.
 * BSP owns all codec/interfaces/I2S resources for process lifetime. Never
 * close, delete, reopen or reconfigure these handles/channels externally.
 * Use one audio-owning task, or an application mutex covering all accesses
 * including read/write and volume/mute. Buffers belong to the caller and must
 * remain valid for the synchronous operation. The pinned IDF-v6 I2S data
 * backend passes 1000 ms to native transfers; chunking/locks/scheduling mean
 * this is not a hard whole-call deadline. Run blocking audio in a worker task.
 * See esp_codec_dev's native return contract for read/write errors. */
esp_codec_dev_handle_t bsp_audio_get_speaker(void);
esp_codec_dev_handle_t bsp_audio_get_mic(void);

/* Speaker volume 0-100; INVALID_ARG outside that range, INVALID_STATE before
 * readiness. Codec errors map to ESP_FAIL. Uses the same owning-task/mutex
 * contract; one operation may make multiple bounded I2C transfers. */
esp_err_t bsp_audio_set_volume(int percent);
esp_err_t bsp_audio_set_mute(bool mute);

#ifdef __cplusplus
}
#endif
