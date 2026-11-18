/* SPDX-License-Identifier: Apache-2.0
 * Only the ADC/calibration calls used by Watcher. Constants are API test IDs. */
#pragma once
#include "idf_bsp_stub.h"
typedef void *adc_oneshot_unit_handle_t;
typedef void *adc_cali_handle_t;
enum { ADC_UNIT_1=0, ADC_CHANNEL_2=2, ADC_BITWIDTH_DEFAULT=0, ADC_ATTEN_DB_2_5=1 };
typedef struct { int unit_id; } adc_oneshot_unit_init_cfg_t;
typedef struct { int bitwidth, atten; } adc_oneshot_chan_cfg_t;
typedef struct { int unit_id, chan, atten, bitwidth; } adc_cali_curve_fitting_config_t;
esp_err_t adc_oneshot_new_unit(const adc_oneshot_unit_init_cfg_t *cfg, adc_oneshot_unit_handle_t *out);
esp_err_t adc_oneshot_del_unit(adc_oneshot_unit_handle_t handle);
esp_err_t adc_oneshot_config_channel(adc_oneshot_unit_handle_t handle, int channel, const adc_oneshot_chan_cfg_t *cfg);
esp_err_t adc_cali_create_scheme_curve_fitting(const adc_cali_curve_fitting_config_t *cfg, adc_cali_handle_t *out);
esp_err_t adc_oneshot_read(adc_oneshot_unit_handle_t handle, int channel, int *out);
esp_err_t adc_cali_raw_to_voltage(adc_cali_handle_t handle, int raw, int *out);
