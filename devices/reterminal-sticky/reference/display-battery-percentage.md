# Display battery percentage correctly

Sources: Seeed's [ESP-IDF Pages and Peripherals](https://www.seeedstudio.com/sticky/docs/en/device-guide/esp-pages/), [`sticky_battery.cpp`](https://github.com/Seeed-Projects/sticky-esp-idf-dashboard/blob/main/main/devices/sticky_battery.cpp), and [`sticky_charger.cpp`](https://raw.githubusercontent.com/Seeed-Projects/sticky-esp-idf-dashboard/main/main/devices/sticky_charger.cpp). These are official demo APIs, not current repository Target APIs; the current Target does not provide a BQ27220 BSP driver.

## ESP-IDF page integration

```text
BQ27220 -> sticky_battery_read() --+
                                   +-> AppState.battery -> Battery Page
External power -> sticky_charger_read()
```

Call `update_battery()` when entering the Battery page or when AI / OK / Power button posts `RefreshPage` on that page. Store gauge and external-power results separately: each needs its own value, validity flag, and error code. A gauge failure must not hide a valid external-power state, or vice versa.

The Page Renderer only reads `AppState.battery`; it does not access I2C or GPIO. After a valid percentage read, clamp the value to 0–100 before calculating text or bar width. Let the normal App flow refresh the display after both reads finish.

## Device implementation contract

- `sticky_battery_init(bus)` adds the BQ27220 to the existing shared I2C1 bus at **400 kHz**, probes it, and reuses the stored device handle. Do not create another bus on GPIO0/GPIO1.
- `sticky_battery_read()` requires successful initialization, reads State of Charge through the demo's `bq27220` component, and clamps the result to **0–100%**.
- `sticky_charger_init()` configures charger-enable **GPIO39** as an output and drives it LOW to enable charging. This output is not the charging-state input.
- `sticky_charger_read()` reads **GPIO9** and returns true when external power is present. The demo names this Boolean `charging`, but the measured signal is external-power presence.

## Display it without misleading the user

- Read both values when entering the Battery page or on an AI-button manual refresh; do not refresh e-paper continuously just to poll the battery.
- Update percentage text only after a successful gauge read. Show `Battery: --%` on failure rather than presenting a stale value as fresh.
- Display the clamped SOC as the percentage; do not derive a precise-looking percentage from voltage alone.
- Show USB/external power separately from percentage, and do not use GPIO9 alone to claim that the battery is charging or full.
- In the official demo, the Battery page uses the normal monochrome full-refresh path after both reads finish. See [Display refresh implementations](display-refresh.md).

Example UI states are `Battery: 82%`, `Battery: 82% · USB`, and `Battery: --%`. Keep gauge validity, external-power presence, and panel refresh status as separate state values.
