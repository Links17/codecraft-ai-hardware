/* SPDX-License-Identifier: Apache-2.0 */
#include "audio_stub.h"
#include "bsp_audio.h"
#include "bsp_io_expander.h"
#include "bsp_pins.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>

enum { EXP=1,DIR,RAIL,BUS,CHANNELS,TX_INIT,TX_ENABLE,RX_INIT,RX_ENABLE,
       DATA,GPIO,SPK_CTRL,SPK_CODEC,SPK_DEV,PROBE,MIC_CTRL,MIC_CODEC,MIC_DEV,
       OPEN_SPK,OPEN_MIC,GAIN,DEL_MIC_CODEC,DEL_MIC_CTRL,DEL_SPK_CODEC,
       DEL_SPK_CTRL,DEL_GPIO,DEL_DATA,RX_DISABLE,RX_DELETE,TX_DISABLE,TX_DELETE,VOLUME,MUTE };
static int fault,cleanup_failure,calls,bus_token;
static bool alternate, gain_set;
static fake_channel_t tx={.direction=0},rx={.direction=1};
static fake_interface_t data,gpio,spk_ctrl,spk_codec,mic_ctrl,mic_codec;
static fake_codec_device_t speaker={.direction=0},mic={.direction=1};
static esp_err_t step(int n)
{ calls++;return n==fault || n==cleanup_failure ? ESP_FAIL : ESP_OK; }
#define TRY(n) do { esp_err_t err=step(n);if(err!=ESP_OK)return err; } while(0)
static const fake_interface_t *acquire(fake_interface_t *object,int n)
{ assert(!object->live);if(step(n)!=ESP_OK)return NULL;object->live=true;object->kind=n;return object; }
static int release(const fake_interface_t *object,int n)
{ assert(object && object->live);((fake_interface_t *)object)->live=false;return step(n); }
esp_err_t bsp_io_expander_init(void) { return step(EXP); }
esp_err_t bsp_io_expander_set_direction(int pin,int output)
{ assert(pin==BSP_EXP_PIN_PWR_CODEC_PA && output==1);return step(DIR); }
esp_err_t bsp_io_expander_set_level(int pin,int level)
{ assert(pin==BSP_EXP_PIN_PWR_CODEC_PA && level==1);return step(RAIL); }
esp_err_t bsp_i2c0_get_bus(i2c_master_bus_handle_t *out)
{ TRY(BUS);*out=&bus_token;return ESP_OK; }
esp_err_t i2c_master_probe(i2c_master_bus_handle_t bus,int addr,int timeout)
{ assert(bus==&bus_token && addr==0x13 && timeout==100);TRY(PROBE);return alternate?ESP_FAIL:ESP_OK; }
esp_err_t i2s_new_channel(const i2s_chan_config_t *cfg,i2s_chan_handle_t *out_tx,i2s_chan_handle_t *out_rx)
{ assert(!tx.live && !rx.live && cfg->id==I2S_NUM_0);TRY(CHANNELS);tx.live=rx.live=true;*out_tx=&tx;*out_rx=&rx;return ESP_OK; }
esp_err_t i2s_channel_init_std_mode(i2s_chan_handle_t h,const i2s_std_config_t *cfg)
{
    assert(h->live && !h->initialized && !h->enabled);
    assert(cfg->clk_cfg.sample_rate==BSP_AUDIO_SAMPLE_RATE && cfg->gpio_cfg.mclk==BSP_PIN_I2S_MCLK);
    if(h==&rx)assert(cfg->slot_cfg.slot_mask==I2S_STD_SLOT_RIGHT);
    TRY(h==&tx?TX_INIT:RX_INIT);h->initialized=true;return ESP_OK;
}
esp_err_t i2s_channel_enable(i2s_chan_handle_t h)
{ assert(h->live && h->initialized && !h->enabled);TRY(h==&tx?TX_ENABLE:RX_ENABLE);h->enabled=true;return ESP_OK; }
esp_err_t i2s_channel_disable(i2s_chan_handle_t h)
{
    assert(h->live);TRY(h==&rx?RX_DISABLE:TX_DISABLE);
    if(!h->enabled)return ESP_ERR_INVALID_STATE;
    h->enabled=false;return ESP_OK;
}
esp_err_t i2s_del_channel(i2s_chan_handle_t h)
{ assert(h->live && !h->enabled && !data.live);TRY(h==&rx?RX_DELETE:TX_DELETE);h->live=h->initialized=false;return ESP_OK; }
const audio_codec_data_if_t *audio_codec_new_i2s_data(audio_codec_i2s_cfg_t *cfg)
{ assert(cfg->rx_handle==&rx && cfg->tx_handle==&tx && rx.enabled && tx.enabled);return acquire(&data,DATA); }
const audio_codec_gpio_if_t *audio_codec_new_gpio(void) { return acquire(&gpio,GPIO); }
const audio_codec_ctrl_if_t *audio_codec_new_i2c_ctrl(audio_codec_i2c_cfg_t *cfg)
{
    assert(cfg->bus_handle==&bus_token);
    if(cfg->addr==0x30)return acquire(&spk_ctrl,SPK_CTRL);
    assert(cfg->addr==(alternate?0x14:0x13));return acquire(&mic_ctrl,MIC_CTRL);
}
const audio_codec_if_t *es8311_codec_new(es8311_codec_cfg_t *cfg)
{ assert(cfg->ctrl_if==&spk_ctrl && spk_ctrl.live && cfg->gpio_if==&gpio && gpio.live);return acquire(&spk_codec,SPK_CODEC); }
const audio_codec_if_t *es7243_codec_new(es7243_codec_cfg_t *cfg)
{ assert(!alternate && cfg->ctrl_if==&mic_ctrl && mic_ctrl.live);return acquire(&mic_codec,MIC_CODEC); }
const audio_codec_if_t *es7243e_codec_new(es7243e_codec_cfg_t *cfg)
{ assert(alternate && cfg->ctrl_if==&mic_ctrl && mic_ctrl.live);return acquire(&mic_codec,MIC_CODEC); }
esp_codec_dev_handle_t esp_codec_dev_new(esp_codec_dev_cfg_t *cfg)
{
    assert(data.live && cfg->data_if==&data && cfg->codec_if->live);
    fake_codec_device_t *dev=cfg->dev_type==ESP_CODEC_DEV_TYPE_OUT?&speaker:&mic;
    assert(!dev->live);
    if(step(dev==&speaker?SPK_DEV:MIC_DEV)!=ESP_OK)return NULL;
    dev->live=true;return dev;
}
int esp_codec_dev_open(esp_codec_dev_handle_t dev,esp_codec_dev_sample_info_t *cfg)
{
    assert(dev->live && !dev->opened && data.live && cfg->sample_rate==BSP_AUDIO_SAMPLE_RATE);
    TRY(dev==&speaker?OPEN_SPK:OPEN_MIC);dev->opened=true;return ESP_CODEC_DEV_OK;
}
void esp_codec_dev_delete(esp_codec_dev_handle_t dev)
{
    assert(dev->live && data.live && (dev==&speaker?spk_codec.live:mic_codec.live));
    /* Pinned SDK delete closes the device; close may already disable I2S.
     * It frees this device but does not free its borrowed interfaces. */
    if(dev->opened)(dev==&speaker?&tx:&rx)->enabled=false;
    dev->live=dev->opened=false;
}
int audio_codec_delete_codec_if(const audio_codec_if_t *h)
{
    if(h==&mic_codec) { assert(!mic.live && mic_ctrl.live);return release(h,DEL_MIC_CODEC); }
    assert(h==&spk_codec && !speaker.live && spk_ctrl.live && gpio.live);return release(h,DEL_SPK_CODEC);
}
int audio_codec_delete_ctrl_if(const audio_codec_ctrl_if_t *h)
{
    if(h==&mic_ctrl) { assert(!mic_codec.live);return release(h,DEL_MIC_CTRL); }
    assert(h==&spk_ctrl && !spk_codec.live);return release(h,DEL_SPK_CTRL);
}
int audio_codec_delete_gpio_if(const audio_codec_gpio_if_t *h)
{ assert(h==&gpio && !spk_codec.live);return release(h,DEL_GPIO); }
int audio_codec_delete_data_if(const audio_codec_data_if_t *h)
{ assert(h==&data && !speaker.live && !mic.live);return release(h,DEL_DATA); }
int esp_codec_dev_set_in_gain(esp_codec_dev_handle_t h,float gain)
{ assert(h==&mic && mic.live && mic.opened && gain==BSP_AUDIO_MIC_GAIN_DB);TRY(GAIN);gain_set=true;return ESP_CODEC_DEV_OK; }
int esp_codec_dev_set_out_vol(esp_codec_dev_handle_t h,int percent)
{ assert(h==&speaker && speaker.live && speaker.opened && percent>=0 && percent<=100);return step(VOLUME); }
int esp_codec_dev_set_out_mute(esp_codec_dev_handle_t h,bool mute)
{ (void)mute;assert(h==&speaker && speaker.live && speaker.opened);return step(MUTE); }
static void clean(void)
{ assert(!tx.live && !rx.live && !data.live && !gpio.live && !spk_ctrl.live && !spk_codec.live && !speaker.live && !mic_ctrl.live && !mic_codec.live && !mic.live); }
static void success(void)
{
    assert(bsp_audio_init()==ESP_OK);
    assert(bsp_audio_get_speaker()==&speaker && bsp_audio_get_mic()==&mic);
    assert(speaker.opened && mic.opened && tx.enabled && rx.enabled && gain_set);
    int before=calls;assert(bsp_audio_init()==ESP_OK && before==calls);
    assert(bsp_audio_set_volume(50)==ESP_OK && bsp_audio_set_mute(false)==ESP_OK);
}
int main(int argc,char **argv)
{
    assert(argc>=2);
    assert(!bsp_audio_get_speaker() && !bsp_audio_get_mic());
    assert(bsp_audio_set_volume(50)==ESP_ERR_INVALID_STATE && bsp_audio_set_mute(false)==ESP_ERR_INVALID_STATE);
    if(!strcmp(argv[1],"retry-ready") || !strcmp(argv[1],"retry-channel")) {
        fault=!strcmp(argv[1],"retry-ready")?OPEN_SPK:TX_INIT;
        assert(bsp_audio_init()==ESP_FAIL);fault=0;success();return 0;
    }
    if(!strcmp(argv[1],"controls")) {
        success();int before=calls;
        assert(bsp_audio_set_volume(-1)==ESP_ERR_INVALID_ARG && bsp_audio_set_volume(101)==ESP_ERR_INVALID_ARG && calls==before);
        fault=VOLUME;assert(bsp_audio_set_volume(50)==ESP_FAIL);
        fault=MUTE;assert(bsp_audio_set_mute(true)==ESP_FAIL);fault=0;success();return 0;
    }
    if(!strcmp(argv[1],"variant-e")) { alternate=true;success();return 0; }
    fault=atoi(argv[1]);cleanup_failure=argc>2?atoi(argv[2]):0;alternate=argc>3;
    if(!fault) { success();return 0; }
    assert(bsp_audio_init()==ESP_FAIL);
    assert(!bsp_audio_get_speaker() && !bsp_audio_get_mic());
    assert(bsp_audio_set_volume(50)==ESP_ERR_INVALID_STATE && bsp_audio_set_mute(true)==ESP_ERR_INVALID_STATE);
    if(cleanup_failure) {
        int before=calls;fault=cleanup_failure=0;
        assert(bsp_audio_init()==ESP_ERR_INVALID_STATE && calls==before);
    } else { clean();fault=0;success(); }
    return 0;
}
