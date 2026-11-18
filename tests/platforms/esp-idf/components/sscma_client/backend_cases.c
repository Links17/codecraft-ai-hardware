/* SPDX-License-Identifier: Apache-2.0
 * Execute real SSCMA lifecycle code. Transport/JSON/decode are narrow doubles,
 * not protocol/camera emulation. Worker execution is deterministic at join. */
#include "camera_sscma.h"
#include "sscma_proto.h"
#undef free
#include <assert.h>
#include <stdlib.h>
#include <string.h>
enum { BUS=1,ADD,PM_CREATE,INIT_RESET,PM_DELETE,REMOVE,PM_ACQUIRE,TX_ALLOC,RX_ALLOC,
       POWER_OFF,POWER_ON,RESET_HOLD,RESET_RELEASE,SENSOR,SAMPLE,IMAGE_ALLOC,BASE64,
       SHUT_RESET,SHUT_POWER,PM_RELEASE,SEM,TASK,BREAK,NO_REPLY };
enum { IDLE,EXPECT_OFF,EXPECT_ON,EXPECT_HOLD,EXPECT_RELEASE,ACTIVE,CLEANUP };
static int fault,cleanup_fault,calls,phase,allocations,delete_order;
static bool bus,device,pm,awake,initializing=true,powered,sem,sem_signaled,worker,slow_join;
static int device_token,pm_token,sem_token;
static void (*task_fn)(void *);
static void *buffers[3];
static int64_t now;
static int pending,response_type,command_id;
static char command_name[16];
static esp_err_t step(int n){calls++;return n==fault||n==cleanup_fault?ESP_FAIL:ESP_OK;}
#define TRY(n) do {esp_err_t e=step(n);if(e!=ESP_OK)return e;} while(0)
esp_err_t spi_bus_initialize(int host,const spi_bus_config_t *cfg,int dma)
{assert(host==7&&cfg->sclk_io_num==1&&cfg->max_transfer_sz==SSCMA_MAX_READ+1&&dma==SPI_DMA_CH_AUTO);TRY(BUS);if(bus)return ESP_ERR_INVALID_STATE;bus=true;return ESP_OK;}
esp_err_t spi_bus_add_device(int host,const spi_device_interface_config_t *cfg,spi_device_handle_t *out)
{assert(host==7&&bus&&!device&&cfg->queue_size==1);TRY(ADD);device=true;*out=&device_token;return ESP_OK;}
esp_err_t spi_bus_remove_device(spi_device_handle_t handle)
{assert(device&&handle==&device_token);delete_order++;TRY(REMOVE);device=false;return ESP_OK;}
esp_err_t esp_pm_lock_create(int type,int arg,const char *name,esp_pm_lock_handle_t *out)
{assert(device&&!pm&&type==ESP_PM_NO_LIGHT_SLEEP&&!arg&&name);TRY(PM_CREATE);pm=true;*out=&pm_token;return ESP_OK;}
esp_err_t esp_pm_lock_delete(esp_pm_lock_handle_t handle)
{assert(pm&&!awake&&handle==&pm_token&&!delete_order);TRY(PM_DELETE);pm=false;return ESP_OK;}
esp_err_t esp_pm_lock_acquire(esp_pm_lock_handle_t handle)
{assert(pm&&!awake&&handle==&pm_token);TRY(PM_ACQUIRE);awake=true;return ESP_OK;}
esp_err_t esp_pm_lock_release(esp_pm_lock_handle_t handle)
{assert(pm&&awake&&handle==&pm_token);TRY(PM_RELEASE);awake=false;return ESP_OK;}
static esp_err_t power(bool on)
{
    if(on){assert(phase==EXPECT_ON);esp_err_t e=step(POWER_ON);phase=e==ESP_OK?EXPECT_HOLD:CLEANUP;if(e==ESP_OK)powered=true;return e;}
    if(phase==EXPECT_OFF){esp_err_t e=step(POWER_OFF);phase=e==ESP_OK?EXPECT_ON:CLEANUP;return e;}
    assert(phase==CLEANUP);esp_err_t e=step(SHUT_POWER);if(e==ESP_OK)powered=false;phase=IDLE;return e;
}
static esp_err_t reset(bool hold)
{
    if(initializing){assert(hold);esp_err_t e=step(INIT_RESET);if(e==ESP_OK)initializing=false;return e;}
    if(phase==EXPECT_HOLD){assert(hold);esp_err_t e=step(RESET_HOLD);phase=e==ESP_OK?EXPECT_RELEASE:CLEANUP;return e;}
    if(phase==EXPECT_RELEASE){assert(!hold);esp_err_t e=step(RESET_RELEASE);phase=e==ESP_OK?ACTIVE:CLEANUP;return e;}
    assert(hold);phase=CLEANUP;return step(SHUT_RESET);
}
static bool has_data(void){return phase!=ACTIVE||(pending>0&&fault!=NO_REPLY);}
int64_t esp_timer_get_time(void){return now;}
void vTaskDelay(TickType_t ticks){now+=(int64_t)ticks*1000;}
void *heap_caps_malloc(size_t size,int caps)
{
    int index=caps==MALLOC_CAP_DMA?(size==SSCMA_PACKET?0:1):2;
    if(index==0){phase=EXPECT_OFF;delete_order=0;}
    assert(!buffers[index]);
    if(step(index==0?TX_ALLOC:index==1?RX_ALLOC:IMAGE_ALLOC)!=ESP_OK){phase=CLEANUP;return NULL;}
    buffers[index]=malloc(size);assert(buffers[index]);allocations++;return buffers[index];
}
void test_free(void *ptr)
{
    if(!ptr)return;
    for(int i=0;i<3;i++)if(buffers[i]==ptr){buffers[i]=NULL;allocations--;free(ptr);return;}
    assert(!"free of unowned buffer");
}
void sscma_packet(uint8_t *out,uint8_t cmd,const uint8_t *payload,uint16_t length)
{
    assert(cmd==SSCMA_CMD_WRITE&&payload&&length<SSCMA_PACKET);
    memcpy(out,payload,length);out[length]=0;
    if(strstr((char *)out,"SENSOR")){command_id=SENSOR;strcpy(command_name,"SENSOR");}
    else if(strstr((char *)out,"SAMPLE")){command_id=SAMPLE;strcpy(command_name,"SAMPLE");}
    else {assert(strstr((char *)out,"BREAK"));command_id=BREAK;strcpy(command_name,"BREAK");}
}
esp_err_t spi_device_transmit(spi_device_handle_t handle,spi_transaction_t *t)
{assert(device&&handle==&device_token&&t->tx_buffer&&t->length==SSCMA_PACKET*8);TRY(command_id);pending=command_id==SAMPLE?2:1;return ESP_OK;}
char *sscma_rx_next(sscma_rx_t *rx)
{assert(rx);if(!pending||fault==NO_REPLY)return NULL;response_type=pending==1&&command_id==SAMPLE?SSCMA_TYPE_EVENT:SSCMA_TYPE_RESPONSE;pending--;return "fixture";}
bool sscma_rx_feed(sscma_rx_t *rx,const uint8_t *data,size_t size)
{(void)rx;(void)data;(void)size;assert(!"transport fixture already supplies replies");return false;}
void sscma_rx_free(sscma_rx_t *rx){assert(rx);pending=0;}
static cJSON root={.kind=1},number={.kind=2},string={.kind=3},data={.kind=4},resolution={.kind=5},dimension={.kind=2,.valueint=2};
cJSON *cJSON_Parse(const char *text){assert(!strcmp(text,"fixture"));return &root;}
void cJSON_Delete(cJSON *json){assert(!json||json==&root);}
cJSON *cJSON_GetObjectItem(const cJSON *json,const char *name)
{
    if(!json)return NULL;
    if(!strcmp(name,"type")){number.valueint=response_type;return &number;}
    if(!strcmp(name,"code")){number.valueint=0;return &number;}
    if(!strcmp(name,"name")){string.string=command_name;return &string;}
    if(!strcmp(name,"data"))return &data;
    if(!strcmp(name,"image")){string.string="fixture8";return &string;}
    if(!strcmp(name,"resolution"))return &resolution;
    return NULL;
}
const char *cJSON_GetStringValue(const cJSON *json){return json&&json->kind==3?json->string:NULL;}
bool cJSON_IsNumber(const cJSON *json){return json&&json->kind==2;}
int cJSON_GetArraySize(const cJSON *json){return json==&resolution?2:0;}
cJSON *cJSON_GetArrayItem(const cJSON *json,int index){assert(json==&resolution&&(index==0||index==1));return &dimension;}
int mbedtls_base64_decode(unsigned char *out,size_t size,size_t *written,const unsigned char *in,size_t length)
{assert(size>=4&&in&&length==8);if(step(BASE64)!=ESP_OK)return -1;memcpy(out,"\xff\xd8\xff\xd9",4);*written=4;return 0;}
SemaphoreHandle_t xSemaphoreCreateBinary(void)
{assert(!sem);if(step(SEM)!=ESP_OK)return NULL;sem=true;return &sem_token;}
int xSemaphoreGive(SemaphoreHandle_t handle)
{assert(sem&&handle==&sem_token&&!sem_signaled&&!allocations);sem_signaled=true;return pdTRUE;}
int xSemaphoreTake(SemaphoreHandle_t handle,TickType_t ticks)
{
    assert(sem&&handle==&sem_token);
    if(slow_join&&ticks!=portMAX_DELAY){slow_join=false;return 0;}
    assert(worker&&task_fn);task_fn(NULL);assert(sem_signaled&&!worker);sem_signaled=false;return pdTRUE;
}
int xTaskCreateWithCaps(void (*fn)(void *),const char *name,unsigned stack,void *arg,int priority,void *out,int caps)
{assert(!worker&&fn&&name&&stack&&priority&&caps&&!arg&&!out);if(step(TASK)!=ESP_OK)return 0;worker=true;task_fn=fn;return pdPASS;}
void vTaskDeleteWithCaps(void *task){assert(worker&&!task);worker=false;}
static void callback(const camera_frame_t *frame,void *ctx){(void)frame;(void)ctx;assert(!"worker runs after stop in this lifecycle fixture");}
static void success(void)
{
    camera_frame_t frame={0};assert(camera_capture(&frame)==ESP_OK&&frame.jpeg&&frame.len==4);
    assert(device&&bus&&!powered&&!awake&&allocations==1);
    camera_release(&frame);assert(!allocations);assert(camera_capture(&frame)==ESP_OK);camera_release(&frame);
}
int main(int argc,char **argv)
{
    assert(argc>=2);
    camera_sscma_config_t cfg={.name="test",.host=7,.sclk=1,.mosi=2,.miso=3,.cs=4,.power=power,.reset=reset,.has_data=has_data,.resolution=3,.stream_resolution=1};
    if(!strcmp(argv[1],"invalid")){
        assert(!camera_sscma(NULL));cfg.power=NULL;assert(!camera_sscma(&cfg));cfg.power=power;cfg.has_data=NULL;assert(!camera_sscma(&cfg));return 0;
    }
    camera_register(camera_sscma(&cfg));
    if(!strcmp(argv[1],"configure-twice")){assert(!camera_sscma(&cfg));success();return 0;}
    if(!strncmp(argv[1],"stream",6)){
        fault=argc>2?atoi(argv[2]):0;slow_join=!strcmp(argv[1],"stream-slow");
        if(fault){assert(camera_stream_start(callback,&cfg)!=ESP_OK&&!allocations&&!awake&&!worker);fault=0;}
        assert(camera_stream_start(callback,&cfg)==ESP_OK&&worker&&powered&&allocations==2);
        camera_stream_stop();assert(!worker&&!powered&&!awake&&!allocations);success();return 0;
    }
    fault=atoi(argv[1]);cleanup_fault=argc>2?atoi(argv[2]):0;
    if(!fault){success();return 0;}
    camera_frame_t frame={.len=123};esp_err_t ret=camera_capture(&frame);
    assert(ret!=ESP_OK&&frame.len==123&&!frame.jpeg&&!allocations&&!worker);
    if(fault==NO_REPLY)assert(ret==ESP_ERR_TIMEOUT&&now>=5000000);
    bool permanent=cleanup_fault||fault==SHUT_RESET||fault==SHUT_POWER||fault==PM_RELEASE;
    if(fault<=INIT_RESET&&!cleanup_fault)assert(!device&&!pm);
    if(permanent){
        fault=cleanup_fault=0;int before=calls;
        assert(camera_capture(&frame)==ESP_ERR_INVALID_STATE&&calls==before);
        assert(camera_stream_start(callback,&cfg)==ESP_ERR_INVALID_STATE&&calls==before);
    }
    else{fault=0;delete_order=0;success();}
    return 0;
}
