<p align="right"><a href="README.md">English</a> · <strong>简体中文</strong></p>

# esp-idf/sensecap-indicator

设备知识：[AGENTS.md](../../../../devices/sensecap-indicator/AGENTS.md)。硬件事实在该入口及其来源中维护。

在仓库根目录构建/检查：`python3 codecraft.py validate --target esp-idf/sensecap-indicator`。

示例、原生接口引用和工具链选择见 `target.json`。构建结果与设备观测分别记录。

BSP 公共头文件位于 `bsp/include/`，实现与私有头文件位于 `bsp/src/`。每个示例拥有独立的 `bsp.cmake` 和托管依赖声明；导出项目包含该示例选择的接口及源码闭包。参见[原生组合与布局](../../../../docs/development/native-compositions.md)。

GX 与 DX 屏幕组件已有带来源的原生配置。context、new 和定向 Target 验证可使用 `--variant gx` 或 `--variant dx`；完整 Target 验证会构建两种配置。仓库沿用历史 GX 构建默认值；导出会记录所选变体并将其设为原生默认值。面板／PCB 身份及修订兼容性须单独确认，目前仍为 unknown。参见[硬件变体选择](../../../../docs/development/hardware-variants.md)与[固定版本厂商来源](../../../../devices/sensecap-indicator/reference/display-variants.md)。
