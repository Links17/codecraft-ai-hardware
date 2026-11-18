# arduino platform rules

The [root contract](../../AGENTS.md) governs. Device facts belong in devices/<device>/AGENTS.md and its reference files.

No hardware Target is registered yet. New Targets require fqbn, exact core/library versions, board-manager URLs, and standalone sketches. Do not treat contract test fixtures as supported boards.

Every Target must declare examples, toolchain provenance, native interface references, and dependencies in target.json. Supported operations and their limits are in platform.json. Run `python3 codecraft.py validate --target arduino/<device>`. Never infer device verification from a build.
