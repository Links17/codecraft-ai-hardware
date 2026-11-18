---
name: codecraft-develop
description: Develop hardware applications and repository contributions with native Target implementations.
---

# Develop

Read the root two-part contract and obtain context for the selected Target.
Start from devices/AGENTS.md and the selected Device's authored AGENTS.md. Follow
[Device documents and shared references](../../docs/development/device-documents.md)
when editing knowledge, specifications, sources or acceptance. Follow the matching
platforms/<stack>/AGENTS.md for native work. Use codecraft-ideate when the
application brief needs clarification. Generate private projects with
`new --target <id> --example <name> --output projects/<name>`; explicit external
directories remain supported. Use --brief <file.json> for a confirmed brief.
Keep generated application AGENTS content sourced from project.yaml and preserve
custom rules outside its marked region. See [project workspaces](../../docs/development/project-workspaces.md).
Preserve application/BSP boundaries and user changes; finish with the required
validation report.

All commands above use `python3 codecraft.py <command>` from the repository root. Read the root AGENTS.md before acting.

For SenseCraft platform management or CodeCraft Hub tasks, use the official external sensecraft-cli Skill; see [external setup and routing](../../docs/development/sensecraft-cli.md). Install/select the required external tool version when needed and follow its task-specific reference.

For CodeCraft inference functionality, select a Capability/Provider from cloud-catalog. Use new --capabilities with reviewed selections; the export contains the selected pinned standalone Skill package and its API client. Run python3 codecraft.py lock-project . after deliberate application or environment updates; the initial import provenance remains intact.

Maintain README.md and README.zh_CN.md together. All other engineering documents, including AGENTS.md, SKILL.md, API references, plans and reports, use one English source. Update generators and local references with documentation changes; never generate translated Agent rules or duplicate hardware facts.

Use skill-release prepare/check/apply for standalone package changes, following docs/development/skill-releases.md. Keep helper maintenance under skills/_cloud and runtime imports package-local. Review candidate bytes, separate versions and the exact digest before applying; never automatically accept hash drift or rewrite original provenance. Exported applications use the same public CLI and source lock.

For ESP-IDF source selection and BSP dependencies, follow [native composition rules](../../docs/development/native-compositions.md).

For assembly selection, export and revision-specific evidence, follow [hardware variant rules](../../docs/development/hardware-variants.md).
