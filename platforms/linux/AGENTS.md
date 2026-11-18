# linux platform rules

The [root contract](../../AGENTS.md) governs. Device facts belong in devices/<device>/AGENTS.md and its reference files.

Preserve overlays and native demos. GPIO uses chip/line addressing; clean up claims on exit. OS image/kernel are unknown until observed; dtc compilation is separate from device operation.

Every Target must declare examples, toolchain provenance, native interface references, and dependencies in target.json. Supported operations and their limits are in platform.json. Run `python3 codecraft.py validate --target linux/<device>`. Never infer device verification from a build.
