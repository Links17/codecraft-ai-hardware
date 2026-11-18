/* button_led: hold XIAO BOOT to cycle the WS2812 through red/green/blue.
 * Demonstrates bsp_button + bsp_led. Button callbacks run in the BSP task
 * and only publish color state. The main task owns all blocking RMT writes. */
#include <stdatomic.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "bsp_button.h"
#include "bsp_led.h"
#include "esp_log.h"

static const char *TAG = "button_led";
static atomic_int s_color;

static void on_button(bool pressed, void *arg)
{
    (void)arg;
    if (!pressed) return;
    /* One callback task writes; the main task reads one atomic snapshot. */
    atomic_store(&s_color, (atomic_load(&s_color) + 1) % 3);
}

void app_main(void)
{
    ESP_ERROR_CHECK(bsp_led_init());
    ESP_ERROR_CHECK(bsp_button_init(on_button));
    int previous_color = -1;
    for (;;) {
        static const uint8_t colors[3][3] = {{32, 0, 0}, {0, 32, 0}, {0, 0, 32}};
        int color = atomic_load(&s_color);
        if (color != previous_color) ESP_LOGI(TAG, "color %d", color);
        previous_color = color;
        if (bsp_button_pressed()) bsp_led_set_rgb(colors[color][0], colors[color][1], colors[color][2]);
        else bsp_led_off();
        vTaskDelay(pdMS_TO_TICKS(50));
    }
}
