---
name: codecraft-build
description: Build native firmware and run checks without flashing or publishing.
---

# Build

Run `validate --static`, then `validate --target <id>` for each affected Target. The complete software gate is `validate`. A missing prerequisite is not_run, never passed. No build command flashes or publishes. Diagnose failures before retrying.

All commands above use `python3 codecraft.py <command>` from the repository root. Read the root AGENTS.md before acting.

In a generated application, use `python3 codecraft.py build-project .`; explicitly accept reviewed application/toolchain changes with `python3 codecraft.py lock-project .`. The bundled `python3 build.py [--lock]` commands remain compatible. Do not use reference-Target validation to bypass an application's lock.

ESP-IDF examples use explicit BSP compositions. Read docs/development/native-compositions.md when changing native source selection, BSP layout or dependencies. Keep the profile, native manifests, Target example scope and lock aligned; settle native lock updates before final source-fingerprint validation. A successful compiler command must also pass the actual BSP-source/requirement check.

For sourced hardware variants, use context/new/validate --variant as described in docs/development/hardware-variants.md. Keep the Device facts, Target/native profile, export selection and lock aligned. The full Target gate covers all variants. A build default is not physical identification; physical evidence must identify its variant and an observed compatible revision. Unknown compatibility remains unresolved.
