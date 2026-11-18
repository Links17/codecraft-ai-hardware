/* SPDX-License-Identifier: Apache-2.0; narrow host API double. */
#pragma once
#include "idf_bsp_stub.h"
enum { GPIO_MODE_OUTPUT=1, GPIO_PULLUP_ENABLE=1 };
typedef struct { uint64_t pin_bit_mask; int mode, pull_up_en; } gpio_config_t;
esp_err_t gpio_config(const gpio_config_t *cfg);
esp_err_t gpio_set_level(int pin, int level);
