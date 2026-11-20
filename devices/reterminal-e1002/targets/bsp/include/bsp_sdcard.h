/*
 * Copyright (c) 2026 CodeCraft AI Hardware contributors.
 * SPDX-License-Identifier: Apache-2.0
 *
 * reTerminal E1002 microSD slot (J5, ST-TF-003J), wired for SPI mode:
 *   CLOCK = GPIO 7, CMD/MOSI = GPIO 9, DAT0/MISO = GPIO 8, CD/DAT3/CS = GPIO 14.
 * The bus is shared with the e-paper panel (CS = GPIO 10); bsp_epd also
 * routes MISO so either device may initialise the bus first.
 * Card power rail TF_CARD_PWR is switched by a TPS22916 load switch (U13),
 * enable GPIO 16 active high. Card-detect switch on GPIO 15 shorts to GND
 * when a card is inserted (active low, internal pull-up).
 * Facts from the vendor schematic E1001 V1.2, sheet 06 Peripherals
 * (CC BY-SA 4.0); the E1002 shares the E1001 mainboard
 * (see docs/vendor-sources.md).
 */
#pragma once

#include <stdbool.h>

#include "esp_err.h"
#include "sdmmc_cmd.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Task context only. One storage-owning task or application mutex must
 * serialize mount/unmount and all operations on the borrowed card. Close all
 * files and complete card operations before unmount; no ISR or non-blocking
 * callbacks. Native FAT/SDSPI waits have no BSP-imposed total deadline; rail
 * startup also includes the existing 20 ms delay. Use a worker task.
 *
 * Powers the SD rail and mounts FAT at mount_point without formatting on
 * failure. Existing SPI2 must match this board's pins/transfer configuration;
 * an already-initialized result does not verify compatibility. Bus/rail are
 * board-owned and remain available after mount failure or unmount.
 * Repeating the same path is a no-op; another path returns INVALID_STATE.
 * BSP owns a path copy and mounted card. out_card is optional and cleared on
 * failure; the returned handle is borrowed until any attempted unmount and
 * must not be freed/unmounted through SDK calls. Failed mount cleans native
 * partial attachment and permits retry; failed unmount requires reset.
 * Physical card/rail state and recovery are not established by software. */
esp_err_t bsp_sdcard_init(const char *mount_point, sdmmc_card_t **out_card);

/* Reads active-low card detect. Output is preserved on error. A detected
 * card is not proof of a mounted or usable filesystem. May run before init. */
esp_err_t bsp_sdcard_is_inserted(bool *inserted);

/* Rejects another path while mounted. After native unmount is attempted,
 * all borrowed handles are invalid even on error: IDF can free the card before
 * a later failure. Failed unmount blocks mount/unmount until reset. Repeated
 * successful deinit is a no-op; shared SPI2 and the rail remain available. */
esp_err_t bsp_sdcard_deinit(const char *mount_point);

#ifdef __cplusplus
}
#endif
