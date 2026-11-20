/* SPDX-License-Identifier: Apache-2.0
 * Execute real expander initialization against synthetic I2C transactions.
 */
#include "idf_bsp_stub.h"
#include "bsp_io_expander.h"
#include "freertos/semphr.h"
#include <assert.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>

static int fail_step, cleanup_failure, calls, bus_token, dev_token;
static bool bus, device, probed;
static bool fail_write, write_applied;
static int writes;
static uint8_t registers[8]={255,255,255,255,255,255,255,255};
static pthread_mutex_t expander_lock, gate=PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t changed=PTHREAD_COND_INITIALIZER;
static bool mutex_alive, lock_timeout, pause_write, write_waiting, release_write, mutex_waiter;
static esp_err_t step(int n)
{ ++calls;return (fail_step && n==fail_step) || (cleanup_failure && n==cleanup_failure) ? ESP_FAIL : ESP_OK; }
#define TRY(n) do { if(step(n)!=ESP_OK) return ESP_FAIL; } while(0)
SemaphoreHandle_t xSemaphoreCreateMutex(void)
{
    assert(!mutex_alive);
    if(step(10)!=ESP_OK) return NULL;
    assert(pthread_mutex_init(&expander_lock,NULL)==0);mutex_alive=true;return &expander_lock;
}
int xSemaphoreTake(SemaphoreHandle_t mutex,TickType_t timeout)
{
    assert(mutex_alive && mutex==&expander_lock && timeout==100);
    if(lock_timeout)return 0;
    int ret=pthread_mutex_trylock(mutex);
    if(ret==EBUSY) {
        pthread_mutex_lock(&gate);mutex_waiter=true;pthread_cond_broadcast(&changed);pthread_mutex_unlock(&gate);
        ret=pthread_mutex_lock(mutex);
    }
    assert(ret==0);return pdTRUE;
}
void xSemaphoreGive(SemaphoreHandle_t mutex) { assert(pthread_mutex_unlock(mutex)==0); }
void vSemaphoreDelete(SemaphoreHandle_t mutex)
{ assert(mutex_alive && mutex==&expander_lock);assert(pthread_mutex_destroy(mutex)==0);mutex_alive=false; }
esp_err_t i2c_new_master_bus(const i2c_master_bus_config_t *c, i2c_master_bus_handle_t *out)
{ (void)c;assert(!bus);TRY(1);bus=true;*out=&bus_token;return ESP_OK; }
esp_err_t i2c_master_bus_add_device(i2c_master_bus_handle_t b, const i2c_device_config_t *c, i2c_master_dev_handle_t *out)
{ (void)c;assert(b==&bus_token && bus && !device);TRY(2);device=true;*out=&dev_token;return ESP_OK; }
esp_err_t i2c_master_probe(i2c_master_bus_handle_t b, int address, int timeout)
{ (void)address;(void)timeout;assert(b==&bus_token && bus);TRY(3);probed=true;return ESP_OK; }
esp_err_t i2c_master_transmit_receive(i2c_master_dev_handle_t d, const uint8_t *data, size_t size, uint8_t *out, size_t out_size, int timeout)
{
    (void)timeout;assert(d==&dev_token && device && probed && size==1 && out_size==1);
    int index=data[0]>=6 ? data[0] : data[0]+2;
    TRY(index);*out=registers[data[0]];return ESP_OK;
}
esp_err_t i2c_master_transmit(i2c_master_dev_handle_t d, const uint8_t *data, size_t size, int timeout)
{
    (void)timeout;assert(d==&dev_token && device && probed && size==2);
    assert(data[0]<8);
    pthread_mutex_lock(&gate);
    if(pause_write) {
        assert(!write_waiting || release_write); /* no second RMW before first finishes */
        write_waiting=true;pthread_cond_broadcast(&changed);
        while(!release_write)pthread_cond_wait(&changed,&gate);
    }
    writes++;
    if (!fail_write || write_applied) registers[data[0]]=data[1];
    pthread_mutex_unlock(&gate);
    return fail_write ? ESP_FAIL : ESP_OK;
}
esp_err_t i2c_master_bus_rm_device(i2c_master_dev_handle_t d)
{ assert(d==&dev_token && device);TRY(8);device=false;probed=false;return ESP_OK; }
esp_err_t i2c_del_master_bus(i2c_master_bus_handle_t b)
{ assert(b==&bus_token && bus && !device);TRY(9);bus=false;return ESP_OK; }

static void success(void)
{
    assert(bsp_io_expander_init()==ESP_OK);
    assert(bus && device && probed);
    assert(bsp_io_expander_set_level(0,1)==ESP_OK);
    int before=calls;
    assert(bsp_io_expander_init()==ESP_OK && calls==before);
    i2c_master_bus_handle_t b=NULL;
    assert(bsp_i2c0_get_bus(&b)==ESP_OK && b==&bus_token && calls==before);
}

static void *write_pin(void *arg)
{ assert(bsp_io_expander_set_level((int)(intptr_t)arg,0)==ESP_OK);return NULL; }

int main(int argc,char **argv)
{
    assert(argc>=2);
    if(strcmp(argv[1],"retry")==0) {
        fail_step=3;assert(bsp_io_expander_init()==ESP_FAIL);
        fail_step=0;success();return 0;
    }
    if(strcmp(argv[1],"concurrent")==0) {
        success();pause_write=true;pthread_t first,second;
        assert(pthread_create(&first,NULL,write_pin,(void *)(intptr_t)0)==0);
        pthread_mutex_lock(&gate);while(!write_waiting)pthread_cond_wait(&changed,&gate);pthread_mutex_unlock(&gate);
        assert(pthread_create(&second,NULL,write_pin,(void *)(intptr_t)1)==0);
        pthread_mutex_lock(&gate);while(!mutex_waiter)pthread_cond_wait(&changed,&gate);
        release_write=true;pthread_cond_broadcast(&changed);pthread_mutex_unlock(&gate);
        assert(pthread_join(first,NULL)==0 && pthread_join(second,NULL)==0);
        assert(registers[2]==0xfc);return 0;
    }
    if(strcmp(argv[1],"lock-timeout")==0) {
        success();lock_timeout=true;int before=calls,level=42,written=writes;
        assert(bsp_io_expander_set_direction(0,1)==ESP_ERR_TIMEOUT);
        assert(bsp_io_expander_set_level(0,0)==ESP_ERR_TIMEOUT);
        assert(bsp_io_expander_get_level(0,&level)==ESP_ERR_TIMEOUT && level==42);
        assert(calls==before && writes==written);lock_timeout=false;success();return 0;
    }
    if(strcmp(argv[1],"shadow-output")==0 || strcmp(argv[1],"shadow-config")==0) {
        success();write_applied=argc>2 && atoi(argv[2]);
        bool direction=strcmp(argv[1],"shadow-config")==0;
        for(int port=0;port<2;port++) {
            int pin=port*8, reg=(direction?6:2)+port;
            fail_write=true;
            assert((direction?bsp_io_expander_set_direction(pin,1):bsp_io_expander_set_level(pin,0))==ESP_FAIL);
            fail_write=false;
            /* A failed transfer may or may not have reached the chip. A failed
             * resync must not issue another write based on a stale shadow. */
            fail_step=direction?reg:reg+2;int before=writes;
            assert((direction?bsp_io_expander_set_direction(pin+1,1):bsp_io_expander_set_level(pin+1,0))==ESP_FAIL);
            assert(writes==before);fail_step=0;
            assert((direction?bsp_io_expander_set_direction(pin+1,1):bsp_io_expander_set_level(pin+1,0))==ESP_OK);
            assert(registers[reg]==(write_applied?0xfc:0xfd));
        }
        return 0;
    }
    fail_step=atoi(argv[1]);cleanup_failure=argc>2 ? atoi(argv[2]) : 0;
    if(!fail_step) { success();return 0; }
    assert(bsp_io_expander_init()==(fail_step==10?ESP_ERR_NO_MEM:ESP_FAIL));
    int level;
    assert(bsp_io_expander_get_level(0,&level)==ESP_ERR_INVALID_STATE);
    assert(bsp_io_expander_set_direction(0,1)==ESP_ERR_INVALID_STATE);
    assert(bsp_io_expander_set_level(0,1)==ESP_ERR_INVALID_STATE);
    if(cleanup_failure) {
        assert(bus);int before=calls;fail_step=0;cleanup_failure=0;
        i2c_master_bus_handle_t b=(void *)1;
        assert(bsp_i2c0_get_bus(&b)==ESP_ERR_INVALID_STATE && !b);
        assert(calls==before);
    } else {
        assert(!bus && !device && !mutex_alive);fail_step=0;success();
    }
    return 0;
}
