/*
 * SPDX-FileCopyrightText: 2023 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#pragma once

#include "esp_lcd_touch.h"
#include "driver/i2c_master.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Native IDF I2C device, borrowed for the lifetime of the touch handle.
 * The BSP owns power, reset and interrupt routing. This driver polls; both
 * GPIO numbers must be GPIO_NUM_NC and interrupt_callback must be NULL.
 * Returns a handle only after initialization succeeds. Delete the handle
 * before removing the I2C device. Calls must be serialized by the owner.
 * Transactions use raw payloads with no LCD command/control prefix. */
esp_err_t esp_lcd_touch_new_i2c_spd2010(i2c_master_dev_handle_t device,
    const esp_lcd_touch_config_t *config, esp_lcd_touch_handle_t *tp);

/* Vendor SPD2010 0.0.1 touch protocol: 7-bit I2C address. */
#define ESP_LCD_TOUCH_SPD2010_ADDRESS 0x53

#ifdef __cplusplus
}
#endif
