# reTerminal Sticky

## Overview

Compact magnetic 3.97-inch 4-level grayscale e-paper device with touch, three buttons, environmental/motion sensors, RTC, microphone, buzzer, microSD, Wi-Fi/BLE and a 750 mAh battery.

## Usage

Best for low-frequency, always-visible notes, weather, schedules and status dashboards. Pocket size makes it suitable for both handheld and stationary use. Stick it to magnetic surfaces, or the back of your phone. Mount it to any surface with the adhesive magnetic ring accessory.

## Profile

| Field | Value |
| --- | --- |
| ID | reterminal-sticky |
| Format | 5 |
| Revision | unknown |
| Maintenance | unassigned |
| Maturity | experimental |

## Physical layout

Vendor-described layout, viewed from the front in portrait orientation. See the [hardware overview][vendor-hardware] and [product images](reference/image-generation.md); the physical revision of a tested unit remains unknown.

- Dimensions (height × width × thickness): 106 × 65.5 × 7.3 mm
- Weight: 70 g
- Protection: IP40 (not waterproof)

Card-style body with a light silver-grey front bezel and glass touch cover. The rear shell is light silver-grey, with four N52 magnets in the four corners and a center metal ring beneath the shell (it works with the adhesive magnetic ring accessory). All four edges are white. Three buttons sit along the upper part of the right edge, from top to bottom: AI/OK/Power (grey), Up (white), Down (white). The microSD slot is on the lower part of the left edge. On the bottom, from left to right: reset hole, microphone, lanyard hole, charging LED and USB-C port.

## Hardware notes

The [vendor hardware overview][vendor-hardware] documents the following modules. The pin table also retains the [native header][pins] and [pinned official demo][vendor-demo] as implementation references. These source notes describe documented hardware, not a new physical observation.

### Platform

- ESP-IDF (the registered Target stack)

- Arduino (vendor examples; no Arduino Target is registered for Sticky)

### Controller

- Main controller: ESP32-S3
- PSRAM capacity: 8 MB
- Physical flash capacity remains unknown for an identified unit. The vendor lists 32 MB QSPI Flash, while `targets/sdkconfig.defaults` configures a 16 MB address range. The configuration is not a measurement of the installed chip.

### Connectivity

#### Wireless

- 2.4 GHz Wi-Fi

- BLE 5.0

#### Wired interface:

- USB-C for power, data, firmware download and debugging (CH343P USB-UART)

- Expandable storage: microSD via SPI, sharing SPI2 with the display

### Inputs

#### Sensors

- SHT40 temperature/humidity (I2C)
- LSM6DS3TR-C 6-axis IMU (I2C)
- PDM digital microphone
- Real-time clock: PCF8563 (I2C)

#### Controls

- Buttons: AI / OK / Power, Up, Down; Reset via CHIP_PU
- Touch: GT911 capacitive touch panel (I2C)

### Outputs

#### Display

- 3.97-inch E-Ink, 4-level grayscale
- Panel controller candidates in the official demo: SSD1677 or SSD2677. The [pinned panel implementation][vendor-panel] detects the controller; it does not establish which revision uses which panel. The current Target implements SSD1677 only and has no detection.
- Native resolution: 800 × 480 px (horizontal)
- Pixel density: 235 ppi

#### Audio output

- Onboard buzzer (PWM)

### Power

- Battery: 750 mAh single-cell lithium
- Fuel gauge: BQ27220 (I2C)
- Charging: USB-C; red/green charging indicator (red while charging, green when fully charged)

### Accessories

- Mounting accessory: Adhesive magnetic ring for non-metal surfaces; confirm package contents with the supplier.

### Pins and signals

Sticky exposes no user-accessible connector pins. This table is for development reference only.

Required at boot: drive GPIO45 (HOLD) and GPIO46 (LOCK) HIGH to keep the power rail and power controller on.

| Function          | Hardware                             | Bus                        | Signals                                                        | Constraints                                                                                                                                                                                                                     |
| ----------------- | ------------------------------------ | -------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Display           | E-paper, SSD1677 or SSD2677          | SPI2, 20 MHz               | SCK=13, MOSI=14, MISO=12, CS=15, DC=16, RST=17, BUSY=18, EN=47 | RST active low; BUSY high while busy; EN high = powered. SPI2 is shared with microSD, which needs its own CS.                                                                                                                   |
| Touch             | GT911                                | I2C0                       | SDA=3, SCL=2, INT=21, RST=41, EN=42                            | Address 0x5D (fallback 0x14). The digitizer counts Y from the bottom, so flip Y in software.                                                                                                                                    |
| microSD           | microSD card                         | SPI2 (shared with display) | CS=8, EN=10, DET=11                                            | EN high = powered; DET low = card inserted.                                                                                                                                                                                     |
| Sensors and clock | SHT40, LSM6DS3TR-C, PCF8563, BQ27220 | I2C1                       | SDA=1, SCL=0; IMU INT=7                                        | Addresses 0x44, 0x6A, 0x51, 0x55. All share one bus instance.                                                                                                                                                                   |
| Keys              | AI/OK/Power, Up, Down                | GPIO                       | 4, 5, 6                                                        | Active low. GPIO4 is the deep-sleep wake source.                                                                                                                                                                                |
| Microphone        | PDM digital microphone               | PDM                        | CLK=19, DATA=20, EN=38                                         | EN high = powered.                                                                                                                                                                                                              |
| Buzzer            | Onboard buzzer                       | PWM                        | GPIO48                                                         |                                                                                                                                                                                                                                 |
| Power control     | Power and charger                    | GPIO                       | HOLD=45, LOCK=46, charger EN=39, external-power detect=9       | HOLD and LOCK active high. Charger EN: the demo drives it low to enable charging; the active level is unconfirmed against the factory firmware, so treat it as unverified until measured. Detect high = external power present. |
| USB-UART          | CH343P                               | UART                       | TX=43, RX=44                                                   |                                                                                                                                                                                                                                 |
| Reset             | Reset button hole                    | CHIP_PU                    | not a GPIO                                                     |                                                                                                                                                                                                                                 |

## Intent routing

Locate references and targets based on intent. Target is the BSP in [`targets/`](targets/README.md). Reference is a guide in `reference/` for implementation of functions.

| Intent                           | Covers                                                                                                          | Reference                                                                                                                                                                                                                                                                                                                                                    | Target                                                                                                             |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| Refresh the e-paper display      | Grayscale full, monochrome full and monochrome partial refresh                                                  | [display-refresh.md](reference/display-refresh.md)                                                                                                                                                                                                                                                                                                           | `bsp_epd_update`, `bsp_epd_update_gray4`; example `epd_hello`.                      |
| Identify the panel controller    | Read chip ID with `0x70` (`0x07` = SSD2677, else SSD1677), then apply that chip's busy timeout and reset timing | Demo source: [`resolve_panel_model()`](https://github.com/Seeed-Projects/sticky-esp-idf-dashboard/blob/1a28b2a11da2df3819c3a6f34561793f562d53c8/components/seeed_epaper/epaper_panel.c), [`sticky_display_init()`](https://github.com/Seeed-Projects/sticky-esp-idf-dashboard/blob/1a28b2a11da2df3819c3a6f34561793f562d53c8/main/devices/sticky_display.cpp) | None                                                                                                               |
| Update only the status-bar clock | Minute event, change detection, redraw of the `HH:MM` area, partial refresh                                     | [display-rtc-time.md](reference/display-rtc-time.md)                                                                                                                                                                                                                                                                                                         | Display only; no RTC driver                                                                                        |
| Add an information page          | Renderer, page registration, navigation, `AppState` data flow                                                   | [add-information-page.md](reference/add-information-page.md)                                                                                                                                                                                                                                                                                                 | None                                                                                                               |
| Navigate with buttons or swipes  | Button presses and horizontal swipes mapped to page and refresh events                                          | [button-touch-navigation.md](reference/button-touch-navigation.md)                                                                                                                                                                                                                                                                                           | `bsp_button_init`, `bsp_button_pressed`; example `button_hello`. No touch driver |
| Sleep and wake                   | AI hold-to-sleep, shutdown order, active-low EXT1 wake, page-state restore                                      | [deep-sleep-wake.md](reference/deep-sleep-wake.md)                                                                                                                                                                                                                                                                                                           | None                                                                                                               |
| Show battery and charging state  | BQ27220 percentage, external-power presence, separate validity states                                           | [display-battery-percentage.md](reference/display-battery-percentage.md)                                                                                                                                                                                                                                                                                     | None                                                                                                               |
| React to orientation changes     | Stable IMU orientation events, refresh only when the IMU page is visible                                        | [imu-orientation-monitoring.md](reference/imu-orientation-monitoring.md)                                                                                                                                                                                                                                                                                     | None                                                                                                               |
| Capture audio                    | AI-triggered one-second PDM sample with scoped microphone power                                                 | [microphone-capture.md](reference/microphone-capture.md)                                                                                                                                                                                                                                                                                                     | None                                                                                                               |
| Read files from microSD          | Mount, read and unmount around the SPI2 bus shared with the display                                             | [microsd-text-page.md](reference/microsd-text-page.md)                                                                                                                                                                                                                                                                                                       | None                                                                                                               |
| Read temperature and humidity    | SHT40 reading on shared I2C1                                                                                    | None                                                                                                                                                                                                                                                                                                                                                         | `bsp_sht4x_read`; example `sht4x`                                                       |
| Create images of the device      | Official product shots and use scenes with descriptions; physical details image models often get wrong          | [image-generation.md](reference/image-generation.md)                                                                                                                                                                                                                                                                                                         | None                                                                                                               |

## Specifications

### Controller

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Physical flash capacity (`flash`) | integer | — | MB | unknown | — | Vendor documentation lists 32 MB while the Target configures 16 MB; identify the installed chip and revision before changing the address range. |
| Controller (`mcu`) | string | ESP32-S3 | — | documented | [notes][notes] | Main controller: {value} |
| PSRAM capacity (`psram`) | integer | 8 | MB | documented | [notes][notes] | PSRAM capacity: {value} MB |

### Connectivity

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Sensor bus (`bus`) | string | I2C1 | — | documented | [notes][notes] | SHT40 reading on shared {value} |
| USB connector (`usb`) | string | USB-C | — | documented | [notes][notes] | {value} for power, data, firmware download |

### Inputs

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Keys (`keys`) | string | AI / OK / Power, Up, Down | — | documented | [notes][notes] | Buttons: {value}; Reset |
| Environmental sensor (`sensor`) | string | SHT40 | — | documented | [notes][notes] | {value} temperature/humidity |

### Outputs

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Panel candidates recognized by the vendor demo (`display`) | string | SSD1677 or SSD2677 | — | documented | [notes][notes] | Panel controller candidates in the official demo: {value}. |
| Native panel height (`display_height`) | integer | 480 | px | documented | [notes][notes] | 800 × {value} px |
| Native panel width (`display_width`) | integer | 800 | px | documented | [notes][notes] | Native resolution: {value} × 480 px |

### Power

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Documented battery capacity (`battery_capacity`) | integer | 750 | mAh | documented | [notes][notes] | Battery: {value} mAh single-cell lithium |

### Accessories

| Fact | Type | Value | Unit | Status | Source | Assertion / reason |
| --- | --- | --- | --- | --- | --- | --- |
| Supported mounting accessory (`accessories_details`) | string | Adhesive magnetic ring | — | documented | [notes][notes] | Mounting accessory: {value} for non-metal surfaces |

## Limitations

- Physical board revision and fresh on-device verification are not recorded.
- The Target exposes display, keys and temperature/humidity only; the official demo guides do not add native drivers or prove their integration here.
- Installed flash capacity remains unknown; keep the existing 16 MB configuration until the chip is identified.
- The Target supports SSD1677 only; SSD2677 operation and panel-to-revision mapping remain unverified.
- Charger-enable polarity on GPIO39 remains unconfirmed against factory firmware and measurement.

## Source conflicts

| Source | Resolution |
| --- | --- |
| [notes][notes] | Vendor flash capacity and the native configured address range describe different things; keep installed capacity unknown until measured. Panel detection in the official demo does not establish revision compatibility for this Target. |

## Physical acceptance

### Preconditions

Identify the actual unit, revision, required peripherals and authorized write scope. Run one selected native example at a time. Record source digest, toolchain, stimuli, actual observations and recovery; a plan or build is not a physical pass.

### identity

- Interfaces: none
- Source: [target][target]

Record board identity, observed revision, connected port/drive and approved write scope.

Expected: Identity and revision are unambiguous and match this Device.

### recovery

- Interfaces: none
- Source: [target][target]

After the functional cases, power-cycle/restart using the documented normal procedure.

Expected: Device returns to the documented working state; record failures and recovery steps.

### button-hello

- Interfaces: input
- Source: [target][target]

Run `button_hello` under the confirmed write scope and observe the selected hardware.

Expected: log AI/Up/Down presses.

### epd-hello

- Interfaces: display
- Source: [target][target]

Run `epd_hello` under the confirmed write scope and observe the selected hardware.

Expected: test pattern, full refresh, then an inverted fast refresh.

### sht4x

- Interfaces: environment
- Source: [target][target]

Run `sht4x` under the confirmed write scope and observe the selected hardware.

Expected: temperature/humidity log once a second.

## Sources

- [Hardware source notes][notes]
- [Official product page][vendor-product]
- [Official store][vendor-store]
- [Vendor hardware overview][vendor-hardware]
- [Vendor playground][vendor-playground]
- [Official demo at 1a28b2a][vendor-demo]
- [Official panel detection at 1a28b2a][vendor-panel]
- [Native build instructions][readme]
- [Native Target][target]
- [Native pin definitions][pins]
- [Display API contract][epd-api]
- [Add information page][guide-add-information-page]
- [Button touch navigation][guide-button-touch-navigation]
- [Deep sleep wake][guide-deep-sleep-wake]
- [Display battery percentage][guide-display-battery-percentage]
- [Display refresh][guide-display-refresh]
- [Display rtc time][guide-display-rtc-time]
- [Image generation][guide-image-generation]
- [Imu orientation monitoring][guide-imu-orientation-monitoring]
- [Microphone capture][guide-microphone-capture]
- [Microsd text page][guide-microsd-text-page]

[notes]: AGENTS.md#hardware-notes
[vendor-product]: https://www.seeedstudio.com/sticky/
[vendor-store]: https://www.seeedstudio.com/reTerminal-Sticky-p-6861.html
[vendor-hardware]: https://www.seeedstudio.com/sticky/docs/en/device-guide/hardware-overview/
[vendor-playground]: https://github.com/Seeed-Projects/reterminal-sticky-playground-registry/tree/main
[vendor-demo]: https://github.com/Seeed-Projects/sticky-esp-idf-dashboard/tree/1a28b2a11da2df3819c3a6f34561793f562d53c8
[vendor-panel]: https://github.com/Seeed-Projects/sticky-esp-idf-dashboard/blob/1a28b2a11da2df3819c3a6f34561793f562d53c8/components/seeed_epaper/epaper_panel.c
[readme]: targets/README.md
[target]: targets/target.json
[pins]: targets/bsp/include/bsp_pins.h
[epd-api]: targets/bsp/include/bsp_epd.h
[guide-add-information-page]: reference/add-information-page.md
[guide-button-touch-navigation]: reference/button-touch-navigation.md
[guide-deep-sleep-wake]: reference/deep-sleep-wake.md
[guide-display-battery-percentage]: reference/display-battery-percentage.md
[guide-display-refresh]: reference/display-refresh.md
[guide-display-rtc-time]: reference/display-rtc-time.md
[guide-image-generation]: reference/image-generation.md
[guide-imu-orientation-monitoring]: reference/imu-orientation-monitoring.md
[guide-microphone-capture]: reference/microphone-capture.md
[guide-microsd-text-page]: reference/microsd-text-page.md
