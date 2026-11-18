/* SPDX-License-Identifier: Apache-2.0; narrow touch host API double. */
#pragma once
#include "idf_bsp_stub.h"
#define GPIO_NUM_NC (-1)
#define ESP_LCD_TOUCH_IO_I2C_SPD2010_ADDRESS 0x53
#define __containerof(ptr, type, field) ((type *)((char *)(ptr)-offsetof(type,field)))
typedef struct esp_lcd_panel_io_t esp_lcd_panel_io_t;
typedef struct { int unused; } esp_lcd_panel_io_callbacks_t;
struct esp_lcd_panel_io_t {
    esp_err_t (*rx_param)(esp_lcd_panel_io_t *,int,void *,size_t);
    esp_err_t (*tx_param)(esp_lcd_panel_io_t *,int,const void *,size_t);
    esp_err_t (*tx_color)(esp_lcd_panel_io_t *,int,const void *,size_t);
    esp_err_t (*del)(esp_lcd_panel_io_t *);
    esp_err_t (*register_event_callbacks)(esp_lcd_panel_io_t *,const esp_lcd_panel_io_callbacks_t *,void *);
};
typedef void *esp_lcd_touch_handle_t;
typedef struct {
    int x_max,y_max,rst_gpio_num,int_gpio_num;
    struct { int reset,interrupt; } levels;
    struct { int swap_xy,mirror_x,mirror_y; } flags;
} esp_lcd_touch_config_t;
esp_err_t i2c_master_receive(i2c_master_dev_handle_t dev,uint8_t *buffer,size_t size,int timeout);
esp_err_t esp_lcd_touch_new_i2c_spd2010(esp_lcd_panel_io_handle_t io,const esp_lcd_touch_config_t *config,esp_lcd_touch_handle_t *out);
esp_err_t esp_lcd_touch_del(esp_lcd_touch_handle_t handle);
esp_err_t esp_lcd_touch_read_data(esp_lcd_touch_handle_t handle);
