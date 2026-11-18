/* SPDX-License-Identifier: Apache-2.0
 * Shared native display-contract scenarios; each Target supplies its actual
 * BSP/pins. BUSY levels and wait budgets follow that BSP's epd_wait_idle. */
#include "epd_stub.h"
#include "bsp_epd.h"
#include "bsp_pins.h"
#undef free
#include <assert.h>
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
enum { OUT_CONFIG=1,BUSY_CONFIG,INIT_POWER,RESET_IDLE,ALLOC,BUS,ADD,
       UPDATE_POWER=10,RESET_LOW,RESET_HIGH,DC_COMMAND,DC_DATA,TRANSMIT };
static int fault,calls,token,transfers,dc,busy_reads,jam_wait;
static bool bus,device,initializing=true,pause_alloc,pause_transfer,waiting,released;
static void *chunk;
static size_t chunk_size;
static int64_t now;
static uint64_t wire_hash;
static pthread_mutex_t gate=PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t changed=PTHREAD_COND_INITIALIZER;
static esp_err_t step(int n){calls++;return fault==n?ESP_FAIL:ESP_OK;}
#define TRY(n) do{esp_err_t e=step(n);if(e!=ESP_OK)return e;}while(0)
static void pause_here(void)
{
    pthread_mutex_lock(&gate);waiting=true;pthread_cond_broadcast(&changed);
    while(!released)pthread_cond_wait(&changed,&gate);
    pthread_mutex_unlock(&gate);
}
esp_err_t gpio_config(const gpio_config_t *cfg)
{
    if(cfg->mode==GPIO_MODE_INPUT){assert(cfg->pin_bit_mask==(1ULL<<BSP_PIN_EPD_BUSY));return step(BUSY_CONFIG);}
    assert(cfg->mode==GPIO_MODE_OUTPUT&&(cfg->pin_bit_mask&(1ULL<<BSP_PIN_EPD_RST)));
    return step(OUT_CONFIG);
}
esp_err_t gpio_set_level(int pin,int level)
{
#ifdef TEST_STICKY
    if(pin==BSP_PIN_EPD_EN){assert(level==1);return step(initializing?INIT_POWER:UPDATE_POWER);}
#endif
    if(pin==BSP_PIN_EPD_RST){
        if(initializing){assert(level==1);return step(RESET_IDLE);}
        return step(level?RESET_HIGH:RESET_LOW);
    }
    assert(pin==BSP_PIN_EPD_DC);dc=level;return step(level?DC_DATA:DC_COMMAND);
}
int gpio_get_level(int pin)
{
    assert(pin==BSP_PIN_EPD_BUSY);busy_reads++;
    bool busy=jam_wait&&busy_reads>=jam_wait;
#ifdef TEST_STICKY
    return busy;
#else
    return !busy;
#endif
}
void *heap_caps_malloc(size_t size,int caps)
{
    assert(!chunk&&size&&caps==MALLOC_CAP_DMA);
    if(step(ALLOC)!=ESP_OK)return NULL;
    if(pause_alloc)pause_here();
    chunk=malloc(size);assert(chunk);chunk_size=size;return chunk;
}
void test_free(void *ptr){assert(ptr&&ptr==chunk&&!device);free(ptr);chunk=NULL;chunk_size=0;}
esp_err_t spi_bus_initialize(int host,const spi_bus_config_t *cfg,int dma)
{
    assert(host==SPI2_HOST&&dma==SPI_DMA_CH_AUTO&&cfg->max_transfer_sz==(int)chunk_size);
    assert(cfg->sclk_io_num==BSP_PIN_EPD_SCLK&&cfg->mosi_io_num==BSP_PIN_EPD_MOSI);
#ifdef TEST_STICKY
    assert(cfg->miso_io_num==BSP_PIN_EPD_MISO);
#else
    assert(cfg->miso_io_num==BSP_PIN_SD_MISO);
#endif
    TRY(BUS);if(bus)return ESP_ERR_INVALID_STATE;bus=true;return ESP_OK;
}
esp_err_t spi_bus_add_device(int host,const spi_device_interface_config_t *cfg,spi_device_handle_t *out)
{
    assert(bus&&!device&&chunk&&host==SPI2_HOST&&cfg->spics_io_num==BSP_PIN_EPD_CS);
    assert(cfg->clock_speed_hz==BSP_EPD_SPI_HZ&&cfg->queue_size==1&&cfg->mode==0);
    TRY(ADD);device=true;initializing=false;*out=&token;return ESP_OK;
}
esp_err_t spi_device_polling_transmit(spi_device_handle_t handle,spi_transaction_t *t)
{
    assert(device&&chunk&&handle==&token&&t->tx_buffer==chunk&&t->length&&!(t->length%8)&&t->length/8<=chunk_size);
    if(pause_transfer&&!waiting)pause_here();
    TRY(TRANSMIT);transfers++;
    wire_hash=(wire_hash^(unsigned)dc)*1099511628211ULL;
    for(size_t i=0;i<t->length/8;i++)wire_hash=(wire_hash^((uint8_t *)chunk)[i])*1099511628211ULL;
    return ESP_OK;
}
int64_t esp_timer_get_time(void){return now;}
void vTaskDelay(unsigned ticks){now+=(int64_t)ticks*1000;}
static uint8_t *frame;
static uint64_t update(bool full,const uint8_t *prev)
{
    wire_hash=14695981039346656037ULL;busy_reads=0;
    assert(bsp_epd_update(frame,prev,full)==ESP_OK&&transfers&&frame[0]==0xaa&&frame[BSP_EPD_FRAME_BYTES-1]==0xaa);
    return wire_hash;
}
static void init_ok(void)
{assert(bsp_epd_init()==ESP_OK&&device&&chunk);int before=calls;assert(bsp_epd_init()==ESP_OK&&calls==before);}
static void *worker(void *arg)
{if(arg)assert(bsp_epd_init()==ESP_OK);else assert(bsp_epd_update(frame,NULL,true)==ESP_OK);return NULL;}
int main(int argc,char **argv)
{
    assert(argc>=2);frame=malloc(BSP_EPD_FRAME_BYTES);assert(frame);memset(frame,0xaa,BSP_EPD_FRAME_BYTES);
    if(!strcmp(argv[1],"concurrent-init")||!strcmp(argv[1],"concurrent-update")){
        pause_alloc=!strcmp(argv[1],"concurrent-init");pause_transfer=!pause_alloc;
        if(!pause_alloc)init_ok();pthread_t task;
        assert(!pthread_create(&task,NULL,worker,pause_alloc?(void *)1:NULL));
        pthread_mutex_lock(&gate);while(!waiting)pthread_cond_wait(&changed,&gate);pthread_mutex_unlock(&gate);
        int before=calls;
        assert(bsp_epd_init()==ESP_ERR_INVALID_STATE&&calls==before);
        assert(bsp_epd_update(frame,NULL,true)==ESP_ERR_INVALID_STATE&&calls==before);
#ifdef TEST_STICKY
        assert(bsp_epd_update_gray4(frame)==ESP_ERR_INVALID_STATE&&calls==before);
#endif
        pthread_mutex_lock(&gate);released=true;pthread_cond_broadcast(&changed);pthread_mutex_unlock(&gate);
        assert(!pthread_join(task,NULL));pause_transfer=pause_alloc=false;init_ok();update(true,NULL);free(frame);return 0;
    }
    if(!strcmp(argv[1],"unready")){
        assert(bsp_epd_update(frame,NULL,true)==ESP_ERR_INVALID_STATE&&!calls);
#ifdef TEST_STICKY
        assert(bsp_epd_update_gray4(frame)==ESP_ERR_INVALID_STATE&&!calls);
#endif
        init_ok();update(true,NULL);free(frame);return 0;
    }
    if(!strcmp(argv[1],"borrowed")){bus=true;init_ok();update(true,NULL);free(frame);return 0;}
    if(!strcmp(argv[1],"null")){
        init_ok();int before=calls;assert(bsp_epd_update(NULL,NULL,true)==ESP_ERR_INVALID_ARG&&calls==before);
#ifdef TEST_STICKY
        assert(bsp_epd_update_gray4(NULL)==ESP_ERR_INVALID_ARG&&calls==before);
#endif
        update(true,NULL);free(frame);return 0;
    }
    if(!strcmp(argv[1],"full-null")){
        init_ok();uint64_t full=update(true,NULL);assert(update(false,NULL)==full);free(frame);return 0;
    }
    if(!strcmp(argv[1],"runtime")){
        init_ok();fault=atoi(argv[2]);assert(bsp_epd_update(frame,NULL,true)==ESP_FAIL);fault=0;
        init_ok();update(true,NULL);free(frame);return 0;
    }
    if(!strcmp(argv[1],"busy")){
        init_ok();jam_wait=atoi(argv[2]);int64_t before=now;
        assert(bsp_epd_update(frame,NULL,true)==ESP_ERR_TIMEOUT&&now-before>=TEST_BUSY_TIMEOUT_MS*1000LL);
        jam_wait=0;update(true,NULL);free(frame);return 0;
    }
#ifdef TEST_STICKY
    if(!strcmp(argv[1],"gray")){
        init_ok();uint64_t full=update(true,NULL);
        uint8_t *gray=calloc(1,BSP_EPD_GRAY4_FRAME_BYTES);assert(gray);
        if(argc>2){fault=atoi(argv[2]);assert(bsp_epd_update_gray4(gray)==ESP_FAIL);fault=0;}
        assert(bsp_epd_update_gray4(gray)==ESP_OK);assert(update(false,frame)==full);
        free(gray);free(frame);return 0;
    }
    if(!strcmp(argv[1],"gray-busy")){
        init_ok();uint8_t *gray=calloc(1,BSP_EPD_GRAY4_FRAME_BYTES);assert(gray);
        jam_wait=atoi(argv[2]);assert(bsp_epd_update_gray4(gray)==ESP_ERR_TIMEOUT);
        jam_wait=0;assert(bsp_epd_update_gray4(gray)==ESP_OK);free(gray);free(frame);return 0;
    }
    if(!strcmp(argv[1],"recover-full")){
        init_ok();uint64_t full=update(true,NULL);assert(update(false,frame)!=full);
        fault=UPDATE_POWER;assert(bsp_epd_update(frame,frame,false)==ESP_FAIL);fault=0;
        assert(update(false,frame)==full);free(frame);return 0;
    }
#endif
    fault=atoi(argv[1]);
    if(fault){assert(bsp_epd_init()==(fault==ALLOC?ESP_ERR_NO_MEM:ESP_FAIL));assert(!chunk&&!device);fault=0;}
    init_ok();update(true,NULL);free(frame);return 0;
}
