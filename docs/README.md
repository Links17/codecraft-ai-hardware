<p align="right"><strong>English</strong> · <a href="README.zh_CN.md">简体中文</a></p>

# Documentation

Only README files have Chinese counterparts. Engineering guidance, rules, Skills and reports are maintained in English.

## Current rules and implementation

- [Repository and contribution contract](../AGENTS.md)
- [Architecture and migration](architecture/overview.md)
- [Capability and Provider policy migration](architecture/capability-provider-policy.md)
- [Simulation scope decision](architecture/simulation-scope.md)
- [AI development guide](development/ai-guide.md)
- [Standalone Skill release workflow](development/skill-releases.md)
- [Host test ownership and focused execution](development/testing.md)
- [ESP-IDF BSP composition and layout](development/native-compositions.md)
- [Hardware variants and native build selection](development/hardware-variants.md)
- [Generated device/capability inventory](inventory.md)
- [Generated vendor index](vendor-sources.md)
- [Device acceptance](on-device-validation.md)

## Planning and open work

- [Distilled planning baseline](development/codecraft-hardware-distilled.md) — stable planning address; current behavior is documented in the architecture guide.
- [Optimization plan and TODOs](development/optimization-plan.md) — the sole ledger for OPT-01 through OPT-19.

Hardware facts and original source records live under devices/<device>/reference/.

## Historical reviews and execution evidence

Reports describe the source and environment at the stated date. They do not override current rules or promote changed source to verified status.

- [Refactor validation](reviews/refactor-validation.md)
- [Capability and cloud Skill review](reviews/capability-review.md)
- [Optimization execution snapshot, 2026-11-18](reviews/optimization-progress-2026-11-18.md)
- [Native-driver optimization snapshot, 2026-11-18](reviews/optimization-drivers-2026-11-18.md)
- [BSP lifecycle optimization snapshot, 2026-11-18](reviews/optimization-lifecycle-2026-11-18.md)
- [Native I/O contract optimization snapshot, 2026-11-18](reviews/optimization-io-contracts-2026-11-18.md)
- [BSP peripheral and caller contract snapshot, 2026-11-18](reviews/optimization-peripheral-contracts-2026-11-18.md)
- [Cloud domain and Provider policy snapshot, 2026-11-18](reviews/optimization-cloud-policy-2026-11-18.md)
- [Skill delivery and public entry snapshot, 2026-11-18](reviews/optimization-skill-delivery-2026-11-18.md)
- [Test ownership and discovery snapshot, 2026-11-18](reviews/optimization-test-ownership-2026-11-18.md)
- [Native composition and BSP layout snapshot, 2026-11-18](reviews/optimization-native-composition-2026-11-18.md)
- [Sourced hardware variant snapshot, 2026-11-18](reviews/optimization-hardware-variants-2026-11-18.md)
- [Submission validation snapshot, 2026-11-18](reviews/submission-validation-2026-11-18.md)
