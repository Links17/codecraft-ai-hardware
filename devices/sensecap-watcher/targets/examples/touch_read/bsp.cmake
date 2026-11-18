# Copyright (c) 2026 CodeCraft AI Hardware contributors.
# SPDX-License-Identifier: Apache-2.0
# Native composition for this example; no implicit all-peripheral fallback.
set(CODECRAFT_BSP_SOURCES
    "src/bsp_display.c"
    "src/bsp_io_expander.c"
    "src/bsp_touch.c"
)
set(CODECRAFT_BSP_REQUIRES
    esp_driver_i2c
    esp_driver_ledc
    esp_lcd
    esp_lcd_spd2010
    esp_lcd_touch
    esp_lcd_touch_spd2010
    freertos
    log
)
