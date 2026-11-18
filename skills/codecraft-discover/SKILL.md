---
name: codecraft-discover
description: Discover registered devices, Targets and native interfaces with explicit unknowns.
---

# Discover

Use `discover --interface <id>` (repeatable) and optional `--platform <id>`. Show matching candidates, limitations and unknowns. No matches means no registered implementation, not proof about all hardware. Load `context --target <id>` before development; do not guess missing pins or board revisions.

All commands above use `python3 codecraft.py <command>` from the repository root. Read the root AGENTS.md before acting.

Use cloud-catalog and resolve-capability for cloud capabilities; a peripheral interface list is not a Capability registry. Current entries are llm, asr, tts and image-generation, with Providers pinning standalone Skills maintained in this repository. Do not assume missing network, credential references, privacy decisions or resource bounds are satisfied.
