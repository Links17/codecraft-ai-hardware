/* SPDX-License-Identifier: Apache-2.0
 * Execute the real BSP C file with deterministic resource/failure doubles.
 * Each process starts with fresh BSP static state; no private state is reset.
 */
#include "idf_bsp_stub.h"
#include "bsp_display.h"
#include "bsp_io_expander.h"
#include "bsp_pins.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum {
    EXPANDER=1, DIRECTION, RAIL, TIMER, CHANNEL, BUS, IO, PANEL,
    RESET, INIT, MIRROR, ON, DUTY, UPDATE,
    PANEL_FREE, IO_FREE, BUS_FREE, CHANNEL_STOP, CHANNEL_FREE, TIMER_PAUSE, TIMER_FREE
};
static int fail_step, cleanup_failure, calls;
static bool timer, channel, bus, io, panel, ready, stopped, paused;
static bool rail_on;
static int io_token, panel_token;

static esp_err_t step(int id)
{
    ++calls;
    return (id==fail_step || id==cleanup_failure) ? ESP_FAIL : ESP_OK;
}
#define TRY(id) do { if(step(id)!=ESP_OK) return ESP_FAIL; } while(0)

void vTaskDelay(int ticks) { assert(ticks>=0); }
esp_err_t bsp_io_expander_init(void) { return step(EXPANDER); }
esp_err_t bsp_io_expander_set_direction(int pin, int output)
{ assert(pin==BSP_EXP_PIN_PWR_LCD && output==1); return step(DIRECTION); }
esp_err_t bsp_io_expander_set_level(int pin, int level)
{ assert(pin==BSP_EXP_PIN_PWR_LCD && level==1); TRY(RAIL); rail_on=true; return ESP_OK; }

esp_err_t ledc_timer_config(const ledc_timer_config_t *c)
{
    if(c->deconfigure) { assert(timer && paused && !channel); TRY(TIMER_FREE); timer=false; }
    else { assert(!timer); TRY(TIMER); timer=true; paused=false; }
    return ESP_OK;
}
esp_err_t ledc_channel_config(const ledc_channel_config_t *c)
{
    if(c->deconfigure) { assert(channel && stopped); TRY(CHANNEL_FREE); channel=false; }
    else { assert(timer && !channel); TRY(CHANNEL); channel=true; stopped=false; }
    return ESP_OK;
}
esp_err_t ledc_set_duty(int mode, int ch, uint32_t duty)
{ (void)mode;(void)ch;(void)duty;assert(channel); return step(DUTY); }
esp_err_t ledc_update_duty(int mode, int ch)
{ (void)mode;(void)ch;assert(channel);return step(UPDATE); }
esp_err_t ledc_stop(int mode, int ch, uint32_t idle)
{ (void)mode;(void)ch;assert(channel && idle==0);TRY(CHANNEL_STOP);stopped=true;return ESP_OK; }
esp_err_t ledc_timer_pause(int mode, int t)
{ (void)mode;(void)t;assert(timer && !channel);TRY(TIMER_PAUSE);paused=true;return ESP_OK; }
esp_err_t spi_bus_initialize(int host, const spi_bus_config_t *c, int dma)
{ (void)c;(void)dma;assert(host==SPI3_HOST && !bus);TRY(BUS);bus=true;return ESP_OK; }
esp_err_t spi_bus_free(int host)
{ assert(host==SPI3_HOST && bus && !io);TRY(BUS_FREE);bus=false;return ESP_OK; }
esp_err_t esp_lcd_new_panel_io_spi(esp_lcd_spi_bus_handle_t host, const esp_lcd_panel_io_spi_config_t *c, esp_lcd_panel_io_handle_t *out)
{ (void)c;assert(host==SPI3_HOST && bus && !io);TRY(IO);io=true;*out=&io_token;return ESP_OK; }
esp_err_t esp_lcd_panel_io_del(esp_lcd_panel_io_handle_t handle)
{ assert(handle==&io_token && io && !panel);TRY(IO_FREE);io=false;return ESP_OK; }
esp_err_t esp_lcd_new_panel_spd2010(esp_lcd_panel_io_handle_t handle, const esp_lcd_panel_dev_config_t *c, esp_lcd_panel_handle_t *out)
{ (void)c;assert(handle==&io_token && io && !panel);TRY(PANEL);panel=true;*out=&panel_token;return ESP_OK; }
esp_err_t esp_lcd_panel_del(esp_lcd_panel_handle_t handle)
{ assert(handle==&panel_token && panel);TRY(PANEL_FREE);panel=false;ready=false;return ESP_OK; }
esp_err_t esp_lcd_panel_reset(esp_lcd_panel_handle_t handle)
{ assert(handle==&panel_token && panel);return step(RESET); }
esp_err_t esp_lcd_panel_init(esp_lcd_panel_handle_t handle)
{ assert(handle==&panel_token && panel);TRY(INIT);ready=true;return ESP_OK; }
esp_err_t esp_lcd_panel_mirror(esp_lcd_panel_handle_t handle, bool x, bool y)
{ assert(handle==&panel_token && panel && ready && !x && !y);return step(MIRROR); }
esp_err_t esp_lcd_panel_disp_on_off(esp_lcd_panel_handle_t handle, bool on)
{ assert(handle==&panel_token && panel && ready && on);return step(ON); }

static void success(void)
{
    esp_lcd_panel_handle_t p=NULL;esp_lcd_panel_io_handle_t i=NULL;
    assert(bsp_display_init(&p,&i)==ESP_OK);
    assert(p==&panel_token && i==&io_token && panel && io && bus && channel && timer && ready);
    int before=calls;
    assert(bsp_display_init(NULL,NULL)==ESP_OK && calls==before);
    p=NULL;i=NULL;assert(bsp_display_init(&p,&i)==ESP_OK);
    assert(p==&panel_token && i==&io_token && calls==before);
    assert(bsp_display_set_brightness(0)==ESP_OK);
}

int main(int argc,char **argv)
{
    assert(argc>=2);
    if(strcmp(argv[1],"retry")==0) {
        fail_step=RESET;
        assert(bsp_display_init(NULL,NULL)==ESP_FAIL);
        fail_step=0;
        success(); /* The old driver returns an allocated but uninitialized panel. */
        return 0;
    }
    fail_step=atoi(argv[1]);cleanup_failure=argc>2 ? atoi(argv[2]) : 0;
    assert(bsp_display_set_brightness(50)==ESP_ERR_INVALID_STATE);
    if(!fail_step) { success();return 0; }
    esp_lcd_panel_handle_t p=(void *)1;esp_lcd_panel_io_handle_t i=(void *)1;
    assert(bsp_display_init(&p,&i)==ESP_FAIL);
    assert(!p && !i); /* Never expose incomplete or stale handles. */
    assert(bsp_display_set_brightness(50)==ESP_ERR_INVALID_STATE);
    if(fail_step>RAIL) assert(rail_on); /* Shared touch power must survive rollback. */
    if(cleanup_failure) {
        assert(panel || io || bus || channel || timer);
        int before=calls;
        fail_step=0;cleanup_failure=0;
        assert(bsp_display_init(&p,&i)==ESP_ERR_INVALID_STATE);
        assert(!p && !i && calls==before); /* No double release or handle overwrite. */
    } else {
        assert(!panel && !io && !bus && !channel && !timer);
        fail_step=0;success();
    }
    puts("display failure/retry invariants passed");
    return 0;
}
