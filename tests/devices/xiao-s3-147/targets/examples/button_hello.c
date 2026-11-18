/* SPDX-License-Identifier: Apache-2.0 */
#include "peripheral_stub.h"
#include "bsp_button.h"
#include "bsp_display.h"
#include <setjmp.h>
#include <string.h>
static jmp_buf finished;
static int queue,ready,updates,count,received;
static bsp_button_id_t events[2];
static bool in_callback,drop,backlight=true;
void app_main(void);
esp_err_t bsp_display_init(esp_lcd_panel_handle_t *out){ready=1;*out=&ready;return ESP_OK;}
esp_err_t bsp_display_backlight(bool on){assert(ready&&!in_callback);updates++;backlight=on;return ESP_OK;}
QueueHandle_t xQueueCreate(unsigned length,unsigned size){assert(length>=2&&size==sizeof(bsp_button_id_t));queue=1;return &queue;}
int xQueueSend(QueueHandle_t q,const void *item,TickType_t wait){assert(q==&queue&&queue&&in_callback&&wait==0);if(drop)return pdFALSE;assert(count<2);events[count++]=*(const bsp_button_id_t *)item;return pdTRUE;}
int xQueueReceive(QueueHandle_t q,void *item,TickType_t wait){assert(q==&queue&&!in_callback&&wait==portMAX_DELAY);if(received==count)longjmp(finished,1);*(bsp_button_id_t *)item=events[received++];return pdTRUE;}
esp_err_t bsp_button_init(bsp_button_cb_t cb,void *arg){assert(ready);in_callback=true;cb(BSP_BUTTON_USR1,true,arg);cb(BSP_BUTTON_USR1,false,arg);cb(BSP_BUTTON_USR2,true,arg);in_callback=false;return ESP_OK;}
int main(int argc,char **argv){assert(argc==2);drop=!strcmp(argv[1],"queue-full");if(!setjmp(finished))app_main();assert(updates==(drop?0:1)&&backlight==drop);return 0;}
