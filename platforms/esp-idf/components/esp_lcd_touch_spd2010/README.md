<p align="right"><strong>English</strong> · <a href="README.zh_CN.md">简体中文</a></p>

# SPD2010 polling touch driver

The driver borrows an IDF 6 i2c_master_dev_handle_t. The BSP owns device registration, bus lifetime, power, reset and interrupt routing; GPIO fields must be GPIO_NUM_NC and interrupt_callback must be NULL. Call esp_lcd_touch_new_i2c_spd2010 with the native device and delete the touch handle before removing that device. Serialize calls from the owning task.

Raw writes and reads preserve the vendor protocol and 200 us delays. Each I2C call times out after 100 ms. Invalid frame sizes and incomplete chunk polling return errors without publishing coordinates. An I2C timeout is not a hard deadline for the complete polling operation.

Based on Espressif esp_lcd_touch_spd2010 0.0.1 under Apache-2.0; see license.txt and the retained copyright headers. The repository component version is 1.0.0. Its host tests exercise allocation, native transaction framing, malformed packets and errors; hardware behavior requires Device evidence.
