/* SPDX-License-Identifier: Apache-2.0; synthetic packets, no hardware claim. */
#undef calloc
#undef free
#include "esp_lcd_touch_spd2010.h"
#include <string.h>
static const char *mode;
static int token,allocated,reg,reads,writes,delays;
static void *memory;
void *test_calloc(size_t n,size_t size) {
    assert(!allocated);if(!strcmp(mode,"alloc"))return NULL;
    memory=calloc(n,size);assert(memory);allocated=1;return memory;
}
void test_free(void *p) {assert(allocated&&p==memory);allocated=0;free(p);}
void esp_rom_delay_us(uint32_t us) {assert(us==200);delays++;}
esp_err_t i2c_master_transmit(i2c_master_dev_handle_t device,const uint8_t *p,size_t n,int timeout) {
    assert(device==&token&&timeout==100&&(n==2||n==4));writes++;
    reg=p[0]|p[1]<<8;
    if(n==4)assert(reg==2&&p[2]==1&&p[3]==0);
    if(!strcmp(mode,"init-write")&&reg==0x26)return ESP_FAIL;
    if(!strcmp(mode,"wire-error")&&reg==0x20)return ESP_FAIL;
    return ESP_OK;
}
esp_err_t i2c_master_receive(i2c_master_dev_handle_t device,uint8_t *p,size_t n,int timeout) {
    assert(device==&token&&timeout==100&&n>0&&n<=64);reads++;memset(p,0,n);
    if(reg==0x26){assert(n==18);return !strcmp(mode,"init-read")?ESP_FAIL:ESP_OK;}
    if(reg==0x20) {
        assert(n==4);p[0]=1;p[2]=10;
        if(!strcmp(mode,"short-point"))p[2]=4;
        if(!strcmp(mode,"unaligned"))p[2]=11;
        if(!strcmp(mode,"short-gesture")){p[0]=2;p[2]=6;}
        if(!strcmp(mode,"gesture")){p[0]=2;p[2]=7;}
        if(!strcmp(mode,"mixed-gesture")){p[0]=3;p[2]=8;}
        if(!strcmp(mode,"oversize"))p[2]=65;
        if(!strcmp(mode,"poll-empty")){p[0]=0;p[1]=8;p[2]=0;}
    } else if(reg==0x300) {
        assert(n==10||n==11||n==4||n==6||n==7||n==8);
        if(n>=10){p[4]=1;p[5]=0x23;p[6]=0x56;p[7]=0x14;p[8]=7;}
        if(n>=6&&n<=8){p[4]=0xF6;if(n>=7)p[6]=3;}
    } else if(reg==0x2fc) {
        assert(n==8);p[5]=0x82;
        if(!strcmp(mode,"bad-status"))p[5]=0x7f;
        if(!strcmp(mode,"remain-oversize")){p[5]=0;p[2]=33;}
        if(!strcmp(mode,"remain-empty")){p[5]=0;p[2]=0;}
        if(!strcmp(mode,"chunk-timeout")){p[5]=0;p[2]=4;}
    } else assert(false);
    return ESP_OK;
}
int main(int argc,char **argv) {
    assert(argc==2);mode=argv[1];
    esp_lcd_touch_config_t config={.rst_gpio_num=GPIO_NUM_NC,.int_gpio_num=GPIO_NUM_NC,.x_max=412,.y_max=412};
    esp_lcd_touch_handle_t touch=(void *)1;
    if(!strcmp(mode,"invalid")){
        assert(esp_lcd_touch_new_i2c_spd2010(&token,&config,NULL)==ESP_ERR_INVALID_ARG);
        assert(esp_lcd_touch_new_i2c_spd2010(NULL,&config,&touch)==ESP_ERR_INVALID_ARG&&!touch);
        config.int_gpio_num=1;
        assert(esp_lcd_touch_new_i2c_spd2010(&token,&config,&touch)==ESP_ERR_NOT_SUPPORTED&&!touch&&!allocated);
        return 0;
    }
    esp_err_t status=esp_lcd_touch_new_i2c_spd2010(&token,&config,&touch);
    if(!strcmp(mode,"alloc")||!strcmp(mode,"init-write")||!strcmp(mode,"init-read")) {
        assert(status==(!strcmp(mode,"alloc")?ESP_ERR_NO_MEM:ESP_FAIL)&&!touch&&!allocated);return 0;
    }
    assert(status==ESP_OK&&allocated&&writes==1&&reads==1&&delays==2&&!touch->io);
    status=touch->read_data(touch);
    if(!strcmp(mode,"success")) {
        uint16_t x=0,y=0,strength=0;uint8_t count=0;
        assert(status==ESP_OK&&touch->get_xy(touch,&x,&y,&strength,&count,1));
        assert(count==1&&x==0x123&&y==0x456&&strength==7);
        assert(!touch->get_xy(touch,&x,&y,&strength,&count,1));
    } else if(!strcmp(mode,"poll-empty")||!strcmp(mode,"gesture")||!strcmp(mode,"mixed-gesture"))assert(status==ESP_OK&&!touch->data.points);
    else {
        int expected=ESP_ERR_INVALID_SIZE;
        if(!strcmp(mode,"oversize")||!strcmp(mode,"bad-status"))expected=ESP_ERR_INVALID_RESPONSE;
        if(!strcmp(mode,"wire-error"))expected=ESP_FAIL;
        if(!strcmp(mode,"chunk-timeout"))expected=ESP_ERR_TIMEOUT;
        assert(status==expected&&!touch->data.points);
    }
    assert(touch->del(touch)==ESP_OK&&!allocated);
    return 0;
}
