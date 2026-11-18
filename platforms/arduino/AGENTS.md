# arduino platform rules

The [root contract](../../AGENTS.md) governs. Device facts belong in devices/<device>/AGENTS.md and its reference files.

The Wio Terminal and post-October-2025 Grove Beginner Kit Targets declare FQBN, exact CLI/core/library versions, board-manager URLs and standalone sketches. Hardware facts and physical observations belong to their Device. Use the declared core and explicit library selection; other installed board profiles do not establish compatibility.

Every Target must declare examples, toolchain provenance, native interface references, and dependencies in target.json. Supported operations and their limits are in platform.json. Run `python3 codecraft.py validate --target arduino/<device>`. Never infer device verification from a build.
