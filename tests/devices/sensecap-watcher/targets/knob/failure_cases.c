/* SPDX-License-Identifier: Apache-2.0; real PCNT BSP with stateful host doubles. */
#include "pcnt_stub.h"
#include "bsp_knob.h"
#include "bsp_io_expander.h"
#include "bsp_pins.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
enum { EXP=1,DIR,UNIT,FILTER,CHAN_A,CHAN_B,EDGE_A,LEVEL_A,EDGE_B,LEVEL_B,ENABLE,CLEAR,START,
       STOP,DISABLE,DEL_B,DEL_A,DEL_UNIT };
static int fault,cleanup_fault,calls,unit_token,a_token,b_token;
static bool unit,a,b,enabled,started;
static esp_err_t step(int id) { ++calls;return id==fault || id==cleanup_fault ? ESP_FAIL : ESP_OK; }
#define TRY(id) do { if(step(id)!=ESP_OK)return ESP_FAIL; } while(0)
esp_err_t bsp_io_expander_init(void) { return step(EXP); }
esp_err_t bsp_io_expander_set_direction(int pin,int output)
{ assert(pin==BSP_EXP_PIN_KNOB_BTN && !output);return step(DIR); }
esp_err_t bsp_io_expander_get_level(int pin,int *level)
{ assert(pin==BSP_EXP_PIN_KNOB_BTN);*level=0;return ESP_OK; }
esp_err_t pcnt_new_unit(const pcnt_unit_config_t *c,pcnt_unit_handle_t *out)
{ (void)c;assert(!unit);TRY(UNIT);unit=true;*out=&unit_token;return ESP_OK; }
esp_err_t pcnt_unit_set_glitch_filter(pcnt_unit_handle_t h,const pcnt_glitch_filter_config_t *c)
{ (void)c;assert(h==&unit_token && unit);return step(FILTER); }
esp_err_t pcnt_new_channel(pcnt_unit_handle_t h,const pcnt_chan_config_t *c,pcnt_channel_handle_t *out)
{
    assert(h==&unit_token && unit && !enabled);
    if(c->edge_gpio_num==BSP_PIN_KNOB_A) { assert(!a);TRY(CHAN_A);a=true;*out=&a_token; }
    else { assert(!b);TRY(CHAN_B);b=true;*out=&b_token; }
    return ESP_OK;
}
esp_err_t pcnt_channel_set_edge_action(pcnt_channel_handle_t h,int positive,int negative)
{ (void)positive;(void)negative;assert(unit && !enabled);return step(h==&a_token ? EDGE_A : EDGE_B); }
esp_err_t pcnt_channel_set_level_action(pcnt_channel_handle_t h,int high,int low)
{ (void)high;(void)low;assert(unit && !enabled);return step(h==&a_token ? LEVEL_A : LEVEL_B); }
esp_err_t pcnt_unit_enable(pcnt_unit_handle_t h)
{ assert(h==&unit_token && unit && !enabled && a && b);TRY(ENABLE);enabled=true;return ESP_OK; }
esp_err_t pcnt_unit_clear_count(pcnt_unit_handle_t h)
{ assert(h==&unit_token && enabled);return step(CLEAR); }
esp_err_t pcnt_unit_start(pcnt_unit_handle_t h)
{ assert(h==&unit_token && enabled && !started);TRY(START);started=true;return ESP_OK; }
esp_err_t pcnt_unit_stop(pcnt_unit_handle_t h)
{ assert(h==&unit_token && enabled);TRY(STOP);started=false;return ESP_OK; }
esp_err_t pcnt_unit_disable(pcnt_unit_handle_t h)
{ assert(h==&unit_token && enabled && !started);TRY(DISABLE);enabled=false;return ESP_OK; }
esp_err_t pcnt_del_channel(pcnt_channel_handle_t h)
{
    assert(unit && !enabled);
    if(h==&b_token) { assert(b);TRY(DEL_B);b=false; }
    else { assert(a && !b);TRY(DEL_A);a=false; }
    return ESP_OK;
}
esp_err_t pcnt_del_unit(pcnt_unit_handle_t h)
{ assert(h==&unit_token && unit && !enabled && !a && !b);TRY(DEL_UNIT);unit=false;return ESP_OK; }
esp_err_t pcnt_unit_get_count(pcnt_unit_handle_t h,int *count)
{ assert(h==&unit_token && started);*count=7;return ESP_OK; }
static void success(void)
{
    assert(bsp_knob_init()==ESP_OK && unit && a && b && enabled && started);
    int before=calls;assert(bsp_knob_init()==ESP_OK && calls==before);
    int delta=-1;assert(bsp_knob_get_delta(&delta)==ESP_OK && delta==7);
    assert(bsp_knob_get_delta(NULL)==ESP_ERR_INVALID_ARG && bsp_knob_button_pressed());
}
int main(int argc,char **argv)
{
    assert(argc>=2);
    if(strcmp(argv[1],"retry")==0) { fault=FILTER;assert(bsp_knob_init()==ESP_FAIL);fault=0;success();return 0; }
    fault=atoi(argv[1]);cleanup_fault=argc>2 ? atoi(argv[2]) : 0;
    if(!fault){success();return 0;}
    assert(bsp_knob_init()==ESP_FAIL);
    int delta;
    assert(bsp_knob_get_delta(&delta)==ESP_ERR_INVALID_STATE && !bsp_knob_button_pressed());
    if(cleanup_fault) {
        assert(unit);int before=calls;fault=cleanup_fault=0;
        assert(bsp_knob_init()==ESP_ERR_INVALID_STATE && calls==before);
    } else {
        assert(!unit && !a && !b && !enabled && !started);fault=0;success();
    }
    return 0;
}
