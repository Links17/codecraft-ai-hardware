/* SPDX-License-Identifier: Apache-2.0
 * Narrow host test doubles for Watcher display and expander ESP-IDF calls.
 * Numeric constants below are test API identities, not hardware facts.
 */
#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef int esp_err_t;
enum { ESP_OK=0, ESP_FAIL=-1, ESP_ERR_NO_MEM=0x101, ESP_ERR_INVALID_STATE=0x103,
       ESP_ERR_INVALID_ARG=0x102, ESP_ERR_NOT_FOUND=0x105, ESP_ERR_NOT_SUPPORTED=0x106,
       ESP_ERR_TIMEOUT=0x107, ESP_ERR_INVALID_RESPONSE=0x108 };
typedef void *esp_lcd_panel_handle_t;
typedef void *esp_lcd_panel_io_handle_t;
typedef int esp_lcd_spi_bus_handle_t;
typedef void *i2c_master_bus_handle_t;
typedef void *i2c_master_dev_handle_t;
enum { I2C_CLK_SRC_DEFAULT=0, I2C_ADDR_BIT_LEN_7=0 };
typedef struct {
    int i2c_port, sda_io_num, scl_io_num, clk_source, glitch_ignore_cnt;
    struct { bool enable_internal_pullup; } flags;
} i2c_master_bus_config_t;
typedef struct { int dev_addr_length, device_address, scl_speed_hz; } i2c_device_config_t;
esp_err_t i2c_new_master_bus(const i2c_master_bus_config_t *config, i2c_master_bus_handle_t *bus);
esp_err_t i2c_del_master_bus(i2c_master_bus_handle_t bus);
esp_err_t i2c_master_bus_add_device(i2c_master_bus_handle_t bus, const i2c_device_config_t *config, i2c_master_dev_handle_t *dev);
esp_err_t i2c_master_bus_rm_device(i2c_master_dev_handle_t dev);
esp_err_t i2c_master_probe(i2c_master_bus_handle_t bus, int address, int timeout);
esp_err_t i2c_master_transmit(i2c_master_dev_handle_t dev, const uint8_t *data, size_t size, int timeout);
esp_err_t i2c_master_transmit_receive(i2c_master_dev_handle_t dev, const uint8_t *data, size_t size, uint8_t *output, size_t output_size, int timeout);
enum { SPI2_HOST=1, SPI3_HOST=2, SPI_DMA_CH_AUTO=3, LEDC_TIMER_0=0, LEDC_LOW_SPEED_MODE=0,
       LEDC_CHANNEL_1=1, LEDC_TIMER_10_BIT=10, LEDC_AUTO_CLK=0, LEDC_INTR_DISABLE=0,
       LCD_RGB_ELEMENT_ORDER_RGB=0 };
#define BIT(n) (1U << (n))
#define pdMS_TO_TICKS(n) (n)
#define ESP_RETURN_ON_ERROR(call, tag, ...) do { (void)(tag); esp_err_t e_=(call); if(e_!=ESP_OK) return e_; } while(0)
#define ESP_RETURN_ON_FALSE(test, error, tag, ...) do { (void)(tag); if(!(test)) return (error); } while(0)
#define ESP_GOTO_ON_ERROR(call, label, tag, ...) do { (void)(tag); ret=(call); if(ret!=ESP_OK) goto label; } while(0)
#define ESP_GOTO_ON_FALSE(test, error, label, tag, ...) do { (void)(tag); if(!(test)) { ret=(error); goto label; } } while(0)
#define ESP_LOGI(tag, ...) ((void)(tag))
#define ESP_LOGE(tag, ...) ((void)(tag))
#define ESP_LOGW(tag, ...) ((void)(tag))
static inline const char *esp_err_to_name(esp_err_t error) { (void)error; return "injected error"; }
void vTaskDelay(int ticks);

typedef struct { int speed_mode, duty_resolution, timer_num, freq_hz, clk_cfg; bool deconfigure; } ledc_timer_config_t;
typedef struct { int speed_mode, channel, timer_sel, intr_type, gpio_num, duty, hpoint; bool deconfigure; } ledc_channel_config_t;
typedef struct { int sclk_io_num, data0_io_num, data1_io_num, data2_io_num, data3_io_num, max_transfer_sz,
                     mosi_io_num, miso_io_num, quadwp_io_num, quadhd_io_num; } spi_bus_config_t;
typedef struct {
    int cs_gpio_num, dc_gpio_num, spi_mode, pclk_hz, trans_queue_depth, lcd_cmd_bits, lcd_param_bits;
    struct { bool quad_mode; } flags;
} esp_lcd_panel_io_spi_config_t;
typedef struct { struct { bool use_qspi_interface; } flags; } spd2010_vendor_config_t;
typedef struct { int reset_gpio_num, rgb_ele_order, bits_per_pixel; void *vendor_config; } esp_lcd_panel_dev_config_t;

esp_err_t ledc_timer_config(const ledc_timer_config_t *config);
esp_err_t ledc_channel_config(const ledc_channel_config_t *config);
esp_err_t ledc_set_duty(int mode, int channel, uint32_t duty);
esp_err_t ledc_update_duty(int mode, int channel);
esp_err_t ledc_stop(int mode, int channel, uint32_t idle);
esp_err_t ledc_timer_pause(int mode, int timer);
esp_err_t spi_bus_initialize(int host, const spi_bus_config_t *config, int dma);
esp_err_t spi_bus_free(int host);
esp_err_t esp_lcd_new_panel_io_spi(esp_lcd_spi_bus_handle_t bus, const esp_lcd_panel_io_spi_config_t *config, esp_lcd_panel_io_handle_t *io);
esp_err_t esp_lcd_panel_io_del(esp_lcd_panel_io_handle_t io);
esp_err_t esp_lcd_new_panel_spd2010(esp_lcd_panel_io_handle_t io, const esp_lcd_panel_dev_config_t *config, esp_lcd_panel_handle_t *panel);
esp_err_t esp_lcd_panel_del(esp_lcd_panel_handle_t panel);
esp_err_t esp_lcd_panel_reset(esp_lcd_panel_handle_t panel);
esp_err_t esp_lcd_panel_init(esp_lcd_panel_handle_t panel);
esp_err_t esp_lcd_panel_mirror(esp_lcd_panel_handle_t panel, bool x, bool y);
esp_err_t esp_lcd_panel_disp_on_off(esp_lcd_panel_handle_t panel, bool on);
