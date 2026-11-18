/* SPDX-License-Identifier: Apache-2.0 */
#include "peripheral_stub.h"
#include "bsp_led.h"
#include "bsp_pins.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
static int calls,fail_at,alive,color;
static esp_err_t step(void){return ++calls==fail_at?ESP_FAIL:ESP_OK;}
esp_err_t led_strip_new_rmt_device(const led_strip_config_t *c,const led_strip_rmt_config_t *rmt,led_strip_handle_t *out){
    assert(!alive&&c->strip_gpio_num==BSP_PIN_WS2812_DATA&&c->max_leds==1&&rmt->resolution_hz==10000000);
    esp_err_t e=step();if(!e){alive=1;*out=&alive;}return e;}
esp_err_t led_strip_set_pixel(led_strip_handle_t s,uint32_t index,uint32_t r,uint32_t g,uint32_t b){assert(s==&alive&&alive&&index==0&&r==1&&g==2&&b==3);color=123;return step();}
esp_err_t led_strip_refresh(led_strip_handle_t s){assert(s==&alive&&alive);return step();}
esp_err_t led_strip_clear(led_strip_handle_t s){assert(s==&alive&&alive);color=0;return step();}
int main(int argc,char **argv){
    assert(argc==2);const char *mode=argv[1];
    if(!strcmp(mode,"unready")){assert(bsp_led_set_rgb(1,2,3)==ESP_ERR_INVALID_STATE);assert(bsp_led_off()==ESP_ERR_INVALID_STATE&&!calls);return 0;}
    fail_at=atoi(mode);esp_err_t e=bsp_led_init();if(fail_at){assert(e==ESP_FAIL&&!alive);assert(bsp_led_off()==ESP_ERR_INVALID_STATE);fail_at=0;assert(bsp_led_init()==ESP_OK);}else assert(e==ESP_OK);
    assert(bsp_led_set_rgb(1,2,3)==ESP_OK);int before=calls;assert(bsp_led_init()==ESP_OK&&calls==before&&color==123);
    calls=0;fail_at=!strcmp(mode,"pixel")||!strcmp(mode,"clear")?1:(!strcmp(mode,"refresh")?2:0);
    e=!strcmp(mode,"clear")?bsp_led_off():bsp_led_set_rgb(1,2,3);assert(e==(fail_at?ESP_FAIL:ESP_OK));
    fail_at=0;assert(bsp_led_off()==ESP_OK&&!color);return 0;
}
