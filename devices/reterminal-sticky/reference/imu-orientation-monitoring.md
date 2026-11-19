# Monitor IMU orientation without unnecessary refreshes

Source: Seeed's [ESP-IDF Pages and Peripherals](https://www.seeedstudio.com/sticky/docs/en/device-guide/esp-pages/). APIs below belong to `Sticky_dashboard_demo`.

## Use background state monitoring

Initialize the IMU on the shared sensor bus with `board_sensor_i2c_bus()`, then start `sticky_imu_start_monitoring()` once during application startup.

The official monitoring task:

1. Reads acceleration every **100 ms**.
2. Requires the same candidate orientation for **5 consecutive samples** before treating it as stable.
3. Stores the latest state through the Device module.
4. Posts `AppEvent::OrientationChanged` only when the stable orientation actually changes.

The stability filter prevents small movements from producing repeated events and e-paper refreshes.

## Gate UI updates by the visible page

```text
IMU monitor -> stable change -> OrientationChanged
            -> sticky_imu_get_state() -> AppState.imu
            -> IMU Renderer -> refresh only if the IMU page is visible
```

When `OrientationChanged` arrives while another page is active, return without refreshing. The monitoring task continues to store state, so the IMU page can use the latest value when opened.

`update_imu()` should preserve `valid` and `error` separately from the orientation value. The Renderer draws the stored arrow or an instruction to hold the device upright; it never reads the IMU directly. Background orientation events do not trigger the buzzer in the official demo.

Use this pattern for continuous state that should redraw the UI only on meaningful changes, not for ordinary data that can be read once on page entry.
