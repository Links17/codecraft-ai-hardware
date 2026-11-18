/* SPDX-License-Identifier: Apache-2.0; narrow touch host API double. */
#pragma once
#include "idf_bsp_stub.h"
#define GPIO_NUM_NC (-1)
#define ESP_LCD_TOUCH_SPD2010_ADDRESS 0x53
typedef void *esp_lcd_touch_handle_t;
typedef struct {
    int x_max,y_max,rst_gpio_num,int_gpio_num;
    struct { int reset,interrupt; } levels;
    struct { int swap_xy,mirror_x,mirror_y; } flags;
} esp_lcd_touch_config_t;
esp_err_t i2c_master_receive(i2c_master_dev_handle_t dev,uint8_t *buffer,size_t size,int timeout);
esp_err_t esp_lcd_touch_new_i2c_spd2010(i2c_master_dev_handle_t device,const esp_lcd_touch_config_t *config,esp_lcd_touch_handle_t *out);
esp_err_t esp_lcd_touch_del(esp_lcd_touch_handle_t handle);
esp_err_t esp_lcd_touch_read_data(esp_lcd_touch_handle_t handle);
