[English](README.md)

# CodeCraft CLI

独立的 Rust 创作 CLI。运行时从所选仓库或项目读取数据，不把资料编译进二进制。
普通命令从不调用 Cargo。

在仓库根目录运行 `sh tools/cli/install.sh` 构建并安装一次
（Windows 使用 `tools/cli/install.ps1`），然后使用 `codecraft --help`。
仅在更新 Rust 代码、依赖或更换编译器、目标平台时重新安装；Cargo 复用未变化的产物。
下载的二进制不需要安装 Rust 或 Python。从源码构建需要 Cargo 和原生链接器。

使用 `cargo test --locked --package codecraft` 运行集成测试。测试归属
 tests/tools/cli/，平台实现归属 platforms/<stack>/native.rs。
参见[运行时与更新策略](../../docs/development/rust-cli.md)。
