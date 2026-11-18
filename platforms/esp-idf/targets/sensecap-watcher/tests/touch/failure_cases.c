/* SPDX-License-Identifier: Apache-2.0; real BSP C, synthetic resource failures. */
#include "touch_stub.h"
#include "bsp_touch.h"
#include "bsp_io_expander.h"
#include "bsp_pins.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>

enum { EXP=1,LCD_DIR,RAIL,TOUCH_DIR,BUS,DEV,TOUCH,READ,DEL_TOUCH,DEL_DEV,DEL_BUS };
static int fault,cleanup_fault,calls,polls,initial_nacks,bus_token,dev_token,touch_token;
static bool bus,device,touch,rail;
static esp_err_t step(int id)
{ ++calls;return id==fault || id==cleanup_fault ? ESP_FAIL : ESP_OK; }
#define TRY(id) do { if(step(id)!=ESP_OK) return ESP_FAIL; } while(0)
void vTaskDelay(int ticks) { assert(ticks>=0); }
esp_err_t bsp_io_expander_init(void) { return step(EXP); }
esp_err_t bsp_io_expander_set_direction(int pin,int output)
{ assert((pin==BSP_EXP_PIN_PWR_LCD && output==1) || (pin==BSP_EXP_PIN_TOUCH_INT && !output));return step(output ? LCD_DIR : TOUCH_DIR); }
esp_err_t bsp_io_expander_set_level(int pin,int level)
{ assert(pin==BSP_EXP_PIN_PWR_LCD && level==1);TRY(RAIL);rail=true;return ESP_OK; }
esp_err_t i2c_new_master_bus(const i2c_master_bus_config_t *c,i2c_master_bus_handle_t *out)
{ (void)c;assert(!bus);TRY(BUS);bus=true;*out=&bus_token;return ESP_OK; }
esp_err_t i2c_master_bus_add_device(i2c_master_bus_handle_t b,const i2c_device_config_t *c,i2c_master_dev_handle_t *out)
{ (void)c;assert(b==&bus_token && bus && !device);TRY(DEV);device=true;*out=&dev_token;return ESP_OK; }
esp_err_t i2c_master_bus_rm_device(i2c_master_dev_handle_t d)
{ assert(d==&dev_token && device && !touch);TRY(DEL_DEV);device=false;return ESP_OK; }
esp_err_t i2c_del_master_bus(i2c_master_bus_handle_t b)
{ assert(b==&bus_token && bus && !device);TRY(DEL_BUS);bus=false;return ESP_OK; }
esp_err_t i2c_master_transmit(i2c_master_dev_handle_t d,const uint8_t *p,size_t n,int timeout)
{ (void)p;(void)n;(void)timeout;assert(d==&dev_token && device);return ESP_OK; }
esp_err_t i2c_master_receive(i2c_master_dev_handle_t d,uint8_t *p,size_t n,int timeout)
{ (void)p;(void)n;(void)timeout;assert(d==&dev_token && device);return ESP_OK; }
esp_err_t esp_lcd_touch_new_i2c_spd2010(i2c_master_dev_handle_t d,const esp_lcd_touch_config_t *c,esp_lcd_touch_handle_t *out)
{ (void)c;assert(d==&dev_token && device && !touch);TRY(TOUCH);touch=true;*out=&touch_token;return ESP_OK; }
esp_err_t esp_lcd_touch_read_data(esp_lcd_touch_handle_t h)
{ assert(h==&touch_token && touch);++polls;return step(READ)!=ESP_OK || polls<=initial_nacks ? ESP_ERR_TIMEOUT : ESP_OK; }
esp_err_t esp_lcd_touch_del(esp_lcd_touch_handle_t h)
{ assert(h==&touch_token && touch);TRY(DEL_TOUCH);touch=false;return ESP_OK; }
static void success(void)
{
    esp_lcd_touch_handle_t h=NULL;
    assert(bsp_touch_init(&h)==ESP_OK && h==&touch_token && touch && device && bus);
    assert(bsp_touch_get_handle()==h);
    int before=calls;
    assert(bsp_touch_init(NULL)==ESP_OK && calls==before);
}
int main(int argc,char **argv)
{
    assert(argc>=2);assert(!bsp_touch_get_handle());
    if(strcmp(argv[1],"timeout")==0) {
        fault=READ;assert(bsp_touch_init(NULL)==ESP_ERR_TIMEOUT);
        assert(polls==25 && !bsp_touch_get_handle() && !bus);
        fault=0;success();return 0;
    }
    if(strcmp(argv[1],"late-ready")==0) { initial_nacks=24;success();assert(polls==25);return 0; }
    fault=atoi(argv[1]);cleanup_fault=argc>2 ? atoi(argv[2]) : 0;
    if(!fault) { success();return 0; }
    esp_lcd_touch_handle_t h=(void *)1;
    esp_err_t expected=fault==READ ? ESP_ERR_TIMEOUT : ESP_FAIL;
    assert(bsp_touch_init(&h)==expected && !h && !bsp_touch_get_handle());
    if(fault>RAIL)assert(rail);
    if(cleanup_fault) {
        int before=calls;fault=cleanup_fault=0;
        assert(bsp_touch_init(&h)==ESP_ERR_INVALID_STATE && !h && calls==before);
        assert(bus);
    } else {
        assert(!touch && !device && !bus);
        fault=0;success();
    }
    return 0;
}
