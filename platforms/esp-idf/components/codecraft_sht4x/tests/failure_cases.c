/* SPDX-License-Identifier: Apache-2.0 */
#include <assert.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "sensor_stub.h"

#ifdef TEST_BSP
#include "bsp_sht4x.h"
#include "bsp_pins.h"
#define initialize() bsp_sht4x_init()
#define read_sensor(t,h) bsp_sht4x_read(t,h)
#else
#include "codecraft_sht4x.h"
static codecraft_sht4x_handle_t sensor;
#define initialize() codecraft_sht4x_create(test_bus,&test_config,100,&sensor)
#define read_sensor(t,h) codecraft_sht4x_read(sensor,t,h)
#endif

static void *reader(void *unused)
{
    (void)unused;
    float t=-1,h=-1;
    assert(read_sensor(&t,&h)==ESP_OK);
    assert(fabsf(t-25.0f)<0.001f && fabsf(h-56.50095f)<0.001f);
    return NULL;
}

static void concurrent_reads(void)
{
    pthread_t first,second;
    pause_conversion=true;
    assert(pthread_create(&first,NULL,reader,NULL)==0);
    pthread_mutex_lock(&gate);
    while (!conversion_waiting) pthread_cond_wait(&changed,&gate);
    pthread_mutex_unlock(&gate);
    assert(pthread_create(&second,NULL,reader,NULL)==0);
    pthread_mutex_lock(&gate);
    while (!mutex_waiter) pthread_cond_wait(&changed,&gate);
    assert(commands==1 && receives==0);
    pthread_mutex_unlock(&gate);
    /* The first reader is still inside conversion, and the second is waiting
     * on its device mutex. A separate bus device must still make progress. */
    i2c_master_dev_handle_t other=NULL;
    i2c_device_config_t cfg=test_config; cfg.device_address=0x51;
    assert(i2c_master_bus_add_device(test_bus,&cfg,&other)==ESP_OK);
    uint8_t data=0;
    assert(i2c_master_transmit(other,&data,1,100)==ESP_OK && other_calls==1);
    assert(i2c_master_bus_rm_device(other)==ESP_OK);
    pthread_mutex_lock(&gate); release_conversion=true;
    pthread_cond_broadcast(&changed); pthread_mutex_unlock(&gate);
    assert(pthread_join(first,NULL)==0 && pthread_join(second,NULL)==0);
    assert(commands==2 && receives==2);
}

int main(int argc, char **argv)
{
    assert(argc==2);
    /* Fixed protocol vectors: raw T=26214 => 25 C, raw RH=32768 => 56.50095%. */
    memcpy(frame,(uint8_t[]){0x66,0x66,0x93,0x80,0x00,0xA2},6);
    float t=-123,h=-456;
    if (!strcmp(argv[1],"before-init")) {
        assert(read_sensor(&t,&h)==ESP_ERR_INVALID_STATE);
        assert(t==-123 && h==-456); return 0;
    }
#ifndef TEST_BSP
    if (!strcmp(argv[1],"invalid-create")) {
        assert(codecraft_sht4x_create(NULL,&test_config,100,&sensor)==ESP_ERR_INVALID_ARG);
        assert(codecraft_sht4x_create(test_bus,NULL,100,&sensor)==ESP_ERR_INVALID_ARG);
        assert(codecraft_sht4x_create(test_bus,&test_config,0,&sensor)==ESP_ERR_INVALID_ARG);
        assert(codecraft_sht4x_create(test_bus,&test_config,100,NULL)==ESP_ERR_INVALID_ARG);
        check_clean(); return 0;
    }
    int requested=atoi(argv[1]);
    if (requested>=ALLOC && requested<=ADD) {
        fault=requested;
        esp_err_t expected=requested==PROBE?ESP_ERR_NOT_FOUND:requested==ADD?ESP_FAIL:ESP_ERR_NO_MEM;
        assert(initialize()==expected && sensor==NULL); check_clean(); fault=0;
    }
#endif
#ifdef TEST_STICKY
    int requested=atoi(argv[1]);
    if ((requested>=ALLOC && requested<=ADD)||!strcmp(argv[1],"bus-failure")) {
        fault=requested?requested:10;
        assert(initialize()!=ESP_OK);check_clean();fault=0;
    }
#endif
    assert(initialize()==ESP_OK && devices==1);
    if (!strcmp(argv[1],"init")) {
#ifdef TEST_BSP
#ifdef TEST_STICKY
        assert(attached_address==BSP_I2C_ADDR_SHT4X && attached_speed==BSP_I2C1_FREQ_HZ && bus_creates==1);
#else
        assert(attached_address==BSP_I2C_ADDR_SHT4X && attached_speed==BSP_I2C0_FREQ_HZ);
#endif
        assert(initialize()==ESP_OK && devices==1);
#else
        codecraft_sht4x_handle_t saved=sensor;
        assert(initialize()==ESP_ERR_INVALID_ARG && sensor==saved && devices==1);
#endif
    } else if (!strcmp(argv[1],"concurrent")) {
        concurrent_reads();
    } else if (!strcmp(argv[1],"invalid-read")) {
        assert(read_sensor(NULL,&h)==ESP_ERR_INVALID_ARG);
        assert(read_sensor(&t,NULL)==ESP_ERR_INVALID_ARG);
        assert(commands==0);
    } else if (!strcmp(argv[1],"crc-temperature") || !strcmp(argv[1],"crc-humidity")) {
        size_t byte=!strcmp(argv[1],"crc-temperature")?2:5;
        frame[byte]^=1;
        assert(read_sensor(&t,&h)==ESP_ERR_INVALID_CRC && t==-123 && h==-456);
        frame[byte]^=1; reader(NULL);
    } else if (!strcmp(argv[1],"timeout-tx") || !strcmp(argv[1],"timeout-rx") || !strcmp(argv[1],"timeout-lock")) {
        fault=!strcmp(argv[1],"timeout-tx")?TRANSMIT:!strcmp(argv[1],"timeout-rx")?RECEIVE:LOCK;
        assert(read_sensor(&t,&h)==ESP_ERR_TIMEOUT && t==-123 && h==-456);
        fault=0; reader(NULL); /* error paths must release the device mutex */
    } else if (!strcmp(argv[1],"limits")) {
        memcpy(frame,(uint8_t[]){0,0,0x81,0,0,0x81},6);
        assert(read_sensor(&t,&h)==ESP_OK && t==-45.0f && h==0.0f);
        memcpy(frame,(uint8_t[]){255,255,0xAC,255,255,0xAC},6);
        assert(read_sensor(&t,&h)==ESP_OK && t==130.0f && h==100.0f);
    } else reader(NULL);
#ifndef TEST_BSP
    if (!strcmp(argv[1],"delete-failure")) {
        fault=REMOVE; codecraft_sht4x_handle_t saved=sensor;
        assert(codecraft_sht4x_delete(&sensor)==ESP_FAIL && sensor==saved);
        assert(devices==1 && allocations==1 && mutexes==1);
        fault=0; reader(NULL);
    }
    assert(codecraft_sht4x_delete(&sensor)==ESP_OK && sensor==NULL);
    assert(codecraft_sht4x_delete(&sensor)==ESP_ERR_INVALID_ARG);
    check_clean();
#endif
    return 0;
}
