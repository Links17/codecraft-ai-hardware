# esp-idf platform rules

The [root contract](../../AGENTS.md) governs. Device facts belong in devices/<device>/AGENTS.md and its reference files.

Keep BSP and sdkconfig under targets/<device>. Use the version in target.json; imported v6.0.1 references do not override the current v6.0.2 build target. Preserve LVGL locking and non-blocking callbacks. Shared components belong in components/.

Every Target must declare examples, toolchain provenance, native interface references, and dependencies in target.json. Supported operations and their limits are in platform.json. Run `python3 codecraft.py validate --target esp-idf/<device>`. Never infer device verification from a build.

BSP public contracts stay in include/; implementation/private headers belong in src/. Each example MUST declare its sources and requirements in bsp.cmake, optional managed packages in main/idf_component.yml, and matching Target example inputs/dependencies/interface scopes. Native component registration MUST remain in the board BSP CMakeLists.txt. Preserve required system components such as esp_psram when using MINIMAL_BUILD. Read [native composition rules](../../docs/development/native-compositions.md); regenerate locks through the native tool before final source/evidence checks.

Declared hardware variants use native CMake profiles and distinct build cases/output directories. Verify actual cache selection and BSP compile definitions. Follow [hardware variant rules](../../docs/development/hardware-variants.md); keep physical revision compatibility separate from a build profile.
