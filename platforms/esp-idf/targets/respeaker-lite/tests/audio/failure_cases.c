/* SPDX-License-Identifier: Apache-2.0
 * Execute the real BSP; no SDK, board, firmware clock or acoustics simulation. */
#include "bsp_audio.h"
#include "bsp_pins.h"
#include "audio_stub.h"
#include <assert.h>
#include <limits.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <string.h>

static atomic_int calls;
static int failure,cleanup_failure,bus,xmos,codec,tx,rx,lock_requests;
static bool bus_live,xmos_live,codec_live,tx_live,rx_live,tx_enabled,rx_enabled,mutex_live;
static bool initializing=true,disable_applied,partial,concurrent_control,duplex;
static pthread_mutex_t lock=PTHREAD_MUTEX_INITIALIZER,gate=PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t condition=PTHREAD_COND_INITIALIZER;
static bool first_held,second_waiting,release_first,rx_waiting,tx_entered;
static int control_takes,trace[32],trace_count;
static uint8_t codec_regs[256];
static uint32_t timeout_seen;
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
    mutex_live=true;lock_requests=0;return &lock;
}
int xSemaphoreTake(SemaphoreHandle_t mutex,TickType_t wait)
{
    assert(mutex==&lock&&mutex_live);
    assert(wait==pdMS_TO_TICKS(100)
#ifdef TEST_ORIGINAL
           ||wait==portMAX_DELAY
#endif
    );
    pthread_mutex_lock(&gate);
    if(concurrent_control&&++control_takes==2){second_waiting=true;pthread_cond_broadcast(&condition);}
    pthread_mutex_unlock(&gate);
    int stage=initializing?(lock_requests++?16:8):34;
    if(step(stage)!=ESP_OK)return 0;
    assert(pthread_mutex_lock(&lock)==0);return pdTRUE;
}
void xSemaphoreGive(SemaphoreHandle_t mutex){assert(mutex==&lock);assert(pthread_mutex_unlock(&lock)==0);}
void vSemaphoreDelete(SemaphoreHandle_t mutex)
{
    assert(mutex==&lock&&mutex_live&&!bus_live&&!tx_live&&!rx_live);mutex_live=false;
}
esp_err_t i2c_new_master_bus(const i2c_master_bus_config_t *c,i2c_master_bus_handle_t *out)
{
    assert(mutex_live&&!bus_live&&c->i2c_port==0&&c->sda_io_num==BSP_PIN_I2C_SDA&&c->scl_io_num==BSP_PIN_I2C_SCL&&c->glitch_ignore_cnt==7);
    esp_err_t ret=step(2);if(ret==ESP_OK){bus_live=true;*out=&bus;}return ret;
}
esp_err_t i2c_master_bus_add_device(i2c_master_bus_handle_t b,const i2c_device_config_t *c,i2c_master_dev_handle_t *out)
{
    assert(b==&bus&&bus_live&&c->dev_addr_length==I2C_ADDR_BIT_LEN_7&&c->scl_speed_hz==BSP_I2C_FREQ_HZ);
    bool is_xmos=c->device_address==BSP_I2C_ADDR_XMOS;
    assert(is_xmos||c->device_address==BSP_I2C_ADDR_CODEC);
    assert(is_xmos?!xmos_live:!codec_live);
    esp_err_t ret=step(is_xmos?3:4);
    if(ret==ESP_OK){if(is_xmos){xmos_live=true;*out=&xmos;}else{codec_live=true;*out=&codec;}}
    return ret;
}
esp_err_t i2c_master_bus_rm_device(i2c_master_dev_handle_t d)
{
    assert(bus_live&&!tx_live&&!rx_live);
    bool is_codec=d==&codec;assert(is_codec?codec_live:(d==&xmos&&xmos_live));
    esp_err_t ret=step(is_codec?24:25);
    if(ret==ESP_OK){if(is_codec)codec_live=false;else xmos_live=false;}return ret;
}
esp_err_t i2c_del_master_bus(i2c_master_bus_handle_t b)
{
    assert(b==&bus&&bus_live&&!xmos_live&&!codec_live);
    esp_err_t ret=step(26);if(ret==ESP_OK)bus_live=false;return ret;
}
esp_err_t gpio_config(const gpio_config_t *c){assert(c->pin_bit_mask==(1ULL<<BSP_PIN_XMOS_RESET)&&c->mode==GPIO_MODE_OUTPUT);return step(5);}
esp_err_t gpio_set_level(int pin,int level){assert(pin==BSP_PIN_XMOS_RESET);return step(level?6:7);}
void vTaskDelay(unsigned ticks){assert(ticks==pdMS_TO_TICKS(20)||ticks==pdMS_TO_TICKS(3000));}
esp_err_t i2c_master_transmit(i2c_master_dev_handle_t d,const uint8_t *data,size_t size,int timeout)
{
    assert(timeout==100);
    if(d==&xmos){
        assert(xmos_live&&size==3);
        assert(data[0]==(initializing?0xf0:0xf1)&&data[1]==(initializing?0xd8:0x81)&&data[2]==(initializing?4:2));
        if(concurrent_control)trace[trace_count++]=4;
        return step(initializing?9:35);
    }
    assert(d==&codec&&codec_live&&size==2);
    int pos=data[0]==0?0:data[0]==0x41?1:data[0]==0x42?2:3;
    assert(pos<3||data[0]==0x40);
    if(concurrent_control){
        trace[trace_count++]=pos;
        pthread_mutex_lock(&gate);
        if(!first_held){first_held=true;pthread_cond_broadcast(&condition);while(!release_first)pthread_cond_wait(&condition,&gate);}
        pthread_mutex_unlock(&gate);
    }
    esp_err_t ret=step((initializing?17:37)+pos);
    if(ret==ESP_OK)codec_regs[data[0]]=data[1];return ret;
}
esp_err_t i2c_master_receive(i2c_master_dev_handle_t d,uint8_t *data,size_t size,int timeout)
{
    assert(d==&xmos&&xmos_live&&timeout==100&&size==(initializing?4:2));
    if(concurrent_control)trace[trace_count++]=5;
    esp_err_t ret=step(initializing?10:36);if(ret!=ESP_OK)return ret;
    memset(data,0,size);
    if(initializing){data[1]=1;data[2]=0;data[3]=9;}
    if(failure==11){failure=0;data[0]=1;}
    return ESP_OK;
}
esp_err_t i2s_new_channel(const i2s_chan_config_t *c,i2s_chan_handle_t *out_tx,i2s_chan_handle_t *out_rx)
{
    assert(!tx_live&&!rx_live&&c->id==BSP_I2S_PORT&&c->role==I2S_ROLE_SLAVE&&c->dma_desc_num==6&&c->dma_frame_num==240&&c->auto_clear);
    esp_err_t ret=step(12);if(ret==ESP_OK){tx_live=rx_live=true;*out_tx=&tx;*out_rx=&rx;}return ret;
}
esp_err_t i2s_channel_init_std_mode(i2s_chan_handle_t ch,const i2s_std_config_t *c)
{
    assert((ch==&tx&&tx_live)||(ch==&rx&&rx_live));
    assert(c->clk_cfg.sample_rate_hz==BSP_I2S_SAMPLE_RATE&&c->slot_cfg.data_bit_width==32&&c->slot_cfg.slot_mode==I2S_SLOT_MODE_STEREO);
    assert(c->gpio_cfg.mclk==I2S_GPIO_UNUSED&&c->gpio_cfg.bclk==BSP_PIN_I2S_BCLK&&c->gpio_cfg.ws==BSP_PIN_I2S_WS&&c->gpio_cfg.dout==BSP_PIN_I2S_DOUT&&c->gpio_cfg.din==BSP_PIN_I2S_DIN);
    return step(ch==&tx?13:14);
}
esp_err_t i2s_channel_enable(i2s_chan_handle_t ch)
{
    bool tx_channel=ch==&tx;assert(tx_channel?tx_live:(ch==&rx&&rx_live));
    assert(!(tx_channel?tx_enabled:rx_enabled));
    esp_err_t ret=step(tx_channel?15:30);if(ret==ESP_OK){if(tx_channel)tx_enabled=true;else rx_enabled=true;}return ret;
}
esp_err_t i2s_channel_disable(i2s_chan_handle_t ch)
{
    bool tx_channel=ch==&tx;assert(tx_channel?tx_live:(ch==&rx&&rx_live));
    if(!(tx_channel?tx_enabled:rx_enabled))return ESP_ERR_INVALID_STATE;
    esp_err_t ret=step(tx_channel?21:31);
    if(ret==ESP_OK||disable_applied){if(tx_channel)tx_enabled=false;else rx_enabled=false;}return ret;
}
esp_err_t i2s_del_channel(i2s_chan_handle_t ch)
{
    bool tx_channel=ch==&tx;assert(tx_channel?(tx_live&&!tx_enabled):(ch==&rx&&rx_live&&!rx_enabled));
    esp_err_t ret=step(tx_channel?23:22);if(ret==ESP_OK){if(tx_channel)tx_live=false;else rx_live=false;}return ret;
}
esp_err_t i2s_channel_read(i2s_chan_handle_t ch,void *dest,size_t size,size_t *bytes,uint32_t timeout_ms)
{
    assert(ch==&rx&&rx_enabled&&dest&&size>0);timeout_seen=timeout_ms;
    esp_err_t ret=step(32);if(ret!=ESP_OK){*bytes=0;return ret;}
    if(duplex){pthread_mutex_lock(&gate);rx_waiting=true;pthread_cond_broadcast(&condition);while(!tx_entered)pthread_cond_wait(&condition,&gate);pthread_mutex_unlock(&gate);}
    *bytes=partial?16:size;memset(dest,0,*bytes);return partial?ESP_ERR_TIMEOUT:ESP_OK;
}
esp_err_t i2s_channel_write(i2s_chan_handle_t ch,const void *src,size_t size,size_t *bytes,uint32_t timeout_ms)
{
    assert(ch==&tx&&tx_enabled&&src&&size>0);if(!duplex)timeout_seen=timeout_ms;
    esp_err_t ret=step(33);if(ret!=ESP_OK){*bytes=0;return ret;}
    if(duplex){pthread_mutex_lock(&gate);assert(rx_waiting);tx_entered=true;pthread_cond_broadcast(&condition);pthread_mutex_unlock(&gate);}
    *bytes=partial?16:size;return partial?ESP_ERR_TIMEOUT:ESP_OK;
}
static void *volume_worker(void *unused){(void)unused;assert(bsp_audio_set_volume(25)==ESP_OK);return NULL;}
static void *mute_worker(void *unused){(void)unused;assert(!bsp_audio_muted());return NULL;}
static void *rx_worker(void *unused){(void)unused;int32_t buf[8];assert(bsp_audio_mic_read(buf,4,17)==4);return NULL;}
int main(int argc,char **argv)
{
    assert(argc>=2);const char *mode=argv[1];int32_t buf[8]={0};
    if(!strcmp(mode,"unready")){
        assert(bsp_audio_muted());assert(bsp_audio_set_volume(50)==ESP_ERR_INVALID_STATE);
        assert(bsp_audio_mic_start()==ESP_ERR_INVALID_STATE);bsp_audio_mic_stop();
        assert(bsp_audio_mic_read(buf,4,17)==0&&bsp_audio_write(buf,4,17)==0&&calls==0);return 0;
    }
    failure=atoi(mode);cleanup_failure=argc>2?atoi(argv[2]):0;
    int expected=failure,cleanup=cleanup_failure;
    esp_err_t ret=bsp_audio_init();
    if(expected){
        assert(ret!=ESP_OK&&failure==0);
        assert(bsp_audio_muted()&&bsp_audio_mic_start()==ESP_ERR_INVALID_STATE);
        assert(bsp_audio_set_volume(60)==ESP_ERR_INVALID_STATE&&bsp_audio_mic_read(buf,4,17)==0&&bsp_audio_write(buf,4,17)==0);
        if(cleanup){int prior=calls;assert(cleanup_failure==0&&bsp_audio_init()==ESP_ERR_INVALID_STATE&&calls==prior);return 0;}
        assert(!mutex_live&&!bus_live&&!xmos_live&&!codec_live&&!tx_live&&!rx_live);
        assert(bsp_audio_init()==ESP_OK);
    }else assert(ret==ESP_OK);
    initializing=false;
    if(!strcmp(mode,"timeout-units")){
        assert(bsp_audio_mic_start()==ESP_OK);
        assert(bsp_audio_mic_read(buf,4,17)==4&&timeout_seen==17);
        assert(bsp_audio_write(buf,4,23)==4&&timeout_seen==23);return 0;
    }
    int prior=calls;assert(bsp_audio_init()==ESP_OK&&calls==prior);
    assert(tx_enabled&&!rx_enabled&&codec_regs[0x41]==(uint8_t)(int8_t)(-127+60*127/100));
    assert(bsp_audio_mic_start()==ESP_OK);prior=calls;assert(bsp_audio_mic_start()==ESP_OK&&calls==prior);
    if(!strcmp(mode,"duplex")){
        duplex=true;pthread_t thread;assert(pthread_create(&thread,NULL,rx_worker,NULL)==0);
        pthread_mutex_lock(&gate);while(!rx_waiting)pthread_cond_wait(&condition,&gate);pthread_mutex_unlock(&gate);
        assert(bsp_audio_write(buf,4,17)==4);pthread_join(thread,NULL);return 0;
    }
    if(!strcmp(mode,"concurrent-control")){
        concurrent_control=true;pthread_t first,second;assert(pthread_create(&first,NULL,volume_worker,NULL)==0);
        pthread_mutex_lock(&gate);while(!first_held)pthread_cond_wait(&condition,&gate);pthread_mutex_unlock(&gate);
        assert(pthread_create(&second,NULL,mute_worker,NULL)==0);
        pthread_mutex_lock(&gate);while(!second_waiting)pthread_cond_wait(&condition,&gate);release_first=true;pthread_cond_broadcast(&condition);pthread_mutex_unlock(&gate);
        pthread_join(first,NULL);pthread_join(second,NULL);
        const int expected_trace[]={0,1,2,3,4,5};assert(trace_count==6&&memcmp(trace,expected_trace,sizeof(expected_trace))==0);return 0;
    }
    if(!strcmp(mode,"partial")){
        partial=true;assert(bsp_audio_mic_read(buf,4,17)==2&&bsp_audio_write(buf,4,17)==2);return 0;
    }
    if(!strcmp(mode,"stop-failure")||!strcmp(mode,"stop-applied")){
        failure=31;disable_applied=!strcmp(mode,"stop-applied");bsp_audio_mic_stop();
        prior=calls;assert(bsp_audio_mic_read(buf,4,17)==0&&bsp_audio_mic_start()==ESP_ERR_INVALID_STATE&&calls==prior);
        bsp_audio_mic_stop();assert(!rx_enabled&&bsp_audio_mic_start()==ESP_OK);return 0;
    }
    if(!strcmp(mode,"controls")){
        for(int n=34;n<=40;n++){
            failure=n;
            if(n<=36)assert(bsp_audio_muted());else assert(bsp_audio_set_volume(40)==ESP_FAIL);
            assert(failure==0);
        }
        failure=34;assert(bsp_audio_set_volume(40)==ESP_ERR_TIMEOUT);
        assert(bsp_audio_set_volume(-1)==ESP_OK&&codec_regs[0x41]==0x81&&codec_regs[0x42]==0x81&&codec_regs[0x40]==0x0c);
        assert(bsp_audio_set_volume(101)==ESP_OK&&codec_regs[0x41]==0&&codec_regs[0x42]==0&&codec_regs[0x40]==0);
        assert(!bsp_audio_muted());
    }
    prior=calls;
    assert(bsp_audio_mic_read(NULL,4,17)==0&&bsp_audio_write(NULL,4,17)==0);
    assert(bsp_audio_mic_read(buf,0,17)==0&&bsp_audio_write(buf,0,17)==0);
    size_t huge=(size_t)INT_MAX/(2*sizeof(int32_t))+1;
    assert(bsp_audio_mic_read(buf,huge,17)==0&&bsp_audio_write(buf,huge,17)==0&&calls==prior);
    failure=32;assert(bsp_audio_mic_read(buf,4,17)==0);failure=33;assert(bsp_audio_write(buf,4,17)==0);
    bsp_audio_mic_stop();prior=calls;bsp_audio_mic_stop();assert(calls==prior);
    failure=30;assert(bsp_audio_mic_start()==ESP_FAIL&&bsp_audio_mic_read(buf,4,17)==0);
    assert(bsp_audio_mic_start()==ESP_OK);return 0;
}
