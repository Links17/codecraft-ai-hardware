---
name: codecraft-develop
description: Develop hardware applications and repository contributions with native Target implementations.
---

# Develop

Read the root two-part contract and obtain context for the selected Target. Hardware facts come from devices/<device>/AGENTS.md and reference/. Native BSPs/examples remain in platforms/<stack>/targets/<device>. Use codecraft-ideate when the application brief needs clarification. Generate private projects with `python3 codecraft.py new --target <id> --example <name> --output projects/<name>`; explicit external directories remain supported. Use --brief <file.json> for a confirmed brief. Keep generated AGENTS content sourced from project.yaml and preserve custom rules outside its marked region. See [project workspaces](../../docs/development/project-workspaces.md). Preserve application/BSP boundaries and user changes; finish with the required validation report.

All commands above use `python3 codecraft.py <command>` from the repository root. Read the root AGENTS.md before acting.

For cloud functionality, select a Capability/Provider from cloud-catalog. Use new --capabilities with reviewed selections; the export contains the selected pinned standalone Skill package and its API client. Run python3 codecraft.py lock-project . after deliberate application or environment updates; the initial import provenance remains intact.

Maintain README.md and README.zh_CN.md together. All other engineering documents, including AGENTS.md, SKILL.md, API references, plans and reports, use one English source. Update generators and local references with documentation changes; never generate translated Agent rules or duplicate hardware facts.

Use skill-release prepare/check/apply for standalone package changes, following docs/development/skill-releases.md. Keep helper maintenance under skills/_cloud and runtime imports package-local. Review candidate bytes, separate versions and the exact digest before applying; never automatically accept hash drift or rewrite original provenance. Exported applications use the same public CLI and source lock.

ESP-IDF examples use explicit BSP compositions. Read docs/development/native-compositions.md when changing native source selection, BSP layout or dependencies. Keep the profile, native manifests, Target example scope and lock aligned; settle native lock updates before final source-fingerprint validation. A successful compiler command must also pass the actual BSP-source/requirement check.

For sourced hardware variants, use context/new/validate --variant as described in docs/development/hardware-variants.md. Keep the Device facts, Target/native profile, export selection and lock aligned. The full Target gate covers all variants. A build default is not physical identification; physical evidence must identify its variant and an observed compatible revision. Unknown compatibility remains unresolved.
