/* SPDX-License-Identifier: Apache-2.0
 * Narrow codec/I2S double. Constants are SDK API identities for host tests. */
#pragma once
#include "idf_bsp_stub.h"
typedef struct { bool live, initialized, enabled; int direction; } fake_channel_t;
typedef fake_channel_t *i2s_chan_handle_t;
typedef struct { bool live; int kind; } fake_interface_t;
typedef fake_interface_t audio_codec_data_if_t;
typedef fake_interface_t audio_codec_ctrl_if_t;
typedef fake_interface_t audio_codec_gpio_if_t;
typedef fake_interface_t audio_codec_if_t;
typedef struct { bool live, opened; int direction; } fake_codec_device_t;
typedef fake_codec_device_t *esp_codec_dev_handle_t;
enum { I2S_NUM_0=0, I2S_ROLE_MASTER=0, I2S_DATA_BIT_WIDTH_16BIT=16,
       I2S_SLOT_MODE_MONO=1, I2S_STD_SLOT_RIGHT=2, GPIO_NUM_NC=-1,
       ESP_CODEC_DEV_WORK_MODE_DAC=1, ESP_CODEC_DEV_TYPE_OUT=1,
       ESP_CODEC_DEV_TYPE_IN=2, ESP_CODEC_DEV_OK=0 };
typedef struct { int id, role; } i2s_chan_config_t;
typedef struct { int sample_rate; } i2s_std_clk_config_t;
typedef struct { int bits, mode, slot_mask; } i2s_std_slot_config_t;
typedef struct {
    i2s_std_clk_config_t clk_cfg;
    i2s_std_slot_config_t slot_cfg;
    struct { int mclk,bclk,ws,dout,din;
             struct { bool mclk_inv,bclk_inv,ws_inv; } invert_flags; } gpio_cfg;
} i2s_std_config_t;
#define I2S_CHANNEL_DEFAULT_CONFIG(i,r) { .id=(i), .role=(r) }
#define I2S_STD_CLK_DEFAULT_CONFIG(rate) { .sample_rate=(rate) }
#define I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(b,m) { .bits=(b), .mode=(m) }
typedef struct { int port; i2s_chan_handle_t rx_handle,tx_handle; } audio_codec_i2s_cfg_t;
typedef struct { int addr; i2c_master_bus_handle_t bus_handle; } audio_codec_i2c_cfg_t;
typedef struct { float pa_voltage,codec_dac_voltage; } esp_codec_dev_hw_gain_t;
typedef struct {
    const audio_codec_ctrl_if_t *ctrl_if;
    const audio_codec_gpio_if_t *gpio_if;
    int codec_mode,pa_pin;
    bool pa_reverted,master_mode,use_mclk,digital_mic,invert_mclk,invert_sclk;
    esp_codec_dev_hw_gain_t hw_gain;
} es8311_codec_cfg_t;
typedef struct { const audio_codec_ctrl_if_t *ctrl_if; } es7243_codec_cfg_t;
typedef struct { const audio_codec_ctrl_if_t *ctrl_if; } es7243e_codec_cfg_t;
typedef struct { int dev_type; const audio_codec_if_t *codec_if;
                 const audio_codec_data_if_t *data_if; } esp_codec_dev_cfg_t;
typedef struct { int bits_per_sample,channel,sample_rate; } esp_codec_dev_sample_info_t;
esp_err_t i2s_new_channel(const i2s_chan_config_t *cfg,i2s_chan_handle_t *tx,i2s_chan_handle_t *rx);
esp_err_t i2s_channel_init_std_mode(i2s_chan_handle_t handle,const i2s_std_config_t *cfg);
esp_err_t i2s_channel_enable(i2s_chan_handle_t handle);
esp_err_t i2s_channel_disable(i2s_chan_handle_t handle);
esp_err_t i2s_del_channel(i2s_chan_handle_t handle);
const audio_codec_data_if_t *audio_codec_new_i2s_data(audio_codec_i2s_cfg_t *cfg);
const audio_codec_gpio_if_t *audio_codec_new_gpio(void);
const audio_codec_ctrl_if_t *audio_codec_new_i2c_ctrl(audio_codec_i2c_cfg_t *cfg);
const audio_codec_if_t *es8311_codec_new(es8311_codec_cfg_t *cfg);
const audio_codec_if_t *es7243_codec_new(es7243_codec_cfg_t *cfg);
const audio_codec_if_t *es7243e_codec_new(es7243e_codec_cfg_t *cfg);
esp_codec_dev_handle_t esp_codec_dev_new(esp_codec_dev_cfg_t *cfg);
int esp_codec_dev_open(esp_codec_dev_handle_t handle,esp_codec_dev_sample_info_t *cfg);
void esp_codec_dev_delete(esp_codec_dev_handle_t handle);
int audio_codec_delete_codec_if(const audio_codec_if_t *handle);
int audio_codec_delete_ctrl_if(const audio_codec_ctrl_if_t *handle);
int audio_codec_delete_gpio_if(const audio_codec_gpio_if_t *handle);
int audio_codec_delete_data_if(const audio_codec_data_if_t *handle);
int esp_codec_dev_set_in_gain(esp_codec_dev_handle_t handle,float gain);
int esp_codec_dev_set_out_vol(esp_codec_dev_handle_t handle,int percent);
int esp_codec_dev_set_out_mute(esp_codec_dev_handle_t handle,bool mute);
