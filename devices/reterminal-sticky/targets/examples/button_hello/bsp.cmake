# Copyright (c) 2026 CodeCraft AI Hardware contributors.
# SPDX-License-Identifier: Apache-2.0
# Native composition for this example; no implicit all-peripheral fallback.
set(CODECRAFT_BSP_SOURCES
    "src/bsp_button.c"
)
set(CODECRAFT_BSP_REQUIRES
    esp_driver_gpio
    freertos
    log
)
