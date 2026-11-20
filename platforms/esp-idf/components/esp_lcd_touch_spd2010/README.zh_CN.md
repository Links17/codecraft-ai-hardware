<p align="right"><a href="README.md">English</a> · <strong>简体中文</strong></p>

# SPD2010 轮询触摸驱动

驱动借用 IDF 6 的 i2c_master_dev_handle_t。BSP 负责设备注册、总线生命周期、电源、复位及中断路由；GPIO 字段须为 GPIO_NUM_NC，interrupt_callback 须为空。向 esp_lcd_touch_new_i2c_spd2010 传入原生设备，移除设备前先删除触摸句柄。由所属任务串行调用。

原始读写保留厂商协议及 200 us 延时。每次 I²C 调用超时为 100 ms。非法数据帧及未完成的分块轮询返回错误，不发布坐标。单次 I²C 超时不是整个轮询操作的硬截止时间。

基于 Apache-2.0 许可的 Espressif esp_lcd_touch_spd2010 0.0.1；参见 license.txt 和保留的版权头。仓库组件版本为 1.0.0。主机测试覆盖分配、原生事务格式、异常数据帧和错误；硬件行为需要 Device 实测证据。
