<p align="right"><strong>English</strong> · <a href="README.zh_CN.md">简体中文</a></p>

# esp-idf/reterminal-e1002

Device knowledge: [AGENTS.md](../../../../devices/reterminal-e1002/AGENTS.md). Hardware facts are maintained there and in its references.

Build/check: `python3 codecraft.py validate --target esp-idf/reterminal-e1002` from the repository root.

See `target.json` for examples, native interface references and exact toolchain selection. Build results and device observations are separate.

BSP public headers live in `bsp/include/`; implementation and private headers live in `bsp/src/`. Each example has its own `bsp.cmake` and managed dependency manifest. Exported projects include that example’s selected interfaces and source closure. See [native composition and layout](../../../../docs/development/native-compositions.md).
