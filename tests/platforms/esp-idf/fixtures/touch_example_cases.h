/* SPDX-License-Identifier: Apache-2.0 */
#include "peripheral_stub.h"
#include "bsp_touch.h"
#ifdef WATCHER_TOUCH_EXAMPLE
#include "bsp_display.h"
#endif
#include <setjmp.h>
#include <string.h>
static jmp_buf finished;
static int frame,reads,gets,presses,releases,errors;
void app_main(void);
#ifdef WATCHER_TOUCH_EXAMPLE
esp_err_t bsp_display_init(esp_lcd_panel_handle_t *panel,esp_lcd_panel_io_handle_t *io){assert(!panel&&!io);return ESP_OK;}
#endif
esp_err_t bsp_touch_init(esp_lcd_touch_handle_t *out){*out=&frame;return ESP_OK;}
esp_err_t esp_lcd_touch_read_data(esp_lcd_touch_handle_t touch){assert(touch==&frame);reads++;return frame==1?ESP_FAIL:ESP_OK;}
esp_err_t esp_lcd_touch_get_data(esp_lcd_touch_handle_t touch,esp_lcd_touch_point_data_t *point,uint8_t *count,uint8_t max){
    assert(touch==&frame&&max==1&&frame!=1);gets++;point->x=10;point->y=20;point->strength=30;*count=frame==3?0:1;return frame==2?ESP_FAIL:ESP_OK;}
void stub_log(const char *tag,const char *fmt,...){(void)tag;if(!strncmp(fmt,"press x=",8))presses++;if(!strcmp(fmt,"released"))releases++;if(!strncmp(fmt,"touch sample failed",19))errors++;}
const char *esp_err_to_name(esp_err_t err){(void)err;return "stub";}
void vTaskDelay(TickType_t ticks){assert(ticks==pdMS_TO_TICKS(20));if(++frame==4)longjmp(finished,1);}
int main(void){if(!setjmp(finished))app_main();assert(reads==4&&gets==3&&presses==1&&releases==1&&errors==2);return 0;}
