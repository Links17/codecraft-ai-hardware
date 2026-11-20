/* SPDX-License-Identifier: Apache-2.0
 * Shared task-boundary fixture; each Target supplies its own keys and API. */
#include "peripheral_stub.h"
#include "bsp_button.h"
#include "bsp_pins.h"
#include <assert.h>
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
static int calls,fail_at,created,frame,callbacks;
static bool early,observe,advance,init_returned,poll_only;
static int observed=-1,context;
static TickType_t tick_base;
static TaskFunction_t saved_task;
static void *saved_arg;
static pthread_mutex_t gate=PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t changed=PTHREAD_COND_INITIALIZER;
#ifdef BUTTON_SINGLE
static esp_err_t initialize(bsp_button_cb_t cb,void *arg){(void)arg;return bsp_button_init(cb);}
static bool pressed(int key){(void)key;return bsp_button_pressed();}
static void callback(bool value,void *arg){
    assert(arg==NULL);
#else
static esp_err_t initialize(bsp_button_cb_t cb,void *arg){return bsp_button_init(cb,arg);}
static bool pressed(int key){return bsp_button_pressed((BUTTON_KEY_TYPE)key);}
static void callback(BUTTON_KEY_TYPE key,bool value,void *arg){
    assert((int)key==0&&arg==&context);
#endif
    if(early)assert(!init_returned);
    assert(callbacks<2&&value==(callbacks==0));assert(pressed(0)==value);callbacks++;
}
#ifdef BUTTON_SINGLE
static void other_callback(bool value,void *arg){(void)value;(void)arg;assert(false);}
#else
static void other_callback(BUTTON_KEY_TYPE key,bool value,void *arg){(void)key;(void)value;(void)arg;assert(false);}
#endif
static void *run_task(void *unused){(void)unused;saved_task(saved_arg);assert(false);return NULL;}
esp_err_t gpio_config(const gpio_config_t *c){assert(c->mode==GPIO_MODE_INPUT&&c->pull_up_en==GPIO_PULLUP_ENABLE);return ++calls==fail_at?ESP_FAIL:ESP_OK;}
int gpio_get_level(int pin){bool raw=(frame==1||(frame>=3&&frame<=5));return pin==BUTTON_FIRST_GPIO&&!poll_only?(!raw):1;}
TickType_t xTaskGetTickCount(void){TickType_t step=pdMS_TO_TICKS(20);return tick_base+(TickType_t)frame*(step?step:1);}
void vTaskDelay(TickType_t ticks){
    TickType_t expected=pdMS_TO_TICKS(20);assert(ticks==(expected?expected:1));
    if(observe){pthread_mutex_lock(&gate);observed=frame;pthread_cond_broadcast(&changed);
        while(!advance){
            pthread_cond_wait(&changed,&gate);
        }
        advance=false;
        pthread_mutex_unlock(&gate);
    }
    if(++frame==10)pthread_exit(NULL);
}
int xTaskCreate(TaskFunction_t task,const char *name,unsigned stack,void *arg,unsigned priority,void *handle){
    assert(name&&stack>=2048&&priority==5&&!handle);if(++calls==fail_at)return pdFALSE;
    assert(!created);created++;saved_task=task;saved_arg=arg;
    if(early){pthread_t worker;assert(!pthread_create(&worker,NULL,run_task,NULL));pthread_join(worker,NULL);}
    return pdPASS;
}
int main(int argc,char **argv){
    assert(argc==2);const char *mode=argv[1];assert(!pressed(0));
#ifndef BUTTON_SINGLE
    assert(!pressed(-1)&&!pressed(BUTTON_COUNT));
#endif
    early=!strcmp(mode,"early-callback");poll_only=!strcmp(mode,"poll-only");fail_at=atoi(mode);
    bsp_button_cb_t cb=poll_only?NULL:callback;
    esp_err_t e=initialize(cb,&context);
    if(fail_at){assert(e==(fail_at==1?ESP_FAIL:ESP_ERR_NO_MEM)&&!created);assert(!pressed(0));fail_at=0;assert(initialize(cb,&context)==ESP_OK);}else assert(e==ESP_OK);
    init_returned=true;int before=calls;assert(initialize(cb,&context)==ESP_OK&&created==1&&calls==before);
    assert(initialize(other_callback,&context)==ESP_ERR_INVALID_STATE&&created==1&&calls==before);
#ifndef BUTTON_SINGLE
    assert(initialize(cb,NULL)==ESP_ERR_INVALID_STATE&&created==1&&calls==before);
#endif
    if(early){assert(callbacks==2&&!pressed(0));return 0;}
    if(!strcmp(mode,"samples")||!strcmp(mode,"wrap")||!strcmp(mode,"min-tick")||poll_only){
        if(!strcmp(mode,"wrap"))tick_base=UINT32_MAX-7;
        observe=true;pthread_t worker;assert(!pthread_create(&worker,NULL,run_task,NULL));
        for(int i=0;i<10;i++){
            pthread_mutex_lock(&gate);while(observed!=i)pthread_cond_wait(&changed,&gate);
            if(TEST_TICK_MS==10)assert(pressed(0)==(!poll_only&&i>=5&&i<8));
#ifndef BUTTON_SINGLE
            for(int key=1;key<BUTTON_COUNT;key++)assert(!pressed(key));
            assert(!pressed(-1)&&!pressed(BUTTON_COUNT));
#endif
            advance=true;pthread_cond_broadcast(&changed);pthread_mutex_unlock(&gate);
        }
        pthread_join(worker,NULL);assert(callbacks==(poll_only?0:2)&&!pressed(0));
    }
    return 0;
}
