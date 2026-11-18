/* SPDX-License-Identifier: Apache-2.0 */
#include "peripheral_stub.h"
#include "bsp_battery.h"
#include "bsp_pins.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
static int calls,fail_at,alive,calibrated,power,reads,deletes;
static bool unsupported,cleanup_fail;
static TickType_t delay;
static esp_err_t step(void){return ++calls==fail_at?ESP_FAIL:ESP_OK;}
esp_err_t gpio_config(const gpio_config_t *c){assert(c->pin_bit_mask==(1ULL<<BSP_PIN_VBAT_EN));return step();}
esp_err_t gpio_set_level(int pin,int level){assert(pin==BSP_PIN_VBAT_EN);power=level;return step();}
esp_err_t adc_oneshot_new_unit(const adc_oneshot_unit_init_cfg_t *c,adc_oneshot_unit_handle_t *out){
    assert(!alive&&c->unit_id==ADC_UNIT_1);esp_err_t e=step();if(!e){alive=1;*out=&alive;}return e;}
esp_err_t adc_oneshot_config_channel(adc_oneshot_unit_handle_t u,int ch,const adc_oneshot_chan_cfg_t *c){
    assert(u==&alive&&alive&&ch==ADC_CHANNEL_0&&c->bitwidth==12&&c->atten==12);return step();}
esp_err_t adc_oneshot_del_unit(adc_oneshot_unit_handle_t u){assert(u==&alive&&alive);deletes++;if(cleanup_fail)return ESP_FAIL;alive=0;return ESP_OK;}
esp_err_t adc_cali_create_scheme_curve_fitting(const adc_cali_curve_fitting_config_t *c,adc_cali_handle_t *out){
    assert(c->chan==ADC_CHANNEL_0);esp_err_t e=step();if(unsupported)return ESP_ERR_NOT_SUPPORTED;
    if(!e){calibrated=1;*out=&calibrated;}return e;}
esp_err_t adc_oneshot_read(adc_oneshot_unit_handle_t u,int ch,int *out){
    assert(u==&alive&&alive&&ch==ADC_CHANNEL_0&&power==1);reads++;*out=2048;return step();}
esp_err_t adc_cali_raw_to_voltage(adc_cali_handle_t c,int raw,int *out){assert(c==&calibrated&&raw==2048&&!power);*out=1800;return step();}
void vTaskDelay(TickType_t ticks){assert(power);delay=ticks;}
int main(int argc,char **argv){
    assert(argc>1);const char *mode=argv[1];int out=777;
    if(!strcmp(mode,"unready")){assert(bsp_battery_read_mv(&out)==ESP_ERR_INVALID_STATE);assert(out==777&&!calls);return 0;}
    if(!strcmp(mode,"null")){assert(bsp_battery_read_mv(NULL)==ESP_ERR_INVALID_ARG);assert(!calls);return 0;}
    if(!strcmp(mode,"fallback"))unsupported=true;
    if(!strcmp(mode,"cleanup")){fail_at=4;cleanup_fail=true;}
    else fail_at=atoi(mode);
    esp_err_t result=bsp_battery_init();
    if(fail_at){assert(result==ESP_FAIL);assert(!power);assert(bsp_battery_read_mv(&out)==ESP_ERR_INVALID_STATE&&out==777);
        if(cleanup_fail){assert(alive&&deletes==1);int before=calls;assert(bsp_battery_init()==ESP_ERR_INVALID_STATE&&calls==before);return 0;}
        assert(!alive&&!calibrated);fail_at=0;calls=0;assert(bsp_battery_init()==ESP_OK);
    }else assert(result==ESP_OK);
    int before=calls;assert(bsp_battery_init()==ESP_OK&&calls==before);
    calls=0;fail_at=0;
    if(!strcmp(mode,"read")){assert(argc==3);fail_at=atoi(argv[2]);assert(bsp_battery_read_mv(&out)==ESP_FAIL&&out==777);assert(!power);fail_at=0;}
    if(!strcmp(mode,"off-recovery")){
        fail_at=3;assert(bsp_battery_read_mv(&out)==ESP_FAIL&&out==777);
        calls=0;fail_at=1;int sampled=reads;assert(bsp_battery_read_mv(&out)==ESP_FAIL&&out==777&&reads==sampled);
        fail_at=0;
    }
    assert(bsp_battery_read_mv(&out)==ESP_OK);assert(out==(unsupported?(2048*3100/4095)*2:3600));
    assert(!power&&alive&&delay>=pdMS_TO_TICKS(10)+1);return 0;
}
