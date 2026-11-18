/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * SPD2010 capacitive touch on I2C1. Bus/pin facts from the vendor BSP
 * (SenseCAP-Watcher-Firmware components/sensecap-watcher, Apache 2.0);
 * reimplemented on the IDF v6 i2c_master driver.
 */

#include "bsp_touch.h"

#include "bsp_display.h"
#include "bsp_io_expander.h"
#include "bsp_pins.h"

#include "driver/i2c_master.h"
#include "esp_check.h"
#include "esp_lcd_touch_spd2010.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "bsp_touch";

static i2c_master_bus_handle_t s_bus;
static i2c_master_dev_handle_t s_device;
static esp_lcd_touch_handle_t s_touch;
static bool s_ready;

static esp_err_t touch_rollback(void)
{
    s_ready = false;
    if (s_touch) {
        ESP_RETURN_ON_ERROR(esp_lcd_touch_del(s_touch), TAG, "delete touch");
        s_touch = NULL;
    }
    if (s_device) {
        ESP_RETURN_ON_ERROR(i2c_master_bus_rm_device(s_device), TAG, "delete touch device");
        s_device = NULL;
    }
    if (s_bus) {
        ESP_RETURN_ON_ERROR(i2c_del_master_bus(s_bus), TAG, "delete I2C1");
        s_bus = NULL;
    }
    /* The LCD/touch rail is board-owned and stays powered for the display. */
    return ESP_OK;
}

esp_err_t bsp_touch_init(esp_lcd_touch_handle_t *out_handle)
{
    if (out_handle) {
        *out_handle = NULL;
    }
    if (s_ready) {
        if (out_handle) {
            *out_handle = s_touch;
        }
        return ESP_OK;
    }
    ESP_RETURN_ON_FALSE(!s_touch && !s_device && !s_bus, ESP_ERR_INVALID_STATE, TAG,
                        "incomplete rollback; reset required");
    esp_err_t ret;

    /* The touch controller sits in the display assembly and is fed by the
     * LCD rail, so it answers no I2C until that rail is on (bsp_display does
     * the same; both may be up already). */
    ESP_RETURN_ON_ERROR(bsp_io_expander_init(), TAG, "expander");
    ESP_RETURN_ON_ERROR(bsp_io_expander_set_direction(BSP_EXP_PIN_PWR_LCD, 1), TAG, "lcd rail dir");
    ESP_RETURN_ON_ERROR(bsp_io_expander_set_level(BSP_EXP_PIN_PWR_LCD, 1), TAG, "lcd rail on");
    vTaskDelay(pdMS_TO_TICKS(100));   /* let the controller boot, as the vendor BSP does */
    ESP_RETURN_ON_ERROR(bsp_io_expander_set_direction(BSP_EXP_PIN_TOUCH_INT, 0),
                        TAG, "touch int input");

    i2c_master_bus_config_t bus_cfg = {
        .i2c_port = 1,
        .sda_io_num = BSP_PIN_TOUCH_SDA,
        .scl_io_num = BSP_PIN_TOUCH_SCL,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    ESP_RETURN_ON_ERROR(i2c_new_master_bus(&bus_cfg, &s_bus), TAG, "i2c1 bus");

    const i2c_device_config_t dev_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = ESP_LCD_TOUCH_SPD2010_ADDRESS,
        .scl_speed_hz = BSP_I2C_FREQ_HZ,
    };
    ESP_GOTO_ON_ERROR(i2c_master_bus_add_device(s_bus, &dev_cfg, &s_device),
                      fail, TAG, "touch device");

    const esp_lcd_touch_config_t tp_cfg = {
        .x_max = BSP_LCD_H_RES,
        .y_max = BSP_LCD_V_RES,
        .rst_gpio_num = GPIO_NUM_NC, /* shared with the LCD reset */
        .int_gpio_num = GPIO_NUM_NC, /* lives on the IO expander instead */
        .levels = { .reset = 0, .interrupt = 0 },
        .flags = { .swap_xy = 0, .mirror_x = 0, .mirror_y = 0 },
    };
    ESP_GOTO_ON_ERROR(esp_lcd_touch_new_i2c_spd2010(s_device, &tp_cfg, &s_touch),
                      fail, TAG, "spd2010 touch");

    /* One read wakes the controller up (vendor BSP note). It then NACKs
     * I2C while its touch firmware boots, so poll until a read succeeds
     * instead of returning a handle that errors for the first ~100 ms. */
    vTaskDelay(pdMS_TO_TICKS(50));
    for (int attempt = 0; attempt < 25; attempt++) {
        ret = esp_lcd_touch_read_data(s_touch);
        if (ret == ESP_OK) {
            break;
        }
        vTaskDelay(pdMS_TO_TICKS(20));
    }
    if (ret != ESP_OK) {
        goto fail;
    }

    s_ready = true;
    if (out_handle) {
        *out_handle = s_touch;
    }
    ESP_LOGI(TAG, "touch ready (%dx%d)", BSP_LCD_H_RES, BSP_LCD_V_RES);
    return ESP_OK;

fail:
    if (touch_rollback() != ESP_OK) {
        ESP_LOGE(TAG, "touch rollback incomplete; reset required");
    }
    return ret;
}

esp_lcd_touch_handle_t bsp_touch_get_handle(void)
{
    return s_ready ? s_touch : NULL;
}
