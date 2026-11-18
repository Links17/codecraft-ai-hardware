# Hardware architecture and migration

The source plan is [codecraft-hardware-distilled.md](../development/codecraft-hardware-distilled.md), including the user clarification that Capability serves cloud Skills. Root AGENTS retains two mandatory parts: repository usage and contributor constraints.

## Owners

| Domain | Owns | Must not own |
| --- | --- | --- |
| Device | Physical identity/revision, canonical typed facts, references, assets, physical evidence | Native toolchain or translated duplicate numeric facts |
| Platform / Target | Native adapter, BSP, configuration, examples, peripheral interfaces, native tests and simulation | Shared cloud Skill Capability taxonomy |
| Capability | Contracts and integration resources consumed by cloud Skills | A separate Capability for each GPIO/display/audio peripheral or a cloud runtime |
| Skill | Agent development and cloud API workflows, graph/export/lock/evidence orchestration | Native implementations selected by stack-specific shared-code branches |

The registered Capabilities are llm, asr, tts and image-generation. Their repository-skill Providers bind to complete standalone packages under skills/, imported from codecraft-gadgets-cloud at the user’s request. Each Provider pins the local package files and records its upstream provenance. HTTP/authentication client code belongs to these Skills; the cloud server remains external. Runtime execution requires neither the original cloud checkout nor another installed Skill.

The cloud domain uses neutral registry/graph primitives and accepts caller-injected Target lookup; it does not import the hardware Catalog. Capability 2.0.0 separates stable semantics from Provider policy 1.0.0 while preserving the standalone Skill 1.0.1 packages. See [Provider policy and migration](capability-provider-policy.md) for ownership, restrictive schemas, effective defaults and existing-project compatibility.

## Contracts and source graph

Platform metadata and Device/Target records without variants use schema_version 2. Device/Target records declaring variants require schema_version 3, which older consumers reject before silently omitting selection inputs. Device facts have a type, one value, status, localized labels and a source assertion containing {value}. Known values must appear in the cited source assertion; unknown values are null with an explanation. The renderer uses the same value in both languages. Native headers/DTS and original reference evidence retain their original content and attribution. Target.device is the only Device-to-Target registration; reverse indexes are derived. See [variant selection and compatibility](../development/hardware-variants.md).

Targets declare inputs, dependencies, example_inputs and example_dependencies. Native interface metadata references headers or explicitly scoped example sources. Typed native configuration values must cite their source; unmeasured resource bounds remain unknown. Native interface selection is separate from cloud Skill Capability discovery. `cloud-catalog` lists Capabilities/Providers; `resolve-capability` reports eligible/unknown/unsupported prerequisites and resource constraints. `prepare-capability` validates inputs and produces an argument envelope for the installed Skill without invoking it. `context --provider <id>` adds only selected contract dependencies. `check-cloud-skills` verifies bundled packages and runs only --help; optional --skills-root checks separately installed copies. Cloud catalog, resolution and preparation do not require a hardware Target or hardware catalog. An explicit --target is validated as optional context; it does not certify firmware integration. Package checks compare the complete pinned inventory, reject missing/extra/symlink files, and run --help from a fresh copy of verified source without installed bytecode or PYTHONPATH. Source changes require a reviewed contract update, not automatic acceptance.

skills/_shared/graph.py resolves the transitive closure used by context, project export and evidence fingerprints. A resource.json contains schema_version 1, kind=resource, repository-relative inputs and dependencies. Missing references, escapes, broken links and dependency cycles are rejected. Explicit files may be binary resources; build/cache directories are excluded. Export never silently drops dependencies. The graph includes the actual platform adapter, runtime helpers, metadata, declared native inputs, source references, native locks and license notices. Generated views and new observation logs do not invalidate themselves.

## Native operations and results

Each platforms/<stack>/adapter.py owns build, cases, probe and validate_target. Shared runtime.py loads the declared adapter, executes commands and verifies schema_version 2 envelopes. The result must match the requested Target, operation, source fingerprint and complete expected case set; duplicate/omitted cases and exit/status contradictions fail.

All ten operations are declared. Inspection, project generation, builds, host checks and source packaging have implementations. Configuration remains native. Simulation has no registered implementation; flashing, device observations and monitoring use authorized native/manual workflows. Unsupported operations return not_supported with a reason and exit 2; unavailable tools return not_run. No device write is part of the software gate.

ESP-IDF BSPs separate public include/ contracts from src/ implementation. Each example owns an explicit native composition and selected managed dependencies; Target example scopes and runtime resource closures match that composition. The adapter verifies actual compiled BSP sources and requirements after the compiler succeeds. See [native composition and migration](../development/native-compositions.md). This selection does not introduce peripheral cloud Capabilities.

## Host verification ownership

The common test runner in skills/_shared/testing.py discovers nested owner-local modules and runs plain functions and unittest cases. Core integration tests live under skills/_shared/tests, client maintenance under skills/_cloud/tests, gate/entry tests with codecraft-validate, and native tests with their component or Target. Capability conformance and Device acceptance retain separate ownership. Use `python3 codecraft.py test --list` and `test --path <owner>` for inventory/focused runs; the full gate uses the same runner. [The testing guide](../development/testing.md) defines discovery, fixture/status behavior and the retained OPT-13 migration mapping.

## Portable application projects

The stable public entry is `python3 codecraft.py` from the repository or a new
exported application. The root script only loads the shared CLI; native commands
remain owned by platform adapters. The former `python3 skills/_shared/codecraft.py`
entry continues to accept the same commands, JSON results and exit statuses.
Absolute invocation from another working directory resolves the owning repository
from the script, while explicit project paths remain caller-selected.

In an exported application, use `python3 codecraft.py verify-project .`,
`python3 codecraft.py lock-project .` after reviewing changes, and
`python3 codecraft.py build-project .`. Builds use the existing source/toolchain
lock checks. `python3 build.py [--lock]` remains compatible. No global install is
required. Old exports keep their original files and continue using their bundled
build.py; adopting the public entry requires a new export or reviewed migration.
Repository-only Skill release maintenance is documented in
[the release workflow](../development/skill-releases.md).

`new --target <id> --example <name> --output <new-directory>` exports exactly the declared example projection and dependency closure. User projects live outside the repository. project.yaml is JSON-compatible YAML 1.2. The project carries the actual adapter, generic runtime, native files, source references, licenses, paired README instructions and English-only engineering documents. Optional `--capabilities <selection.json>` imports selected contracts and their complete standalone Skill packages into the exported source graph and codecraft.lock. Only selected packages are included. Credentials and sibling repository paths are excluded. A host Skill package does not establish firmware integration; plain native build validation remains independent of cloud clients.

codecraft.lock separately retains the initial import graph/repository revision and the current application inventory. `python3 build.py --lock` explicitly accepts reviewed application changes and records the actual toolchain. `python3 build.py` refuses drift or an environment differing from the lock. `verify-project` checks integrity; `package` exports locked source and explicit binary dependencies, never uploads and never silently includes build output.

ESP-IDF locks include actual version, SDK commit/submodules/change fingerprint, compiler and Python version. Linux checks host Python syntax and compiles DTS; physical OS/kernel compatibility remains unknown. Arduino requires exact CLI/core/library versions but has no registered board Target.

## Evidence and generated views

Schema v2 evidence records source/Target/revision/toolchain, commands, environment, timestamp, operator, limitations, named results and retained sanitized log hashes. Build verification requires all native cases (including Linux overlays) plus a clean external project build from the same source fingerprint. Version 1 records remain historical and cannot certify v2. Changed adapters, metadata, native sources, contracts or dependencies make earlier evidence stale.

Device verification additionally requires a known matching physical revision, actual observations and every required acceptance case. Interface-specific verification remains scoped to its cases; one passing button test cannot verify the whole device. Maintenance and maturity remain independent.

`generate` derives Device AGENTS, root indexes, vendor references, the native interface matrix and CI Target matrix. `generate --check` detects drift. CI reads the generated Target matrix and calls the same validation entry; it does not maintain board lists separately.

## Migration and acceptance

| Retired path | Owner / entry |
| --- | --- |
| esp32/boards, esp32/components | platforms/esp-idf/targets, platforms/esp-idf/components |
| linux/boards | platforms/linux/targets |
| arduino/boards | platforms/arduino/targets |
| tools/validate.sh | python3 codecraft.py validate |
| Shared native build switch | platforms/<stack>/adapter.py |
| Peripheral Capability directories | Target.interfaces and native BSP headers |

Run static/host checks, affected native builds and generated project checks, then the complete software gate. See [validation evidence](../reviews/refactor-validation.md). Physical revisions, on-device observations, licensed images and simulator coverage stay explicitly unverified where no evidence is available. Cloud API calls are not made by validation. The source Skill README reports a prior image-generation HTTP 502; local contract/mock tests must not be described as a live service pass. Roll back a committed migration using its repository revision while preserving outstanding user changes; do not maintain duplicate driver trees.
