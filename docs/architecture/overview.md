# Hardware repository architecture

The repository has four owners. Devices own hardware knowledge and native Targets;
Platforms supply shared software-stack infrastructure; Capabilities define cloud Skill
contracts; Skills orchestrate development and provide standalone cloud clients.
The governing requirements are [codecraft-hardware-distilled.md](../development/codecraft-hardware-distilled.md).

| Owner | Authoritative inputs | Derived outputs |
| --- | --- | --- |
| Device / Target | Per-device knowledge, authored specifications, assets, target.json, native BSP/configuration/examples | Device index, native interface bindings, scoped source closure and support state |
| Platform | adapter, platform.json, shared build helpers and reusable components | Native build cases, stack validation and CI matrix |
| Capability / Provider | semantic schema, service policy, client bindings and complete package inventory | Resolution candidates, effective schemas and prepared argument arrays |
| Skill | workflow instructions, orchestration, source graph, validation and standalone clients | Task context, project lock, build receipt and reviewed release candidate |

Each Device registers its native Target at targets/target.json. That manifest
selects one software stack; peripheral interfaces belong to the Target. Capabilities are consumed by cloud
Skills and do not represent GPIO, display or individual device peripherals.
Cloud servers, accounts, pairing, telemetry and publishing infrastructure are external.

## Device knowledge entry

Each Device has one authored English AGENTS.md containing knowledge, sourced
specification tables and acceptance procedures. The deterministic reader follows
[Device documents and shared references][device-documents]. Shared documentation
has one maintained owner and is referenced through links. devices/AGENTS.md is the
derived directory index; Device documents themselves are never regenerated.

Device knowledge includes hardware behavior, reference implementation notes,
protocols, sources and media. Supporting material belongs in the device's
reference/ directory when needed. Concrete Target implementations live under
devices/<device>/targets/, including BSPs, examples and board configuration.
Platform owns shared stack/runtime adapters, build helpers and reusable components.
Target manifests bind native interfaces to implementations; Target READMEs document software
integration and build procedures. A Target can depend on Device reference source
through the same declared graph; it does not duplicate that source.

Assets are declared inline; an empty list means none are registered. Only actual
asset files need assets/. Dated observations, structured evidence and raw logs
live in tests/devices/<device>/ and are linked from the Device entry. Acceptance
procedures stay in the authored Device document. Board-specific host tests and fixtures live
in tests/devices/<device>/targets/; observations, records and logs are
excluded from host discovery. All other tests, fixtures and mocks also live under
tests/, grouped by the source owner according to [test ownership](../development/testing.md).

```text
devices/
  AGENTS.md                  # Device directory index
  <device>/
    AGENTS.md                # Knowledge, sourced specifications and acceptance
    reference/               # Supporting reference material, when needed
    assets/                  # Actual registered media, when present
    targets/
      target.json            # Device × software stack binding
      bsp/                   # Board drivers, where the stack uses a BSP
      examples/              # Standalone native examples
                             # Linux retains its native overlays/ and demos/
platforms/<stack>/
  platform.json              # Stack/runtime adaptation contract
  adapter.py
  components/                # Reusable native components, where needed
  cmake/                     # Shared native build helpers, where needed
tests/
  AGENTS.md                  # Test directory index and evidence rules
  devices/<device>/
    targets/                 # Board-specific host tests and fixtures
    observations.md          # Attributed observations, when available
    records/                 # Structured evidence
    logs/                    # Original sanitized logs
  platforms/<stack>/         # Adapter tests and shared test support
    components/<component>/  # Shared component tests and fixtures
  capabilities/              # Shared policy/harness and per-Capability tests
  skills/                    # Core, client, release and validation tests
```

Target IDs remain <stack>/<device>; the stack is metadata, not another directory
inside targets/. Native software stacks retain their own ABIs. Each native file has
one owner: Targets reference shared Platform resources through their declared
dependency closure. Platform directories do not contain board copies or forwarding
paths. The same layout is preserved in generated projects and their locks.

Source graph schema 3 and application locks hash complete files. Exports copy the
authored Device entry unchanged; derived indexes and evidence summaries live
outside it. Editing hardware guidance or acceptance changes source identity.

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

The [V0.2 ledger](../development/v0.2-todo.md) tracks the design target separately from current implementation. SenseCraft platform operations use the official external sensecraft-cli and bundled Skill, with [setup/routing guidance](../development/sensecraft-cli.md) in this repository. Authentication, platform HTTP calls and command implementation stay upstream. Existing CodeCraft inference clients remain in their Skill packages; the verified platform command set does not replace them. MQTT/local/edge Providers and a registered simulator are pending. The existing simulation decision is a current limitation, not completion of V0.2 simulator acceptance.

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

Parsed Device Markdown uses schema 5 and Target manifests use schema 3, each with an explicit variants object.
A selected variant follows context, export, native configuration, locks and
evidence. A build default does not identify a physical assembly. See
[hardware variants](../development/hardware-variants.md).

## Validation and maintained content

Host tests live under tests/, grouped by behavior owner, and are collected
recursively through one runner. Device physical acceptance is separate. Use `test --list`,
`test --path <owner>` and `validate --static`; select native builds using the
[root validation policy](../../AGENTS.md#required-validation-and-delivery).
No-option `validate` runs the complete gate and does not filter by changed files.
Unchanged firmware/native inputs do not require compilation; inspect every
selected check's result.
Support is derived from source-bound evidence, not README assertions. A native
build and a clean locked export are required for build-verified status; physical
support requires actual revision-specific observations.

README files are bilingual. Engineering guidance is English and describes the
current contract. Generated views are updated from their owning inputs. Source
provenance and real observations remain attributable; software that has no
current consumer, duplicate command entries and transition-only records are not
maintained architecture. See [testing](../development/testing.md),
[Skill releases](../development/skill-releases.md) and [open TODOs](../development/optimization-plan.md).

[device-documents]: ../development/device-documents.md
