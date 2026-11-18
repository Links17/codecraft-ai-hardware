/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * SenseCAP Watcher microSD slot: second device on the shared SPI2 bus
 * (CS=GPIO46, the Himax camera is the other device), card-detect on IO
 * expander pin 4 (low = inserted), power rail on expander pin 8.
 * The SSCMA camera driver tolerates an already-initialized SPI2 bus and
 * vice versa; max_transfer_sz is kept >= 4096 so either may init first.
 */
#pragma once

#include <stdbool.h>

#include "esp_err.h"
#include "sdmmc_cmd.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Task context only: use one storage-owning task or an application mutex for
 * mount/unmount and all access through the borrowed card. Close every file and
 * finish all card operations before unmount. Do not use from ISRs, button or
 * non-blocking UI callbacks. The expander has bounded per-call waits; native
 * FAT/SDSPI operations have no BSP-imposed total deadline. Use a worker task.
 *
 * Powers the SD rail, ensures the board-configured shared SPI2 bus exists and
 * mounts FAT at mount_point (e.g. "/sdcard"). Never formats on failure. An
 * existing SPI2 bus must use this board's documented pins/configuration; an
 * already-initialized result cannot verify another component's bus settings.
 * The shared bus and rail remain available after failed mount or unmount.
 *
 * Repeating the same path succeeds; a different path returns INVALID_STATE.
 * The BSP owns a copy of the path and the mounted card. out_card is optional,
 * borrowed until unmount, and set to NULL on failure. Do not free/unmount it
 * through SDK calls. SDK mount failure cleans its partial attachment; a BSP
 * retry is supported. After a failed unmount, reset is required. */
esp_err_t bsp_sdcard_init(const char *mount_point, sdmmc_card_t **out_card);

/* Reads card detect (expander pin 4, active low). Output is unchanged on error;
 * this reading does not establish that the card is mounted or usable. */
esp_err_t bsp_sdcard_is_inserted(bool *inserted);

/* Same path only. Once SDK unmount is attempted, all borrowed card handles are
 * invalid, even on error: IDF may free the card before reporting a later error.
 * A failed attempt blocks further mount/unmount until reset. Successful repeated
 * deinit is a no-op. The shared SPI2 bus and rail are left available. */
esp_err_t bsp_sdcard_deinit(const char *mount_point);

#ifdef __cplusplus
}
#endif
