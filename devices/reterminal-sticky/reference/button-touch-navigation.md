# Button and touch navigation with ESP-IDF

Source: Seeed's [ESP-IDF Pages and Peripherals](https://www.seeedstudio.com/sticky/docs/en/device-guide/esp-pages/). APIs and behavior below are from `Sticky_dashboard_demo`.

## Map physical input to application events

| Input | `AppEvent` | Application behavior |
| --- | --- | --- |
| Short press Up | `PreviousPage` | Previous page |
| Short press Down | `NextPage` | Next page |
| Swipe right | `PreviousPage` | Previous page |
| Swipe left | `NextPage` | Next page |
| Short press AI / OK / Power button | `RefreshPage` | Read and refresh the current page |
| Hold AI / OK / Power button for about two seconds | `EnterDeepSleep` | Start the ordered sleep sequence |

The button adapters register these events through `sticky_buttons_init()`. A button callback should only call `app_event_post(event)`; it must not refresh e-paper, access a peripheral, control the buzzer, or modify page state directly.

## Recognize a horizontal swipe

`sticky_touch` converts GT911 coordinates for the installed screen orientation. On finger release, accept a page-changing swipe only when:

- horizontal movement is at least **120 logical pixels**; and
- horizontal movement is greater than **twice** the vertical movement.

Otherwise ignore the gesture. Map negative `delta_x` to `NextPage` and positive `delta_x` to `PreviousPage`. Do not rotate or flip the coordinates again in the App or Page layer.

## Handle events in one place

```text
Button / Touch -> AppEvent queue -> handle_app_event()
               -> update PageId or data -> Renderer -> Display refresh
```

The main loop waits for events and handles time-consuming work in task context. After a page change or manual refresh, the App layer may call `sticky_buzzer_beep()`; background state events should not automatically produce repeated sounds.

For the hold-to-sleep sequence and GPIO4 wake configuration, see [Deep sleep and wake](deep-sleep-wake.md).
