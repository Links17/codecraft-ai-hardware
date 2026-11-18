/* SPDX-License-Identifier: Apache-2.0 */
#include "peripheral_stub.h"
#include "bsp_button.h"
#include "bsp_display.h"
#include "bsp_pins.h"
#include <setjmp.h>
static jmp_buf finished;
static int ready,pending,updates,draws;
static bool in_callback,backlight;
void app_main(void);
TaskHandle_t xTaskGetCurrentTaskHandle(void){return &ready;}
int xTaskNotifyGive(TaskHandle_t task){assert(task==&ready&&in_callback);pending++;return pdTRUE;}
uint32_t ulTaskNotifyTake(int clear,TickType_t wait){assert(!in_callback&&clear==pdFALSE&&wait==portMAX_DELAY);if(!pending)longjmp(finished,1);return (uint32_t)pending--;}
esp_err_t bsp_display_init(esp_lcd_panel_handle_t *out){ready=1;*out=&ready;return ESP_OK;}
esp_err_t bsp_display_backlight_set(bool value){assert(ready&&!in_callback);updates++;backlight=value;return ESP_OK;}
bool bsp_display_backlight_get(void){assert(!in_callback);return backlight;}
esp_err_t esp_lcd_panel_draw_bitmap(esp_lcd_panel_handle_t panel,int x0,int y0,int x1,int y1,const void *data){assert(panel==&ready&&!in_callback&&x0==0&&x1==BSP_LCD_H_RES&&y1==y0+1&&*(const uint16_t *)data==0xffff);draws++;return ESP_OK;}
esp_err_t bsp_button_init(bsp_button_cb_t cb){assert(ready&&draws==BSP_LCD_V_RES);in_callback=true;cb(true,NULL);cb(false,NULL);cb(true,NULL);in_callback=false;return ESP_OK;}
int main(void){if(!setjmp(finished))app_main();assert(updates==3&&backlight&&!in_callback);return 0;}
