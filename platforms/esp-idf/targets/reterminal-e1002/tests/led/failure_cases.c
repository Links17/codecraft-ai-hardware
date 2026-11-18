/* SPDX-License-Identifier: Apache-2.0 */
#include "peripheral_stub.h"
#include "bsp_led.h"
#include "bsp_pins.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
static int calls,fail_at,level=-1;
static esp_err_t step(void){return ++calls==fail_at?ESP_FAIL:ESP_OK;}
esp_err_t gpio_config(const gpio_config_t *c){assert(c->pin_bit_mask==1ULL<<BSP_PIN_LED);return step();}
esp_err_t gpio_set_level(int pin,int value){assert(pin==BSP_PIN_LED);level=value;return step();}
int main(int argc,char **argv){
    assert(argc==2);const char *mode=argv[1];
    if(!strcmp(mode,"unready")){bsp_led_set(true);assert(!calls&&level==-1);return 0;}
    fail_at=atoi(mode);esp_err_t e=bsp_led_init();
    if(fail_at){assert(e==ESP_FAIL);int before=calls;bsp_led_set(true);assert(calls==before);fail_at=0;assert(bsp_led_init()==ESP_OK);}else assert(e==ESP_OK);
    assert(level==1);bsp_led_set(true);assert(!level);int before=calls;
    assert(bsp_led_init()==ESP_OK&&calls==before&&!level);
    if(!strcmp(mode,"write-error")){fail_at=calls+1;bsp_led_set(false);fail_at=0;}
    bsp_led_set(false);assert(level==1);return 0;
}
