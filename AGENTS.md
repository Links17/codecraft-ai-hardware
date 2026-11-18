# Repository Contract for AI Agents

This file is the mandatory entry point for using or changing this repository.
Read Part I for every task. Part II also applies when changing repository
code, documentation, metadata, skills, tests, or workflows. Building an existing
example or creating a project outside the repository does not by itself make
the task a repository contribution.

**MUST** and **MUST NOT** are requirements. An unmet requirement must be reported;
it must not be silently omitted or counted as satisfied. These rules operate
within the user's instructions and the environment's permissions. Local
`AGENTS.md` files and Skills add task-specific rules; they do not grant authority
to take actions outside the user's request.

Repository-wide scope, source, and evidence requirements apply at every layer;
local guidance MUST NOT weaken them. If instructions conflict, identify the
conflicting files and resolve the applicable rule before the dependent action.
MUST NOT silently select the easier rule. If the conflict cannot be resolved
from the user's instructions and authoritative sources, ask for the necessary
decision while continuing independent work.

## Part I: Current repository and usage rules

### Repository scope and current structure

This repository contains Seeed board support packages (BSPs), standalone demos,
verified hardware facts, development workflows and standalone Agent clients for
CodeCraft cloud APIs. Cloud clients live in their Skill packages. Server runtime,
device provisioning/pairing, account management and telemetry infrastructure
remain external and MUST NOT be introduced here.

The implementation separates device facts, software stacks, cloud Skill contracts, and Agent workflows:

| Path | Responsibility |
| --- | --- |
| `devices/<board>/` | Generated knowledge entry, metadata, source references, assets and device evidence |
| `capabilities/<capability>/` | Reusable contracts and integration resources consumed by cloud Skills |
| `platforms/esp-idf/targets/<board>/` | ESP-IDF BSP, board configuration, and standalone examples |
| `platforms/esp-idf/components/` | Components shared by ESP-IDF boards |
| `platforms/linux/targets/<board>/` | Linux device support, overlays, and demos |
| `platforms/arduino/targets/<board>/` | Arduino board profiles and sketches, rules in `platforms/arduino/AGENTS.md` |
| `skills/` | Hardware development workflows and independently installable cloud API Skills |
| `skills/_cloud/` | Cloud client maintenance source, import provenance and offline protocol tests |
| `skills/_shared/` | Shared orchestration and its core integration tests |
| `skills/codecraft-validate/tests/` | Validation entry, public CLI and gate/discovery tests |
| `docs/`, `.github/` | Reference documentation, contribution guidance, and CI |

Choose the platform by software stack, not chip name. An ESP32 using Arduino
belongs to the Arduino workflow. MUST NOT substitute another platform's build
or deployment procedure.

Device AGENTS.md files and reference/ own hardware knowledge. Target manifests own software configuration and implementation bindings. Platform adapters preserve native toolchains. Generated indexes below are checked against these sources; unknown verification remains unknown. A README listing is not proof of a passing build or working hardware.

### Task selection and required AI skills

1. Start with `git status --short --branch`; preserve existing changes.
2. Determine whether the task is inspection, project development/build/device
   use, or a repository contribution. For mixed tasks, apply contribution
   rules to the repository changes. Use `python3 codecraft.py discover` to find candidates and `python3 codecraft.py context --target <platform>/<device>` to collect their reference closure. Read-only questions do not require
   installing toolchains or running builds.
3. For development, identify the intended output location, board, software
   stack, and relevant hardware revision before relying on those choices.
   Keep user-specific application code outside the reference repository unless
   the user requests a repository example or contribution.
4. Load the matching routing-table entries and local rules before editing or
   executing a platform operation. MUST NOT load every README by default.

Before AI-assisted development, all five skills MUST be installed and available:
`codecraft-develop`, `codecraft-setup`, `codecraft-build`,
`codecraft-device-test`, and `codecraft-debug`. Maintained sources are in
`skills/`. If any is missing, choose an installation method appropriate to the
environment, install it, and verify availability without waiting for the user
to request installation. No client or installation directory is mandatory.

The discovery and validation workflows also have `codecraft-discover` and `codecraft-validate` Skills. Use only the Skills matching the task. Availability does not require loading
all five, and installation does not authorize flashing, Git writes, or
publishing. A missing toolchain must be handled through `codecraft-setup`;
a failed operation must be diagnosed through `codecraft-debug` before retrying.

### Task-specific context routing

| Task | Read before the relevant operation |
| --- | --- |
| Code change | `docs/development/ai-guide.md`, relevant headers and neighboring implementation |
| Environment bootstrap or missing toolchain | `skills/codecraft-setup/SKILL.md`, Target manifest and device knowledge entry |
| ESP-IDF board work | `devices/<board>/AGENTS.md`, `platforms/esp-idf/AGENTS.md`, `platforms/esp-idf/targets/<board>/target.json`, matching entry in `docs/vendor-sources.md` |
| Linux board work | `devices/<board>/AGENTS.md`, `platforms/linux/AGENTS.md`, `platforms/linux/targets/<board>/target.json`, matching entry in `docs/vendor-sources.md` |
| Arduino board work | `devices/<board>/AGENTS.md`, `platforms/arduino/AGENTS.md`, `platforms/arduino/targets/<board>/target.json`, matching entry in `docs/vendor-sources.md` |
| New board | Part II, `docs/development/ai-guide.md` onboarding section, platform rules, `docs/vendor-sources.md` |
| Build, tests, dependencies, partitions | `skills/codecraft-build/SKILL.md`, device knowledge entry, Target manifest and platform configuration (`sdkconfig.defaults`, `target.json`, as applicable) |
| Firmware image planning, merging or verification | `docs/development/firmware-images.md`, `skills/codecraft-build/SKILL.md`, Target firmware profile and Platform implementation |
| Flashing or on-device testing | `skills/codecraft-device-test/SKILL.md`, board deployment instructions |
| Diagnosis | `skills/codecraft-debug/SKILL.md`, failing command/output and affected board context |
| Documentation or Agent rules | Part II, `docs/README.md`, affected rules and their referenced files |
| Skills or validation changes | `skills/README.md`, `skills/validation.md`, `docs/development/testing.md`, affected Skills and validation implementation |
| CodeCraft cloud API operation | The matching `skills/codecraft-{llm,asr,tts,image-generation}/SKILL.md` and its API reference; use only existing task authorization |
| Commit or PR | `docs/development/ai-guide.md`, `.github/CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md` |
| Upload, online flashing, or sharing firmware | The CodeCraft Hub section below and the linked CLI documentation |

### Hardware facts and uncertainty

- Follow this priority: **vendor specifications and measured results → board
  pins header → BSP implementation → hardware guide → README/demo code**.
  Consult `docs/vendor-sources.md` and the underlying source; a link alone
  does not verify the claim.
- Every hardware fact introduced or changed in code MUST have a nearby source
  comment. References must identify the source file/revision or measurement
  sufficiently to check the claim. MUST NOT invent pins, addresses, polarities,
  voltage limits, memory sizes, timing requirements, or device identities.
- Do not extrapolate a fact from a similar board, chip family, or different
  hardware revision. Missing information remains `unknown`; absence of
  evidence is not proof of compatibility or incompatibility.
- If required facts are missing or sources conflict, stop the operations that
  depend on them, record the gap/conflict, and seek the missing evidence or user
  decision. Continue independent work. MUST NOT choose a convenient value to
  make a build or test pass.
- Verify the declared toolchain, dependencies, and relevant board revision
  before making a compatibility claim. A build on another version is evidence
  only for the version actually used.

### Operation boundaries

- MUST NOT overwrite, revert, clean, or include unrelated user changes. Read
  an already-modified file before editing it and preserve changes outside the
  requested scope.
- Device writes require explicit authorization for the current session and
  confirmation of the target board and port/drive. Existing authorization
  remains valid within its scope; do not ask again for the same authorized
  action. A generic serial port or removable drive is not proof of identity.
- Flash readback or backup is not a prerequisite for flashing. Flashing does
  not guarantee preservation of user data and does not authorize full-chip
  erase; erase requires an explicit user request.
- Commit, push, PR, merge, and publication actions must each stay within the
  granted scope. Authorization for one does not imply the next. A build or
  repository edit does not authorize a device write or publication.
- MUST NOT expose or commit credentials, device secrets, private keys, personal
  data, or unsanitized logs. Generated firmware and temporary build output must
  remain outside versioned source.
- Report what actually ran. Metadata checks, compilation, file transfer,
  simulation, and physical behavior are distinct results; none proves the
  next. MUST NOT present a stale binary as the output of a failed new build.

### CodeCraft Hub

[CodeCraft Hub](https://test-sensecraft.seeed.cc/wiki/en/sensecraft-cli/) is a
separate firmware-sharing platform. This repository does not implement it.

Only when the user requests upload, online flashing, or sharing, use
[`@seeed-studio/sensecraft-cli`](https://test-sensecraft.seeed.cc/wiki/en/sensecraft-cli/)
to generate and upload the required package. Follow that documentation to
install the CLI and its Agent skill. An ordinary build, local flash, or board
change is not an upload request. Hardware facts remain owned by this repository;
platform success must not change the hardware verification status.


### Generated discovery index

<!-- CODECRAFT_INDEX_START -->
<!-- source_sha256: 5df43d1a9c9c4e02a3c8d1f311adbcdcafe4205296957f45e412e758f7e0f589 -->

| Device | Target | Implementations | Build + project | Device |
| --- | --- | --- | --- | --- |
| [Grove Beginner Kit for Arduino](devices/grove-beginner-kit/AGENTS.md) | arduino/grove-beginner-kit | audio, display, environment, gpio, input, led, motion | build-verified | not_run |
| [reSpeaker Lite (XIAO ESP32-S3)](devices/respeaker-lite/AGENTS.md) | esp-idf/respeaker-lite | audio, input, led | build-verified | not_run |
| [reTerminal (CM4)](devices/reterminal/AGENTS.md) | linux/reterminal | audio, environment, gpio, input, led | build-verified | not_run |
| [reTerminal E1001](devices/reterminal-e1001/AGENTS.md) | esp-idf/reterminal-e1001 | audio, display, environment, input, led, power, rtc, storage | build-verified | not_run |
| [reTerminal E1002](devices/reterminal-e1002/AGENTS.md) | esp-idf/reterminal-e1002 | audio, display, environment, input, led, power, rtc, storage | build-verified | not_run |
| [reTerminal Sticky](devices/reterminal-sticky/AGENTS.md) | esp-idf/reterminal-sticky | display, environment, input | build-verified | not_run |
| [SenseCAP Indicator](devices/sensecap-indicator/AGENTS.md) | esp-idf/sensecap-indicator | display, gpio, input, touch | build-verified | not_run |
| [SenseCAP Watcher](devices/sensecap-watcher/AGENTS.md) | esp-idf/sensecap-watcher | audio, camera, display, gpio, input, power, storage, touch | build-verified | not_run |
| [Wio Terminal](devices/wio-terminal/AGENTS.md) | arduino/wio-terminal | audio, display, gpio, input, ir, motion, storage, wireless | build-verified | not_run |
| [XIAO ESP32-S3 1.47-inch Touch Display](devices/xiao-s3-147/AGENTS.md) | esp-idf/xiao-s3-147 | audio, display, input | build-verified | not_run |

Platforms: [arduino](platforms/arduino/AGENTS.md), [esp-idf](platforms/esp-idf/AGENTS.md), [linux](platforms/linux/AGENTS.md)

Cloud Skill Capabilities: [contracts](capabilities/AGENTS.md)
- [asr](capabilities/asr/AGENTS.md) · 2.0.0 · codecraft-asr · API execution: not_run
- [image-generation](capabilities/image-generation/AGENTS.md) · 2.0.0 · codecraft-image-generation · API execution: not_run
- [llm](capabilities/llm/AGENTS.md) · 2.0.0 · codecraft-llm · API execution: not_run
- [tts](capabilities/tts/AGENTS.md) · 2.0.0 · codecraft-tts · API execution: not_run
<!-- CODECRAFT_INDEX_END -->

## Part II: Developer contribution constraints

### Change scope and implementation ownership

Before editing, identify the affected files, boards/platforms, source of truth,
and required validation. A contribution MUST solve the requested problem at
the owning layer and preserve unrelated behavior.

- Board-specific reusable logic belongs in the board BSP. ESP-IDF components
  shared by two or more boards belong in `platforms/esp-idf/components/`. Pages, state
  machines, animations, and application tasks belong in examples/applications.
- Keep standalone examples independently buildable. Keep testable logic
  independent of platform runtimes where possible; behavior changes require
  relevant host tests when that behavior can be tested on the host.
- MUST NOT introduce cloud runtime or account/platform implementation into
  hardware support. MUST NOT force a shared code ABI across software stacks.
- For a new board or changed hardware fact, establish the vendor/source record
  first, then update the owning header/BSP/profile and its documentation.
  Record source conflicts and their resolution in devices/<device>/reference/ and reference them from the device knowledge entry.
- New devices MUST provide device.json, reference/ sources, a Target manifest and native examples. Target native interfaces MUST cite their implementation paths. Capability is a cloud Skill consumption boundary, not a peripheral taxonomy; MUST NOT register GPIO, display or audio as individual Capabilities. Run `python3 codecraft.py generate` and `python3 codecraft.py generate --check`; root/device indexes, native interface and CI matrices are generated and MUST NOT be registered manually. Add meaningful positive/negative contract tests for new schema or adapter behavior.
- Toolchain, dependency, partition, and persistent-data changes MUST state
  compatibility and recovery implications. A directory move must not silently
  change a toolchain, hardware value, or firmware behavior.

### Documentation and rule changes

- Maintained `README.md` files MUST have a Simplified Chinese
  `README.zh_CN.md` counterpart with reciprocal links and equivalent commands,
  requirements and exceptions. All other engineering documents MUST use one
  English `.md` file: AGENTS, CLAUDE, SKILL, API references, architecture,
  contribution rules, plans, TODOs and reports MUST NOT have Chinese copies.
  Imported original evidence and third-party upstream documentation retain
  their original language and attribution. Structured localized labels may
  support README views; physical facts still have one canonical typed value.
  Generated engineering views and exported application rules use English;
  generated application README files retain both languages.
- State current behavior and proposed architecture separately. An architecture
  proposal does not establish implementation. Only document a generated
  index or automatic check as implemented when its producer/check exists.
- Maintain a fact at its owning source and reference or generate other views.
  MUST NOT hand-edit files or regions explicitly marked as generated; change
  their source and rerun the generator. Existing manually maintained indexes
  remain manual until a generator replaces them.
- Every rule MUST identify its applicable task and required action. If a
  prerequisite is missing, specify the blocked step and report it; do not add
  blanket approval requests or block independent work. Examples and translated
  rules MUST NOT contradict the governing requirement.
- Rule changes MUST review affected Skills, local rules, linked guidance, and
  validation behavior for contradictions. MUST NOT remove a requirement merely
  to make a failing check appear successful. Report documentation/implementation
  gaps explicitly rather than claiming new enforcement exists.
- A structural change MUST update references, commands, tests, CI and affected
  documentation together. Remove superseded implementations and entry points;
  MUST NOT retain forwarding modules, mixed schema readers or transition-only tests.

### Enforced ownership and source closure

- Device metadata MUST hold one typed value per fact. Localized views MUST render that value; translated numeric specifications MUST NOT be stored separately. Known facts MUST match their cited source assertions. All Device records MUST use schema v3 and declare variants, using an empty object when none exist.
- Target metadata MUST declare native interfaces, common inputs, per-example inputs and dependencies. The Device-to-Target index MUST be derived from Target.device; duplicate backlinks are forbidden. All Target records MUST use schema v3 with an explicit variants object. Platform and adapter protocol versions remain independent.
- Native build/configuration logic MUST live in platforms/<stack>. Shared Skill code MUST NOT branch on stack IDs to implement native operations.
- Context, project export and evidence MUST use the same transitive dependency graph. Never filter out missing dependencies to make export pass. The graph MUST include the actual adapter and all pipeline code.
- A project lock MUST preserve initial import provenance separately from explicitly reviewed application updates. Builds MUST check the actual toolchain against the current lock.
- Evidence MUST name complete expected cases and the source digest. Changed source/adapter/contracts invalidate prior verification. Physical promotion additionally requires matching revision and named acceptance observations.
- Capability contracts are consumed by cloud Skills. Device peripherals and native interfaces MUST NOT be registered as Capabilities. This repository MUST NOT implement the consuming cloud service.
- Cloud domain code MUST NOT import or construct the hardware Catalog. Use neutral registry primitives and caller-injected Target lookup. Stable semantics belong to Capability; service policy belongs to a separately versioned Provider policy. Provider constraints MUST NOT weaken the Capability schema, and defaults require explicit Capability permission. See `docs/architecture/capability-provider-policy.md` for ownership and enforcement boundaries.
- Cloud Skill packages MUST run independently after copying one directory. Runtime imports MUST remain inside the package. A repository-skill Provider MUST pin all package files and declare the package as an export dependency. Source changes require reviewed hash updates and offline client tests; validation MUST NOT call real cloud APIs or use real credentials.
- Bundle changes MUST use the candidate/check/review/apply workflow in `docs/development/skill-releases.md`. Apply MUST name the reviewed candidate digest, rerun isolated conformance and reject source drift. Package, API, Capability and policy versions MUST remain separately reviewed; original import provenance MUST NOT be rewritten. Packaging MUST NOT imply installation or publication.
- ESP-IDF examples MUST keep native BSP composition, Target example scope and managed dependency locks aligned. Public headers stay in include/ and private implementation in src/. Validate actual build-source selection and portable exports; changing source layout MUST NOT silently change hardware configuration or dependency versions. See `docs/development/native-compositions.md`.
- Hardware variants MUST come from sourced Device facts and explicit Target/native bindings. Carry the selected variant through context, export, locks, native build cases and physical evidence. A declared build default MUST NOT imply panel detection or revision compatibility; one variant's observations MUST NOT promote another. Unknown revision mappings remain unresolved. See `docs/development/hardware-variants.md`.
- Host tests MUST live with their owning core, cloud, Capability, platform, component or Target. Use the recursive public test runner; each current test MUST be discovered once at its owning layer. Gate/entry tests remain with codecraft-validate; physical acceptance is not part of automatic host discovery. See `docs/development/testing.md`.
- Document and invoke repository tools through `python3 codecraft.py`. The public entry is the only repository/application CLI. It loads skills/_shared/cli.py; native commands remain in platform adapters. New exports MUST carry the public entry in their graph and lock.

### Required validation and delivery

During contribution work, run the smallest relevant checks first, then the
complete gate before delivery. Select the board checks by the actual platform:

| Command | What it establishes |
| --- | --- |
| `python3 codecraft.py validate --static` | Repository checks and host tests |
| `python3 codecraft.py validate --target esp-idf/<board>` | ESP-IDF example builds with an activated, board-appropriate IDF |
| `python3 codecraft.py validate --target linux/<board>` | Linux source checks; inspect whether overlay compilation ran |
| `python3 codecraft.py validate --target arduino/<board>` | Arduino sketches compiled with the declared core/libraries |
| `python3 codecraft.py validate` | Complete current gate; inspect substeps and skips before summarizing |

Documentation/rule changes additionally require checking referenced paths,
commands, README language equivalence, English-only engineering documents and applicability. Shared tools, discovery,
or CI changes require coverage of every affected platform. Pin, display, bus,
and power changes require board-revision-specific physical evidence before
being described as ready to merge, as required by `.github/CONTRIBUTING.md`.

If a required check cannot run, report its command, missing prerequisite, and
unverified scope. Do not silently weaken it or claim the complete gate passed.
An exit code of zero does not turn skipped substeps into successful checks.
Use these result meanings in reports; the CLI emits a versioned JSON envelope, typed errors and these distinct statuses:

- `passed`: the specified check actually ran and met its acceptance criteria.
- `failed`: it ran and failed.
- `skipped`: it was intentionally omitted; state why and what remains unverified.
- `not_run`: it did not run, including missing toolchain/device prerequisites.
- `not_supported`: the operation is explicitly unsupported; missing evidence or
  a missing local tool is not proof of non-support.

Final delivery MUST separately report:

1. Changes and scope, including compatibility implications where applicable.
2. Static/host check results and the complete-gate outcome.
3. Build/check results per affected board and actual toolchain. If none are
   affected, say so; do not imply firmware was built.
4. On-device verification and evidence, or an explicit statement it was not
   performed. Record board revision, tested behavior, environment, and result.
5. Failed, skipped, unsupported, and unperformed checks, and remaining limits.

Review the final diff against the starting worktree. A passing check does not
authorize a commit, publication, or a stronger hardware-support claim. When
commits/PRs are requested, follow `.github/CONTRIBUTING.md` and the PR template;
use English imperative Conventional Commit subjects and include only the
authorized changes.
