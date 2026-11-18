---
name: codecraft-validate
description: Validate repository contracts, generated indexes, native builds and evidence.
---

# Validate

Run `generate --check`, `validate --static` and affected Target builds. The no-option validate command runs the complete software gate without device writes. Inspect every status and exit code. Record device observations only through record-evidence with real revision, source digest, toolchain, operator and retained sanitized log. A simulator or build never establishes physical behavior.

All commands above use `python3 codecraft.py <command>` from the repository root. Read the root AGENTS.md before acting.

The documentation gate requires paired README files and rejects Chinese copies of other engineering documents. Check both repository and exported-project navigation. Preserve original third-party evidence and fail on stale Skill inventories instead of silently accepting new fingerprints.

For changed standalone packages, follow docs/development/skill-releases.md. Check the exact candidate, review its digest and versions, then explicitly apply it; application reruns isolated client conformance. A passing candidate does not publish, authorize a live API task or replace the complete repository gate.

For focused host checks, use `python3 codecraft.py test --path <owner>`; use `test --list` to inspect collected IDs. Read docs/development/testing.md before moving tests. Preserve the recorded ID mapping and full scenario coverage; do not keep old forwarding wrappers that execute the same suite twice. Skips and fixture/collection failures must remain visible.

ESP-IDF examples use explicit BSP compositions. Read docs/development/native-compositions.md when changing native source selection, BSP layout or dependencies. Keep the profile, native manifests, Target example scope and lock aligned; settle native lock updates before final source-fingerprint validation. A successful compiler command must also pass the actual BSP-source/requirement check.

For sourced hardware variants, use context/new/validate --variant as described in docs/development/hardware-variants.md. Keep the Device facts, Target/native profile, export selection and lock aligned. The full Target gate covers all variants. A build default is not physical identification; physical evidence must identify its variant and an observed compatible revision. Unknown compatibility remains unresolved.
