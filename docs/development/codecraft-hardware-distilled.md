# CodeCraft Hardware architecture plan (distilled)

This retained planning baseline defines the hardware repository scope. The [implementation and migration map](../architecture/overview.md) describes current behavior.

The repository supplies discoverable, attributable and verifiable Seeed hardware knowledge, BSPs, native examples, development Skills and evidence. Accounts, cloud runtime, communities, platform resource management and publishing belong elsewhere. User applications live outside this reference repository.

## Architecture

Four content owners: devices owns physical identity/revision, facts, sources, assets and device evidence; platforms owns software-stack adapters, native Targets, configuration, tests and simulation; capabilities owns reusable contracts consumed by cloud Skills, with their inputs/outputs, configuration, resources, errors and limitations; skills owns workflows, scripts, shared logic and the validation entry. Root AGENTS provides global rules, routing and a generated light index; README provides quick start; docs explains architecture; CI calls the shared gate.

A Device is independent of software stack. A Target implements one Device on one stack. Capabilities serve cloud Skills and reference Targets/dependencies when device implementations are needed. GPIO, display, audio and other peripherals are Device facts and Target native interfaces, not individual Capabilities. This boundary reflects the user clarification; consuming cloud-facing contracts does not add a cloud runtime to this repository. Standardize metadata, operations and results while preserving native drivers/build systems; do not force a cross-platform ABI.

The user’s follow-up also includes the four standalone cloud API Skill packages under skills/. Their clients, local package references and offline tests are maintained here; the cloud server remains outside this repository.

## Device knowledge

Each device has one AGENTS entry and reference/ sources. Generate devices/AGENTS from device Overviews. Include Overview/scenarios and physical orientation where known, controller/memory/storage and software stacks, connectivity/pin maps/Grove, inputs/outputs, power/battery/accessories, assets/purchase links and sources. Omit absent hardware and mark missing facts unknown. Cite primary vendor sources, BSP/DTS/pins or measurements for pins, addresses, electrical limits and compatibility. Retain source conflicts and their resolution. Maintain each fact once and generate or reference its other views.

## Development and maintenance

- Load only task-relevant device, Target, dependency, limitation and Skill context. Every reference must resolve.
- Declare inspect/configure/generate/build/host-test/simulate/flash/device-test/logs/package support and reasons for unavailability.
- Generate external projects from clean directories through the development workflow; record selections in project.yaml and lock versions in codecraft.lock, with minimum validation instructions.
- Keep tests, simulators and assets with their Device, Platform or Capability. Simulators state coverage; assets record provenance, license, version and checksum. Device imagery must match revision, dimensions and alpha.
- Generate device indexes, capability and CI matrices and enforce generation drift checks. Share structured bilingual facts; do not register lists manually.
- Preserve user work, never guess hardware facts or commit secrets, retain durable sanitized evidence, and perform physical writes only within authorization.

## Validation and evidence

Static checks cover structure, sources, secrets, licensing and formatting. Knowledge checks cover index completeness, reference closure, task context and generated consistency. Host/contract tests cover logic, interfaces, resources and positive/negative compatibility. Build affected Targets and generated projects. Run simulator cases only when a simulator declares coverage. Physical validation names revision, flashing, behavior and recovery.

Use passed, failed, skipped, not_supported and not_run distinctly. Skips and unperformed work do not pass. build-verified requires Target builds and generated-project checks; device-verified requires revision, Target, toolchain and functional hardware cases. Keep maturity and maintenance separate. Evidence records repository revision, Device/revision, Target, toolchain, commands, environment, results, logs, limitations and operator. Reassess evidence after hardware/toolchain/capability changes. New boards need static/knowledge/contracts and one Target build; blocked builds remain explicitly experimental.

## Collaboration and rollout

Hardware teams own facts/BSPs/Targets/assets/device evidence; capability maintainers own contracts/compatibility; core maintainers own shared structure/indexes/adapters/tools; QA/DX owns generation/docs/verification. Contributions identify scope/owner, establish sources, edit the owning module, run validation, receive domain review and derive support from evidence. PRs explain purpose, affected objects, sources/licenses, tests, unknowns, compatibility and rollback. Reject missing sources, broken references, duplicate registration and conflated verification claims.

Roll out in order: unify device knowledge and generated indexes; complete discovery/context; connect adapters and reproducible project generation; progressively add owned simulation, imagery and physical evidence. Long-term HIL resources/retest cadence, large-asset storage and support for partial boards remain open decisions.

Original plan: [CodeCraft hardware architecture](https://seeedstudio.feishu.cn/docx/QgNjdqDbwotGQcxDKHmcxYMvn6b), V0.1, 2026-11-17.
