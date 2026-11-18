/* SPDX-License-Identifier: Apache-2.0 */
#include "peripheral_stub.h"
#include "bsp_sdcard.h"
#include "bsp_pins.h"
#include <assert.h>
#undef malloc
#undef free
#include <stdlib.h>
#include <string.h>
static int calls,fail_at,allocations,unmounts;
static bool absent,borrowed,unmount_early,unmount_late;
static sdmmc_card_t card;
static const char *owned_path;
static esp_err_t step(void){return ++calls==fail_at?ESP_FAIL:ESP_OK;}
void *test_malloc(size_t size){if(step()!=ESP_OK)return NULL;void *p=malloc(size);assert(p);allocations++;return p;}
void test_free(void *p){if(p){assert(allocations==1);allocations--;free(p);}}
esp_err_t gpio_config(const gpio_config_t *c){assert(c->pin_bit_mask==1ULL<<BSP_PIN_SD_EN||c->pin_bit_mask==1ULL<<BSP_PIN_SD_DET);return step();}
esp_err_t gpio_set_level(int pin,int level){assert(pin==BSP_PIN_SD_EN&&level==1);return step();}
int gpio_get_level(int pin){assert(pin==BSP_PIN_SD_DET);return absent;}
void vTaskDelay(TickType_t ticks){assert(ticks==pdMS_TO_TICKS(20));}
esp_err_t spi_bus_initialize(int host,const spi_bus_config_t *c,int dma){
    assert(host==SPI2_HOST&&dma==SPI_DMA_CH_AUTO&&c->max_transfer_sz==4000);
    assert(c->sclk_io_num==BSP_PIN_SD_SCLK&&c->mosi_io_num==BSP_PIN_SD_MOSI&&c->miso_io_num==BSP_PIN_SD_MISO);
    esp_err_t e=step();return e?e:(borrowed?ESP_ERR_INVALID_STATE:ESP_OK);}
esp_err_t esp_vfs_fat_sdspi_mount(const char *path,const sdmmc_host_t *host,const sdspi_device_config_t *slot,const esp_vfs_fat_sdmmc_mount_config_t *cfg,sdmmc_card_t **out){
    assert(!card.alive&&!cfg->format_if_mount_failed&&cfg->max_files==5&&cfg->allocation_unit_size==16384);
    assert(host->slot==SPI2_HOST&&slot->host_id==SPI2_HOST&&slot->gpio_cs==BSP_PIN_SD_CS);
    esp_err_t e=step();if(!e){owned_path=path;card.alive=1;*out=&card;}return e;}
esp_err_t esp_vfs_fat_sdcard_unmount(const char *path,sdmmc_card_t *c){
    assert(c==&card&&card.alive&&!strcmp(path,"/sd")&&!strcmp(owned_path,path));unmounts++;
    if(unmount_early)return ESP_FAIL;
    card.alive=0;owned_path=NULL;return unmount_late?ESP_FAIL:ESP_OK;}
int main(int argc,char **argv){
    assert(argc>1);const char *mode=argv[1];sdmmc_card_t *out=(void *)1;
    if(!strcmp(mode,"null")){assert(bsp_sdcard_init(NULL,&out)==ESP_ERR_INVALID_ARG&&!out&&!calls);assert(bsp_sdcard_deinit(NULL)==ESP_ERR_INVALID_ARG);return 0;}
    if(!strcmp(mode,"detect")){bool inserted=true;fail_at=1;assert(bsp_sdcard_is_inserted(&inserted)==ESP_FAIL&&inserted);assert(bsp_sdcard_is_inserted(NULL)==ESP_ERR_INVALID_ARG);return 0;}
    absent=!strcmp(mode,"absent");borrowed=!strcmp(mode,"borrowed-bus");fail_at=!strcmp(mode,"allocation")?5:atoi(mode);
    char path[]="/sd";esp_err_t e=bsp_sdcard_init(path,&out);
    if(absent||fail_at){assert(e==(absent?ESP_ERR_NOT_FOUND:(fail_at==5?ESP_ERR_NO_MEM:ESP_FAIL)));assert(!out&&!allocations&&!card.alive);
        absent=false;fail_at=0;calls=0;assert(bsp_sdcard_init(path,&out)==ESP_OK);
    }else assert(e==ESP_OK);
    assert(out==&card&&allocations==1);int before=calls;
    assert(bsp_sdcard_init("/sd",NULL)==ESP_OK&&calls==before);
    assert(bsp_sdcard_init("/other",&out)==ESP_ERR_INVALID_STATE&&!out&&calls==before);
    assert(bsp_sdcard_deinit("/other")==ESP_ERR_INVALID_STATE&&!unmounts);
    path[1]='x'; /* caller's storage is no longer the mount path */
    unmount_early=!strcmp(mode,"unmount-early");unmount_late=!strcmp(mode,"unmount-late");
    e=bsp_sdcard_deinit("/sd");assert(!allocations&&unmounts==1);
    if(unmount_early||unmount_late){assert(e==ESP_FAIL);assert(bsp_sdcard_deinit("/sd")==ESP_ERR_INVALID_STATE);assert(bsp_sdcard_init("/sd",&out)==ESP_ERR_INVALID_STATE&&!out&&unmounts==1);}
    else {assert(e==ESP_OK&&!card.alive);assert(bsp_sdcard_deinit("/sd")==ESP_OK&&unmounts==1);assert(bsp_sdcard_init("/sd",&out)==ESP_OK);assert(bsp_sdcard_deinit("/sd")==ESP_OK);}
    return 0;
}
