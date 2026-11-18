# Hardware repository architecture

The repository has four owners. Device records describe physical hardware;
Platforms implement software stacks and Targets; Capabilities define cloud Skill
contracts; Skills orchestrate development and provide standalone cloud clients.
The governing requirements are [codecraft-hardware-distilled.md](../development/codecraft-hardware-distilled.md).

| Owner | Authoritative inputs | Derived outputs |
| --- | --- | --- |
| Device | device.json, reference sources, asset manifests, physical acceptance and evidence | Device AGENTS, discovery index and support state |
| Platform / Target | adapter, platform.json, target.json, native BSP/configuration/examples, owner-local tests | Native build cases, scoped exports and CI matrix |
| Capability / Provider | semantic schema, service policy, client bindings and complete package inventory | Resolution candidates, effective schemas and prepared argument arrays |
| Skill | workflow instructions, orchestration, source graph, validation and standalone clients | Task context, project lock, build receipt and reviewed release candidate |

A Device can have multiple Targets. Each Target uses one native software stack;
peripheral interfaces belong to that Target. Capabilities are consumed by cloud
Skills and do not represent GPIO, display or individual device peripherals.
Cloud servers, accounts, pairing, telemetry and publishing infrastructure are external.

## Dependency and invocation boundaries

The public command is `python3 codecraft.py`. The root bootstrap loads
`skills/_shared/cli.py`; platform adapters own native build behavior. Repository
and exported application commands share one result contract. The application
workflow is `new`, `verify-project`, `lock-project`, `build-project`, then
`package` when a source archive is needed. Build and package never write a device.

The cloud catalog imports neutral registry/graph primitives and its own schema.
It does not import the hardware Catalog. Optional Target context is injected by
the composition layer and validated only when supplied. Resolution selects a
Provider; preparation validates semantic and policy constraints and returns an
argument array. Only an authorized standalone Skill execution opens user files,
reads credentials or contacts a service. See [Capability and Provider policy](capability-provider-policy.md).

Context, export, locks and evidence use the same transitive source graph. Missing
inputs fail. Exports contain native sources, the selected adapter and the actual
orchestration implementation; a selected cloud Provider adds its complete pinned
Skill package. The immutable import origin and the reviewed application snapshot
are recorded separately. A changed source or toolchain invalidates verification.

## Private projects and V0.2 alignment

User applications may be generated under ignored projects/<name> or explicit external paths. project.yaml owns a validated brief; creation and relocking render its marked application AGENTS region without replacing custom rules. Reference graphs reject private-project inputs, while application locks still cover their complete source inventory. Ideation context adds the ideate and discover Skills. See [project workspaces](../development/project-workspaces.md).

The [V0.2 ledger](../development/v0.2-todo.md) tracks the design target separately from current implementation. Cloud clients still live in Skill packages; sensecraft-cli migration, MQTT/local/edge Providers and a registered simulator are pending. The existing simulation decision is a current limitation, not completion of V0.2 simulator acceptance.

## Native implementation

ESP-IDF BSPs separate public include/ contracts from private src/ implementation.
Each example declares its native composition and managed dependencies. The
adapter checks actual compiled sources and requirements after a successful build.
Board wiring and resource ownership stay in BSPs; shared protocols stay in
components. See [native compositions](../development/native-compositions.md).

Arduino Targets declare exact CLI, core, FQBN and library versions. The adapter
checks installed inputs, fingerprints the selected dependencies and passes
explicit library paths to the compiler. Sketches remain independent native
applications. Linux Targets own their overlays and device-interface demos;
source validation and overlay compilation are reported separately.

All Device and Target manifests use schema 3 with an explicit variants object.
A selected variant follows context, export, native configuration, locks and
evidence. A build default does not identify a physical assembly. See
[hardware variants](../development/hardware-variants.md).

## Validation and maintained content

Host tests live with their behavior owner and are collected recursively through
one runner. Device physical acceptance is separate. Use `test --list`,
`test --path <owner>`, `validate --static` and `validate`; inspect every result.
Support is derived from source-bound evidence, not README assertions. A native
build and a clean locked export are required for build-verified status; physical
support requires actual revision-specific observations.

README files are bilingual. Engineering guidance is English and describes the
current contract. Generated views are updated from their owning inputs. Source
provenance and real observations remain attributable; software that has no
current consumer, duplicate command entries and transition-only records are not
maintained architecture. See [testing](../development/testing.md),
[Skill releases](../development/skill-releases.md) and [open TODOs](../development/optimization-plan.md).
