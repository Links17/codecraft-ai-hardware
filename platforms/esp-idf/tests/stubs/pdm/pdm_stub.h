/* SPDX-License-Identifier: Apache-2.0
 * Narrow native-I2S lifecycle doubles. Constants are API identities, not pins. */
#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
typedef int esp_err_t;
enum { ESP_OK=0, ESP_FAIL=-1, ESP_ERR_INVALID_ARG=0x102, ESP_ERR_INVALID_STATE=0x103,
       ESP_ERR_TIMEOUT=0x107 };
typedef void *i2s_chan_handle_t;
typedef struct {int id,role;} i2s_chan_config_t;
typedef struct {
    struct {uint32_t sample_rate_hz;} clk_cfg;
    struct {int data_bit_width,slot_mode;} slot_cfg;
    struct {int clk,din;struct {bool clk_inv;} invert_flags;} gpio_cfg;
} i2s_pdm_rx_config_t;
enum { I2S_NUM_0=0,I2S_ROLE_MASTER=1,I2S_DATA_BIT_WIDTH_16BIT=16,I2S_SLOT_MODE_MONO=1,
       GPIO_MODE_OUTPUT=1,GPIO_PULLUP_DISABLE=0,GPIO_PULLDOWN_DISABLE=0,GPIO_INTR_DISABLE=0 };
#define I2S_CHANNEL_DEFAULT_CONFIG(port,role_) ((i2s_chan_config_t){.id=(port),.role=(role_)})
#define I2S_PDM_RX_CLK_DEFAULT_CONFIG(rate) {.sample_rate_hz=(rate)}
#define I2S_PDM_RX_SLOT_DEFAULT_CONFIG(width,mode) {.data_bit_width=(width),.slot_mode=(mode)}
/* A 10 ms tick makes accidental tick-to-millisecond substitutions visible. */
#define pdMS_TO_TICKS(ms) ((ms)/10)
#define ESP_RETURN_ON_ERROR(call,tag,...) do {(void)(tag);esp_err_t e_=(call);if(e_!=ESP_OK)return e_;}while(0)
#define ESP_GOTO_ON_ERROR(call,label,tag,...) do {(void)(tag);ret=(call);if(ret!=ESP_OK)goto label;}while(0)
typedef struct {uint64_t pin_bit_mask;int mode,pull_up_en,pull_down_en,intr_type;} gpio_config_t;
esp_err_t gpio_config(const gpio_config_t *cfg);
esp_err_t gpio_set_level(int pin,int level);
esp_err_t i2s_new_channel(const i2s_chan_config_t *cfg,i2s_chan_handle_t *tx,i2s_chan_handle_t *rx);
esp_err_t i2s_channel_init_pdm_rx_mode(i2s_chan_handle_t channel,const i2s_pdm_rx_config_t *cfg);
esp_err_t i2s_channel_enable(i2s_chan_handle_t channel);
esp_err_t i2s_channel_disable(i2s_chan_handle_t channel);
esp_err_t i2s_del_channel(i2s_chan_handle_t channel);
esp_err_t i2s_channel_read(i2s_chan_handle_t channel,void *buffer,size_t bytes,size_t *out,uint32_t timeout_ms);
