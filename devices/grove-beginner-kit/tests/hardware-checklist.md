# Physical acceptance procedures

Identify the actual unit, revision, required peripherals and authorized device-write scope before running these steps. Build and test one selected sketch at a time. Record source digest, toolchain, stimuli, actual results and recovery. These procedures are not validation results.

After testing, power-cycle and repeat the selected startup checks. Existing dated results are in [observations.md](observations.md); they do not certify current source bytes.

## accelerometer

1. Run `i2c_scan` and confirm 0x19.
2. Open the 9600-baud monitor and confirm the magnitude is near 1 g at rest.
3. Tilt the kit slowly; record which axis changes and in which direction.
4. Tap or shake gently; confirm the LED flashes `ACTIVE` and returns to
   `REST` when motion stops.

## air_pressure_spa06

1. Run `i2c_scan` and record whether 0x77 or 0x76 is present.
2. Open the 9600-baud monitor and confirm the detected address.
3. Confirm lines repeat without blocking; the configured rate is 4 Hz but
   serial printing dominates the loop.
4. Carry the kit up or down a stair flight and compare the pressure and
   altitude trend after several samples.

## button_led

1. Open the 9600-baud monitor and confirm the initial released line.
2. Press and hold the button; confirm the LED follows immediately and the
   pressed line appears once.
3. Release; confirm the LED turns off and the released line appears once.

## buzzer_tones

1. Open the 9600-baud monitor and listen.
2. Confirm four distinct ascending tones and the silent gap.
3. If no sound, verify D5 and the passive buzzer module; do not replace
   `tone()` with a static `digitalWrite(HIGH)`.

## i2c_scan

1. Power the intact kit over USB and open the 9600-baud monitor.
2. Confirm 0x19, 0x38, 0x3C or 0x3D, and 0x77 or 0x76 on an intact supported
   kit. The exact OLED and pressure addresses can differ as documented.
3. If modules are broken out, disconnect one known device and confirm its
   address disappears on the next scan.

## led_blink

1. Power the kit and open the 9600-baud monitor.
2. Confirm a steady 1 Hz blink.
3. If visible but dim, adjust the trimpot on the LED module; do not change
   the GPIO drive in software.

## light_sensor

1. Open the 9600-baud monitor in room light and record the raw value.
2. Cover the sensor with your hand; confirm the raw value moves toward the
   dark threshold and the LED turns on.
3. Remove your hand; confirm the LED turns off above the upper threshold.

## oled_status

1. Run `i2c_scan` and record whether 0x3C or 0x3D is present.
2. Open the 9600-baud monitor and confirm the four text rows appear.
3. Watch for at least three counter updates and confirm the panel and serial
   agree.
4. If the text is upside down, the panel is mounted opposite to the
   `setFlipMode(1)` assumption; set it to 0 and re-check. Do not change the
   I2C address to work around orientation.

## potentiometer

1. Open the 9600-baud monitor.
2. Rotate the potentiometer from stop to stop and record the raw range.
3. Confirm the LED switches near the middle. Do not assume clockwise means
   increasing until observed on the unit.

## sound_sensor

1. Open the 9600-baud monitor or plotter in a quiet room.
2. Clap or speak near the sound sensor; confirm the printed peak rises and
   the LED turns on.
3. Let the room settle; confirm the LED returns off after the hold time.

## temperature_humidity_dht20

1. Run `i2c_scan` and confirm 0x38. If it is missing, this is not the
   supported revision or the sensor is not connected. This Target requires the documented DHT20 assembly.
2. Open the 9600-baud monitor and confirm `DHT20 on I2C 0x38`.
3. Breathe gently near the sensor and wait several samples; humidity should
   move before temperature.
4. Confirm readings update about once per second.
