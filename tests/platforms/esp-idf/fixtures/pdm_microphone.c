/* SPDX-License-Identifier: Apache-2.0
 * Shared scenarios instantiated by each Target's microphone test. Compile
 * against that Target's real BSP and pin header; no physical behavior is faked. */
#include "pdm_stub.h"
#include "bsp_mic.h"
#include "bsp_pins.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
enum { GPIO_CONFIG=1,POWER_ON,NEW,CONFIG,ENABLE,READ,DISABLE,DELETE,POWER_OFF };
static int fault,cleanup_fault,calls,token;
static bool allocated,configured,enabled,powered,disable_applied;
static uint32_t expected_rate=16000,last_timeout;
static esp_err_t step(int n){calls++;return fault==n||cleanup_fault==n?ESP_FAIL:ESP_OK;}
#define TRY(n) do{esp_err_t e=step(n);if(e!=ESP_OK)return e;}while(0)
esp_err_t gpio_config(const gpio_config_t *cfg)
{
#ifdef BSP_PIN_PDM_EN
    assert(cfg->pin_bit_mask==(1ULL<<BSP_PIN_PDM_EN)&&cfg->mode==GPIO_MODE_OUTPUT);
    return step(GPIO_CONFIG);
#else
    (void)cfg;assert(!"this Target has no BSP-controlled mic rail");return ESP_FAIL;
#endif
}
esp_err_t gpio_set_level(int pin,int level)
{
#ifdef BSP_PIN_PDM_EN
    assert(pin==BSP_PIN_PDM_EN);
    if(level){powered=true;return step(POWER_ON);} /* A failed write can apply. */
    assert(!allocated);TRY(POWER_OFF);powered=false;return ESP_OK;
#else
    (void)pin;(void)level;assert(!"unexpected rail write");return ESP_FAIL;
#endif
}
esp_err_t i2s_new_channel(const i2s_chan_config_t *cfg,i2s_chan_handle_t *tx,i2s_chan_handle_t *rx)
{
    assert(!allocated&&!tx&&rx&&cfg->id==I2S_NUM_0&&cfg->role==I2S_ROLE_MASTER);
#ifdef BSP_PIN_PDM_EN
    assert(powered);
#endif
    TRY(NEW);allocated=true;*rx=&token;return ESP_OK;
}
esp_err_t i2s_channel_init_pdm_rx_mode(i2s_chan_handle_t channel,const i2s_pdm_rx_config_t *cfg)
{
    assert(allocated&&!configured&&channel==&token&&cfg->clk_cfg.sample_rate_hz==expected_rate);
    assert(cfg->slot_cfg.data_bit_width==I2S_DATA_BIT_WIDTH_16BIT&&cfg->slot_cfg.slot_mode==I2S_SLOT_MODE_MONO);
    assert(cfg->gpio_cfg.clk==BSP_PIN_PDM_CLK&&cfg->gpio_cfg.din==BSP_PIN_PDM_DATA&&!cfg->gpio_cfg.invert_flags.clk_inv);
    TRY(CONFIG);configured=true;return ESP_OK;
}
esp_err_t i2s_channel_enable(i2s_chan_handle_t channel)
{assert(allocated&&configured&&!enabled&&channel==&token);TRY(ENABLE);enabled=true;return ESP_OK;}
esp_err_t i2s_channel_disable(i2s_chan_handle_t channel)
{
    assert(allocated&&channel==&token);
    if(!enabled)return ESP_ERR_INVALID_STATE;
    esp_err_t e=step(DISABLE);if(e==ESP_OK||disable_applied)enabled=false;return e;
}
esp_err_t i2s_del_channel(i2s_chan_handle_t channel)
{assert(allocated&&!enabled&&channel==&token);TRY(DELETE);allocated=configured=false;return ESP_OK;}
esp_err_t i2s_channel_read(i2s_chan_handle_t channel,void *buffer,size_t bytes,size_t *out,uint32_t timeout_ms)
{
    assert(allocated&&enabled&&channel==&token&&buffer&&out&&bytes==8);
    last_timeout=timeout_ms;((int16_t *)buffer)[0]=123;
    *out=fault==READ?4:8;return step(READ)==ESP_OK?ESP_OK:ESP_ERR_TIMEOUT;
}
static void read_ok(void)
{int16_t buffer[4]={0};size_t count=99;assert(bsp_mic_read(buffer,4,&count,123)==ESP_OK&&count==4&&buffer[0]==123&&last_timeout==123);}
static void clean(void){assert(!allocated&&!configured&&!enabled&&!powered);}
static void success(void)
{
    assert(bsp_mic_init(expected_rate)==ESP_OK);int before=calls;
    assert(bsp_mic_init(expected_rate)==ESP_OK&&calls==before);read_ok();
    assert(bsp_mic_deinit()==ESP_OK);clean();before=calls;
    assert(bsp_mic_deinit()==ESP_OK&&calls==before);
}
int main(int argc,char **argv)
{
    assert(argc>=2);int16_t buffer[4]={0};size_t count=99;
    if(!strcmp(argv[1],"timeout-units")){assert(bsp_mic_init(expected_rate)==ESP_OK);read_ok();return 0;}
    if(!strcmp(argv[1],"partial-read")){
        assert(bsp_mic_init(expected_rate)==ESP_OK);fault=READ;
        assert(bsp_mic_read(buffer,4,&count,123)==ESP_ERR_TIMEOUT&&count==2&&buffer[0]==123&&last_timeout==123);
        fault=0;read_ok();assert(bsp_mic_deinit()==ESP_OK);clean();return 0;
    }
    if(!strcmp(argv[1],"deinit")||!strcmp(argv[1],"disable-applied")){
        assert(bsp_mic_init(expected_rate)==ESP_OK);fault=atoi(argv[2]);disable_applied=!strcmp(argv[1],"disable-applied");
        assert(bsp_mic_deinit()==ESP_FAIL);int before=calls;
        assert(bsp_mic_init(expected_rate)==ESP_ERR_INVALID_STATE&&calls==before);
        assert(bsp_mic_read(buffer,4,&count,123)==ESP_ERR_INVALID_STATE&&count==0&&calls==before);
        fault=0;assert(bsp_mic_deinit()==ESP_OK);clean();success();return 0;
    }
    if(!strcmp(argv[1],"invalid-read")){
        assert(bsp_mic_read(buffer,4,&count,123)==ESP_ERR_INVALID_STATE&&count==0&&!calls);
        assert(bsp_mic_init(expected_rate)==ESP_OK);int before=calls;
        assert(bsp_mic_read(NULL,4,&count,123)==ESP_ERR_INVALID_ARG&&count==0);
        assert(bsp_mic_read(buffer,4,NULL,123)==ESP_ERR_INVALID_ARG);
        assert(bsp_mic_read(buffer,0,&count,123)==ESP_ERR_INVALID_ARG&&count==0);
        assert(bsp_mic_read(buffer,SIZE_MAX,&count,123)==ESP_ERR_INVALID_ARG&&count==0&&calls==before);
        assert(bsp_mic_deinit()==ESP_OK);clean();return 0;
    }
    if(!strcmp(argv[1],"rate")){
        assert(bsp_mic_init(0)==ESP_ERR_INVALID_ARG&&!calls);
        assert(bsp_mic_init(expected_rate)==ESP_OK);int before=calls;
        assert(bsp_mic_init(48000)==ESP_ERR_INVALID_STATE&&calls==before);
        assert(bsp_mic_deinit()==ESP_OK);expected_rate=48000;success();return 0;
    }
    fault=atoi(argv[1]);cleanup_fault=argc>2?atoi(argv[2]):0;
    if(!fault){success();success();return 0;}
    assert(bsp_mic_init(expected_rate)==ESP_FAIL);
    assert(bsp_mic_read(buffer,4,&count,123)==ESP_ERR_INVALID_STATE&&count==0);
    if(cleanup_fault){
        fault=cleanup_fault=0;int before=calls;
        assert(bsp_mic_init(expected_rate)==ESP_ERR_INVALID_STATE&&calls==before);
        assert(bsp_mic_deinit()==ESP_OK);
    }
    clean();fault=0;success();return 0;
}
