# CodeCraft Hardware architecture requirements

This specification defines repository scope, ownership and acceptance. The [architecture guide](../architecture/overview.md) describes the implementation.

The repository supplies discoverable, attributable and verifiable Seeed hardware knowledge, BSPs, native examples, development Skills and evidence. Accounts, cloud runtime, communities, platform resource management and publishing belong elsewhere. User applications live in ignored projects/<name> workspaces or explicitly selected external directories; they are not reference content.

## Architecture

Three content owners: devices owns the directory index, per-device knowledge, physical identity/revision, facts, sources, assets and native Targets under devices/<device>/targets/, including BSPs, examples and board configuration; platforms owns shared software-stack/runtime adapters, build helpers, reusable components and simulation support; skills owns independently installable development workflows and cloud capability packages, including package-local scripts and contracts with their inputs/outputs, configuration, resources, errors and limitations. Development workflow names use sensecraft-development-* and cloud capability names use sensecraft-capabilities-*; every Skill is a direct child of skills/. Each cloud package owns contract.json.

Repository tooling supports these content owners under tools/: codecraft/ owns the public CLI, shared orchestration, parsing, graphs, exports, locks and validation; skill_packages/ owns shared client maintenance, original import provenance and reviewed package release records. Inventories remain outside packages and pin their complete distributed bytes. All repository-maintained tests, fixtures and mocks live under tests/, grouped by Device, Platform, Skill or Tool owner; tests/devices/<device>/ also retains board observations and evidence. Root AGENTS provides global rules, routing and links to the shared indexes; README provides quick start; docs explains architecture; CI calls the shared gate.

A Device is independent of software stack. A Target implements one Device on one stack. Its logical ID is <stack>/<device>, while its sole physical root is devices/<device>/targets/. Register the Device's native Target in targets/target.json, with bsp/, examples/ and native configuration directly beside it. The manifest declares the platform; do not add another stack directory inside targets/. Platform code consumes the Target manifest and shared resources; it must not maintain another board tree or copy Device implementations. Skill contracts describe Agent-host operations; native integration requires explicit sourced Target bindings and evidence. GPIO, display, audio and other peripherals are Device facts and Target native interfaces, not cloud Skill contracts. Consuming cloud-facing contracts does not add a cloud runtime to this repository. Standardize metadata, operations and results while preserving native drivers/build systems; do not force a cross-platform ABI.

Four standalone CodeCraft inference API Skill packages live under skills/. Their clients and local package references are maintained there; offline tests live under tests/; the cloud server remains outside this repository. SenseCraft platform management uses the separately installed official sensecraft-cli and its bundled Skill. This repository owns [setup and routing](sensecraft-cli.md); the external project owns its command, authentication and HTTP implementation.

## Device knowledge

Each device has one authored AGENTS.md containing ordinary Markdown knowledge,
sourced specification tables and physical acceptance procedures. Its format and
reference rules are defined once in [Device documents and shared references][device-documents].
Do not embed a JSON contract, maintain a second rendered copy, or create parallel
Device/acceptance files. Keep actual reference material and assets with the Device,
and observations and evidence under tests/devices/<device>/. Declare missing facts
as unknown and retain source conflicts. The device index and matrices are derived;
generation never rewrites the authored Device entry. Each document has an owner;
other documents link to that authoritative source instead of copying its rules.

## Development and maintenance

- Load only task-relevant device, Target, dependency, limitation and Skill context. Every reference must resolve.
- Declare inspect/configure/generate/build/host-test/simulate/flash/device-test/logs/package support and reasons for unavailability.
- Generate private projects into new directories through the development workflow; record selections in project.yaml and lock versions in codecraft.lock, with minimum validation instructions.
- Keep all repository-maintained tests, mocks and test fixtures under tests/, grouped by source owner according to [test ownership](testing.md). Retain Device observations and evidence in tests/devices/<device>/. Device knowledge, native Targets, implementation references and assets stay with the Device. Simulators state coverage; assets record provenance, license, version and checksum. Device imagery must match revision, dimensions and alpha.
- Generate device indexes, native interface and CI matrices, and the Skill inventory and enforce generation drift checks. Read facts from the authored Device Markdown; do not register lists manually.
- Preserve user work, never guess hardware facts or commit secrets, retain durable sanitized evidence, and perform physical writes only within authorization.

## Validation and evidence

Static checks cover structure, sources, secrets, licensing and formatting. Knowledge checks cover index completeness, reference closure, task context and generated consistency. Host/contract tests cover logic, interfaces, resources and positive/negative compatibility. Build affected Targets and generated projects. Run simulator cases only when a simulator declares coverage. Physical validation names revision, flashing, behavior and recovery.

Use passed, failed, skipped, not_supported and not_run distinctly. Skips and unperformed work do not pass. build-verified requires Target builds and generated-project checks; device-verified requires revision, Target, toolchain and functional hardware cases. Keep maturity and maintenance separate. Evidence records repository revision, Device/revision, Target, toolchain, commands, environment, results, logs, limitations and operator. Reassess evidence after hardware/toolchain/Skill contract changes. New boards need static/knowledge/contracts and one Target build; blocked builds remain explicitly experimental.

## Ownership and acceptance

Hardware teams own facts/BSPs/Targets/assets/device evidence; Skill maintainers own cloud contracts/client conformance; core maintainers own shared structure/indexes/adapters/tools; QA/DX owns generation/docs/verification. Contributions identify scope/owner, establish sources, edit the owning module, run validation, receive domain review and derive support from evidence. PRs explain purpose, affected objects, sources/licenses, tests, unknowns, compatibility and rollback. Reject missing sources, broken references, duplicate registration and conflated verification claims.

Device knowledge, generated indexes, discovery/context, native adapters and reproducible project generation are required software boundaries. Simulation, imagery and physical evidence require their own sourced acceptance. Long-term HIL resources/retest cadence, large-asset storage and support for partial boards remain open decisions.

Design target: [CodeCraft hardware architecture](https://seeedstudio.feishu.cn/docx/QgNjdqDbwotGQcxDKHmcxYMvn6b), V0.2, 2026-11-18, revision 1430. This document describes the implemented boundaries above; it does not declare the entire V0.2 target complete. See the [implementation ledger](v0.2-todo.md) for remaining MQTT/local/edge Providers, simulator ownership, asset links and physical acceptance. The user clarified V02-05 as direct adoption of the external SenseCraft CLI; it does not assert replacement of the separate CodeCraft inference APIs.

[device-documents]: device-documents.md

CLI contract 3 preserves native hardware and repository maintenance commands. SenseCraft owns platform management; standalone inference Skills own direct API execution. Explicit --skills selections replace generic service resolution. Project/lock schema 3 and portable workflow closure preserve selected sources without forwarding commands or mixed-schema readers. See [Skill ownership](../architecture/skill-contracts.md).
