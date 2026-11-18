/* SPDX-License-Identifier: Apache-2.0; host-only IDF protocol boundary. */
#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
typedef int esp_err_t;
typedef void *i2c_master_dev_handle_t;
#define ESP_OK 0
#define ESP_FAIL -1
#define ESP_ERR_INVALID_ARG 1
#define ESP_ERR_NOT_SUPPORTED 2
#define ESP_ERR_NO_MEM 3
#define ESP_ERR_INVALID_SIZE 4
#define ESP_ERR_INVALID_RESPONSE 5
#define ESP_ERR_TIMEOUT 6
#define GPIO_NUM_NC -1
#define CONFIG_ESP_LCD_TOUCH_MAX_POINTS 5
#define portMUX_FREE_VAL 0
#define portENTER_CRITICAL(p) ((void)(p))
#define portEXIT_CRITICAL(p) ((void)(p))
#define ESP_RETURN_ON_FALSE(c,e,tag,...) do {if(!(c)) return (e);} while(0)
#define ESP_RETURN_ON_ERROR(c,tag,...) do {int error=(c);if(error) return error;} while(0)
#define ESP_LOGD(tag,...) do {(void)(tag);if(0) printf(__VA_ARGS__);} while(0)
#define ESP_LOGW ESP_LOGD
#define ESP_LOGI ESP_LOGD
#define ESP_LOGE ESP_LOGD
typedef struct esp_lcd_touch esp_lcd_touch_t;
typedef esp_lcd_touch_t *esp_lcd_touch_handle_t;
typedef struct {
 int x_max,y_max,rst_gpio_num,int_gpio_num;
 void (*interrupt_callback)(esp_lcd_touch_handle_t);
 struct {int reset,interrupt;} levels;
 struct {int swap_xy,mirror_x,mirror_y;} flags;
} esp_lcd_touch_config_t;
struct esp_lcd_touch {
 void *io;
 esp_lcd_touch_config_t config;
 esp_err_t (*read_data)(esp_lcd_touch_handle_t);
 bool (*get_xy)(esp_lcd_touch_handle_t,uint16_t *,uint16_t *,uint16_t *,uint8_t *,uint8_t);
 esp_err_t (*del)(esp_lcd_touch_handle_t);
 struct { struct {int owner;} lock; uint8_t points;
  struct {uint16_t x,y,strength;} coords[CONFIG_ESP_LCD_TOUCH_MAX_POINTS]; } data;
};
esp_err_t i2c_master_transmit(i2c_master_dev_handle_t,const uint8_t *,size_t,int);
esp_err_t i2c_master_receive(i2c_master_dev_handle_t,uint8_t *,size_t,int);
void esp_rom_delay_us(uint32_t);
void *test_calloc(size_t,size_t);
void test_free(void *);
