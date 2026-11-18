---
name: codecraft-setup
description: Install and activate the exact toolchain declared by a hardware Target.
---

# Setup

Read target.json for the exact toolchain and its source. For ESP-IDF, activate the declared installation and verify idf.py --version. Linux source validation needs Python 3 and dtc. Arduino needs the declared FQBN and exact core/library versions. Preserve other toolchains; install missing prerequisites within authorization and report unresolved dependencies.

All commands above use `python3 codecraft.py <command>` from the repository root. Read the root AGENTS.md before acting.
