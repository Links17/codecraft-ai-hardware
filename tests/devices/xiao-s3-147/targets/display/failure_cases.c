/* SPDX-License-Identifier: Apache-2.0
 * Execute the real BSP with narrow native-allocation and DMA doubles. */
#include "bsp_display.h"
#include "bsp_pins.h"
#include "lcd_stub.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int failure,cleanup_failure,calls,delete_calls,commands;
static bool bus_live,io_live,panel_live,borrowed_bus,draw_error;
static int io_object,panel_object;
static uint64_t wire=1469598103934665603ULL;
static const uint16_t *pending;
static size_t pending_count;
static uint16_t pending_value;
static int drains,draws;
static void hash(unsigned value){wire=(wire^value)*1099511628211ULL;}
static esp_err_t step(int stage)
{
    ++calls;
    if(failure==stage){failure=0;return ESP_FAIL;}
    if(cleanup_failure==stage){cleanup_failure=0;return ESP_FAIL;}
    return ESP_OK;
}
esp_err_t gpio_config(const gpio_config_t *c)
{
    hash(1);hash((unsigned)c->pin_bit_mask);hash((unsigned)(c->pin_bit_mask>>32));
    assert(c->mode==GPIO_MODE_OUTPUT);
    if(c->pin_bit_mask==(1ULL<<BSP_PIN_LCD_RST)) return step(3);
    assert(c->pin_bit_mask==((1ULL<<BSP_PIN_LCD_BL)|(1ULL<<BSP_PIN_SD_CS)));
    return step(1);
}
esp_err_t gpio_set_level(int pin,int value)
{
    hash(2);hash(pin);hash(value);
    if(pin==BSP_PIN_SD_CS){assert(value==1);return step(2);}
    if(pin==BSP_PIN_LCD_RST)return step(value?5:4);
    assert(pin==BSP_PIN_LCD_BL);return step(30);
}
void vTaskDelay(unsigned ticks){hash(3);hash(ticks);}
esp_err_t spi_bus_initialize(int host,const spi_bus_config_t *cfg,int dma)
{
    assert(host==SPI2_HOST&&dma==SPI_DMA_CH_AUTO);
    assert(cfg->sclk_io_num==BSP_PIN_LCD_SCLK&&cfg->mosi_io_num==BSP_PIN_LCD_MOSI);
    assert(cfg->miso_io_num==GPIO_NUM_NC&&cfg->quadwp_io_num==GPIO_NUM_NC&&cfg->quadhd_io_num==GPIO_NUM_NC);
    esp_err_t ret=step(6);if(ret!=ESP_OK)return ret;
    if(bus_live||borrowed_bus)return ESP_ERR_INVALID_STATE;
    bus_live=true;return ESP_OK;
}
esp_err_t esp_lcd_new_panel_io_spi(esp_lcd_spi_bus_handle_t bus,const esp_lcd_panel_io_spi_config_t *c,esp_lcd_panel_io_handle_t *out)
{
    assert(bus==SPI2_HOST&&(bus_live||borrowed_bus)&&!io_live);
    assert(c->cs_gpio_num==BSP_PIN_LCD_CS&&c->dc_gpio_num==BSP_PIN_LCD_DC);
    assert(c->spi_mode==0&&c->pclk_hz==40000000&&c->trans_queue_depth==10&&c->lcd_cmd_bits==8&&c->lcd_param_bits==8);
    esp_err_t ret=step(7);if(ret!=ESP_OK)return ret;
    io_live=true;*out=&io_object;return ESP_OK;
}
esp_err_t esp_lcd_new_panel_st7789(esp_lcd_panel_io_handle_t io,const esp_lcd_panel_dev_config_t *c,esp_lcd_panel_handle_t *out)
{
    assert(io==&io_object&&io_live&&!panel_live);
    assert(c->reset_gpio_num==GPIO_NUM_NC&&c->rgb_ele_order==LCD_RGB_ELEMENT_ORDER_RGB&&c->bits_per_pixel==16);
    esp_err_t ret=step(8);if(ret!=ESP_OK)return ret;
    panel_live=true;commands=0;*out=&panel_object;return ESP_OK;
}
esp_err_t esp_lcd_panel_init(esp_lcd_panel_handle_t p){assert(p==&panel_object&&panel_live);return step(9);}
esp_err_t esp_lcd_panel_io_tx_param(esp_lcd_panel_io_handle_t io,int cmd,const void *data,size_t size)
{
    assert(io==&io_object&&io_live);
    if(cmd==-1){
        assert(data==NULL&&size==0);
        esp_err_t ret=step(42);if(ret!=ESP_OK)return ret;
        for(size_t i=0;i<pending_count;i++)assert(pending[i]==pending_value);
        pending=NULL;pending_count=0;++drains;return ESP_OK;
    }
    hash(4);hash(cmd);hash((unsigned)size);
    for(size_t i=0;i<size;i++)hash(((const uint8_t *)data)[i]);
    return step(10+commands++);
}
esp_err_t esp_lcd_panel_mirror(esp_lcd_panel_handle_t p,bool x,bool y){assert(p==&panel_object&&x&&!y);hash(5);hash(x);hash(y);return step(26);}
esp_err_t esp_lcd_panel_set_gap(esp_lcd_panel_handle_t p,int x,int y){assert(p==&panel_object&&x==34&&y==0);hash(6);hash(x);hash(y);return step(27);}
esp_err_t esp_lcd_panel_invert_color(esp_lcd_panel_handle_t p,bool on){assert(p==&panel_object&&!on);hash(7);hash(on);return step(28);}
esp_err_t esp_lcd_panel_disp_on_off(esp_lcd_panel_handle_t p,bool on){assert(p==&panel_object&&on);hash(8);hash(on);return step(29);}
esp_err_t esp_lcd_panel_del(esp_lcd_panel_handle_t p)
{
    assert(p==&panel_object&&panel_live&&io_live);++delete_calls;
    esp_err_t ret=step(40);if(ret==ESP_OK)panel_live=false;return ret;
}
esp_err_t esp_lcd_panel_io_del(esp_lcd_panel_io_handle_t io)
{
    assert(io==&io_object&&io_live&&!panel_live);++delete_calls;
    esp_err_t ret=step(41);if(ret==ESP_OK)io_live=false;return ret;
}
esp_err_t esp_lcd_panel_draw_bitmap(esp_lcd_panel_handle_t p,int x0,int y0,int x1,int y1,const void *data)
{
    assert(p==&panel_object&&panel_live&&!pending);
    assert(x0==0&&x1==BSP_LCD_HRES&&y1>y0&&data);
    pending=data;pending_count=(size_t)(x1-x0)*(y1-y0);pending_value=pending[0];++draws;
    return draw_error?ESP_FAIL:ESP_OK;
}
#ifdef TEST_ORIGINAL
/* Original BSP has no drain entry. Only wire/old-behavior cases use it. */
esp_err_t bsp_display_wait_idle(void){return ESP_ERR_INVALID_STATE;}
#endif
void app_main(void);
int main(int argc,char **argv)
{
    assert(argc>=2);const char *mode=argv[1];
    esp_lcd_panel_handle_t panel=(void *)1;
    if(!strcmp(mode,"wire")){
        assert(bsp_display_init(&panel)==ESP_OK);printf("%llu\n",(unsigned long long)wire);return 0;
    }
    if(!strcmp(mode,"example")){
        app_main();assert(draws==3&&drains==3&&!pending);return 0;
    }
    if(!strcmp(mode,"unready")){
        assert(bsp_display_backlight(true)==ESP_ERR_INVALID_STATE);
        assert(bsp_display_wait_idle()==ESP_ERR_INVALID_STATE&&calls==0);return 0;
    }
    assert(bsp_display_init(NULL)==ESP_ERR_INVALID_ARG&&calls==0);
    borrowed_bus=!strcmp(mode,"borrowed");
    failure=atoi(mode);cleanup_failure=argc>2?atoi(argv[2]):0;
    int expected=failure,cleanup=cleanup_failure;
    esp_err_t ret=bsp_display_init(&panel);
    if(expected){
        assert(ret==ESP_FAIL&&failure==0&&panel==NULL);
        assert(bsp_display_backlight(true)==ESP_ERR_INVALID_STATE);
        assert(bsp_display_wait_idle()==ESP_ERR_INVALID_STATE);
        if(cleanup){
            assert(cleanup_failure==0&&io_live);
            int prior=calls;
            assert(bsp_display_init(&panel)==ESP_ERR_INVALID_STATE&&panel==NULL&&calls==prior);
            return 0;
        }
        assert(!panel_live&&!io_live);
        assert(bsp_display_init(&panel)==ESP_OK);
    }else assert(ret==ESP_OK);
    assert(panel==&panel_object&&panel_live&&io_live);
    int prior=calls;uint64_t prior_wire=wire;
    assert(bsp_display_init(&panel)==ESP_OK&&calls==prior&&wire==prior_wire);
    assert(bsp_display_backlight(false)==ESP_OK);
    failure=30;assert(bsp_display_backlight(true)==ESP_FAIL);
    if(!strcmp(mode,"drain")||!strcmp(mode,"wait-error")||!strcmp(mode,"draw-error")){
        static uint16_t pixels[BSP_LCD_HRES];
        draw_error=!strcmp(mode,"draw-error");
        assert(esp_lcd_panel_draw_bitmap(panel,0,0,BSP_LCD_HRES,1,pixels)==(draw_error?ESP_FAIL:ESP_OK));
        if(!strcmp(mode,"wait-error")){
            failure=42;assert(bsp_display_wait_idle()==ESP_FAIL&&pending);
        }
        assert(bsp_display_wait_idle()==ESP_OK&&!pending);
        pixels[0]=1; /* Reuse is safe only after the drain succeeds. */
    }
    assert(bsp_display_wait_idle()==ESP_OK);
    return 0;
}
