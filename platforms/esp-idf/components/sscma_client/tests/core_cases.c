/* SPDX-License-Identifier: Apache-2.0 */
#include "camera.h"
#include <assert.h>
#include <pthread.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
static uint8_t jpeg[]={0xff,0xd8,0xff,0xd9};
static int inits,captures,releases,starts,stops;
static bool init_fail,capture_fail,start_fail,invalid_frame;
static bool pause_capture,capture_waiting,continue_capture;
static pthread_mutex_t gate=PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t changed=PTHREAD_COND_INITIALIZER;
static esp_err_t init(void){inits++;return init_fail?ESP_FAIL:ESP_OK;}
static esp_err_t capture(camera_frame_t *out)
{
    captures++;
    pthread_mutex_lock(&gate);
    if(pause_capture){capture_waiting=true;pthread_cond_broadcast(&changed);while(!continue_capture)pthread_cond_wait(&changed,&gate);}
    pthread_mutex_unlock(&gate);
    if(capture_fail)return ESP_FAIL;
    *out=(camera_frame_t){.jpeg=jpeg,.len=invalid_frame?0:sizeof(jpeg),.width=2,.height=2};return ESP_OK;
}
static void release(camera_frame_t *frame){assert(frame->jpeg==jpeg);releases++;}
static esp_err_t stream_start(camera_frame_cb_t cb,void *ctx)
{assert(cb&&ctx);starts++;return start_fail?ESP_FAIL:ESP_OK;}
static void stream_stop(void){stops++;}
static void callback(const camera_frame_t *frame,void *ctx){(void)frame;(void)ctx;}
static const camera_driver_t driver={.name="test",.init=init,.capture=capture,.release=release,.stream_start=stream_start,.stream_stop=stream_stop};
static void success(void)
{
    camera_frame_t frame={0};assert(camera_capture(&frame)==ESP_OK&&frame.jpeg==jpeg&&frame.len==sizeof(jpeg));
    camera_release(&frame);assert(!frame.jpeg&&!frame.len);
}
static void *capture_thread(void *arg){assert(camera_capture(arg)==ESP_OK);return NULL;}
int main(int argc,char **argv)
{
    assert(argc==2);camera_frame_t frame={.jpeg=jpeg,.len=123};
    if(!strcmp(argv[1],"missing")) {
        assert(camera_capture(&frame)==ESP_ERR_NOT_SUPPORTED&&frame.len==123);
        assert(camera_stream_start(callback,&frame)==ESP_ERR_NOT_SUPPORTED);camera_stream_stop();return 0;
    }
    if(!strcmp(argv[1],"invalid-driver")) {
        camera_driver_t invalid={0};camera_register(NULL);camera_register(&invalid);
        assert(!camera_get());camera_register(&driver);success();return 0;
    }
    camera_register(&driver);assert(camera_get()==&driver);
    if(!strcmp(argv[1],"busy-frame")) {
        assert(camera_capture(&frame)==ESP_OK);size_t size=frame.len;
        assert(camera_capture(&frame)==ESP_ERR_INVALID_STATE&&frame.jpeg==jpeg&&frame.len==size);
        assert(camera_stream_start(callback,&frame)==ESP_ERR_INVALID_STATE);
        camera_release(&frame);assert(releases==1);success();return 0;
    }
    if(!strcmp(argv[1],"release")) {
        camera_release(NULL);assert(camera_capture(&frame)==ESP_OK);
        camera_frame_t copied=frame;camera_release(&copied);assert(!releases);
        assert(camera_capture(&copied)==ESP_ERR_INVALID_STATE);
        camera_release(&frame);camera_release(&frame);assert(releases==1);success();return 0;
    }
    if(!strcmp(argv[1],"replace")) {
        assert(camera_capture(&frame)==ESP_OK);camera_driver_t replacement=driver;
        camera_register(NULL);camera_register(&replacement);assert(camera_get()==&driver);
        camera_release(&frame);success();assert(inits==1);return 0;
    }
    if(!strcmp(argv[1],"null")) {
        assert(camera_capture(NULL)==ESP_ERR_INVALID_ARG);
        assert(camera_stream_start(NULL,&frame)==ESP_ERR_INVALID_ARG&&!inits);
        success();return 0;
    }
    if(!strcmp(argv[1],"init-failure")) {
        init_fail=true;assert(camera_capture(&frame)==ESP_FAIL&&frame.len==123&&!captures);
        init_fail=false;success();assert(inits==2);return 0;
    }
    if(!strcmp(argv[1],"capture-failure")) {
        capture_fail=true;assert(camera_capture(&frame)==ESP_FAIL&&frame.len==123&&!releases);
        capture_fail=false;success();assert(inits==1);return 0;
    }
    if(!strcmp(argv[1],"invalid-frame")) {
        invalid_frame=true;assert(camera_capture(&frame)==ESP_ERR_INVALID_RESPONSE&&frame.len==123&&releases==1);
        invalid_frame=false;success();return 0;
    }
    if(!strcmp(argv[1],"stream-failure")) {
        start_fail=true;assert(camera_stream_start(callback,&frame)==ESP_FAIL);
        camera_stream_stop();assert(!stops);start_fail=false;success();return 0;
    }
    if(!strcmp(argv[1],"stream")) {
        assert(camera_stream_start(callback,&frame)==ESP_OK&&starts==1);
        assert(camera_capture(&frame)==ESP_ERR_INVALID_STATE&&frame.len==123);
        assert(camera_stream_start(callback,&frame)==ESP_ERR_INVALID_STATE);
        camera_stream_stop();camera_stream_stop();assert(stops==1);success();return 0;
    }
    if(!strcmp(argv[1],"concurrent")) {
        pause_capture=true;pthread_t task;camera_frame_t held={0};
        assert(!pthread_create(&task,NULL,capture_thread,&held));
        pthread_mutex_lock(&gate);while(!capture_waiting)pthread_cond_wait(&changed,&gate);pthread_mutex_unlock(&gate);
        assert(camera_capture(&frame)==ESP_ERR_INVALID_STATE&&frame.len==123);
        assert(camera_stream_start(callback,&frame)==ESP_ERR_INVALID_STATE);
        pthread_mutex_lock(&gate);continue_capture=true;pthread_cond_broadcast(&changed);pthread_mutex_unlock(&gate);
        assert(!pthread_join(task,NULL));camera_release(&held);assert(captures==1&&releases==1);return 0;
    }
    success();success();assert(inits==1&&captures==2&&releases==2);return 0;
}
