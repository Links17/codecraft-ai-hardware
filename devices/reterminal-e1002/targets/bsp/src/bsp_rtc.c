/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * PCF8563 driver written for this BSP. Register map (time/date block at
 * 0x02, BCD encoding, VL integrity flag) cross-checked against:
 *  - Zephyr drivers/rtc/rtc_pcf8563.c (Apache-2.0)
 *  - Zephyr board dts boards/seeed/reterminal_e1001 (chip at I2C0 0x51)
 *  - NXP PCF8563 datasheet (public register specification)
 */
#include "bsp_rtc.h"
#include "bsp_i2c0_internal.h"
#include "bsp_pins.h"
#include "codecraft_pcf8563.h"

static codecraft_pcf8563_handle_t s_device;

esp_err_t bsp_rtc_init(void)
{
    if (s_device) return ESP_OK;
    i2c_master_bus_handle_t bus;
    esp_err_t err = bsp_i2c0_bus_get(&bus);
    if (err != ESP_OK) return err;
    /* Board wiring/address/speed remain owned by the sourced pins header. */
    const i2c_device_config_t config = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = BSP_I2C_ADDR_RTC,
        .scl_speed_hz = BSP_I2C0_FREQ_HZ,
    };
    return codecraft_pcf8563_create(bus, &config, 100, &s_device);
}

esp_err_t bsp_rtc_get_time(struct tm *out_time)
{
    return codecraft_pcf8563_get_time(s_device, out_time);
}

esp_err_t bsp_rtc_set_time(const struct tm *time)
{
    return codecraft_pcf8563_set_time(s_device, time);
}
