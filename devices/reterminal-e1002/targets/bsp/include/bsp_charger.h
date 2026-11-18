/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Onboard Silergy SY6974B single-cell Li-Po charger on I2C1 (address 0x6B).
 * Charging itself is autonomous (hardware CC/CV); this driver exists to
 * report charge state to the UI and to tune the charge current/voltage.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    BSP_CHARGER_STATUS_DISCHARGING = 0, /* no valid input power */
    BSP_CHARGER_STATUS_NOT_CHARGING,    /* powered, but not charging */
    BSP_CHARGER_STATUS_PRECHARGE,       /* deeply discharged battery */
    BSP_CHARGER_STATUS_FAST_CHARGE,
    BSP_CHARGER_STATUS_FULL,
} bsp_charger_status_t;

/* Task context only: init is serialized startup before worker tasks; no ISR
 * or non-blocking UI/button callback calls. After startup, individual getters
 * and setters may run concurrently: a device mutex spans each full register
 * read or read-modify-write. It does not make a series of public calls atomic;
 * use one application owner/lock for multi-call policy changes. Do not modify
 * charger registers through another client while this BSP owns the device.
 * Handles, I2C1 bus and mutex belong to the BSP for the process lifetime.
 *
 * Repeat successful init is a no-op, preserving runtime settings. Failed init
 * releases owned device/bus/mutex; incomplete cleanup blocks init until reset.
 * Hardware settings may be partially changed even after successful cleanup;
 * supported retry replays the complete original reset/default sequence.
 * Ready requires all initial register operations. Null outputs fail before
 * I/O; all getters preserve output on error. Runtime mutex wait is 100 ms
 * converted to ticks (minimum one tick), and each I2C call uses 100 ms. Setters
 * use read plus write. Init includes the original reset delay and native
 * setup/cleanup waits. These policies are not hard whole-call deadlines.
 * Failed writes leave the applied state uncertain; retry the complete desired
 * setting or read it back. Lock timeout performs no I/O.
 *
 * Probe the part ID, reset to defaults, disable the I2C watchdog (so the
 * configuration persists without periodic host traffic) and apply the
 * vendor board settings: 1000 mA requested charge current (encoded as 960 mA in 60 mA steps),
 * 4208 mV charge voltage. These preserve the existing board settings. Returns ESP_ERR_NOT_FOUND when the
 * chip does not answer or reports a wrong part ID. */
esp_err_t bsp_charger_init(void);

/* Aggregate charge state for UI display. */
esp_err_t bsp_charger_get_status(bsp_charger_status_t *out_status);

/* True when a valid input source is present (REG0A BUS_GD). */
esp_err_t bsp_charger_is_input_present(bool *out_present);

/* Enable/disable charging (REG01 CHG_CONFIG). */
esp_err_t bsp_charger_set_charge_enabled(bool enabled);

/* Constant-charge current in mA. Set clamps to 0-3000 mA in 60 mA steps. */
esp_err_t bsp_charger_get_charge_current_ma(uint16_t *out_ma);
esp_err_t bsp_charger_set_charge_current_ma(uint16_t ma);

/* Raw fault register (REG09) for diagnostics; 0 means no faults. Bit
 * layout: [7] watchdog, [6] boost, [5:4] charge fault, [3] battery OVP,
 * [2:0] NTC fault. */
esp_err_t bsp_charger_get_faults(uint8_t *out_fault);

#ifdef __cplusplus
}
#endif
