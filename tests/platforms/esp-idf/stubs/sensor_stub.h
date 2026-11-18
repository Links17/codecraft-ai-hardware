/* SPDX-License-Identifier: Apache-2.0
 * Narrow synchronous I2C / task / mutex doubles. API constants are test IDs. */
#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <pthread.h>

typedef int esp_err_t;
enum { ESP_OK=0, ESP_FAIL=-1, ESP_ERR_NO_MEM=0x101, ESP_ERR_INVALID_ARG=0x102,
       ESP_ERR_INVALID_STATE=0x103, ESP_ERR_NOT_FOUND=0x105,
       ESP_ERR_TIMEOUT=0x107, ESP_ERR_INVALID_RESPONSE=0x108, ESP_ERR_INVALID_CRC=0x109 };
typedef void *i2c_master_bus_handle_t;
typedef struct fake_device *i2c_master_dev_handle_t;
enum { I2C_ADDR_BIT_LEN_7=0, I2C_NUM_1=1, I2C_CLK_SRC_DEFAULT=0 };
typedef struct {int i2c_port,sda_io_num,scl_io_num,clk_source,glitch_ignore_cnt;
                struct {unsigned enable_internal_pullup:1;} flags;} i2c_master_bus_config_t;
typedef struct { int dev_addr_length, device_address, scl_speed_hz; } i2c_device_config_t;
esp_err_t i2c_new_master_bus(const i2c_master_bus_config_t *cfg,i2c_master_bus_handle_t *out);
esp_err_t i2c_master_probe(i2c_master_bus_handle_t bus, int addr, int timeout);
esp_err_t i2c_master_bus_add_device(i2c_master_bus_handle_t bus, const i2c_device_config_t *cfg, i2c_master_dev_handle_t *out);
esp_err_t i2c_master_bus_rm_device(i2c_master_dev_handle_t dev);
esp_err_t i2c_master_transmit(i2c_master_dev_handle_t dev, const uint8_t *data, size_t size, int timeout);
esp_err_t i2c_master_receive(i2c_master_dev_handle_t dev, uint8_t *data, size_t size, int timeout);
esp_err_t i2c_master_transmit_receive(i2c_master_dev_handle_t dev, const uint8_t *data, size_t size, uint8_t *out, size_t count, int timeout);

typedef unsigned TickType_t;
typedef pthread_mutex_t *SemaphoreHandle_t;
#define pdMS_TO_TICKS(ms) ((TickType_t)(ms))
#define pdTRUE 1
SemaphoreHandle_t xSemaphoreCreateMutex(void);
int xSemaphoreTake(SemaphoreHandle_t lock, TickType_t timeout);
void xSemaphoreGive(SemaphoreHandle_t lock);
void vSemaphoreDelete(SemaphoreHandle_t lock);
void vTaskDelay(TickType_t ticks);
void *test_calloc(size_t count, size_t size);
void test_free(void *ptr);

enum { ALLOC=1, MUTEX, PROBE, ADD, TRANSMIT, RECEIVE, REMOVE, LOCK, TRANSCEIVE };
extern int fault, allocations, mutexes, devices, commands, receives, other_calls;
extern int attached_address, attached_speed;
extern int bus_creates;
extern uint8_t frame[8], sent[8];
extern size_t sent_size;
extern const i2c_master_bus_handle_t test_bus;
extern const i2c_device_config_t test_config;
extern pthread_mutex_t gate;
extern pthread_cond_t changed;
extern bool pause_conversion, conversion_waiting, release_conversion, mutex_waiter;
void check_clean(void);
