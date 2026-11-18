/* SPDX-License-Identifier: Apache-2.0 */
#include "peripheral_stub.h"
#include "bsp_charger.h"
#include "bsp_pins.h"
#include <assert.h>
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
static int calls,fail_at,cleanup_fail,bus,device,mutex_alive;
static bool bad_id,lock_timeout,runtime,locked,concurrent,first_read,second_waiting,release_first,in_rmw;
static uint8_t regs[16];
static pthread_mutex_t mutex=PTHREAD_MUTEX_INITIALIZER,gate=PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t changed=PTHREAD_COND_INITIALIZER;
static int takes;
static esp_err_t step(void){return ++calls==fail_at?ESP_FAIL:ESP_OK;}
SemaphoreHandle_t xSemaphoreCreateMutex(void){assert(!mutex_alive);if(step()!=ESP_OK)return NULL;mutex_alive=1;return &mutex;}
int xSemaphoreTake(SemaphoreHandle_t m,TickType_t wait){
    assert(m==&mutex&&mutex_alive&&wait==pdMS_TO_TICKS(100));if(lock_timeout)return pdFALSE;
    if(concurrent){pthread_mutex_lock(&gate);takes++;if(takes==2){second_waiting=true;pthread_cond_broadcast(&changed);}pthread_mutex_unlock(&gate);}
    pthread_mutex_lock(&mutex);assert(!locked);locked=true;return pdTRUE;}
void xSemaphoreGive(SemaphoreHandle_t m){assert(m==&mutex&&locked);locked=false;pthread_mutex_unlock(&mutex);}
void vSemaphoreDelete(SemaphoreHandle_t m){assert(m==&mutex&&mutex_alive&&!bus&&!device&&!locked);mutex_alive=0;}
esp_err_t i2c_new_master_bus(const i2c_master_bus_config_t *c,i2c_master_bus_handle_t *out){
    assert(!bus&&c->i2c_port==1&&c->sda_io_num==BSP_PIN_I2C1_SDA&&c->scl_io_num==BSP_PIN_I2C1_SCL);esp_err_t e=step();if(!e){bus=1;*out=&bus;}return e;}
esp_err_t i2c_master_probe(i2c_master_bus_handle_t b,int addr,int timeout){assert(b==&bus&&bus&&addr==BSP_I2C_ADDR_CHARGER&&timeout==100);return step();}
esp_err_t i2c_master_bus_add_device(i2c_master_bus_handle_t b,const i2c_device_config_t *c,i2c_master_dev_handle_t *out){
    assert(b==&bus&&bus&&!device&&c->device_address==BSP_I2C_ADDR_CHARGER&&c->scl_speed_hz==100000);esp_err_t e=step();if(!e){device=1;*out=&device;}return e;}
esp_err_t i2c_master_bus_rm_device(i2c_master_dev_handle_t d){assert(d==&device&&device);if(cleanup_fail==1)return ESP_FAIL;device=0;return ESP_OK;}
esp_err_t i2c_del_master_bus(i2c_master_bus_handle_t b){assert(b==&bus&&bus&&!device);if(cleanup_fail==2)return ESP_FAIL;bus=0;return ESP_OK;}
esp_err_t i2c_master_transmit_receive(i2c_master_dev_handle_t d,const uint8_t *tx,size_t ts,uint8_t *rx,size_t rs,int timeout){
    assert(d==&device&&device&&ts==1&&rs==1&&*tx<16&&timeout==100);assert(!runtime||locked);
    if(concurrent){assert(!in_rmw);in_rmw=true;pthread_mutex_lock(&gate);
        if(!first_read){first_read=true;pthread_cond_broadcast(&changed);while(!release_first)pthread_cond_wait(&changed,&gate);}pthread_mutex_unlock(&gate);}
    *rx=bad_id&&*tx==11?0:regs[*tx];return step(); /* partial output even on error */
}
esp_err_t i2c_master_transmit(i2c_master_dev_handle_t d,const uint8_t *data,size_t size,int timeout){
    assert(d==&device&&device&&size==2&&data[0]<16&&timeout==100);assert(!runtime||locked);
    if(concurrent){assert(in_rmw);in_rmw=false;}
    regs[data[0]]=data[1];return step(); /* write may apply before error */
}
void vTaskDelay(TickType_t ticks){assert(ticks==pdMS_TO_TICKS(10));}
static void *set_current(void *unused){(void)unused;assert(bsp_charger_set_charge_current_ma(600)==ESP_OK);return NULL;}
static void *set_enable(void *unused){(void)unused;assert(bsp_charger_set_charge_enabled(true)==ESP_OK);return NULL;}
int main(int argc,char **argv){
    assert(argc>1);const char *mode=argv[1];regs[11]=0x40;regs[2]=0xc0;regs[4]=7;regs[5]=0x3f;
    bsp_charger_status_t status=(bsp_charger_status_t)99;uint16_t ma=999;uint8_t faults=99;bool present=true;
    if(!strcmp(mode,"unready")){assert(bsp_charger_get_status(&status)==ESP_ERR_INVALID_STATE&&status==99);assert(bsp_charger_get_faults(&faults)==ESP_ERR_INVALID_STATE&&faults==99);assert(bsp_charger_set_charge_current_ma(600)==ESP_ERR_INVALID_STATE&&!calls);return 0;}
    if(!strcmp(mode,"null")){assert(bsp_charger_get_status(NULL)==ESP_ERR_INVALID_ARG);assert(bsp_charger_is_input_present(NULL)==ESP_ERR_INVALID_ARG);assert(bsp_charger_get_charge_current_ma(NULL)==ESP_ERR_INVALID_ARG);assert(bsp_charger_get_faults(NULL)==ESP_ERR_INVALID_ARG&&!calls);return 0;}
    bad_id=!strcmp(mode,"part-id");fail_at=atoi(mode);
    if(!strcmp(mode,"cleanup")){assert(argc==3);fail_at=13;cleanup_fail=atoi(argv[2]);}
    esp_err_t e=bsp_charger_init();
    if(fail_at||bad_id){assert(e==(fail_at==1?ESP_ERR_NO_MEM:(bad_id||fail_at==3?ESP_ERR_NOT_FOUND:ESP_FAIL)));
        assert(bsp_charger_get_status(&status)==ESP_ERR_INVALID_STATE&&status==99);
        if(cleanup_fail){int before=calls;assert(bsp_charger_init()==ESP_ERR_INVALID_STATE&&calls==before&&bus&&mutex_alive);assert(device==(cleanup_fail==1));return 0;}
        assert(!bus&&!device&&!mutex_alive);fail_at=0;bad_id=false;assert(bsp_charger_init()==ESP_OK);
    }else assert(e==ESP_OK);
    assert((regs[2]&0x3f)==16&&(regs[2]&0xc0)==0xc0);assert(regs[4]==0x5f&&regs[5]==0x0f);
    runtime=true;int before=calls;assert(bsp_charger_init()==ESP_OK&&calls==before);
    if(!strcmp(mode,"lock-timeout")){lock_timeout=true;assert(bsp_charger_get_faults(&faults)==ESP_ERR_TIMEOUT&&faults==99);assert(bsp_charger_set_charge_enabled(true)==ESP_ERR_TIMEOUT&&calls==before);return 0;}
    if(!strcmp(mode,"runtime")){
        calls=0;fail_at=atoi(argv[2]);
        if(fail_at==1){assert(bsp_charger_get_faults(&faults)==ESP_FAIL&&faults==99);calls=0;assert(bsp_charger_get_charge_current_ma(&ma)==ESP_FAIL&&ma==999);calls=0;assert(bsp_charger_get_status(&status)==ESP_FAIL&&status==99);calls=0;assert(bsp_charger_is_input_present(&present)==ESP_FAIL&&present);}
        else assert(bsp_charger_set_charge_current_ma(600)==ESP_FAIL);
        fail_at=0;assert(!locked);
    }
    if(!strcmp(mode,"concurrent")){
        concurrent=true;pthread_t a,b;assert(!pthread_create(&a,NULL,set_current,NULL));
        pthread_mutex_lock(&gate);while(!first_read)pthread_cond_wait(&changed,&gate);pthread_mutex_unlock(&gate);
        assert(!pthread_create(&b,NULL,set_enable,NULL));pthread_mutex_lock(&gate);
        while(!second_waiting)pthread_cond_wait(&changed,&gate);release_first=true;pthread_cond_broadcast(&changed);pthread_mutex_unlock(&gate);
        pthread_join(a,NULL);pthread_join(b,NULL);assert(!in_rmw&&takes==2&&regs[2]==0xca&&(regs[1]&0x10));concurrent=false;
    }
    assert(bsp_charger_set_charge_current_ma(65535)==ESP_OK&&regs[2]==0xf2);
    assert(bsp_charger_get_charge_current_ma(&ma)==ESP_OK&&ma==3000);
    assert(bsp_charger_set_charge_current_ma(59)==ESP_OK&&regs[2]==0xc0);
    regs[1]=0xef;assert(bsp_charger_set_charge_enabled(true)==ESP_OK&&regs[1]==0xff);
    assert(bsp_charger_set_charge_enabled(false)==ESP_OK&&regs[1]==0xef);
    const bsp_charger_status_t expected[]={BSP_CHARGER_STATUS_NOT_CHARGING,BSP_CHARGER_STATUS_PRECHARGE,BSP_CHARGER_STATUS_FAST_CHARGE,BSP_CHARGER_STATUS_FULL};
    for(unsigned i=0;i<4;i++){regs[8]=(uint8_t)(4|(i<<3));assert(bsp_charger_get_status(&status)==ESP_OK&&status==expected[i]);}
    regs[8]=0;assert(bsp_charger_get_status(&status)==ESP_OK&&status==BSP_CHARGER_STATUS_DISCHARGING);
    regs[10]=0x80;assert(bsp_charger_is_input_present(&present)==ESP_OK&&present);regs[9]=0xa5;assert(bsp_charger_get_faults(&faults)==ESP_OK&&faults==0xa5);
    before=calls;assert(bsp_charger_init()==ESP_OK&&before==calls&&regs[2]==0xc0);return 0;
}
