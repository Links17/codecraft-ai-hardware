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
#include "codecraft_pcf8563.h"

#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>

/* Register addresses. */
#define PCF8563_REG_TIME_DATE 0x02 /* sec, min, hour, day, wday, month, year */

/* Field masks (unused bits read back as garbage — always mask). */
#define PCF8563_VL_FLAG      0x80 /* seconds reg bit 7: clock integrity low */
#define PCF8563_SECONDS_MASK 0x7F
#define PCF8563_MINUTES_MASK 0x7F
#define PCF8563_HOURS_MASK   0x3F /* 24-hour mode */
#define PCF8563_DAYS_MASK    0x3F
#define PCF8563_WEEKDAYS_MASK 0x07
#define PCF8563_MONTHS_MASK  0x1F

struct codecraft_pcf8563 {
    i2c_master_dev_handle_t dev;
    int timeout_ms;
};

static uint8_t bin2bcd(uint8_t v)
{
    return (uint8_t)(((v / 10) << 4) | (v % 10));
}

static uint8_t bcd2bin(uint8_t v)
{
    return (uint8_t)((v >> 4) * 10 + (v & 0x0F));
}

esp_err_t codecraft_pcf8563_create(i2c_master_bus_handle_t bus,
                                  const i2c_device_config_t *config,
                                  int timeout_ms, codecraft_pcf8563_handle_t *out)
{
    if (!out || *out || !bus || !config || timeout_ms <= 0) return ESP_ERR_INVALID_ARG;
    codecraft_pcf8563_handle_t rtc = calloc(1, sizeof(*rtc));
    if (!rtc) return ESP_ERR_NO_MEM;
    rtc->timeout_ms = timeout_ms;
    esp_err_t err = i2c_master_probe(bus, config->device_address, timeout_ms);
    if (err != ESP_OK) {
        err = ESP_ERR_NOT_FOUND;
    } else {
        err = i2c_master_bus_add_device(bus, config, &rtc->dev);
    }
    if (err != ESP_OK) {
        free(rtc);
        return err;
    }
    *out = rtc;
    return ESP_OK;
}

esp_err_t codecraft_pcf8563_delete(codecraft_pcf8563_handle_t *rtc)
{
    if (!rtc || !*rtc) return ESP_ERR_INVALID_ARG;
    esp_err_t err = i2c_master_bus_rm_device((*rtc)->dev);
    if (err != ESP_OK) return err;
    free(*rtc);
    *rtc = NULL;
    return ESP_OK;
}

static bool valid_time(const struct tm *time)
{
    return time->tm_year >= 100 && time->tm_year <= 199 &&
           time->tm_mon >= 0 && time->tm_mon <= 11 &&
           time->tm_mday >= 1 && time->tm_mday <= 31 &&
           time->tm_wday >= 0 && time->tm_wday <= 6 &&
           time->tm_hour >= 0 && time->tm_hour <= 23 &&
           time->tm_min >= 0 && time->tm_min <= 59 &&
           time->tm_sec >= 0 && time->tm_sec <= 59;
}

esp_err_t codecraft_pcf8563_get_time(codecraft_pcf8563_handle_t rtc, struct tm *out_time)
{
    if (!out_time) return ESP_ERR_INVALID_ARG;
    if (!rtc) return ESP_ERR_INVALID_STATE;
    uint8_t reg = PCF8563_REG_TIME_DATE;
    uint8_t raw[7];
    esp_err_t err = i2c_master_transmit_receive(rtc->dev, &reg, 1, raw, sizeof(raw), rtc->timeout_ms);
    if (err != ESP_OK) {
        return err;
    }
    if (raw[0] & PCF8563_VL_FLAG) {
        return ESP_ERR_INVALID_STATE; /* oscillator stopped; time is garbage */
    }
    const uint8_t masks[] = { PCF8563_SECONDS_MASK, PCF8563_MINUTES_MASK,
        PCF8563_HOURS_MASK, PCF8563_DAYS_MASK, PCF8563_WEEKDAYS_MASK,
        PCF8563_MONTHS_MASK, 0xFF };
    for (size_t i = 0; i < sizeof(raw); i++) {
        raw[i] &= masks[i];
        if (i != 4 && ((raw[i] & 0x0F) > 9 || (raw[i] >> 4) > 9)) {
            return ESP_ERR_INVALID_RESPONSE;
        }
    }
    struct tm parsed = {
        .tm_sec = bcd2bin(raw[0]), .tm_min = bcd2bin(raw[1]),
        .tm_hour = bcd2bin(raw[2]), .tm_mday = bcd2bin(raw[3]),
        .tm_wday = raw[4], .tm_mon = bcd2bin(raw[5]) - 1,
        .tm_year = bcd2bin(raw[6]) + 100, /* existing BSP convention: 20xx */
        .tm_yday = -1, .tm_isdst = -1,
    };
    if (!valid_time(&parsed)) return ESP_ERR_INVALID_RESPONSE;
    *out_time = parsed;
    return ESP_OK;
}

esp_err_t codecraft_pcf8563_set_time(codecraft_pcf8563_handle_t rtc, const struct tm *time)
{
    if (!time) return ESP_ERR_INVALID_ARG;
    if (!rtc) return ESP_ERR_INVALID_STATE;
    if (!valid_time(time)) {
        return ESP_ERR_INVALID_ARG;
    }
    uint8_t buf[8];
    buf[0] = PCF8563_REG_TIME_DATE;
    buf[1] = bin2bcd((uint8_t)time->tm_sec);
    buf[2] = bin2bcd((uint8_t)time->tm_min);
    buf[3] = bin2bcd((uint8_t)time->tm_hour);
    buf[4] = bin2bcd((uint8_t)time->tm_mday);
    buf[5] = (uint8_t)time->tm_wday;
    buf[6] = bin2bcd((uint8_t)(time->tm_mon + 1)); /* century bit clear */
    buf[7] = bin2bcd((uint8_t)(time->tm_year - 100));
    return i2c_master_transmit(rtc->dev, buf, sizeof(buf), rtc->timeout_ms);
}
