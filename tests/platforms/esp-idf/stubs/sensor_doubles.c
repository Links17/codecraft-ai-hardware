/* SPDX-License-Identifier: Apache-2.0 */
#undef calloc
#undef free
#include <assert.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include "sensor_stub.h"

int fault, allocations, mutexes, devices, commands, receives, other_calls;
int attached_address, attached_speed;
int bus_creates;
#ifdef TEST_STICKY
#include "bsp_pins.h"
esp_err_t i2c_new_master_bus(const i2c_master_bus_config_t *c,i2c_master_bus_handle_t *out)
{
    assert(c->i2c_port==I2C_NUM_1&&c->sda_io_num==BSP_PIN_I2C1_SDA&&c->scl_io_num==BSP_PIN_I2C1_SCL);
    assert(c->glitch_ignore_cnt==7&&c->flags.enable_internal_pullup&&bus_creates==0);
    if(fault==10)return ESP_FAIL;
    ++bus_creates;*out=test_bus;return ESP_OK;
}
#endif
uint8_t frame[8], sent[8];
size_t sent_size;
static int bus_identity;
const i2c_master_bus_handle_t test_bus = &bus_identity;
/* Arbitrary test configuration; BSP tests separately assert their real header. */
const i2c_device_config_t test_config = { .device_address=0x44, .scl_speed_hz=100000 };
struct fake_device { bool used, pending; int address; };
static struct fake_device slots[4];
pthread_mutex_t gate = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t changed = PTHREAD_COND_INITIALIZER;
bool pause_conversion, conversion_waiting, release_conversion, mutex_waiter;

void *test_calloc(size_t count, size_t size)
{
    if (fault==ALLOC) return NULL;
    void *p=calloc(count,size); assert(p); allocations++; return p;
}
void test_free(void *ptr) { if (ptr) { allocations--; assert(allocations>=0); free(ptr); } }
SemaphoreHandle_t xSemaphoreCreateMutex(void)
{
    if (fault==MUTEX) return NULL;
    pthread_mutex_t *m=malloc(sizeof(*m)); assert(m);
    assert(pthread_mutex_init(m,NULL)==0); mutexes++; return m;
}
int xSemaphoreTake(SemaphoreHandle_t lock, TickType_t timeout)
{
    assert(lock && timeout>0);
    if (fault==LOCK) return 0;
    int result=pthread_mutex_trylock(lock);
    if (result==EBUSY) {
        pthread_mutex_lock(&gate); mutex_waiter=true;
        pthread_cond_broadcast(&changed); pthread_mutex_unlock(&gate);
        result=pthread_mutex_lock(lock);
    }
    assert(result==0); return pdTRUE;
}
void xSemaphoreGive(SemaphoreHandle_t lock) { assert(pthread_mutex_unlock(lock)==0); }
void vSemaphoreDelete(SemaphoreHandle_t lock)
{
    assert(lock && pthread_mutex_destroy(lock)==0); free(lock); mutexes--; assert(mutexes>=0);
}
void vTaskDelay(TickType_t ticks)
{
    assert(ticks>=10);
    pthread_mutex_lock(&gate);
    if (pause_conversion) {
        conversion_waiting=true; pthread_cond_broadcast(&changed);
        while (!release_conversion) pthread_cond_wait(&changed,&gate);
    }
    pthread_mutex_unlock(&gate);
}
esp_err_t bsp_i2c0_bus_get(i2c_master_bus_handle_t *out) { *out=test_bus; return ESP_OK; }
esp_err_t i2c_master_probe(i2c_master_bus_handle_t bus, int addr, int timeout)
{
    assert(bus==test_bus && addr>0 && timeout==100);
    return fault==PROBE ? ESP_ERR_TIMEOUT : ESP_OK;
}
esp_err_t i2c_master_bus_add_device(i2c_master_bus_handle_t bus, const i2c_device_config_t *cfg, i2c_master_dev_handle_t *out)
{
    assert(bus==test_bus && cfg && out && cfg->scl_speed_hz>0);
    if (fault==ADD) return ESP_FAIL;
    attached_address=cfg->device_address; attached_speed=cfg->scl_speed_hz;
    for (size_t i=0;i<4;i++) if (!slots[i].used) {
        slots[i]=(struct fake_device){.used=true,.address=cfg->device_address};
        *out=&slots[i]; devices++; return ESP_OK;
    }
    assert(!"duplicate initialization exhausted devices"); return ESP_FAIL;
}
esp_err_t i2c_master_bus_rm_device(i2c_master_dev_handle_t dev)
{
    assert(dev && dev->used);
    if (fault==REMOVE) return ESP_FAIL;
    dev->used=false; devices--; assert(devices>=0); return ESP_OK;
}
esp_err_t i2c_master_transmit(i2c_master_dev_handle_t dev, const uint8_t *data, size_t size, int timeout)
{
    assert(dev && dev->used && data && size<=sizeof(sent) && timeout==100);
    if (fault==TRANSMIT) return ESP_ERR_TIMEOUT;
    pthread_mutex_lock(&gate);
    if (size==1 && data[0]==0xFD) {
        assert(!dev->pending && "interleaved SHT4x conversion");
        dev->pending=true; commands++;
    } else other_calls++;
    memcpy(sent,data,size); sent_size=size;
    pthread_mutex_unlock(&gate); return ESP_OK;
}
esp_err_t i2c_master_receive(i2c_master_dev_handle_t dev, uint8_t *data, size_t size, int timeout)
{
    assert(dev && dev->used && data && size==6 && timeout==100);
    pthread_mutex_lock(&gate); assert(dev->pending); dev->pending=false; receives++;
    memcpy(data,frame,size); pthread_mutex_unlock(&gate);
    return fault==RECEIVE ? ESP_ERR_TIMEOUT : ESP_OK;
}
esp_err_t i2c_master_transmit_receive(i2c_master_dev_handle_t dev, const uint8_t *data, size_t size, uint8_t *out, size_t count, int timeout)
{
    assert(dev && dev->used && data && size==1 && data[0]==2 && count==7 && timeout==100);
    if (fault==TRANSCEIVE) return ESP_ERR_TIMEOUT;
    memcpy(out,frame,count); return ESP_OK;
}
void check_clean(void) { assert(allocations==0 && mutexes==0 && devices==0); }
