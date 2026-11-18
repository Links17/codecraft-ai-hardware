/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 */
#include "bsp_led.h"
#include "bsp_pins.h"

#include "driver/gpio.h"
#include "esp_log.h"

static bool s_ready;

esp_err_t bsp_led_init(void)
{
    if (s_ready) return ESP_OK;
    const gpio_config_t cfg = {
        .pin_bit_mask = 1ULL << BSP_PIN_LED,
        .mode = GPIO_MODE_OUTPUT,
    };
    esp_err_t err = gpio_config(&cfg);
    if (err == ESP_OK) err = gpio_set_level(BSP_PIN_LED, 1); /* active-low off */
    if (err == ESP_OK) s_ready = true;
    return err;
}

void bsp_led_set(bool on)
{
    if (!s_ready) return;
    esp_err_t err = gpio_set_level(BSP_PIN_LED, on ? 0 : 1); /* active low */
    if (err != ESP_OK) ESP_LOGE("bsp_led", "LED write failed; physical state uncertain");
}
