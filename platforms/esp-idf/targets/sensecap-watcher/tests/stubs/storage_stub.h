/* SPDX-License-Identifier: Apache-2.0; narrow host API double. */
#pragma once
#include "idf_bsp_stub.h"
typedef struct { int identity; } sdmmc_card_t;
typedef struct { int slot; } sdmmc_host_t;
typedef struct { int gpio_cs, host_id; } sdspi_device_config_t;
typedef struct { bool format_if_mount_failed; int max_files, allocation_unit_size; } esp_vfs_fat_sdmmc_mount_config_t;
#define SDSPI_HOST_DEFAULT() ((sdmmc_host_t){.slot=SPI2_HOST})
#define SDSPI_DEVICE_CONFIG_DEFAULT() ((sdspi_device_config_t){0})
esp_err_t esp_vfs_fat_sdspi_mount(const char *path, const sdmmc_host_t *host,
    const sdspi_device_config_t *slot, const esp_vfs_fat_sdmmc_mount_config_t *cfg, sdmmc_card_t **out);
esp_err_t esp_vfs_fat_sdcard_unmount(const char *path, sdmmc_card_t *card);
