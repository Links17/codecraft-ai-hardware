<p align="right"><strong>English</strong> · <a href="README.zh_CN.md">简体中文</a></p>

# esp-idf/sensecap-indicator

Device knowledge: [AGENTS.md](../../../../devices/sensecap-indicator/AGENTS.md). Hardware facts are maintained there and in its references.

Build/check: `python3 codecraft.py validate --target esp-idf/sensecap-indicator` from the repository root.

See `target.json` for examples, native interface references and exact toolchain selection. Build results and device observations are separate.

BSP public headers live in `bsp/include/`; implementation and private headers live in `bsp/src/`. Each example has its own `bsp.cmake` and managed dependency manifest. Exported projects include that example’s selected interfaces and source closure. See [native composition and layout](../../../../docs/development/native-compositions.md).

GX and DX display assemblies have sourced native profiles. Use `--variant gx` or `--variant dx` with context, new or focused Target validation. The full Target validation builds both. The historical repository build default is GX; exports record their selected variant and use it as the native default. Panel/PCB identity and revision compatibility remain unknown until established separately. See [hardware variant selection](../../../../docs/development/hardware-variants.md) and [pinned vendor evidence](../../../../devices/sensecap-indicator/reference/display-variants.md).
