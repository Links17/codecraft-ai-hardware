/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Onboard buzzer driven by LEDC PWM on GPIO 45 (Zephyr board dts:
 * pwm-buzzer on ledc0 channel 0). Useful for key-press feedback and
 * attention alerts on a device with a slow e-paper display.
 */
#pragma once

#include <stdint.h>

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Task context only: one buzzer-owning task/application mutex serializes
 * init/tone/stop and the whole beep. No ISR or non-blocking callback calls.
 * BSP reserves low-speed LEDC timer 0/channel 0 for the process lifetime;
 * no other client may reconfigure/delete them. Timer/channel configuration
 * is board-owned native state, not an independently allocated BSP handle.
 * Failed init remains unready and can be retried to configure the same
 * reserved resources. Success configures silence; repeated success is a
 * no-op preserving an active tone. Hardware state after errors is uncertain.
 * Native LEDC calls have no BSP-imposed total deadline. */
esp_err_t bsp_buzzer_init(void);

/* Start a continuous tone at freq_hz (audible range roughly 100-8000 Hz),
 * 50% duty. Requires readiness and nonzero frequency; supported frequencies
 * are determined by the native clock/resolution. Call bsp_buzzer_stop() to
 * silence. Native errors propagate and may leave part of a change applied;
 * the owner must retry stop when silence is required. */
esp_err_t bsp_buzzer_tone(uint32_t freq_hz);

/* Ready-only silence request (duty 0); retry after native errors. */
esp_err_t bsp_buzzer_stop(void);

/* Blocking convenience, holding the application owner/lock through stop.
 * Zero duration requests tone then immediate stop; positive durations delay
 * by the native tick conversion with at least one tick, then request stop.
 * Scheduling and LEDC waits add latency; no exact acoustic duration or hard
 * total deadline is promised. A tone error returns immediately with uncertain
 * output; stop errors are returned to the caller for recovery. */
esp_err_t bsp_buzzer_beep(uint32_t freq_hz, uint32_t duration_ms);

#ifdef __cplusplus
}
#endif
