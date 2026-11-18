<p align="right"><strong>English</strong> · <a href="README.zh_CN.md">简体中文</a></p>

# esp-idf/sensecap-watcher

Device knowledge: [AGENTS.md](../../../../devices/sensecap-watcher/AGENTS.md). Hardware facts are maintained there and in its references.

Build/check: `python3 codecraft.py validate --target esp-idf/sensecap-watcher` from the repository root.

See `target.json` for examples, native interface references and exact toolchain selection. Build results and device observations are separate.

BSP public headers live in `bsp/include/`; implementation and private headers live in `bsp/src/`. Each example has its own `bsp.cmake` and managed dependency manifest. Exported projects include that example’s selected interfaces and source closure. See [native composition and layout](../../../../docs/development/native-compositions.md).

## Single-file image

After a successful native build, run `python3 platforms/esp-idf/targets/sensecap-watcher/tools/merge_image.py <build-directory>`. Use --check-only for layout validation. The tool reads native flasher_args.json, validates chip, offsets and source files, then uses esptool to merge the bootloader, partition table and app. Output defaults to merged-binary.bin and must not already exist. It does not flash or upload.
