/*
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 * Modified 2026 by CodeCraft AI Hardware contributors.
 * Derived from the imported hardware reference esp32/components/camera/camera.h (Apache 2.0).
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#pragma once

#include <stddef.h>
#include <stdint.h>

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/*
 * A still camera, whichever one the board has. Each camera is a backend that
 * fills in a camera_driver_t, and the board registers its one at startup.
 * Callers don't see the backend: they take a JPEG with camera_capture() and
 * hand it back with camera_release(), or watch a stream of frames for a
 * viewfinder with camera_stream_start() and camera_stream_stop().
 */

typedef struct {
    const uint8_t *jpeg;
    size_t len;
    int width, height;
    void *priv;               /* the backend's, for release */
} camera_frame_t;

/* Borrowed frame on the backend's task; data is freed when this returns. Copy
 * data needed later. Do not release it or call stream_stop from this callback.
 * Keep work bounded; post UI updates to the owning UI task/queue. */
typedef void (*camera_frame_cb_t)(const camera_frame_t *frame, void *ctx);

typedef struct {
    const char *name;         /* for logs and UIs: "Himax WiseEye2 (SenseCAP Watcher)" */
    int max_width, max_height;
    /* Once, before the first capture; NULL if there's nothing to set up. */
    esp_err_t (*init)(void);
    /* One JPEG. On success jpeg/len must be nonzero. On error the backend must
     * release any partial frame allocation itself. */
    esp_err_t (*capture)(camera_frame_t *out);
    /* Frees what capture() gave out; NULL if nothing needs freeing. */
    void (*release)(camera_frame_t *frame);
    /* Frames until stream_stop(), smaller ones to keep up; the camera stays
     * powered meanwhile. Both NULL if it can't stream. */
    esp_err_t (*stream_start)(camera_frame_cb_t on_frame, void *ctx);
    void (*stream_stop)(void);
} camera_driver_t;

/* Register once during serialized startup, before any consumer task. The driver
 * and referenced configuration must live for the process. NULL, missing-capture
 * and subsequent registrations are ignored; there is no replacement/shutdown. */
void camera_register(const camera_driver_t *driver);

/* Borrowed descriptor, or NULL. Inspect metadata only; call the wrapper APIs
 * below, not backend function pointers that would bypass ownership. */
const camera_driver_t *camera_get(void);

/*
 * Takes one picture. Starts the backend on first use. One frame is out at a
 * time: until camera_release(), another capture returns ESP_ERR_INVALID_STATE.
 * ESP_ERR_NOT_SUPPORTED if there's no camera; INVALID_ARG for a NULL output.
 * Output is unchanged on failure, including a busy retry using the held frame.
 * Release the exact output object once; keep it and its contents unchanged and
 * alive until release. Copies are not transferable ownership tokens. NULL,
 * foreign and already-released frames are ignored by release.
 *
 * Task context only. Capture/start attempts have a non-waiting ownership gate;
 * a competing attempt returns INVALID_STATE. Use one control-owning task or an
 * application mutex for release/stop and other lifecycle operations; no ISR or
 * callback reentrancy. Buffers are backend-owned, never caller-freed. Capture
 * and stream setup block according to the backend policy, not a generic total
 * deadline; run them on a worker, not a non-blocking UI/button callback.
 */
esp_err_t camera_capture(camera_frame_t *out);
void camera_release(camera_frame_t *frame);

/*
 * Calls on_frame with each frame until camera_stream_stop(), which returns
 * once no more will come. A stream holds the camera as a frame does: capture
 * and another stream return ESP_ERR_INVALID_STATE meanwhile. Starts the
 * backend on first use. ESP_ERR_NOT_SUPPORTED if it can't stream; INVALID_ARG
 * for NULL on_frame. ctx remains caller-owned and valid until stop returns.
 * The control owner must stop before destroying ctx/UI state. Stop may wait
 * without a hard deadline for the worker/callback to finish; never invoke it
 * from on_frame. Repeated stop after completion is a no-op.
 */
esp_err_t camera_stream_start(camera_frame_cb_t on_frame, void *ctx);
void camera_stream_stop(void);

#ifdef __cplusplus
}
#endif
