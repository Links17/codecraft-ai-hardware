/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 */
#include "bsp_buzzer.h"
#include "bsp_pins.h"

#include <stdbool.h>

#include "driver/ledc.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static bool s_ready;

#define BUZZER_TIMER      LEDC_TIMER_0
#define BUZZER_CHANNEL    LEDC_CHANNEL_0
#define BUZZER_RESOLUTION LEDC_TIMER_10_BIT
#define BUZZER_DUTY_ON    (1u << 9) /* 50 % of 10-bit */

esp_err_t bsp_buzzer_init(void)
{
    if (s_ready) return ESP_OK;
    ledc_timer_config_t timer_cfg = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .duty_resolution = BUZZER_RESOLUTION,
        .timer_num = BUZZER_TIMER,
        .freq_hz = 2000,
        .clk_cfg = LEDC_AUTO_CLK,
    };
    esp_err_t err = ledc_timer_config(&timer_cfg);
    if (err != ESP_OK) {
        return err;
    }
    ledc_channel_config_t ch_cfg = {
        .gpio_num = BSP_PIN_BUZZER,
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = BUZZER_CHANNEL,
        .timer_sel = BUZZER_TIMER,
        .duty = 0,
        .hpoint = 0,
    };
    err = ledc_channel_config(&ch_cfg);
    if (err == ESP_OK) s_ready = true;
    return err;
}

esp_err_t bsp_buzzer_tone(uint32_t freq_hz)
{
    if (!s_ready) return ESP_ERR_INVALID_STATE;
    if (!freq_hz) return ESP_ERR_INVALID_ARG;
    esp_err_t err = ledc_set_freq(LEDC_LOW_SPEED_MODE, BUZZER_TIMER, freq_hz);
    if (err != ESP_OK) {
        return err;
    }
    err = ledc_set_duty(LEDC_LOW_SPEED_MODE, BUZZER_CHANNEL, BUZZER_DUTY_ON);
    if (err != ESP_OK) {
        return err;
    }
    return ledc_update_duty(LEDC_LOW_SPEED_MODE, BUZZER_CHANNEL);
}

esp_err_t bsp_buzzer_stop(void)
{
    if (!s_ready) return ESP_ERR_INVALID_STATE;
    esp_err_t err = ledc_set_duty(LEDC_LOW_SPEED_MODE, BUZZER_CHANNEL, 0);
    if (err != ESP_OK) {
        return err;
    }
    return ledc_update_duty(LEDC_LOW_SPEED_MODE, BUZZER_CHANNEL);
}

esp_err_t bsp_buzzer_beep(uint32_t freq_hz, uint32_t duration_ms)
{
    esp_err_t err = bsp_buzzer_tone(freq_hz);
    if (err != ESP_OK) {
        return err;
    }
    if (duration_ms) {
        TickType_t wait = pdMS_TO_TICKS(duration_ms);
        vTaskDelay(wait ? wait : 1);
    }
    return bsp_buzzer_stop();
}
