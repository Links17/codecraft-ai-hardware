/* button_hello: USR1 logs a press; USR2 toggles the backlight.
 * The callback queues events without waiting; the main task owns display
 * operations. A full queue drops extra presses. */
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "bsp_button.h"
#include "bsp_display.h"
#include "esp_log.h"

static const char *TAG = "button_hello";

static void on_button(bsp_button_id_t id, bool pressed, void *arg)
{
    if (!pressed) return;
    (void)xQueueSend((QueueHandle_t)arg, &id, 0);
}

void app_main(void)
{
    esp_lcd_panel_handle_t panel;
    ESP_ERROR_CHECK(bsp_display_init(&panel));
    QueueHandle_t events = xQueueCreate(8, sizeof(bsp_button_id_t));
    configASSERT(events);
    ESP_ERROR_CHECK(bsp_button_init(on_button, events));
    bool backlight = true;
    for (;;) {
        bsp_button_id_t id;
        if (xQueueReceive(events, &id, portMAX_DELAY) != pdTRUE) continue;
        if (id == BSP_BUTTON_USR1) {
            ESP_LOGI(TAG, "USR1 pressed");
        } else if (id == BSP_BUTTON_USR2) {
            backlight = !backlight;
            ESP_ERROR_CHECK(bsp_display_backlight(backlight));
            ESP_LOGI(TAG, "backlight %s", backlight ? "on" : "off");
        }
    }
}
