<p align="right"><a href="README.md">English</a> · <strong>简体中文</strong></p>

# reTerminal overlays

根据需要选择以下两种方案之一：

## 1. `reterminal-peripherals-overlay.dts`（本目录）

仅使用主线驱动的 overlay，覆盖显示屏之外的外设：MCP23008 IO 扩展器（4 个按键、3 个 LED、蜂鸣器）、LTR-303ALS 光传感器、LIS331DLH 加速度计、PCF8563 RTC，以及 GPIO13 上的电源键。

在 reTerminal（64 位 Raspberry Pi OS）上构建和安装：

```sh
dtc -@ -I dts -O dtb -o reterminal-peripherals.dtbo reterminal-peripherals-overlay.dts
sudo cp reterminal-peripherals.dtbo /boot/firmware/overlays/
# 添加到 /boot/firmware/config.txt 后重启：
#   dtoverlay=reterminal-peripherals
```

文件有意使用纯数值常量，使独立的 `dtc`（无需内核头文件或 cpp）也能编译。

## 2. 厂商 overlay（包含显示屏）

5 英寸 DSI 面板（ILI9881x）及其触摸功能需要 Seeed 的树外内核模块。请从 [Seeed-Studio/seeed-linux-dtoverlays](https://github.com/Seeed-Studio/seeed-linux-dtoverlays) 安装厂商 overlay（`overlays/rpi/reTerminal-overlay.dts` 的文件头为 MIT；所在仓库的 COPYING 为内核 GPLv2，因此此处提供链接而不复制源码）。厂商 overlay 也覆盖上述外设，不能同时加载两种方案。
