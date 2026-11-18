/* SPDX-License-Identifier: Apache-2.0 */
#include "bsp_camera.h"
#include "bsp_io_expander.h"
#include "bsp_pins.h"
#include "camera_sscma.h"
#include "driver/gpio.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
enum { EXP=1, SYSTEM_DIR, SYSTEM_ON, CAMERA_DIR, SYNC_DIR, RESET_DIR, RESET_IDLE, GPIO_CONFIG, GPIO_LEVEL };
static int fault,calls,registered;
static camera_driver_t driver;
static esp_err_t step(int n) {calls++;return fault==n?ESP_FAIL:ESP_OK;}
esp_err_t bsp_io_expander_init(void){return step(EXP);}
esp_err_t bsp_io_expander_set_direction(int pin,int output)
{
    if(pin==BSP_EXP_PIN_PWR_SYSTEM){assert(output);return step(SYSTEM_DIR);}
    if(pin==BSP_EXP_PIN_PWR_AI_CHIP){assert(output);return step(CAMERA_DIR);}
    if(pin==BSP_EXP_PIN_CAM_SYNC){assert(!output);return step(SYNC_DIR);}
    assert(pin==BSP_EXP_PIN_CAM_RST&&output);return step(RESET_DIR);
}
esp_err_t bsp_io_expander_set_level(int pin,int level)
{
    if(pin==BSP_EXP_PIN_PWR_SYSTEM){assert(level==1);return step(SYSTEM_ON);}
    if(pin==BSP_EXP_PIN_CAM_RST){assert(level==1);return step(RESET_IDLE);}
    assert(pin==BSP_EXP_PIN_PWR_AI_CHIP);return ESP_OK;
}
esp_err_t bsp_io_expander_get_level(int pin,int *level)
{assert(pin==BSP_EXP_PIN_CAM_SYNC);*level=1;return ESP_OK;}
esp_err_t gpio_config(const gpio_config_t *cfg)
{assert(cfg->pin_bit_mask==(1ULL<<BSP_PIN_SD_CS)&&cfg->mode==GPIO_MODE_OUTPUT);return step(GPIO_CONFIG);}
esp_err_t gpio_set_level(int pin,int level)
{assert(pin==BSP_PIN_SD_CS&&level==1);return step(GPIO_LEVEL);}
void vTaskDelay(int ticks){assert(ticks==pdMS_TO_TICKS(100));}
const camera_driver_t *camera_sscma(const camera_sscma_config_t *cfg)
{
    assert(!fault&&cfg->host==SPI2_HOST&&cfg->cs==BSP_PIN_CAM_CS);
    assert(cfg->sclk==BSP_PIN_SPI2_SCLK&&cfg->mosi==BSP_PIN_SPI2_MOSI&&cfg->miso==BSP_PIN_SPI2_MISO);
    assert(cfg->resolution==3&&cfg->stream_resolution==1&&cfg->power&&cfg->reset&&cfg->has_data);
    return &driver;
}
void camera_register(const camera_driver_t *d){assert(d==&driver);registered++;}
const camera_driver_t *camera_get(void){return registered?&driver:NULL;}
int main(int argc,char **argv)
{
    assert(argc==2);fault=atoi(argv[1]);
    if(!strcmp(argv[1],"registered")){registered=1;assert(bsp_camera_init()==ESP_ERR_INVALID_STATE&&!calls);registered=0;}
    if(fault){assert(bsp_camera_init()==ESP_FAIL&&!registered);fault=0;}
    assert(bsp_camera_init()==ESP_OK&&registered==1);int before=calls;
    assert(bsp_camera_init()==ESP_OK&&registered==1&&before==calls);return 0;
}
