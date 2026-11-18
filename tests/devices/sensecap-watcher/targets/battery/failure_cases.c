/* SPDX-License-Identifier: Apache-2.0 */
#include "adc_stub.h"
#include "bsp_battery.h"
#include "bsp_io_expander.h"
#include "bsp_pins.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>

enum { EXP=1, DIR, RAIL, DET, UNIT, CONFIG, CALI, DELETE_UNIT, READ, CONVERT, PRESENT };
static int fault, cleanup_failure, calls, unit_token, cali_token;
static bool unit, calibrated;
static esp_err_t step(int n)
{ calls++;return n==fault || n==cleanup_failure ? ESP_FAIL : ESP_OK; }
#define TRY(n) do { esp_err_t e=step(n); if(e!=ESP_OK)return e; } while(0)
esp_err_t bsp_io_expander_init(void) { return step(EXP); }
esp_err_t bsp_io_expander_set_direction(int pin,int output)
{
    if(pin==BSP_EXP_PIN_PWR_BAT_ADC) { assert(output);return step(DIR); }
    assert(pin==BSP_EXP_PIN_BAT_DET && !output);return step(DET);
}
esp_err_t bsp_io_expander_set_level(int pin,int level)
{ assert(pin==BSP_EXP_PIN_PWR_BAT_ADC && level==1);return step(RAIL); }
esp_err_t bsp_io_expander_get_level(int pin,int *level)
{ assert(pin==BSP_EXP_PIN_BAT_DET);TRY(PRESENT);*level=1;return ESP_OK; }
esp_err_t adc_oneshot_new_unit(const adc_oneshot_unit_init_cfg_t *cfg,adc_oneshot_unit_handle_t *out)
{ assert(!unit && cfg->unit_id==ADC_UNIT_1);TRY(UNIT);unit=true;*out=&unit_token;return ESP_OK; }
esp_err_t adc_oneshot_config_channel(adc_oneshot_unit_handle_t handle,int channel,const adc_oneshot_chan_cfg_t *cfg)
{ assert(unit && handle==&unit_token && channel==BSP_ADC_CHANNEL_BATTERY && cfg->atten==ADC_ATTEN_DB_2_5);return step(CONFIG); }
esp_err_t adc_cali_create_scheme_curve_fitting(const adc_cali_curve_fitting_config_t *cfg,adc_cali_handle_t *out)
{ assert(unit && !calibrated && cfg->chan==BSP_ADC_CHANNEL_BATTERY);TRY(CALI);calibrated=true;*out=&cali_token;return ESP_OK; }
esp_err_t adc_oneshot_del_unit(adc_oneshot_unit_handle_t handle)
{ assert(unit && !calibrated && handle==&unit_token);TRY(DELETE_UNIT);unit=false;return ESP_OK; }
esp_err_t adc_oneshot_read(adc_oneshot_unit_handle_t handle,int channel,int *out)
{ assert(unit && calibrated && handle==&unit_token && channel==BSP_ADC_CHANNEL_BATTERY);TRY(READ);*out=123;return ESP_OK; }
esp_err_t adc_cali_raw_to_voltage(adc_cali_handle_t handle,int raw,int *out)
{ assert(calibrated && handle==&cali_token && raw==123);TRY(CONVERT);*out=1000;return ESP_OK; }

static void success(void)
{
    assert(bsp_battery_init()==ESP_OK && unit && calibrated);
    int before=calls;assert(bsp_battery_init()==ESP_OK && calls==before);
    uint16_t voltage=0;
    assert(bsp_battery_get_voltage_mv(NULL)==ESP_ERR_INVALID_ARG);
    assert(bsp_battery_get_voltage_mv(&voltage)==ESP_OK && voltage==4100);
    assert(bsp_battery_is_present());
}
int main(int argc,char **argv)
{
    assert(argc>=2);uint16_t voltage=4321;
    assert(bsp_battery_get_voltage_mv(&voltage)==ESP_ERR_INVALID_STATE && voltage==4321);
    if(!strcmp(argv[1],"retry")) {
        fault=CONFIG;assert(bsp_battery_init()==ESP_FAIL);fault=0;success();return 0;
    }
    if(!strcmp(argv[1],"read-errors")) {
        success();
        for(int n=READ;n<=CONVERT;n++) {
            fault=n;assert(bsp_battery_get_voltage_mv(&voltage)==ESP_FAIL && voltage==4321);
        }
        fault=PRESENT;assert(!bsp_battery_is_present());fault=0;success();return 0;
    }
    fault=atoi(argv[1]);cleanup_failure=argc>2?atoi(argv[2]):0;
    if(!fault) { success();return 0; }
    assert(bsp_battery_init()==ESP_FAIL);
    assert(bsp_battery_get_voltage_mv(&voltage)==ESP_ERR_INVALID_STATE && voltage==4321);
    assert(!bsp_battery_is_present());
    if(cleanup_failure) {
        assert(unit && !calibrated);fault=cleanup_failure=0;int before=calls;
        assert(bsp_battery_init()==ESP_ERR_INVALID_STATE && calls==before);
    } else { assert(!unit && !calibrated);fault=0;success(); }
    return 0;
}
