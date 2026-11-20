/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Knob facts: vendor BSP header (Apache 2.0) — quadrature on GPIO41/42, push
 * on expander pin 3, low while pressed (reference board_sensecap_watcher.c calls
 * the same bit EXP_WHEEL, "low while pressed"). The decoder follows the
 * ESP-IDF rotary-encoder PCNT pattern: each channel watches one phase's
 * edges against the other phase's level.
 */
#include "bsp_knob.h"
#include "bsp_io_expander.h"
#include "bsp_pins.h"

#include "driver/pulse_cnt.h"
#include "esp_check.h"
#include "esp_log.h"

static const char *TAG = "bsp_knob";

static pcnt_unit_handle_t s_unit;
static pcnt_channel_handle_t s_chan_a;
static pcnt_channel_handle_t s_chan_b;
static bool s_enabled;
static bool s_ready;

/* ESP-IDF v6.0.2 pulse_cnt.h requires an init-state unit with no live
 * channels before deletion. Stop/disable first, then release channels in
 * reverse acquisition order. Retain any handle whose teardown fails. */
static esp_err_t knob_rollback(void)
{
    if (s_enabled) {
        ESP_RETURN_ON_ERROR(pcnt_unit_stop(s_unit), TAG, "stop unit");
        ESP_RETURN_ON_ERROR(pcnt_unit_disable(s_unit), TAG, "disable unit");
        s_enabled = false;
    }
    if (s_chan_b) {
        ESP_RETURN_ON_ERROR(pcnt_del_channel(s_chan_b), TAG, "delete channel B");
        s_chan_b = NULL;
    }
    if (s_chan_a) {
        ESP_RETURN_ON_ERROR(pcnt_del_channel(s_chan_a), TAG, "delete channel A");
        s_chan_a = NULL;
    }
    if (s_unit) {
        ESP_RETURN_ON_ERROR(pcnt_del_unit(s_unit), TAG, "delete unit");
        s_unit = NULL;
    }
    return ESP_OK;
}

esp_err_t bsp_knob_init(void)
{
    if (s_ready) {
        return ESP_OK;
    }
    ESP_RETURN_ON_FALSE(!s_unit && !s_chan_a && !s_chan_b, ESP_ERR_INVALID_STATE, TAG,
                        "incomplete rollback; reset required");
    esp_err_t ret;
    ESP_RETURN_ON_ERROR(bsp_io_expander_init(), TAG, "expander");
    ESP_RETURN_ON_ERROR(bsp_io_expander_set_direction(BSP_EXP_PIN_KNOB_BTN, 0), TAG, "button dir");

    const pcnt_unit_config_t unit_cfg = {
        .low_limit = -4096,
        .high_limit = 4096,
    };
    ESP_RETURN_ON_ERROR(pcnt_new_unit(&unit_cfg, &s_unit), TAG, "pcnt unit");

    const pcnt_glitch_filter_config_t filter_cfg = {
        .max_glitch_ns = 1000,
    };
    ESP_GOTO_ON_ERROR(pcnt_unit_set_glitch_filter(s_unit, &filter_cfg), fail, TAG, "glitch filter");

    pcnt_chan_config_t chan_cfg = {
        .edge_gpio_num = BSP_PIN_KNOB_A,
        .level_gpio_num = BSP_PIN_KNOB_B,
    };
    ESP_GOTO_ON_ERROR(pcnt_new_channel(s_unit, &chan_cfg, &s_chan_a), fail, TAG, "channel A");
    chan_cfg.edge_gpio_num = BSP_PIN_KNOB_B;
    chan_cfg.level_gpio_num = BSP_PIN_KNOB_A;
    ESP_GOTO_ON_ERROR(pcnt_new_channel(s_unit, &chan_cfg, &s_chan_b), fail, TAG, "channel B");

    ESP_GOTO_ON_ERROR(pcnt_channel_set_edge_action(s_chan_a, PCNT_CHANNEL_EDGE_ACTION_DECREASE,
                                                     PCNT_CHANNEL_EDGE_ACTION_INCREASE),
                      fail, TAG, "A edges");
    ESP_GOTO_ON_ERROR(pcnt_channel_set_level_action(s_chan_a, PCNT_CHANNEL_LEVEL_ACTION_KEEP,
                                                      PCNT_CHANNEL_LEVEL_ACTION_INVERSE),
                      fail, TAG, "A levels");
    ESP_GOTO_ON_ERROR(pcnt_channel_set_edge_action(s_chan_b, PCNT_CHANNEL_EDGE_ACTION_INCREASE,
                                                     PCNT_CHANNEL_EDGE_ACTION_DECREASE),
                      fail, TAG, "B edges");
    ESP_GOTO_ON_ERROR(pcnt_channel_set_level_action(s_chan_b, PCNT_CHANNEL_LEVEL_ACTION_KEEP,
                                                      PCNT_CHANNEL_LEVEL_ACTION_INVERSE),
                      fail, TAG, "B levels");

    ESP_GOTO_ON_ERROR(pcnt_unit_enable(s_unit), fail, TAG, "enable");
    s_enabled = true;
    ESP_GOTO_ON_ERROR(pcnt_unit_clear_count(s_unit), fail, TAG, "clear");
    ESP_GOTO_ON_ERROR(pcnt_unit_start(s_unit), fail, TAG, "start");
    s_ready = true;
    return ESP_OK;

fail:
    if (knob_rollback() != ESP_OK) {
        ESP_LOGE(TAG, "knob rollback incomplete; reset required");
    }
    return ret;
}

esp_err_t bsp_knob_get_delta(int *out_delta)
{
    ESP_RETURN_ON_FALSE(s_ready, ESP_ERR_INVALID_STATE, TAG, "not initialized");
    ESP_RETURN_ON_FALSE(out_delta, ESP_ERR_INVALID_ARG, TAG, "out_delta");
    int count;
    ESP_RETURN_ON_ERROR(pcnt_unit_get_count(s_unit, &count), TAG, "count");
    ESP_RETURN_ON_ERROR(pcnt_unit_clear_count(s_unit), TAG, "clear");
    *out_delta = count;
    return ESP_OK;
}

bool bsp_knob_button_pressed(void)
{
    if (!s_ready) {
        return false;
    }
    int level = 1;
    return bsp_io_expander_get_level(BSP_EXP_PIN_KNOB_BTN, &level) == ESP_OK && !level;
}
