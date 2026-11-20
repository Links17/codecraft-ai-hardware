/* SPDX-License-Identifier: Apache-2.0; narrow PCNT host API double. */
#pragma once
#include "idf_bsp_stub.h"
typedef void *pcnt_unit_handle_t;
typedef void *pcnt_channel_handle_t;
typedef struct { int low_limit,high_limit; } pcnt_unit_config_t;
typedef struct { int max_glitch_ns; } pcnt_glitch_filter_config_t;
typedef struct { int edge_gpio_num,level_gpio_num; } pcnt_chan_config_t;
enum { PCNT_CHANNEL_EDGE_ACTION_DECREASE,PCNT_CHANNEL_EDGE_ACTION_INCREASE,
       PCNT_CHANNEL_LEVEL_ACTION_KEEP,PCNT_CHANNEL_LEVEL_ACTION_INVERSE };
esp_err_t pcnt_new_unit(const pcnt_unit_config_t *,pcnt_unit_handle_t *);
esp_err_t pcnt_del_unit(pcnt_unit_handle_t);
esp_err_t pcnt_unit_set_glitch_filter(pcnt_unit_handle_t,const pcnt_glitch_filter_config_t *);
esp_err_t pcnt_new_channel(pcnt_unit_handle_t,const pcnt_chan_config_t *,pcnt_channel_handle_t *);
esp_err_t pcnt_del_channel(pcnt_channel_handle_t);
esp_err_t pcnt_channel_set_edge_action(pcnt_channel_handle_t,int,int);
esp_err_t pcnt_channel_set_level_action(pcnt_channel_handle_t,int,int);
esp_err_t pcnt_unit_enable(pcnt_unit_handle_t);
esp_err_t pcnt_unit_disable(pcnt_unit_handle_t);
esp_err_t pcnt_unit_start(pcnt_unit_handle_t);
esp_err_t pcnt_unit_stop(pcnt_unit_handle_t);
esp_err_t pcnt_unit_clear_count(pcnt_unit_handle_t);
esp_err_t pcnt_unit_get_count(pcnt_unit_handle_t,int *);
