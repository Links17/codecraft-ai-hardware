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
#include "bsp_sht4x.h"
#include "bsp_i2c0_internal.h"
#include "bsp_pins.h"
#include "codecraft_sht4x.h"

static codecraft_sht4x_handle_t s_device;

esp_err_t bsp_sht4x_init(void)
{
    if (s_device) return ESP_OK;
    i2c_master_bus_handle_t bus;
    esp_err_t err = bsp_i2c0_bus_get(&bus);
    if (err != ESP_OK) return err;
    /* Board wiring/address/speed remain owned by the sourced pins header. */
    const i2c_device_config_t config = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = BSP_I2C_ADDR_SHT4X,
        .scl_speed_hz = BSP_I2C0_FREQ_HZ,
    };
    return codecraft_sht4x_create(bus, &config, 100, &s_device);
}

esp_err_t bsp_sht4x_read(float *temp_c, float *rh_pct)
{
    return codecraft_sht4x_read(s_device, temp_c, rh_pct);
}
