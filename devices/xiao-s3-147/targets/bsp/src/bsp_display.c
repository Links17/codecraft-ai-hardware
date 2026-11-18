/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * The vendor register sequence below is Seeed's verified
 * ST7789-compatible JD9853A sequence, from Seeed_GFX2 (MIT,
 * github.com/Seeed-Studio/Seeed_GFX2) via the imported hardware reference
 * reference:boards/board_seeed_xiao_s3_147.c (Apache 2.0).
 */
#include "bsp_display.h"
#include "bsp_pins.h"

#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "esp_check.h"
#include "esp_log.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_panel_vendor.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static esp_lcd_panel_io_handle_t s_io;
static esp_lcd_panel_handle_t s_panel;
static bool s_ready;

esp_err_t bsp_display_backlight(bool on)
{
    if (!s_ready) return ESP_ERR_INVALID_STATE;
    return gpio_set_level(BSP_PIN_LCD_BL, on);
}

esp_err_t bsp_display_wait_idle(void)
{
    if (!s_ready) return ESP_ERR_INVALID_STATE;
    /* ESP-IDF v6.0.2 esp_lcd/spi/esp_lcd_panel_io_spi.c:
     * tx_param drains queued color transfers; cmd=-1 with no parameters
     * sends nothing. The native wait uses portMAX_DELAY. */
    return esp_lcd_panel_io_tx_param(s_io, -1, NULL, 0);
}

esp_err_t bsp_display_init(esp_lcd_panel_handle_t *out_panel)
{
    if (!out_panel) return ESP_ERR_INVALID_ARG;
    *out_panel = NULL;
    if (s_ready) {
        *out_panel = s_panel;
        return ESP_OK;
    }
    if (s_io || s_panel) return ESP_ERR_INVALID_STATE;

    const gpio_config_t out_cfg = {
        .pin_bit_mask = (1ULL << BSP_PIN_LCD_BL) | (1ULL << BSP_PIN_SD_CS),
        .mode = GPIO_MODE_OUTPUT,
    };
    ESP_RETURN_ON_ERROR(gpio_config(&out_cfg), "bsp_display", "gpio");
    ESP_RETURN_ON_ERROR(gpio_set_level(BSP_PIN_SD_CS, 1), "bsp_display", "SD CS high");

    /* Shared LCD + touch reset: pulse once before either starts (reference
     * board file, init()). */
    const gpio_config_t rst_cfg = {
        .pin_bit_mask = 1ULL << BSP_PIN_LCD_RST,
        .mode = GPIO_MODE_OUTPUT,
    };
    ESP_RETURN_ON_ERROR(gpio_config(&rst_cfg), "bsp_display", "reset gpio");
    ESP_RETURN_ON_ERROR(gpio_set_level(BSP_PIN_LCD_RST, 0), "bsp_display", "reset low");
    vTaskDelay(pdMS_TO_TICKS(20));
    ESP_RETURN_ON_ERROR(gpio_set_level(BSP_PIN_LCD_RST, 1), "bsp_display", "reset high");
    vTaskDelay(pdMS_TO_TICKS(120));

    const spi_bus_config_t bus = {
        .sclk_io_num = BSP_PIN_LCD_SCLK,
        .mosi_io_num = BSP_PIN_LCD_MOSI,
        .miso_io_num = GPIO_NUM_NC,
        .quadwp_io_num = GPIO_NUM_NC,
        .quadhd_io_num = GPIO_NUM_NC,
    };
    esp_err_t ret = spi_bus_initialize(SPI2_HOST, &bus, SPI_DMA_CH_AUTO);
    if (ret != ESP_OK && ret != ESP_ERR_INVALID_STATE) {
        ESP_RETURN_ON_ERROR(ret, "bsp_display", "SPI bus");
    }

    const esp_lcd_panel_io_spi_config_t io_cfg = {
        .cs_gpio_num = BSP_PIN_LCD_CS,
        .dc_gpio_num = BSP_PIN_LCD_DC,
        .spi_mode = 0,
        .pclk_hz = 40 * 1000 * 1000,
        .trans_queue_depth = 10,
        .lcd_cmd_bits = 8,
        .lcd_param_bits = 8,
    };
    ESP_GOTO_ON_ERROR(esp_lcd_new_panel_io_spi(SPI2_HOST, &io_cfg, &s_io),
                      fail, "bsp_display", "panel io");

    const esp_lcd_panel_dev_config_t panel_cfg = {
        .reset_gpio_num = GPIO_NUM_NC,  /* pulsed above */
        .rgb_ele_order = LCD_RGB_ELEMENT_ORDER_RGB,
        .bits_per_pixel = 16,
    };
    ESP_GOTO_ON_ERROR(esp_lcd_new_panel_st7789(s_io, &panel_cfg, &s_panel),
                      fail, "bsp_display", "st7789");
    ESP_GOTO_ON_ERROR(esp_lcd_panel_init(s_panel), fail, "bsp_display", "panel init");
    ESP_GOTO_ON_ERROR(esp_lcd_panel_io_tx_param(s_io, 0x11, NULL, 0),
                      fail, "bsp_display", "sleep out");
    vTaskDelay(pdMS_TO_TICKS(120));

    /* Seeed's verified ST7789-compatible JD9853A sequence (Seeed_GFX2, MIT). */
    static const struct {
        uint8_t cmd, length, data[14];
    } commands[] = {
        {0x13, 0, {0}},
        {0xb6, 2, {0x0a, 0x82}},
        {0xb0, 2, {0x00, 0xe0}},
        {0x3a, 1, {0x55}},
        {0xb2, 5, {0x0c, 0x0c, 0x00, 0x33, 0x33}},
        {0xb7, 1, {0x35}},
        {0xbb, 1, {0x28}},
        {0xc0, 1, {0x0c}},
        {0xc2, 2, {0x01, 0xff}},
        {0xc3, 1, {0x10}},
        {0xc4, 1, {0x20}},
        {0xc6, 1, {0x0f}},
        {0xd0, 2, {0xa4, 0xa1}},
        {0xe0, 14, {0xd0, 0x00, 0x02, 0x07, 0x0a, 0x28, 0x32, 0x44, 0x42, 0x06, 0x0e, 0x12, 0x14, 0x17}},
        {0xe1, 14, {0xd0, 0x00, 0x02, 0x07, 0x0a, 0x28, 0x31, 0x54, 0x47, 0x0e, 0x1c, 0x17, 0x1b, 0x1e}},
    };
    for (size_t i = 0; i < sizeof(commands) / sizeof(commands[0]); i++) {
        ESP_GOTO_ON_ERROR(esp_lcd_panel_io_tx_param(s_io, commands[i].cmd,
                            commands[i].data, commands[i].length),
                            fail, "bsp_display", "vendor register");
    }

    /* Portrait: MADCTL 0x48 (MX+BGR) = mirror X with RGB element order,
     * X offset 34, inversion off (reference devices/seeed-xiao-s3-147.md). */
    ESP_GOTO_ON_ERROR(esp_lcd_panel_mirror(s_panel, true, false), fail, "bsp_display", "mirror");
    ESP_GOTO_ON_ERROR(esp_lcd_panel_set_gap(s_panel, 34, 0), fail, "bsp_display", "gap");
    ESP_GOTO_ON_ERROR(esp_lcd_panel_invert_color(s_panel, false), fail, "bsp_display", "invert");
    ESP_GOTO_ON_ERROR(esp_lcd_panel_disp_on_off(s_panel, true), fail, "bsp_display", "display on");
    vTaskDelay(pdMS_TO_TICKS(120));
    ESP_GOTO_ON_ERROR(gpio_set_level(BSP_PIN_LCD_BL, 1), fail, "bsp_display", "backlight");

    s_ready = true;
    *out_panel = s_panel;
    return ESP_OK;

fail:
    /* The board SPI bus and shared reset remain board-owned. Only release
     * this display's allocations. Uncertain cleanup requires reset. */
    if (s_panel) {
        if (esp_lcd_panel_del(s_panel) != ESP_OK) {
            ESP_LOGE("bsp_display", "panel rollback incomplete; reset required");
            return ret;
        }
        s_panel = NULL;
    }
    if (s_io) {
        if (esp_lcd_panel_io_del(s_io) != ESP_OK) {
            ESP_LOGE("bsp_display", "panel IO rollback incomplete; reset required");
            return ret;
        }
        s_io = NULL;
    }
    return ret;
}
