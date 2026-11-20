/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Display facts: vendor BSP sensecap-watcher.c bsp_lcd_pannel_init()
 * (Apache 2.0) — QSPI bus pins and 40 MHz pixel clock, 32-bit commands,
 * 8-bit params, SPI mode 3, quad_mode, no D/C, use_qspi_interface, RGB
 * element order, 16 bpp, no mirroring; bsp_lcd_backlight_init —
 * LEDC low-speed channel 1, 10-bit duty, on-level high.
 * The panel has no reset line (GPIO_NUM_NC in the vendor BSP); it shares
 * the touch controller's reset, so esp_lcd_panel_reset() is a no-op delay.
 */
#include "bsp_display.h"
#include "bsp_io_expander.h"
#include "bsp_pins.h"

#include "driver/ledc.h"
#include "esp_check.h"
#include "esp_lcd_panel_vendor.h"
#include "esp_lcd_spd2010.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "bsp_display";

#define LCD_PIXEL_CLK_HZ (40 * 1000 * 1000)
#define LCD_CMD_BITS 32
#define LCD_PARAM_BITS 8
#define LCD_SPI_MODE 3
#define LCD_TRANS_QUEUE_DEPTH 10

#define BK_LEDC_TIMER LEDC_TIMER_0
#define BK_LEDC_MODE LEDC_LOW_SPEED_MODE
#define BK_LEDC_CH LEDC_CHANNEL_1
#define BK_LEDC_RES LEDC_TIMER_10_BIT

static esp_lcd_panel_handle_t s_panel;
static esp_lcd_panel_io_handle_t s_io;
static bool s_backlight_ready;
static bool s_timer_ready;
static bool s_bus_ready;
static bool s_ready;

static esp_err_t backlight_init(void)
{
    if (s_backlight_ready) {
        return ESP_OK;
    }
    const ledc_timer_config_t timer = {
        .speed_mode = BK_LEDC_MODE,
        .duty_resolution = BK_LEDC_RES,
        .timer_num = BK_LEDC_TIMER,
        .freq_hz = 5000,
        .clk_cfg = LEDC_AUTO_CLK,
    };
    ESP_RETURN_ON_ERROR(ledc_timer_config(&timer), TAG, "backlight timer");
    s_timer_ready = true;
    const ledc_channel_config_t channel = {
        .speed_mode = BK_LEDC_MODE,
        .channel = BK_LEDC_CH,
        .timer_sel = BK_LEDC_TIMER,
        .intr_type = LEDC_INTR_DISABLE,
        .gpio_num = BSP_PIN_LCD_BACKLIGHT,
        .duty = 0,
        .hpoint = 0,
    };
    ESP_RETURN_ON_ERROR(ledc_channel_config(&channel), TAG, "backlight channel");
    s_backlight_ready = true;
    return ESP_OK;
}

static esp_err_t backlight_set_brightness(int percent)
{
    ESP_RETURN_ON_FALSE(s_backlight_ready, ESP_ERR_INVALID_STATE, TAG, "not initialized");
    if (percent < 0) {
        percent = 0;
    }
    if (percent > 100) {
        percent = 100;
    }
    uint32_t duty = (BIT(BK_LEDC_RES) * percent) / 100;
    ESP_RETURN_ON_ERROR(ledc_set_duty(BK_LEDC_MODE, BK_LEDC_CH, duty), TAG, "duty");
    return ledc_update_duty(BK_LEDC_MODE, BK_LEDC_CH);
}

esp_err_t bsp_display_set_brightness(int percent)
{
    ESP_RETURN_ON_FALSE(s_ready, ESP_ERR_INVALID_STATE, TAG, "display not ready");
    return backlight_set_brightness(percent);
}

/* Release only resources acquired by this module, in reverse order. A failed
 * delete retains its handle and dependent resources; no later init may overwrite
 * them. The LCD/touch rail and shared expander belong to the board, not us.
 * LEDC teardown follows ESP-IDF v6.0.2 driver/ledc.h: stop/deconfigure the
 * exclusive channel, then pause the timer before deconfiguring it. */
static esp_err_t display_rollback(void)
{
    s_ready = false;
    if (s_panel) {
        ESP_RETURN_ON_ERROR(esp_lcd_panel_del(s_panel), TAG, "delete panel");
        s_panel = NULL;
    }
    if (s_io) {
        ESP_RETURN_ON_ERROR(esp_lcd_panel_io_del(s_io), TAG, "delete panel IO");
        s_io = NULL;
    }
    if (s_bus_ready) {
        ESP_RETURN_ON_ERROR(spi_bus_free(SPI3_HOST), TAG, "free QSPI bus");
        s_bus_ready = false;
    }
    if (s_backlight_ready) {
        ESP_RETURN_ON_ERROR(ledc_stop(BK_LEDC_MODE, BK_LEDC_CH, 0), TAG, "stop backlight");
        const ledc_channel_config_t channel = {
            .speed_mode = BK_LEDC_MODE,
            .channel = BK_LEDC_CH,
            .deconfigure = true,
        };
        ESP_RETURN_ON_ERROR(ledc_channel_config(&channel), TAG, "release backlight channel");
        s_backlight_ready = false;
    }
    if (s_timer_ready) {
        ESP_RETURN_ON_ERROR(ledc_timer_pause(BK_LEDC_MODE, BK_LEDC_TIMER), TAG, "pause backlight timer");
        const ledc_timer_config_t timer = {
            .speed_mode = BK_LEDC_MODE,
            .timer_num = BK_LEDC_TIMER,
            .deconfigure = true,
        };
        ESP_RETURN_ON_ERROR(ledc_timer_config(&timer), TAG, "release backlight timer");
        s_timer_ready = false;
    }
    return ESP_OK;
}

esp_err_t bsp_display_init(esp_lcd_panel_handle_t *out_panel, esp_lcd_panel_io_handle_t *out_io)
{
    if (out_panel) {
        *out_panel = NULL;
    }
    if (out_io) {
        *out_io = NULL;
    }
    if (s_ready) {
        if (out_panel) {
            *out_panel = s_panel;
        }
        if (out_io) {
            *out_io = s_io;
        }
        return ESP_OK;
    }
    ESP_RETURN_ON_FALSE(!s_panel && !s_io && !s_bus_ready && !s_backlight_ready && !s_timer_ready,
                        ESP_ERR_INVALID_STATE, TAG, "incomplete rollback; reset required");
    esp_err_t ret;

    /* The rail powers the panel and the touch controller together. */
    ESP_RETURN_ON_ERROR(bsp_io_expander_init(), TAG, "expander");
    ESP_RETURN_ON_ERROR(bsp_io_expander_set_direction(BSP_EXP_PIN_PWR_LCD, 1), TAG, "lcd rail dir");
    ESP_RETURN_ON_ERROR(bsp_io_expander_set_level(BSP_EXP_PIN_PWR_LCD, 1), TAG, "lcd rail on");
    vTaskDelay(pdMS_TO_TICKS(50));

    ESP_GOTO_ON_ERROR(backlight_init(), fail, TAG, "backlight");

    const spi_bus_config_t bus = {
        .sclk_io_num = BSP_PIN_LCD_PCLK,
        .data0_io_num = BSP_PIN_LCD_D0,
        .data1_io_num = BSP_PIN_LCD_D1,
        .data2_io_num = BSP_PIN_LCD_D2,
        .data3_io_num = BSP_PIN_LCD_D3,
        .max_transfer_sz = BSP_LCD_H_RES * BSP_LCD_V_RES * 2,
    };
    ESP_GOTO_ON_ERROR(spi_bus_initialize(SPI3_HOST, &bus, SPI_DMA_CH_AUTO), fail, TAG, "qspi bus");
    s_bus_ready = true;

    const esp_lcd_panel_io_spi_config_t io_cfg = {
        .cs_gpio_num = BSP_PIN_LCD_CS,
        .dc_gpio_num = -1,
        .spi_mode = LCD_SPI_MODE,
        .pclk_hz = LCD_PIXEL_CLK_HZ,
        .trans_queue_depth = LCD_TRANS_QUEUE_DEPTH,
        .lcd_cmd_bits = LCD_CMD_BITS,
        .lcd_param_bits = LCD_PARAM_BITS,
        .flags = {
            .quad_mode = true,
        },
    };
    ESP_GOTO_ON_ERROR(esp_lcd_new_panel_io_spi((esp_lcd_spi_bus_handle_t)SPI3_HOST, &io_cfg, &s_io),
                      fail, TAG, "panel io");

    spd2010_vendor_config_t vendor_cfg = {
        .flags = {
            .use_qspi_interface = 1,
        },
    };
    const esp_lcd_panel_dev_config_t panel_cfg = {
        .reset_gpio_num = -1,
        .rgb_ele_order = LCD_RGB_ELEMENT_ORDER_RGB,
        .bits_per_pixel = 16,
        .vendor_config = &vendor_cfg,
    };
    ESP_GOTO_ON_ERROR(esp_lcd_new_panel_spd2010(s_io, &panel_cfg, &s_panel), fail, TAG, "panel");
    ESP_GOTO_ON_ERROR(esp_lcd_panel_reset(s_panel), fail, TAG, "reset");
    ESP_GOTO_ON_ERROR(esp_lcd_panel_init(s_panel), fail, TAG, "init");
    ESP_GOTO_ON_ERROR(esp_lcd_panel_mirror(s_panel, false, false), fail, TAG, "mirror");
    ESP_GOTO_ON_ERROR(esp_lcd_panel_disp_on_off(s_panel, true), fail, TAG, "disp on");

    ESP_GOTO_ON_ERROR(backlight_set_brightness(100), fail, TAG, "brightness");

    s_ready = true;
    if (out_panel) {
        *out_panel = s_panel;
    }
    if (out_io) {
        *out_io = s_io;
    }
    ESP_LOGI(TAG, "SPD2010 %dx%d QSPI up", BSP_LCD_H_RES, BSP_LCD_V_RES);
    return ESP_OK;

fail:
    if (display_rollback() != ESP_OK) {
        ESP_LOGE(TAG, "initialization failed and rollback is incomplete; reset required");
    }
    return ret;
}
