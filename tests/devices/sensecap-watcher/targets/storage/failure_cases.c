/* SPDX-License-Identifier: Apache-2.0 */
#include "storage_stub.h"
#include "bsp_sdcard.h"
#include "bsp_io_expander.h"
#include "bsp_pins.h"
#undef malloc
#undef free
#include <assert.h>
#include <stdlib.h>
#include <string.h>
enum { EXP=1, RAIL_DIR, RAIL_ON, DET_DIR, DETECT, BUS, ALLOC, MOUNT, UNMOUNT };
static int fault, calls, allocs, mounts, unmounts;
static bool bus, mounted, absent, early_unmount_error;
static sdmmc_card_t card;
static esp_err_t step(int n) { calls++;return fault==n ? ESP_FAIL : ESP_OK; }
#define TRY(n) do { esp_err_t e=step(n);if(e!=ESP_OK)return e; } while(0)
void *test_malloc(size_t size) { if(step(ALLOC)!=ESP_OK)return NULL;allocs++;return malloc(size); }
void test_free(void *p) { if(p){assert(allocs>0);allocs--;free(p);} }
esp_err_t bsp_io_expander_init(void) { return step(EXP); }
esp_err_t bsp_io_expander_set_direction(int pin,int output)
{ if(pin==BSP_EXP_PIN_PWR_SDCARD){assert(output);return step(RAIL_DIR);}assert(pin==BSP_EXP_PIN_SD_DET&&!output);return step(DET_DIR); }
esp_err_t bsp_io_expander_set_level(int pin,int level)
{ assert(pin==BSP_EXP_PIN_PWR_SDCARD&&level==1);return step(RAIL_ON); }
esp_err_t bsp_io_expander_get_level(int pin,int *level)
{ assert(pin==BSP_EXP_PIN_SD_DET);TRY(DETECT);*level=absent;return ESP_OK; }
esp_err_t spi_bus_initialize(int host,const spi_bus_config_t *cfg,int dma)
{
    assert(host==SPI2_HOST&&dma==SPI_DMA_CH_AUTO&&cfg->sclk_io_num==BSP_PIN_SPI2_SCLK);
    assert(cfg->mosi_io_num==BSP_PIN_SPI2_MOSI&&cfg->miso_io_num==BSP_PIN_SPI2_MISO&&cfg->max_transfer_sz==4096);
    TRY(BUS);if(bus)return ESP_ERR_INVALID_STATE;bus=true;return ESP_OK;
}
esp_err_t esp_vfs_fat_sdspi_mount(const char *path,const sdmmc_host_t *host,
    const sdspi_device_config_t *slot,const esp_vfs_fat_sdmmc_mount_config_t *cfg,sdmmc_card_t **out)
{
    assert(bus&&!mounted&&!strcmp(path,"/sdcard")&&host->slot==SPI2_HOST);
    assert(slot->host_id==SPI2_HOST&&slot->gpio_cs==BSP_PIN_SD_CS);
    assert(!cfg->format_if_mount_failed&&cfg->max_files==5&&cfg->allocation_unit_size==16*1024);
    mounts++;TRY(MOUNT);mounted=true;*out=&card;return ESP_OK;
}
esp_err_t esp_vfs_fat_sdcard_unmount(const char *path,sdmmc_card_t *handle)
{
    assert(mounted&&handle==&card&&!strcmp(path,"/sdcard"));unmounts++;
    if(fault==UNMOUNT&&early_unmount_error)return step(UNMOUNT);
    mounted=false;return step(UNMOUNT); /* SDK may free before a later error. */
}
static void success(void)
{
    char path[]="/sdcard";sdmmc_card_t *out=NULL;
    assert(bsp_sdcard_init(path,&out)==ESP_OK&&out==&card&&mounted&&allocs==1);
    path[1]='X'; /* Lifetime belongs to BSP, not this caller buffer. */
    int before=calls;assert(bsp_sdcard_init("/sdcard",NULL)==ESP_OK&&before==calls);
    assert(bsp_sdcard_deinit("/sdcard")==ESP_OK&&!mounted&&allocs==0&&bus);
    before=calls;assert(bsp_sdcard_deinit("/sdcard")==ESP_OK&&before==calls);
}
int main(int argc,char **argv)
{
    assert(argc==2);sdmmc_card_t *out=&card;
    if(!strcmp(argv[1],"wrong-path")) {
        assert(bsp_sdcard_init("/sdcard",&out)==ESP_OK);int before=calls;
        assert(bsp_sdcard_init("/different",&out)==ESP_ERR_INVALID_STATE&&out==NULL&&before==calls);
        assert(bsp_sdcard_deinit("/different")==ESP_ERR_INVALID_STATE&&before==calls&&mounted);
        assert(bsp_sdcard_deinit("/sdcard")==ESP_OK&&allocs==0);return 0;
    }
    if(!strcmp(argv[1],"unmount-late")||!strcmp(argv[1],"unmount-early")) {
        assert(bsp_sdcard_init("/sdcard",&out)==ESP_OK);fault=UNMOUNT;
        early_unmount_error=!strcmp(argv[1],"unmount-early");
        assert(bsp_sdcard_deinit("/sdcard")==ESP_FAIL&&allocs==0&&unmounts==1);
        fault=0;int before=calls;
        assert(bsp_sdcard_init("/sdcard",&out)==ESP_ERR_INVALID_STATE&&out==NULL&&before==calls);
        assert(bsp_sdcard_deinit("/sdcard")==ESP_ERR_INVALID_STATE&&before==calls);return 0;
    }
    assert(bsp_sdcard_init(NULL,&out)==ESP_ERR_INVALID_ARG&&out==NULL);
    assert(bsp_sdcard_deinit(NULL)==ESP_ERR_INVALID_ARG);
    assert(bsp_sdcard_is_inserted(NULL)==ESP_ERR_INVALID_ARG);
    if(!strcmp(argv[1],"absent")) {
        absent=true;assert(bsp_sdcard_init("/sdcard",&out)==ESP_ERR_NOT_FOUND&&out==NULL&&!mounted&&!allocs);
        absent=false;success();return 0;
    }
    if(!strcmp(argv[1],"borrowed-bus")) {bus=true;success();return 0;}
    fault=atoi(argv[1]);
    if(!fault) {success();success();return 0;}
    out=&card;assert(bsp_sdcard_init("/sdcard",&out)==(fault==ALLOC?ESP_ERR_NO_MEM:ESP_FAIL));
    assert(out==NULL&&!mounted&&!allocs);
    if(fault==DETECT){bool inserted=true;assert(bsp_sdcard_is_inserted(&inserted)==ESP_FAIL&&inserted);}
    fault=0;success();return 0;
}
