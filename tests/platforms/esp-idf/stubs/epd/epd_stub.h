/* SPDX-License-Identifier: Apache-2.0
 * Narrow e-paper lifecycle/transfer doubles. Constants below are API IDs. */
#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
typedef int esp_err_t;
enum {ESP_OK=0,ESP_FAIL=-1,ESP_ERR_NO_MEM=0x101,ESP_ERR_INVALID_ARG=0x102,
      ESP_ERR_INVALID_STATE=0x103,ESP_ERR_TIMEOUT=0x107};
typedef void *spi_device_handle_t;
enum {GPIO_MODE_INPUT=0,GPIO_MODE_OUTPUT=1,GPIO_PULLUP_ENABLE=1,SPI2_HOST=1,SPI_DMA_CH_AUTO=2,MALLOC_CAP_DMA=4};
typedef struct {uint64_t pin_bit_mask;int mode,pull_up_en;} gpio_config_t;
typedef struct {int sclk_io_num,mosi_io_num,miso_io_num,quadwp_io_num,quadhd_io_num,max_transfer_sz;} spi_bus_config_t;
typedef struct {int mode,clock_speed_hz,spics_io_num,queue_size;} spi_device_interface_config_t;
typedef struct {size_t length;const void *tx_buffer;} spi_transaction_t;
esp_err_t gpio_config(const gpio_config_t *cfg);
esp_err_t gpio_set_level(int pin,int level);
int gpio_get_level(int pin);
esp_err_t spi_bus_initialize(int host,const spi_bus_config_t *cfg,int dma);
esp_err_t spi_bus_add_device(int host,const spi_device_interface_config_t *cfg,spi_device_handle_t *out);
esp_err_t spi_device_polling_transmit(spi_device_handle_t dev,spi_transaction_t *transaction);
void *heap_caps_malloc(size_t size,int caps);
void test_free(void *ptr);
int64_t esp_timer_get_time(void);
#define pdMS_TO_TICKS(ms) (ms)
void vTaskDelay(unsigned ticks);
static inline void stub_log(const char *tag,const char *fmt,...){(void)tag;(void)fmt;}
#define ESP_LOGI stub_log
#define ESP_LOGE stub_log
static inline const char *esp_err_to_name(esp_err_t error){(void)error;return "injected";}
