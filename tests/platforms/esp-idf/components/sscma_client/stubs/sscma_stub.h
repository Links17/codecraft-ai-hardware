/* SPDX-License-Identifier: Apache-2.0
 * Narrow host doubles for SSCMA lifecycle tests. Constants are API identities,
 * not hardware facts. The tests do not emulate a camera or parse real JSON. */
#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
typedef int esp_err_t;
enum { ESP_OK=0, ESP_FAIL=-1, ESP_ERR_NO_MEM=0x101, ESP_ERR_INVALID_ARG=0x102,
       ESP_ERR_INVALID_STATE=0x103, ESP_ERR_NOT_SUPPORTED=0x106,
       ESP_ERR_TIMEOUT=0x107, ESP_ERR_INVALID_RESPONSE=0x108 };
#define ESP_RETURN_ON_ERROR(call, tag, ...) do { (void)(tag);esp_err_t e_=(call);if(e_!=ESP_OK)return e_; } while(0)
#define ESP_RETURN_ON_FALSE(test, error, tag, ...) do { (void)(tag);if(!(test))return (error); } while(0)
#define ESP_GOTO_ON_ERROR(call, label, tag, ...) do { (void)(tag);ret=(call);if(ret!=ESP_OK)goto label; } while(0)
static inline void stub_log(const char *tag,const char *fmt,...) { (void)tag;(void)fmt; }
#define ESP_LOGI stub_log
#define ESP_LOGW stub_log
#define ESP_LOGE stub_log
#define ESP_LOGD stub_log
static inline const char *esp_err_to_name(esp_err_t error){(void)error;return "injected";}
typedef int spi_host_device_t;
typedef void *spi_device_handle_t;
typedef struct {int sclk_io_num,mosi_io_num,miso_io_num,quadwp_io_num,quadhd_io_num,max_transfer_sz;} spi_bus_config_t;
typedef struct {int clock_speed_hz,mode,input_delay_ns,cs_ena_pretrans,spics_io_num,queue_size;} spi_device_interface_config_t;
typedef struct {size_t length,rxlength;const void *tx_buffer;void *rx_buffer;} spi_transaction_t;
enum {SPI_DMA_CH_AUTO=1,MALLOC_CAP_DMA=2,MALLOC_CAP_SPIRAM=4,MALLOC_CAP_8BIT=8,ESP_PM_NO_LIGHT_SLEEP=1};
esp_err_t spi_bus_initialize(spi_host_device_t host,const spi_bus_config_t *cfg,int dma);
esp_err_t spi_bus_add_device(spi_host_device_t host,const spi_device_interface_config_t *cfg,spi_device_handle_t *out);
esp_err_t spi_bus_remove_device(spi_device_handle_t handle);
esp_err_t spi_device_transmit(spi_device_handle_t handle,spi_transaction_t *transaction);
typedef void *esp_pm_lock_handle_t;
esp_err_t esp_pm_lock_create(int type,int arg,const char *name,esp_pm_lock_handle_t *out);
esp_err_t esp_pm_lock_delete(esp_pm_lock_handle_t handle);
esp_err_t esp_pm_lock_acquire(esp_pm_lock_handle_t handle);
esp_err_t esp_pm_lock_release(esp_pm_lock_handle_t handle);
int64_t esp_timer_get_time(void);
void *heap_caps_malloc(size_t size,int caps);
void test_free(void *ptr);
typedef unsigned TickType_t;
typedef void *SemaphoreHandle_t;
#define pdMS_TO_TICKS(ms) ((TickType_t)(ms))
#define portMAX_DELAY ((TickType_t)-1)
#define pdTRUE 1
#define pdPASS 1
void vTaskDelay(TickType_t ticks);
SemaphoreHandle_t xSemaphoreCreateBinary(void);
int xSemaphoreTake(SemaphoreHandle_t sem,TickType_t ticks);
int xSemaphoreGive(SemaphoreHandle_t sem);
int xTaskCreateWithCaps(void (*fn)(void *),const char *name,unsigned stack,void *arg,int priority,void *out,int caps);
void vTaskDeleteWithCaps(void *task);
typedef struct {int kind,valueint;const char *string;} cJSON;
cJSON *cJSON_Parse(const char *text);
void cJSON_Delete(cJSON *json);
cJSON *cJSON_GetObjectItem(const cJSON *json,const char *name);
const char *cJSON_GetStringValue(const cJSON *json);
bool cJSON_IsNumber(const cJSON *json);
int cJSON_GetArraySize(const cJSON *json);
cJSON *cJSON_GetArrayItem(const cJSON *json,int index);
int mbedtls_base64_decode(unsigned char *out,size_t size,size_t *written,const unsigned char *input,size_t length);
