# Copyright (c) 2026 CodeCraft AI Hardware contributors.
# SPDX-License-Identifier: Apache-2.0
# Native composition for this example; no implicit all-peripheral fallback.
set(CODECRAFT_BSP_SOURCES
    "src/bsp_battery.c"
    "src/bsp_button.c"
    "src/bsp_i2c0_internal.c"
    "src/bsp_led.c"
    "src/bsp_sht4x.c"
)
set(CODECRAFT_BSP_REQUIRES
    codecraft_sht4x
    esp_adc
    esp_driver_gpio
    esp_driver_i2c
    freertos
    log
)
