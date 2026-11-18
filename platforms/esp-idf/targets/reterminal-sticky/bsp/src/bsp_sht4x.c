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
 * plumbing are dropped in favour of a plain single-shot API. The Sticky
 * wires the SHT4x to I2C1 (SDA=1, SCL=0) instead of the E100x's I2C0.
 */
#include "bsp_sht4x.h"
#include "bsp_pins.h"
#include "codecraft_sht4x.h"

static i2c_master_bus_handle_t s_bus;
static codecraft_sht4x_handle_t s_device;

esp_err_t bsp_sht4x_init(void)
{
    if (s_device) return ESP_OK;
    if (!s_bus) {
        /* Sticky wiring remains board-owned; the source is cited in bsp_pins.h. */
        const i2c_master_bus_config_t bus_cfg = {
            .i2c_port = I2C_NUM_1,
            .sda_io_num = BSP_PIN_I2C1_SDA,
            .scl_io_num = BSP_PIN_I2C1_SCL,
            .clk_source = I2C_CLK_SRC_DEFAULT,
            .glitch_ignore_cnt = 7,
            .flags.enable_internal_pullup = true,
        };
        esp_err_t err = i2c_new_master_bus(&bus_cfg, &s_bus);
        if (err != ESP_OK) return err;
    }
    const i2c_device_config_t config = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = BSP_I2C_ADDR_SHT4X,
        .scl_speed_hz = BSP_I2C1_FREQ_HZ,
    };
    return codecraft_sht4x_create(s_bus, &config, 100, &s_device);
}

esp_err_t bsp_sht4x_read(float *temp_c, float *rh_pct)
{
    return codecraft_sht4x_read(s_device, temp_c, rh_pct);
}
