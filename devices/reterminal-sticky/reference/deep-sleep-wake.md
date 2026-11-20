# Deep sleep and wake with ESP-IDF

Source: Seeed's [ESP-IDF Refresh and Low Power](https://www.seeedstudio.com/sticky/docs/en/device-guide/esp-refresh/). APIs below belong to `Sticky_dashboard_demo`.

## Enter sleep in order

Holding AI / OK / Power button for about two seconds posts `AppEvent::EnterDeepSleep`. Do not call `esp_deep_sleep_start()` immediately.

```text
Beep
-> save AppState to RTC retention memory
-> render the monochrome Deep Sleep page
-> sticky_display_refresh_monochrome()
-> sticky_touch_stop()
-> sticky_display_sleep()
-> sticky_power_enter_deep_sleep()
```

The final display refresh must finish before display power is disabled. E-paper retains the sleep image without power. The power module also holds required system-power controls and locks peripheral-enable pins at disabled levels.

## Prevent the holding press from causing an immediate wake

GPIO4 is an **active-low** wake source. Before sleeping, wait until the button reads high again and allow a debounce interval. Otherwise the still-held button can wake the ESP32-S3 immediately.

Configure EXT1 low-level wake:

```cpp
ESP_ERROR_CHECK(esp_sleep_enable_ext1_wakeup_io(
    1ULL << PIN_POWER_BTN, ESP_EXT1_WAKEUP_ANY_LOW));
```

## Restore only useful state

The demo stores a simple `AppState` in `RTC_NOINIT_ATTR` memory and marks it with a Magic value. Restore it only when both conditions hold:

- wake cause is `ESP_SLEEP_WAKEUP_EXT1`; and
- the Magic value matches.

Clear the Magic value after restoration so a normal reset cannot reuse stale state. Do not copy pointers, dynamic allocations, or boot-specific handles into retained state; save only plain data needed to reconstruct the page.

Wake starts `app_main()` again rather than continuing after the sleep call. Reinitialize Board and Device modules, restore the saved page state, read the RTC again, render the restored page, and apply its assigned **full** refresh mode. On non-Home pages, use the newly read RTC time rather than the pre-sleep value.
