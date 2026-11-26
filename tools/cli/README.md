[简体中文](README.zh_CN.md)

# CodeCraft CLI

Standalone Rust creator CLI. Runtime data is read from the selected repository or
project; it is not embedded in the binary. Normal commands never invoke Cargo.

Build/install once with `sh tools/cli/install.sh` from the repository root
(`tools/cli/install.ps1` on Windows), then use `codecraft --help`.
Re-run installation only when updating Rust code/dependencies or changing the
compiler/target; Cargo reuses unchanged outputs. Downloaded binaries require no
Rust or Python installation. Source builds require Cargo and a native linker.

Use `cargo test --locked --package codecraft` for integration tests. Tests belong
in tests/tools/cli/, platform implementation belongs in platforms/<stack>/native.rs.
Read [runtime and update policy](../../docs/development/rust-cli.md).
