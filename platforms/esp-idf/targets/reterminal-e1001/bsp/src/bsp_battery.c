/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 */
#include "bsp_battery.h"
#include "bsp_pins.h"

#include "driver/gpio.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define VBAT_DIVIDER_NUM 2  /* VBAT = 2 x ADC voltage (10k over 10k) */
#define VBAT_SETTLE_MS   10 /* Zephyr power-on-sample-delay-us = 10000 */

static adc_oneshot_unit_handle_t s_adc;
static adc_cali_handle_t s_cali;
static bool s_ready;
static bool s_divider_fault;

esp_err_t bsp_battery_init(void)
{
    if (s_ready) return ESP_OK;
    if (s_adc || s_cali) return ESP_ERR_INVALID_STATE;
    const gpio_config_t en = {
        .pin_bit_mask = 1ULL << BSP_PIN_VBAT_EN,
        .mode = GPIO_MODE_OUTPUT,
    };
    esp_err_t err = gpio_config(&en);
    if (err != ESP_OK) return err;
    err = gpio_set_level(BSP_PIN_VBAT_EN, 0);
    if (err != ESP_OK) return err;

    adc_oneshot_unit_init_cfg_t unit = {
        .unit_id = ADC_UNIT_1,
        .ulp_mode = ADC_ULP_MODE_DISABLE,
    };
    err = adc_oneshot_new_unit(&unit, &s_adc);
    if (err != ESP_OK) return err;
    adc_oneshot_chan_cfg_t chan = {
        .bitwidth = ADC_BITWIDTH_12,
        .atten = ADC_ATTEN_DB_12,
    };
    err = adc_oneshot_config_channel(s_adc, ADC_CHANNEL_0, &chan);
    if (err != ESP_OK) goto fail;
    adc_cali_curve_fitting_config_t cali = {
        .unit_id = ADC_UNIT_1,
        .chan = ADC_CHANNEL_0,
        .atten = ADC_ATTEN_DB_12,
        .bitwidth = ADC_BITWIDTH_12,
    };
    err = adc_cali_create_scheme_curve_fitting(&cali, &s_cali);
    /* Millivolts require the IDF calibration result; do not estimate a
     * transfer function when calibration eFuse data is unavailable. */
    if (err != ESP_OK) goto fail;
    s_ready = true;
    return ESP_OK;

fail:
    if (adc_oneshot_del_unit(s_adc) == ESP_OK) s_adc = NULL;
    else ESP_LOGE("bsp_battery", "ADC rollback incomplete; reset required");
    return err;
}

esp_err_t bsp_battery_read_mv(int *mv)
{
    if (!mv) return ESP_ERR_INVALID_ARG;
    if (!s_ready) return ESP_ERR_INVALID_STATE;
    if (s_divider_fault) {
        esp_err_t recovery = gpio_set_level(BSP_PIN_VBAT_EN, 0);
        if (recovery != ESP_OK) return recovery;
        s_divider_fault = false;
    }
    esp_err_t err = gpio_set_level(BSP_PIN_VBAT_EN, 1);
    int raw = 0;
    if (err == ESP_OK) {
        /* Do not round the sourced minimum settling interval down to zero. */
        vTaskDelay(pdMS_TO_TICKS(VBAT_SETTLE_MS) + 1);
        err = adc_oneshot_read(s_adc, ADC_CHANNEL_0, &raw);
    }
    /* A failed enable write may still have taken effect; always attempt off. */
    esp_err_t off = gpio_set_level(BSP_PIN_VBAT_EN, 0);
    s_divider_fault = off != ESP_OK;
    if (s_divider_fault) ESP_LOGE("bsp_battery", "divider off failed; retry read to recover");
    if (err != ESP_OK) return err;
    if (off != ESP_OK) return off;
    int sensed;
    err = adc_cali_raw_to_voltage(s_cali, raw, &sensed);
    if (err != ESP_OK) return err;
    *mv = sensed * VBAT_DIVIDER_NUM;
    return ESP_OK;
}
