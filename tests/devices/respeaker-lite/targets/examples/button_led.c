/* SPDX-License-Identifier: Apache-2.0 */
#include "peripheral_stub.h"
#include "bsp_button.h"
#include "bsp_led.h"
#include <setjmp.h>
static jmp_buf finished;
static int ready,frame,colors,clears;
static bool in_callback,held=true;
static bsp_button_cb_t callback;
void app_main(void);
esp_err_t bsp_led_init(void){ready=1;return ESP_OK;}
esp_err_t bsp_led_set_rgb(uint8_t r,uint8_t g,uint8_t b){assert(ready&&!in_callback&&!b);assert(frame==0?(r==32&&!g):(g==32&&!r));colors++;return ESP_OK;}
esp_err_t bsp_led_off(void){assert(ready&&!in_callback);clears++;return ESP_OK;}
esp_err_t bsp_button_init(bsp_button_cb_t cb){assert(ready);callback=cb;return ESP_OK;}
bool bsp_button_pressed(void){return held;}
void vTaskDelay(TickType_t ticks){assert(ticks==pdMS_TO_TICKS(50));if(++frame==3)longjmp(finished,1);in_callback=true;held=frame==1;callback(held,NULL);in_callback=false;}
int main(void){if(!setjmp(finished))app_main();assert(colors==2&&clears==1&&!in_callback);return 0;}
