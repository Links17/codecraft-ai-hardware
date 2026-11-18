<p align="right"><a href="README.md">English</a> · <strong>简体中文</strong></p>

# esp-idf/sensecap-watcher

设备知识：[AGENTS.md](../../../../devices/sensecap-watcher/AGENTS.md)。硬件事实在该入口及其来源中维护。

在仓库根目录构建/检查：`python3 codecraft.py validate --target esp-idf/sensecap-watcher`。

示例、原生接口引用和工具链选择见 `target.json`。构建结果与设备观测分别记录。

BSP 公共头文件位于 `bsp/include/`，实现与私有头文件位于 `bsp/src/`。每个示例拥有独立的 `bsp.cmake` 和托管依赖声明；导出项目包含该示例选择的接口及源码闭包。参见[原生组合与布局](../../../../docs/development/native-compositions.md)。

## 单文件镜像

原生构建成功后，执行 `python3 platforms/esp-idf/targets/sensecap-watcher/tools/merge_image.py <build-directory>`；使用 --check-only 只验证布局。工具读取原生 flasher_args.json，校验芯片、偏移和输入文件，然后使用 esptool 合并引导程序、分区表和应用。默认输出 merged-binary.bin，要求该文件尚不存在。工具不会烧录或上传。
