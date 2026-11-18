# Copyright (c) 2026 CodeCraft AI Hardware contributors.
# SPDX-License-Identifier: Apache-2.0
# Native composition for this example; no implicit all-peripheral fallback.
set(CODECRAFT_BSP_SOURCES
    "src/bsp_audio.c"
    "src/bsp_io_expander.c"
)
set(CODECRAFT_BSP_REQUIRES
    esp_codec_dev
    esp_driver_i2c
    esp_driver_i2s
    freertos
    log
)
