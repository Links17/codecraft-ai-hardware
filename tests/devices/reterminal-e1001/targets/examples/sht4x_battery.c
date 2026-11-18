/* SPDX-License-Identifier: Apache-2.0 */
#include "peripheral_stub.h"
#include "bsp_button.h"
#include "bsp_battery.h"
#include "bsp_sht4x.h"
#include "bsp_led.h"
#include <assert.h>
#include <setjmp.h>
#include <string.h>
static jmp_buf finished;
static int queue,led,battery,sensor,samples,receives,pending;
static bool in_callback,drop,absent;
static TickType_t ticks;
void app_main(void);
const char *esp_err_to_name(esp_err_t err){(void)err;return "stub";}
esp_err_t bsp_led_init(void){led=1;return ESP_OK;}
esp_err_t bsp_led_set(bool on){(void)on;assert(led&&!in_callback);return ESP_OK;}
esp_err_t bsp_battery_init(void){battery=1;return ESP_OK;}
esp_err_t bsp_battery_read_mv(int *out){assert(battery&&!in_callback);samples++;*out=4000;return ESP_OK;}
esp_err_t bsp_sht4x_init(void){sensor=1;return absent?ESP_ERR_NOT_FOUND:ESP_OK;}
esp_err_t bsp_sht4x_read(float *t,float *rh){assert(sensor&&!in_callback);*t=20;*rh=50;return absent?ESP_ERR_INVALID_STATE:ESP_OK;}
QueueHandle_t xQueueCreate(unsigned length,unsigned size){assert(length>=1&&size==sizeof(bsp_key_t));queue=1;return &queue;}
int xQueueSend(QueueHandle_t q,const void *item,TickType_t wait){assert(q==&queue&&queue&&wait==0&&in_callback&&*(const bsp_key_t *)item==BSP_KEY_GREEN);if(drop)return pdFALSE;pending++;return pdTRUE;}
int xQueueReceive(QueueHandle_t q,void *item,TickType_t wait){assert(q==&queue&&!in_callback&&wait>0);if(++receives==3)longjmp(finished,1);
    if(pending){pending--;*(bsp_key_t *)item=BSP_KEY_GREEN;return pdTRUE;}ticks+=wait;return pdFALSE;}
esp_err_t bsp_button_init(bsp_button_cb_t cb,void *arg){assert(battery&&sensor&&led&&queue);in_callback=true;cb(BSP_KEY_GREEN,true,arg);in_callback=false;return ESP_OK;}
TickType_t xTaskGetTickCount(void){return ticks;}
void vTaskDelay(TickType_t wait){assert(!in_callback);ticks+=wait;}
int main(int argc,char **argv){assert(argc==2);drop=!strcmp(argv[1],"queue-full");absent=!strcmp(argv[1],"sensor-absent");if(!setjmp(finished))app_main();assert(samples==3&&!in_callback);return 0;}
