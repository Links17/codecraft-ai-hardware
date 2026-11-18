# AI development guide

Read both applicable parts of the root AGENTS.md. Use `python3 codecraft.py context --target <platform>/<device>` to collect device facts, native implementations, dependencies, native interfaces and unknowns. Read the selected files for the task; a returned path is not evidence that its contents were checked. Consult primary vendor sources when hardware facts need confirmation. Keep the five required development Skills available and load the matching workflows.

## Application and BSP boundary

Reusable board drivers belong in platforms/<stack>/targets/<device>/bsp; ESP-IDF components shared by multiple boards belong in platforms/esp-idf/components. Pages, state machines, animations and application tasks belong in examples or a private user project under projects/<name> (or an explicitly selected external directory). See [project workspaces and briefs](project-workspaces.md). Tests live with their owning core, cloud client, Capability, Platform, component or Target; validation-entry tests stay with codecraft-validate. See [test ownership and execution](testing.md). Keep testable logic independent of ESP-IDF/LVGL.

For ESP-IDF builds, follow [native composition and layout](native-compositions.md). Match the example BSP source/requirement lists, managed manifest, Target input/dependency/interface scopes and regenerated lock. Keep the native registration in the BSP root; public include/ and private src/ have distinct visibility.

## ESP-IDF runtime invariants

- LVGL access outside the LVGL task must hold the BSP's LVGL lock.
- Button callbacks must remain non-blocking. Move audio, storage and other slow operations into worker tasks.
- Stop every task, timer, callback and event handler that can touch a screen before deleting it.
- Keep the default partition table minimal; validate custom partition and persistent-data changes explicitly.

## Adding a new board

1. Establish devices/<device>/reference/ provenance first. Identify device revision, controller and memory, interfaces/pins, inputs/outputs, power, accessories and software prerequisites. Unknown facts remain unknown. Record conflicts and conclusions in reference/ and expose them through the generated device entry.
2. Add device.json with bilingual Overview/scenarios and source-checked canonical typed facts, source paths, maintenance owner, independent maturity, derived Target indexes (no manual backlinks), unknowns and an asset manifest. All Device/Target records use schema_version 3 with an explicit variants object, empty when none are declared. Add tests/acceptance.json and an actual physical acceptance procedure; do not invent completed observations.
3. Add platforms/<stack>/targets/<device>/target.json with native examples, toolchain provenance, native interface references, common/per-example inputs and dependencies. Preserve native BSP/build conventions. Lock ESP-IDF dependencies; Arduino needs exact CLI/core/library versions and an FQBN. A new stack must declare every operation in platform.json and pass adapter contract tests.
4. Keep peripheral interfaces in Target metadata. Add a Capability only from a concrete cloud Skill consumer contract; include inputs/outputs, configuration, resources, errors, dependencies and integration tests. Put tests, assets and simulators with their owner. A simulator must declare its coverage; unsupported operations must explain why.
5. Run `generate`, `generate --check`, `validate --static`, then `validate --target <id> --projects`. These generate and check device indexes, capability and CI matrices. Never manually register a board in multiple lists. Missing build prerequisites prevent a passing gate; experimental support must state the reason.
6. Collect revision-specific device evidence only under authorization. Keep build, generated-project, simulator and physical results separate. Run the complete gate before delivery.

## Delivery format

Report static/knowledge/host checks, builds per Target with actual toolchain, clean generated-project checks, and on-device verification separately. Include failures, skips, unsupported operations and unperformed checks with their reasons. A build is not hardware validation. Use the root contract and PR template for exact fields.

Requested commits use an English imperative Conventional Commit subject. Preserve unrelated work, credentials stay out of source, and generated firmware stays untracked. A commit does not authorize push, PR or merge. Follow [.github/CONTRIBUTING.md](../../.github/CONTRIBUTING.md).

For sourced assembly/revision differences, read [hardware variants](hardware-variants.md). Device owns the physical facts; Target owns native selections. Preserve explicit variant identity through application export, locks and evidence. Do not derive a physical revision from a build default.
