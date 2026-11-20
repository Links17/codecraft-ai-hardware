/* SPDX-License-Identifier: Apache-2.0 */
#include <assert.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>
#include "sensor_stub.h"
#ifdef TEST_BSP
#include "bsp_rtc.h"
#include "bsp_pins.h"
#define initialize() bsp_rtc_init()
#define read_time(out) bsp_rtc_get_time(out)
#define write_time(in) bsp_rtc_set_time(in)
#else
#include "codecraft_pcf8563.h"
static codecraft_pcf8563_handle_t rtc;
#define initialize() codecraft_pcf8563_create(test_bus,&test_config,100,&rtc)
#define read_time(out) codecraft_pcf8563_get_time(rtc,out)
#define write_time(in) codecraft_pcf8563_set_time(rtc,in)
#endif

int main(int argc, char **argv)
{
    assert(argc==2);
    struct tm out; memset(&out,0xA5,sizeof(out));
    struct tm untouched=out;
    const struct tm valid={.tm_year=126,.tm_mon=10,.tm_mday=18,.tm_wday=3,.tm_hour=13,.tm_min=42,.tm_sec=59};
    memcpy(frame,(uint8_t[]){0x59,0x42,0x13,0x18,0x03,0x11,0x26},7);
    if (!strcmp(argv[1],"before-init")) {
        assert(read_time(&out)==ESP_ERR_INVALID_STATE);
        assert(write_time(&valid)==ESP_ERR_INVALID_STATE);
        assert(memcmp(&out,&untouched,sizeof(out))==0); return 0;
    }
#ifndef TEST_BSP
    if (!strcmp(argv[1],"invalid-create")) {
        assert(codecraft_pcf8563_create(NULL,&test_config,100,&rtc)==ESP_ERR_INVALID_ARG);
        assert(codecraft_pcf8563_create(test_bus,NULL,100,&rtc)==ESP_ERR_INVALID_ARG);
        assert(codecraft_pcf8563_create(test_bus,&test_config,0,&rtc)==ESP_ERR_INVALID_ARG);
        assert(codecraft_pcf8563_create(test_bus,&test_config,100,NULL)==ESP_ERR_INVALID_ARG);
        check_clean(); return 0;
    }
    int requested=atoi(argv[1]);
    if (requested==ALLOC || requested==PROBE || requested==ADD) {
        fault=requested;
        assert(initialize()==(requested==PROBE?ESP_ERR_NOT_FOUND:requested==ADD?ESP_FAIL:ESP_ERR_NO_MEM));
        assert(rtc==NULL); check_clean(); fault=0;
    }
#endif
    assert(initialize()==ESP_OK && devices==1);
    if (!strcmp(argv[1],"init")) {
#ifdef TEST_BSP
        assert(attached_address==BSP_I2C_ADDR_RTC && attached_speed==BSP_I2C0_FREQ_HZ);
        assert(initialize()==ESP_OK && devices==1);
#else
        codecraft_pcf8563_handle_t saved=rtc;
        assert(initialize()==ESP_ERR_INVALID_ARG && rtc==saved && devices==1);
#endif
    } else if (!strcmp(argv[1],"voltage-low")) {
        frame[0]|=0x80; assert(read_time(&out)==ESP_ERR_INVALID_STATE);
        assert(memcmp(&out,&untouched,sizeof(out))==0); frame[0]&=0x7F;
    } else if (!strcmp(argv[1],"corrupt")) {
        const uint8_t bad[][2]={{0,0x6A},{1,0x60},{2,0x24},{3,0x00},{4,0x07},{5,0x00},{5,0x13},{6,0xFA}};
        for (size_t i=0;i<sizeof(bad)/sizeof(bad[0]);i++) {
            uint8_t saved=frame[bad[i][0]]; frame[bad[i][0]]=bad[i][1];
            assert(read_time(&out)==ESP_ERR_INVALID_RESPONSE);
            assert(memcmp(&out,&untouched,sizeof(out))==0); frame[bad[i][0]]=saved;
        }
    } else if (!strcmp(argv[1],"invalid-args")) {
        assert(read_time(NULL)==ESP_ERR_INVALID_ARG && write_time(NULL)==ESP_ERR_INVALID_ARG);
        struct tm bad=valid;
        int *fields[]={&bad.tm_year,&bad.tm_year,&bad.tm_mon,&bad.tm_mday,&bad.tm_wday,&bad.tm_hour,&bad.tm_min,&bad.tm_sec};
        const int values[]={INT_MAX,99,12,0,7,24,60,-1};
        for (size_t i=0;i<sizeof(values)/sizeof(values[0]);i++) {
            bad=valid; *fields[i]=values[i];
            assert(write_time(&bad)==ESP_ERR_INVALID_ARG && sent_size==0);
        }
    } else if (!strcmp(argv[1],"timeout")) {
        fault=TRANSCEIVE; assert(read_time(&out)==ESP_ERR_TIMEOUT);
        assert(memcmp(&out,&untouched,sizeof(out))==0);
        fault=TRANSMIT; assert(write_time(&valid)==ESP_ERR_TIMEOUT); fault=0;
    }
    assert(read_time(&out)==ESP_OK);
    assert(out.tm_year==126 && out.tm_mon==10 && out.tm_mday==18 && out.tm_wday==3);
    assert(out.tm_hour==13 && out.tm_min==42 && out.tm_sec==59 && out.tm_yday==-1 && out.tm_isdst==-1);
    assert(write_time(&valid)==ESP_OK && sent_size==8);
    assert(memcmp(sent,(uint8_t[]){2,0x59,0x42,0x13,0x18,3,0x11,0x26},8)==0);
    /* Existing century/masking convention is preserved. */
    frame[5]|=0x80; assert(read_time(&out)==ESP_OK && out.tm_year==126 && out.tm_mon==10);
#ifndef TEST_BSP
    if (!strcmp(argv[1],"delete-failure")) {
        fault=REMOVE; codecraft_pcf8563_handle_t saved=rtc;
        assert(codecraft_pcf8563_delete(&rtc)==ESP_FAIL && rtc==saved && devices==1 && allocations==1);
        fault=0;
    }
    assert(codecraft_pcf8563_delete(&rtc)==ESP_OK && rtc==NULL);
    assert(codecraft_pcf8563_delete(&rtc)==ESP_ERR_INVALID_ARG); check_clean();
#endif
    return 0;
}
