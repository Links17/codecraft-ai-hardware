# Physical acceptance procedures

Identify the actual unit, revision, required peripherals and authorized device-write scope before running these steps. Build and test one selected sketch at a time. Record source digest, toolchain, stimuli, actual results and recovery. These procedures are not validation results.

After testing, power-cycle and repeat the selected startup checks. Existing dated results are in [observations.md](observations.md); they do not certify current source bytes.

## accelerometer

1. Build and upload with explicit authorization; open serial at 115200 baud.
2. Keep the board flat and still. Confirm the online message and a stable
   magnitude near 1 g.
3. Tilt once around each axis. Confirm the dot moves in the downhill
   direction with the measured mapping `displayX = -yg`, `displayY = xg`.
4. If the probe repeats `NOT FOUND at 0x18`, check `Wire1` and the address;
   do not switch to Grove `Wire` (GPIO 46/45).

## ble_scan

1. Confirm the coprocessor firmware with `rpc_system_version()`; a Wi-Fi-only
   or mismatched image changes the failure mode before any scan logic runs.
2. Build and upload with explicit authorization.
3. Place a known BLE advertiser nearby (a phone, beacon or another board).
4. Confirm its name or address appears and its RSSI changes plausibly with
   distance.
5. Run only this wireless demo while testing. Do not run the Wi-Fi sketch in
   parallel or assume combined behaviour from this repository.

## buzzer_tones

1. Build and upload with explicit authorization; open serial at 115200 baud.
2. Press A and confirm a short, audible 440 Hz tone and the serial line.
3. Press B and confirm a higher-pitched, shorter beep.
4. Press A or B and then C; confirm the output stops and GPIO 12 is low.
5. Check that no tone continues indefinitely after a button action.

## display_buttons

1. Build and upload with explicit authorization.
2. Open the serial monitor at 115200 baud.
3. Press and release each of the eight inputs once.
4. Confirm exactly one press line and one release line per action, with the
   matching LCD box changing state.
5. Confirm the display is landscape and all labels fit without clipping.

## grove_i2c_scan

1. Build and upload with explicit authorization; open serial at 115200 baud.
2. Power down and connect one known 3.3 V Grove I2C device to the left J4.
3. Power up and confirm the device's documented address appears on the LCD and
   serial monitor within three seconds.
4. Disconnect the device and confirm the next scan reports `no ACK on Wire`.
5. Record the address and the external module part number; do not assume a
   generic address from another Grove product.

## ir_nec_sender

1. Build and upload with explicit authorization; open serial at 115200 baud.
2. Point the **back** of the board (emitter left of the microSD slot)
   directly at a known 38 kHz demodulating receiver. A phone camera may show
   only a faint pulse and is not proof of a valid NEC frame; iPhone rear
   cameras often filter 940 nm. Use a TV remote as a camera control.
3. Press A, B and C one at a time and confirm the receiver decodes address
   `0x00` and commands `0x45`, `0x10`, `0x02` respectively.
4. Confirm the receiver does not decode a frame when no button is pressed.
5. If no frame is decoded, check line of sight, receiver supply and the GPIO
   14 drive before changing the NEC timings.

## light_sensor

1. Build and upload with explicit authorization; open serial at 115200 baud.
2. Record the raw value under normal room light.
3. Fully cover the sensor window and record the new value after it settles.
4. Uncover it and confirm the value returns in the opposite direction.
5. Use the observed direction and range to choose an application threshold;
   do not reuse a threshold from another unit without checking.

## microphone_level

1. Build and upload with explicit authorization; open serial at 115200 baud.
2. With the room quiet, record a short baseline for mean, peak-to-peak and
   RMS.
3. Speak or whistle at a normal distance. Confirm all three values rise and
   fall with the sound.
4. Stop making noise and confirm the values return near the baseline.
5. If the signal is stuck at 0 or 4095, inspect the microphone path and the
   analog reference before changing the sketch.

## sd_card_log

1. Format a card of 16 GB or less as FAT32 and insert it before power-up.
2. Build and upload with explicit authorization; open serial at 115200 baud.
3. Confirm `SD mounted`, root entries, `appended /wio_terminal.log`, and the
   read-back `log_bytes=` / `last_line=` values.
4. Remove the card, read it on a computer, and confirm
   `/wio_terminal.log` contains the mount line.
5. Reset and confirm `log_bytes` grows while `last_line` names the new mount;
   verify the LCD still renders normally and no LCD pin is disturbed.

## wifi_scan

1. Follow the vendor Wi-Fi firmware guide to install/verify compatible
   RTL8720DN eRPC firmware. Do not upload the sketch as a substitute for this
   step.
2. Build and upload with explicit authorization; open serial at 115200 baud.
3. Confirm the status progresses to `ready` and a scan reports networks that
   are actually present nearby.
4. Compare the strongest SSIDs/RSSI values with a known local access point;
   record the observed result rather than assuming 5 GHz coverage.
5. Run only this wireless demo while testing. Do not load the BLE sketch in
   parallel or expect concurrent Wi-Fi/BLE behavior from this repository.
