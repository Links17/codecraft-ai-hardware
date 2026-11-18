<p align="right"><strong>English</strong> · <a href="README.zh_CN.md">简体中文</a></p>

# esp-idf/sensecap-watcher

Device knowledge: [AGENTS.md](../../../../devices/sensecap-watcher/AGENTS.md). Hardware facts are maintained there and in its references.

Build/check: `python3 codecraft.py validate --target esp-idf/sensecap-watcher` from the repository root.

See `target.json` for examples, native interface references and exact toolchain selection. Build results and device observations are separate.

BSP public headers live in `bsp/include/`; implementation and private headers live in `bsp/src/`. Each example has its own `bsp.cmake` and managed dependency manifest. Exported projects include that example’s selected interfaces and source closure. See [native composition and layout](../../../../docs/development/native-compositions.md).

## Single-file image

After `python3 codecraft.py validate --target esp-idf/sensecap-watcher --example battery_status`, run `python3 codecraft.py firmware plan --target esp-idf/sensecap-watcher --example battery_status --output .codecraft/watcher-plan.json`, then `python3 codecraft.py firmware merge --plan .codecraft/watcher-plan.json --output .codecraft/watcher-release` and `python3 codecraft.py firmware verify .codecraft/watcher-release`. Keep the declared ESP-IDF environment activated. Outputs must be new. The factory BIN and manifest bind the successful build, native layout and input hashes. The workflow never flashes or uploads.
