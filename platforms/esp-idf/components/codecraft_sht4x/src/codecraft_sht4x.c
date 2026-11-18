/*
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 * Modified 2026 by CodeCraft AI Hardware contributors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * Derived from the imported hardware reference esp32/main/reterminal_sht4x.c (Apache 2.0):
 * protocol, CRC and decoding kept; the polling task and the cJSON command
 * plumbing are dropped in favour of a plain single-shot API.
 */
#include "codecraft_sht4x.h"

#include <math.h>
#include <stdint.h>
#include <stdlib.h>

#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "freertos/task.h"

/* High-precision single-shot: send the measure command, wait ~10 ms,
 * read back 6 bytes (temperature MSB/LSB/CRC, humidity MSB/LSB/CRC). */
#define SHT4X_CMD_MEASURE_HPM 0xFD
#define SHT4X_MEASURE_MS      10

struct codecraft_sht4x {
    i2c_master_dev_handle_t dev;
    SemaphoreHandle_t lock;
    int timeout_ms;
};

/* CRC-8 of each 2-byte word: polynomial 0x31, initialized to 0xFF. */
static uint8_t sht4x_crc(const uint8_t *data, size_t len)
{
    uint8_t crc = 0xFF;
    for (size_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (int bit = 0; bit < 8; bit++) {
            crc = (crc & 0x80) ? (uint8_t)((crc << 1) ^ 0x31) : (uint8_t)(crc << 1);
        }
    }
    return crc;
}

esp_err_t codecraft_sht4x_create(i2c_master_bus_handle_t bus,
                                const i2c_device_config_t *config,
                                int timeout_ms, codecraft_sht4x_handle_t *out)
{
    if (!out || *out || !bus || !config || timeout_ms <= 0) return ESP_ERR_INVALID_ARG;
    codecraft_sht4x_handle_t sensor = calloc(1, sizeof(*sensor));
    if (!sensor) return ESP_ERR_NO_MEM;
    sensor->lock = xSemaphoreCreateMutex();
    if (!sensor->lock) {
        free(sensor);
        return ESP_ERR_NO_MEM;
    }
    sensor->timeout_ms = timeout_ms;
    esp_err_t err = i2c_master_probe(bus, config->device_address, timeout_ms);
    if (err != ESP_OK) {
        err = ESP_ERR_NOT_FOUND;
    } else {
        err = i2c_master_bus_add_device(bus, config, &sensor->dev);
    }
    if (err != ESP_OK) {
        vSemaphoreDelete(sensor->lock);
        free(sensor);
        return err;
    }
    *out = sensor;
    return ESP_OK;
}

esp_err_t codecraft_sht4x_delete(codecraft_sht4x_handle_t *sensor)
{
    if (!sensor || !*sensor) return ESP_ERR_INVALID_ARG;
    esp_err_t err = i2c_master_bus_rm_device((*sensor)->dev);
    if (err != ESP_OK) return err;
    vSemaphoreDelete((*sensor)->lock);
    free(*sensor);
    *sensor = NULL;
    return ESP_OK;
}

static esp_err_t read_locked(codecraft_sht4x_handle_t sensor, float *temp_c, float *rh_pct)
{
    uint8_t cmd = SHT4X_CMD_MEASURE_HPM;
    uint8_t raw[6];
    esp_err_t err = i2c_master_transmit(sensor->dev, &cmd, 1, sensor->timeout_ms);
    if (err != ESP_OK) return err;
    vTaskDelay(pdMS_TO_TICKS(SHT4X_MEASURE_MS) + 1);
    err = i2c_master_receive(sensor->dev, raw, sizeof(raw), sensor->timeout_ms);
    if (err != ESP_OK) return err;
    if (sht4x_crc(raw, 2) != raw[2] || sht4x_crc(raw + 3, 2) != raw[5]) {
        return ESP_ERR_INVALID_CRC;
    }
    uint16_t raw_t = (uint16_t)((raw[0] << 8) | raw[1]);
    uint16_t raw_rh = (uint16_t)((raw[3] << 8) | raw[4]);
    float t = -45.0f + 175.0f * (float)raw_t / 65535.0f;
    float rh = -6.0f + 125.0f * (float)raw_rh / 65535.0f;
    if (rh < 0.0f) rh = 0.0f;
    if (rh > 100.0f) rh = 100.0f;
    if (!isfinite(t) || !isfinite(rh)) return ESP_ERR_INVALID_RESPONSE;
    *temp_c = t;
    *rh_pct = rh;
    return ESP_OK;
}

esp_err_t codecraft_sht4x_read(codecraft_sht4x_handle_t sensor, float *temp_c, float *rh_pct)
{
    if (!temp_c || !rh_pct) return ESP_ERR_INVALID_ARG;
    if (!sensor) return ESP_ERR_INVALID_STATE;
    TickType_t wait = pdMS_TO_TICKS(sensor->timeout_ms);
    if (xSemaphoreTake(sensor->lock, wait ? wait : 1) != pdTRUE) return ESP_ERR_TIMEOUT;
    esp_err_t err = read_locked(sensor, temp_c, rh_pct);
    xSemaphoreGive(sensor->lock);
    return err;
}
