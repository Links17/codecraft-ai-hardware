/* SPDX-License-Identifier: Apache-2.0
 * Actual TCA9535 BSP logic: rollback, shadow recovery and serialized updates. */
#include "bsp_io_expander.h"
#include "bsp_pins.h"
#include "lcd_stub.h"
#include <assert.h>
#include <pthread.h>
#include <stdlib.h>
#include <string.h>

static int failure,cleanup_failure,calls,bus_object,dev_object;
static bool bus_live,dev_live,mutex_live,ready,fallback,missing,write_applied,deny_lock;
static uint8_t registers[8]={0x5a,0xa5,0xff,0xff,0,0,0xff,0xff};
static pthread_mutex_t lock=PTHREAD_MUTEX_INITIALIZER,gate=PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t condition=PTHREAD_COND_INITIALIZER;
static bool hold_write,in_write,second_waiting,release_write;
static int thread_takes;
static esp_err_t step(int n)
{
    ++calls;
    if(failure==n){failure=0;return ESP_FAIL;}
    if(cleanup_failure==n){cleanup_failure=0;return ESP_FAIL;}
    return ESP_OK;
}
SemaphoreHandle_t xSemaphoreCreateMutex(void)
{
    assert(!mutex_live);if(step(1)!=ESP_OK)return NULL;
    mutex_live=true;return &lock;
}
int xSemaphoreTake(SemaphoreHandle_t mutex,TickType_t wait)
{
    assert(mutex==&lock&&mutex_live&&wait==pdMS_TO_TICKS(100));
    if(deny_lock)return 0;
    pthread_mutex_lock(&gate);
    if(hold_write&&++thread_takes==2){second_waiting=true;pthread_cond_broadcast(&condition);}
    pthread_mutex_unlock(&gate);
    assert(pthread_mutex_lock(&lock)==0);return pdTRUE;
}
void xSemaphoreGive(SemaphoreHandle_t mutex){assert(mutex==&lock);assert(pthread_mutex_unlock(&lock)==0);}
void vSemaphoreDelete(SemaphoreHandle_t mutex){assert(mutex==&lock&&mutex_live&&!bus_live&&!dev_live);mutex_live=false;}
esp_err_t i2c_new_master_bus(const i2c_master_bus_config_t *c,i2c_master_bus_handle_t *out)
{
    assert(!bus_live&&mutex_live);
    assert(c->i2c_port==-1&&c->sda_io_num==BSP_PIN_I2C_SDA&&c->scl_io_num==BSP_PIN_I2C_SCL&&c->flags.enable_internal_pullup&&c->glitch_ignore_cnt==7);
    esp_err_t ret=step(2);if(ret==ESP_OK){bus_live=true;*out=&bus_object;}return ret;
}
esp_err_t i2c_master_probe(i2c_master_bus_handle_t bus,int addr,int timeout)
{
    assert(bus==&bus_object&&bus_live&&!dev_live&&timeout==100);
    bool primary=addr==BSP_I2C_ADDR_EXPANDER_PRIMARY;
    assert(primary||addr==BSP_I2C_ADDR_EXPANDER_FALLBACK);
    esp_err_t ret=step(primary?3:4);if(ret!=ESP_OK)return ret;
    return missing||(primary&&fallback)?ESP_ERR_NOT_FOUND:ESP_OK;
}
esp_err_t i2c_master_bus_add_device(i2c_master_bus_handle_t bus,const i2c_device_config_t *c,i2c_master_dev_handle_t *out)
{
    assert(bus==&bus_object&&bus_live&&!dev_live);
    assert(c->device_address==(fallback?BSP_I2C_ADDR_EXPANDER_FALLBACK:BSP_I2C_ADDR_EXPANDER_PRIMARY));
    assert(c->scl_speed_hz==BSP_I2C_FREQ_HZ&&c->dev_addr_length==I2C_ADDR_BIT_LEN_7);
    esp_err_t ret=step(5);if(ret==ESP_OK){dev_live=true;*out=&dev_object;}return ret;
}
esp_err_t i2c_master_bus_rm_device(i2c_master_dev_handle_t dev)
{
    assert(dev==&dev_object&&dev_live&&bus_live);
    esp_err_t ret=step(10);if(ret==ESP_OK)dev_live=false;return ret;
}
esp_err_t i2c_del_master_bus(i2c_master_bus_handle_t bus)
{
    assert(bus==&bus_object&&bus_live&&!dev_live);
    esp_err_t ret=step(11);if(ret==ESP_OK)bus_live=false;return ret;
}
esp_err_t i2c_master_transmit_receive(i2c_master_dev_handle_t dev,const uint8_t *tx,size_t tn,uint8_t *rx,size_t rn,int timeout)
{
    assert(dev==&dev_object&&dev_live&&tn==1&&rn==1&&*tx<8&&timeout==100);
    int stage=ready?20:(*tx<4?4+*tx:2+*tx);
    esp_err_t ret=step(stage);if(ret==ESP_OK)*rx=registers[*tx];return ret;
}
esp_err_t i2c_master_transmit(i2c_master_dev_handle_t dev,const uint8_t *tx,size_t size,int timeout)
{
    assert(dev==&dev_object&&dev_live&&ready&&size==2&&tx[0]<8&&timeout==100);
    pthread_mutex_lock(&gate);
    if(hold_write&&!in_write){in_write=true;pthread_cond_broadcast(&condition);while(!release_write)pthread_cond_wait(&condition,&gate);}
    pthread_mutex_unlock(&gate);
    esp_err_t ret=step(21);if(ret==ESP_OK||write_applied)registers[tx[0]]=tx[1];return ret;
}
static void *write_pin(void *arg)
{
    assert(bsp_io_expander_set_level((int)(intptr_t)arg,0)==ESP_OK);return NULL;
}
int main(int argc,char **argv)
{
    assert(argc>=2);const char *mode=argv[1];
    int value=7;
    assert(bsp_io_expander_set_level(0,0)==ESP_ERR_INVALID_STATE);
    assert(bsp_io_expander_set_direction(0,1)==ESP_ERR_INVALID_STATE);
    assert(bsp_io_expander_get_level(0,&value)==ESP_ERR_INVALID_STATE&&value==7);
    assert(bsp_i2c_get_bus(NULL)==ESP_ERR_INVALID_ARG&&calls==0);
    failure=atoi(mode);cleanup_failure=failure&&argc>2?atoi(argv[2]):0;
    fallback=!strcmp(mode,"fallback");missing=!strcmp(mode,"missing");
    int expected=failure,cleanup=cleanup_failure;
    esp_err_t ret=bsp_io_expander_init();
    if(expected||missing){
        assert(ret!=ESP_OK&&failure==0);
        assert(bsp_io_expander_get_level(0,&value)==ESP_ERR_INVALID_STATE&&value==7);
        if(cleanup){
            assert(cleanup_failure==0&&bus_live&&mutex_live);
            int prior=calls;i2c_master_bus_handle_t bus=(void *)1;
            assert(bsp_i2c_get_bus(&bus)==ESP_ERR_INVALID_STATE&&bus==NULL&&calls==prior);return 0;
        }
        assert(!bus_live&&!dev_live&&!mutex_live);missing=false;
        assert(bsp_io_expander_init()==ESP_OK);
    }else assert(ret==ESP_OK);
    ready=true;
    int prior=calls;i2c_master_bus_handle_t bus=NULL;
    assert(bsp_io_expander_init()==ESP_OK&&bsp_i2c_get_bus(&bus)==ESP_OK&&bus==&bus_object&&calls==prior);
    assert(bsp_io_expander_set_level(-1,0)==ESP_ERR_INVALID_ARG&&bsp_io_expander_set_direction(16,1)==ESP_ERR_INVALID_ARG);
    assert(bsp_io_expander_get_level(0,NULL)==ESP_ERR_INVALID_ARG&&calls==prior);
    if(!strcmp(mode,"concurrent")){
        hold_write=true;pthread_t first,second;
        assert(pthread_create(&first,NULL,write_pin,(void *)(intptr_t)0)==0);
        pthread_mutex_lock(&gate);while(!in_write)pthread_cond_wait(&condition,&gate);pthread_mutex_unlock(&gate);
        assert(pthread_create(&second,NULL,write_pin,(void *)(intptr_t)1)==0);
        pthread_mutex_lock(&gate);while(!second_waiting)pthread_cond_wait(&condition,&gate);
        release_write=true;pthread_cond_broadcast(&condition);pthread_mutex_unlock(&gate);
        pthread_join(first,NULL);pthread_join(second,NULL);assert(registers[2]==0xfc);return 0;
    }
    if(!strcmp(mode,"lock-timeout")){
        deny_lock=true;
        assert(bsp_io_expander_set_level(0,0)==ESP_ERR_TIMEOUT);
        assert(bsp_io_expander_set_direction(0,1)==ESP_ERR_TIMEOUT);
        assert(bsp_io_expander_get_level(0,&value)==ESP_ERR_TIMEOUT&&value==7&&calls==prior);
        deny_lock=false;assert(bsp_io_expander_set_level(0,0)==ESP_OK);return 0;
    }
    if(!strncmp(mode,"shadow-",7)){
        bool direction=!strcmp(mode,"shadow-config");
        write_applied=argc>2&&atoi(argv[2]);cleanup_failure=0;
        int reg=direction?6:2;failure=21;
        assert((direction?bsp_io_expander_set_direction(0,1):bsp_io_expander_set_level(0,0))==ESP_FAIL);
        uint8_t actual=registers[reg];
        failure=20;
        assert((direction?bsp_io_expander_set_direction(1,1):bsp_io_expander_set_level(1,0))==ESP_FAIL&&registers[reg]==actual);
        assert((direction?bsp_io_expander_set_direction(1,1):bsp_io_expander_set_level(1,0))==ESP_OK);
        assert(registers[reg]==(write_applied?0xfc:0xfd));
    }
    failure=20;assert(bsp_io_expander_get_level(0,&value)==ESP_FAIL&&value==7);
    assert(bsp_io_expander_get_level(0,&value)==ESP_OK&&value==0);
    return 0;
}
