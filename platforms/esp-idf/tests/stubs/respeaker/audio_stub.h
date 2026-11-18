/* SPDX-License-Identifier: Apache-2.0
 * Only the GPIO/I2C/I2S/RTOS interfaces used by the reSpeaker audio BSP. */
#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
typedef int esp_err_t;
enum {ESP_OK=0,ESP_FAIL=-1,ESP_ERR_NO_MEM=0x101,ESP_ERR_INVALID_ARG=0x102,
      ESP_ERR_INVALID_STATE=0x103,ESP_ERR_INVALID_SIZE=0x104,ESP_ERR_TIMEOUT=0x107,
      ESP_ERR_INVALID_RESPONSE=0x108};
typedef void *i2c_master_bus_handle_t;
typedef void *i2c_master_dev_handle_t;
typedef void *i2s_chan_handle_t;
typedef void *SemaphoreHandle_t;
typedef unsigned TickType_t;
enum {GPIO_MODE_OUTPUT=1,I2C_CLK_SRC_DEFAULT=0,I2C_ADDR_BIT_LEN_7=7,
      I2S_NUM_0=0,I2S_ROLE_SLAVE=0,I2S_DATA_BIT_WIDTH_32BIT=32,I2S_SLOT_MODE_STEREO=2,
      I2S_GPIO_UNUSED=-1,pdTRUE=1};
#define portMAX_DELAY UINT32_MAX
typedef struct {uint64_t pin_bit_mask;int mode;} gpio_config_t;
typedef struct {int i2c_port,sda_io_num,scl_io_num,clk_source,glitch_ignore_cnt;} i2c_master_bus_config_t;
typedef struct {int dev_addr_length,device_address,scl_speed_hz;} i2c_device_config_t;
typedef struct {int id,role,dma_desc_num,dma_frame_num;bool auto_clear;} i2s_chan_config_t;
typedef struct {int sample_rate_hz;} i2s_std_clk_config_t;
typedef struct {int data_bit_width,slot_mode;} i2s_std_slot_config_t;
typedef struct {i2s_std_clk_config_t clk_cfg;i2s_std_slot_config_t slot_cfg;
                struct {int mclk,bclk,ws,dout,din;} gpio_cfg;} i2s_std_config_t;
#define I2S_CHANNEL_DEFAULT_CONFIG(port,role_) ((i2s_chan_config_t){.id=(port),.role=(role_)})
#define I2S_STD_CLK_DEFAULT_CONFIG(rate) ((i2s_std_clk_config_t){.sample_rate_hz=(rate)})
#define I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(bits,mode) ((i2s_std_slot_config_t){.data_bit_width=(bits),.slot_mode=(mode)})
#define pdMS_TO_TICKS(ms) ((ms)/10)
esp_err_t gpio_config(const gpio_config_t *cfg);
esp_err_t gpio_set_level(int pin,int level);
void vTaskDelay(unsigned ticks);
SemaphoreHandle_t xSemaphoreCreateMutex(void);
int xSemaphoreTake(SemaphoreHandle_t mutex,TickType_t wait);
void xSemaphoreGive(SemaphoreHandle_t mutex);
void vSemaphoreDelete(SemaphoreHandle_t mutex);
esp_err_t i2c_new_master_bus(const i2c_master_bus_config_t *cfg,i2c_master_bus_handle_t *out);
esp_err_t i2c_master_bus_add_device(i2c_master_bus_handle_t bus,const i2c_device_config_t *cfg,i2c_master_dev_handle_t *out);
esp_err_t i2c_master_bus_rm_device(i2c_master_dev_handle_t dev);
esp_err_t i2c_del_master_bus(i2c_master_bus_handle_t bus);
esp_err_t i2c_master_transmit(i2c_master_dev_handle_t dev,const uint8_t *data,size_t size,int timeout);
esp_err_t i2c_master_receive(i2c_master_dev_handle_t dev,uint8_t *data,size_t size,int timeout);
esp_err_t i2s_new_channel(const i2s_chan_config_t *cfg,i2s_chan_handle_t *tx,i2s_chan_handle_t *rx);
esp_err_t i2s_channel_init_std_mode(i2s_chan_handle_t channel,const i2s_std_config_t *cfg);
esp_err_t i2s_channel_enable(i2s_chan_handle_t channel);
esp_err_t i2s_channel_disable(i2s_chan_handle_t channel);
esp_err_t i2s_del_channel(i2s_chan_handle_t channel);
esp_err_t i2s_channel_read(i2s_chan_handle_t channel,void *dest,size_t size,size_t *bytes,uint32_t timeout_ms);
esp_err_t i2s_channel_write(i2s_chan_handle_t channel,const void *src,size_t size,size_t *bytes,uint32_t timeout_ms);
static inline const char *esp_err_to_name(esp_err_t err){(void)err;return "injected";}
static inline void stub_log(const char *tag,const char *fmt,...){(void)tag;(void)fmt;}
#define ESP_LOGI stub_log
#define ESP_LOGE stub_log
#define ESP_RETURN_ON_ERROR(call,tag,...) do {esp_err_t e_=(call);if(e_!=ESP_OK){stub_log(tag,__VA_ARGS__);return e_;}} while(0)
#define ESP_RETURN_ON_FALSE(cond,err,tag,...) do {if(!(cond)){stub_log(tag,__VA_ARGS__);return (err);}} while(0)
#define ESP_GOTO_ON_ERROR(call,label,tag,...) do {ret=(call);if(ret!=ESP_OK){stub_log(tag,__VA_ARGS__);goto label;}} while(0)
