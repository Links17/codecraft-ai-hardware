/* SPDX-License-Identifier: Apache-2.0 */
#include "peripheral_stub.h"
#include "bsp_buzzer.h"
#include "bsp_pins.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
static int calls,fail_at,duty,delays;
static esp_err_t step(void){return ++calls==fail_at?ESP_FAIL:ESP_OK;}
esp_err_t ledc_timer_config(const ledc_timer_config_t *c){assert(c->freq_hz==2000&&c->duty_resolution==10&&c->timer_num==LEDC_TIMER_0);return step();}
esp_err_t ledc_channel_config(const ledc_channel_config_t *c){assert(c->gpio_num==BSP_PIN_BUZZER&&c->channel==LEDC_CHANNEL_0);duty=c->duty;return step();}
esp_err_t ledc_set_freq(int mode,int timer,uint32_t frequency){assert(mode==LEDC_LOW_SPEED_MODE&&timer==LEDC_TIMER_0&&frequency==2000);return step();}
esp_err_t ledc_set_duty(int mode,int channel,uint32_t value){assert(mode==LEDC_LOW_SPEED_MODE&&channel==LEDC_CHANNEL_0);duty=(int)value;return step();}
esp_err_t ledc_update_duty(int mode,int channel){assert(mode==LEDC_LOW_SPEED_MODE&&channel==LEDC_CHANNEL_0);return step();}
void vTaskDelay(TickType_t ticks){assert(ticks==1&&duty==512);delays++;}
int main(int argc,char **argv){
    assert(argc>1);const char *mode=argv[1];
    if(!strcmp(mode,"unready")){assert(bsp_buzzer_tone(2000)==ESP_ERR_INVALID_STATE);assert(bsp_buzzer_stop()==ESP_ERR_INVALID_STATE&&!calls);return 0;}
    fail_at=atoi(mode);esp_err_t e=bsp_buzzer_init();if(fail_at){assert(e==ESP_FAIL);assert(bsp_buzzer_stop()==ESP_ERR_INVALID_STATE);fail_at=0;assert(bsp_buzzer_init()==ESP_OK);}else assert(e==ESP_OK);
    if(!strcmp(mode,"zero-frequency")){int before=calls;assert(bsp_buzzer_tone(0)==ESP_ERR_INVALID_ARG&&before==calls);return 0;}
    if(!strcmp(mode,"short-beep")||!strcmp(mode,"zero-beep")){bool short_beep=!strcmp(mode,"short-beep");assert(bsp_buzzer_beep(2000,short_beep?1:0)==ESP_OK);assert(delays==(short_beep?1:0)&&!duty);return 0;}
    assert(bsp_buzzer_tone(2000)==ESP_OK&&duty==512);int before=calls;assert(bsp_buzzer_init()==ESP_OK&&before==calls&&duty==512);
    if(argc==3){calls=0;fail_at=atoi(argv[2]);e=!strcmp(mode,"tone")?bsp_buzzer_tone(2000):bsp_buzzer_stop();assert(e==ESP_FAIL);fail_at=0;}
    assert(bsp_buzzer_stop()==ESP_OK&&!duty);return 0;
}
