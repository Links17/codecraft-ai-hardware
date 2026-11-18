/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * SenseCAP Indicator touch example: resets and auto-probes the touch
 * controller (FT6336U or GT911), then logs press coordinates. Touch the
 * screen to see output.
 */

#include "bsp_touch.h"

#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "touch_read";

void app_main(void)
{
    esp_lcd_touch_handle_t touch = NULL;
    ESP_ERROR_CHECK(bsp_touch_init(&touch));

    ESP_LOGI(TAG, "touch the screen");
    bool was_pressed = false;
    while (true) {
        esp_lcd_touch_point_data_t point;
        uint8_t count = 0;
        esp_err_t err = esp_lcd_touch_read_data(touch);
        if (err == ESP_OK) err = esp_lcd_touch_get_data(touch, &point, &count, 1);
        if (err != ESP_OK) {
            /* Keep the last observed state; cached coordinates after an I/O
             * error are not a fresh press or release. */
            ESP_LOGW(TAG, "touch sample failed: %s", esp_err_to_name(err));
            vTaskDelay(pdMS_TO_TICKS(20));
            continue;
        }
        bool pressed = count > 0;
        if (pressed) {
            ESP_LOGI(TAG, "press x=%u y=%u strength=%u points=%u",
                     point.x, point.y, point.strength, count);
        } else if (was_pressed) {
            ESP_LOGI(TAG, "released");
        }
        was_pressed = pressed;
        vTaskDelay(pdMS_TO_TICKS(20));
    }
}
