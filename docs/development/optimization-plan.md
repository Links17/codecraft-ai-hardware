# Architecture, embedded implementation and layout optimization TODOs

Updated: **2026-11-18, Asia/Shanghai**. This document consolidates the findings from the Capability/cloud Skill review and the subsequent architecture, embedded and directory-layout assessments. It records **6 historical fixes and 19 optimization items: 13 completed, 6 open (0 P1, 4 P2 and 2 P3)**. The scope remains OPT-01 through OPT-19; no additional optimization items are introduced. Partial implementation is recorded without closing its parent item.

The governing baseline remains [the distilled plan](codecraft-hardware-distilled.md), with [current architecture](../architecture/overview.md), [the completed Capability review](../reviews/capability-review.md) and [retained validation evidence](../reviews/refactor-validation.md). The latest [sourced variant software slice](../reviews/optimization-hardware-variants-2026-11-18.md) passed 240 software checks and an additional DX export/direct-native check. Indicator GX/DX selection now reaches native builds, exports, locks and variant-scoped evidence. OPT-06 remains open because revision compatibility and physical observations are missing. The prior [native composition/layout slice](../reviews/optimization-native-composition-2026-11-18.md) closed OPT-05/14. These results do not establish physical recovery, resource budgets, a second real Provider or live cloud acceptance.

## Status and priority

Checked boxes identify fixes already implemented and covered by retained evidence. Unchecked boxes remain work to do. Classifications distinguish a confirmed source defect, a contract risk, a structural improvement and missing verification; a proposed improvement is not automatically a current runtime failure.

P1 addresses runtime correctness/recovery before further reuse. P2 improves maintainability, contracts or acceptance. P3 is conditional layout/governance work. Suggested owners below are roles, not assigned people or deadlines. Items waiting for hardware, authoritative facts or a real Provider contract retain that prerequisite explicitly.

Maintain this English document as the single TODO ledger, preserving the 19 IDs and their scope. Only README files have Chinese counterparts. Close an item only after its scope and acceptance criteria are met and evidence is linked. Code completion and physical verification remain separate statuses.

## Boundaries to preserve

- Keep the four owners: devices for physical facts/evidence; platforms for native stacks and Targets; capabilities for cloud Skill contracts; skills for Agent workflows, clients and shared orchestration.
- Preserve the root AGENTS repository/contributor sections. Device knowledge and native Target implementations remain separate, connected through generated navigation and references.
- GPIO, display and audio remain Device/Target interfaces. Cloud clients execute on the Agent host; they do not become MCU BSP components. Cloud servers, accounts and provisioning remain external. MakeCode Arcade/GameGo stays excluded.
- Retain native build systems, source citations, licenses, user changes and external application projects. Keep installable Skills at `skills/<name>/SKILL.md`, each independently runnable.
- Preserve one dependency graph for context/export/locks/evidence. Migrations update declarations, generators, tests, CI and navigation together; README language pairs remain aligned and other engineering documents use English only. Missing dependencies must fail.
- Unknown revisions/resources remain unknown. Physical writes and live cloud operations follow the applicable task authorization; this planning task performs neither.

## Completed TODOs

These six items are closed by the [Capability review](../reviews/capability-review.md) and its linked tests/evidence. They are not outstanding firmware fixes.

- [x] **DONE-01 — Remove the mandatory hardware Target from cloud-only discovery/resolution/preparation.** Cloud commands work without Device/Platform catalogs; explicit Target context is still checked.
- [x] **DONE-02 — Align archived TTS/image output schemas with actual clients.** Accept the authentication field; both contracts and matching Provider contract versions became 1.0.1 in that historical fix (OPT-09 later migrates them to 2.0.0). Add prepared-client output/exit conformance tests.
- [x] **DONE-03 — Check complete installed Skill inventories and isolate CLI validation.** Reject extra/missing/symlink files; run pinned source from a fresh copy rather than installed bytecode.
- [x] **DONE-04 — Reject malformed Capability selections and environment/resource constraints.** Invalid empty values and explicit JSON null selections no longer silently become an empty selection list.
- [x] **DONE-05 — Preserve pinned Skill binary assets.** Explicit graph inputs carry assets through context, export, locks and source packages; drift invalidates verification.
- [x] **DONE-06 — Reject malformed or ambiguous CLI mappings.** Fixed arguments must be valid lists; operation flags cannot collide. Regression coverage was expanded by 14 host test functions, including eight prepared-client conformance tests across the above fixes.

## Embedded TODOs

- [x] **OPT-01 · P1 — Correct BSP initialization state and failure rollback.**

  **Type/owner:** Confirmed source defect; hardware/BSP maintainer. **Prerequisites:** None for host reproduction; physical confirmation needs an identified board.

  **Evidence:** [Watcher bsp_display_init](../../platforms/esp-idf/targets/sensecap-watcher/bsp/src/bsp_display.c) stores s_panel before later reset/init/configuration calls finish. A later failure leaves the handle non-null; a subsequent call returns ESP_OK based on that handle alone. This is confirmed by control flow, not by an on-device reproduction.

  **Work:** Separate allocated resources from ready state, roll back owned resources in reverse order, and define behavior after incomplete cleanup. Audit neighboring BSP initialization paths for the same pattern without assuming every driver has the defect. Preserve shared-rail ownership.

  **Done when:** Failure injection at each acquisition/initialization stage cannot report a false ready state, leak/overwrite owned handles or double-release resources; repeated successful initialization and a supported retry after failure are tested. Affected native and external-project builds pass. Physical recovery stays unverified until observed.

  **Completed (2026-11-18):** All eight Watcher BSP units and their shared camera backend have been audited. Display/expander/touch/knob retain the earlier readiness and rollback fixes; audio now owns every interface/channel and publishes only opened, configured devices; battery releases failed ADC setup; camera checks board setup and rolls back backend initialization; storage owns its mount path and blocks reuse after uncertain SDK unmount. Complete cleanup permits tested retry, while incomplete cleanup requires reset without reusing possibly freed pointers. Shared buses and existing rails retain their documented ownership. E1001/E1002 sensor/RTC initialization remains idempotent. The [third snapshot](../reviews/optimization-lifecycle-2026-11-18.md) records stage-specific C failures, repeat/retry behavior, SDK cleanup limitations and passing native/clean-export builds. Physical recovery remains not_run; this closes the recorded software lifecycle scope, not hardware acceptance.

- [x] **OPT-02 · P1 — Specify BSP concurrency, ownership and blocking contracts.**

  **Type/owner:** Confirmed contract gap and concurrency risk; hardware/BSP maintainer. **Prerequisites:** None; coordinate lifecycle decisions with OPT-01.

  **Evidence:** [E1001 SHT4x read](../../platforms/esp-idf/targets/reterminal-e1001/bsp/src/bsp_sht4x.c) performs command → delay → receive without a device-level serialization contract in [its public header](../../platforms/esp-idf/targets/reterminal-e1001/bsp/include/bsp_sht4x.h). The [shared I2C helper](../../platforms/esp-idf/targets/reterminal-e1001/bsp/src/bsp_i2c0_internal.h) already documents serial startup and process-lifetime bus ownership; that does not define concurrent compound sensor operations.

  **Work:** Choose a single device-owning task or per-device serialization, define allowed task/ISR contexts, timeout behavior, handle/buffer ownership and lifecycle. Apply the same review criteria to display/audio/camera APIs. Preserve valid one-time initialization designs; add shutdown/resume only where required by the supported lifecycle.

  **Done when:** Public contracts state maximum blocking policy and failure states; invalid state/input and supported concurrent use have tests. A complete sensor transaction cannot interleave incorrectly, while unrelated bus devices are not unnecessarily blocked during conversion waits. Existing LVGL and callback constraints remain enforced.

  **Completed (2026-11-18):** The earlier Watcher/shared-camera, sensor/RTC and [I/O snapshot](../reviews/optimization-io-contracts-2026-11-18.md) contracts are extended to E100x battery/charger/storage/buzzer/LED, Indicator touch, reSpeaker LED and all six button BSPs. All 41 current public runtime headers now specify context, ownership, lifecycle, failure states and blocking policy, including explicit absence of a hard total deadline where native waits can be indefinite. Compound sensor/charger/expander operations use device-level locks; display/EPD/camera/audio and remaining peripherals use their documented owner/exclusion model. Buttons publish atomic samples and preserve one callback/task registration. Existing examples now queue blocking work to their owner tasks and honor failed touch reads. The [fifth snapshot](../reviews/optimization-peripheral-contracts-2026-11-18.md) retains 245 additional C cases, 24 original-source runtime failures, the complete header inventory and passing native/clean-export builds. OPT-02 is complete for this software scope; real RTOS timing, resource budgets, physical recovery and live acceptance remain unverified under the other TODOs.

- [x] **OPT-03 · P2 — Add executable native-driver failure tests.**

  **Type/owner:** Verification gap; hardware maintainers and QA/DX. **Dependencies:** Use the contracts defined in OPT-01/OPT-02; their focused regression tests are part of those fixes and need not wait for a general harness.

  **Evidence:** Current [ESP-IDF host tests](../../platforms/esp-idf/tests/test_bsp_contract.py) check registration, pin-header definitions and example/dependency bindings. These checks do not execute driver rollback, CRC/error handling or concurrent state transitions.

  **Work:** Introduce narrowly scoped native test doubles for the APIs needed by selected drivers. Test actual C logic for acquisition failures, timeouts, corrupt responses and repeat calls. Place tests with their component/Target and connect them to the common gate.

  **Done when:** Tests fail on the reproduced broken behavior and pass after fixes; cleanup/state invariants are checked without a board. Firmware builds remain distinct from these host tests and from physical verification. Do not build a speculative replacement for the full SDK.

  **Completed (2026-11-18):** [Watcher C fault scenarios](../../platforms/esp-idf/targets/sensecap-watcher/tests/) and the [SHT4x](../../platforms/esp-idf/components/codecraft_sht4x/tests/)/[RTC](../../platforms/esp-idf/components/codecraft_pcf8563/tests/) cases execute real native code with narrow doubles. Initial completion included eight host functions / 124 subprocess scenarios covering initialization/cleanup errors, allocation failures, timeouts, CRC/BCD errors, outputs, retries and deterministic concurrent reads. Selected original bugs fail before correction; corrected implementations pass. The common gate includes [Watcher](../../platforms/esp-idf/targets/sensecap-watcher/tests/test_driver_failures.py), [sensor](../../platforms/esp-idf/components/codecraft_sht4x/tests/test_sensor_drivers.py) and now [shared camera](../../platforms/esp-idf/components/sscma_client/tests/test_camera_failures.py) runners. Coverage has grown to 16 functions / 257 C scenarios in the [145-result third gate](../reviews/optimization-lifecycle-2026-11-18.md). Further driver-specific cases accompany OPT-02; the executable harness and selected-driver coverage are complete.

- [x] **OPT-04 · P2 — Extract duplicated chip protocols into reusable components.**

  **Type/owner:** Confirmed duplication; hardware/component maintainers. **Dependencies:** Define ownership/interfaces before extraction; use OPT-03 tests where applicable.

  **Evidence:** E1001/E1002 copies of bsp_sht4x.c, bsp_rtc.c and bsp_i2c0_internal.c were byte-identical during review. See the [E1001 BSP](../../platforms/esp-idf/targets/reterminal-e1001/bsp/) and [E1002 BSP](../../platforms/esp-idf/targets/reterminal-e1002/bsp/).

  **Work:** Extract reusable protocol/CRC/decoding into `platforms/esp-idf/components/<component>`. Keep pins, bus selection, electrical configuration and board power/reset sequencing in BSP. Evaluate the bus helper separately; identical code alone does not establish hardware compatibility. Retain license/provenance and public API compatibility or document a versioned migration.

  **Done when:** Each extracted protocol has one maintained implementation with component tests; both board BSPs supply explicit configuration. All affected examples and external exports build, source closure remains complete and no hardware fact changes implicitly.

  **Completed (2026-11-18):** `codecraft_sht4x` and `codecraft_pcf8563` each own one protocol implementation, preserving source/license attribution and BSP signatures. E1001/E1002 supply their existing sourced bus/address/speed; their I2C0 helpers remain board-local after ownership review. Both manifests and all eight native projects declare the components. Component and both-board binding tests pass, including preserved configuration and RTC convention, CRC/BCD failures and transaction serialization. All eight affected native examples and both clean exports pass; [records and compatibility notes](../reviews/optimization-drivers-2026-11-18.md) include stricter invalid-input handling and timing policy. No pin or bus configuration changed. The [fourth snapshot](../reviews/optimization-io-contracts-2026-11-18.md) also replaces Sticky's remaining SHT4x protocol copy with the same component, preserving its I2C1 binding. Fifteen board-binding cases and all three native projects plus the clean export pass. The nominal conversion delay now includes the component's extra scheduler tick; no bus-wide lock spans conversion.

- [x] **OPT-05 · P2 — Narrow BSP component and example dependency scopes.**

  **Type/owner:** Structural improvement; platform/BSP maintainers. **Dependencies:** Coordinate component boundaries with OPT-04; record the current dependency/build baseline first.

  **Original review evidence:** [Watcher BSP CMake](../../platforms/esp-idf/targets/sensecap-watcher/bsp/CMakeLists.txt) previously grouped display, camera, audio, storage and other implementations with their dependencies in one component. This broad build dependency is not proof that every object reaches the final firmware.

  **Work:** Separate shared board resources from optional functions where useful. Keep native configuration and make Target common/example dependencies agree with the actual CMake/component graph.

  **Done when:** Minimal examples resolve only the dependencies required by their selected BSP composition, while combined examples retain all needed inputs. Native builds and clean exports pass. Any size/time improvement claim includes measured build or linker-map comparisons.

  **Completed (2026-11-18):** All 28 ESP-IDF examples declare explicit BSP source/requirement lists, selected local components and per-example managed manifests/locks. Target common/example scopes and native-interface bindings match the compositions; runtime component manifests exclude host-only fixtures. Actual native source/requirement lists are checked after compilation. The complete 228-result gate and two additional minimal/combined Watcher exports passed. Protected configuration and retained dependency versions are unchanged. The [ninth snapshot](../reviews/optimization-native-composition-2026-11-18.md) retains before/after component graphs without asserting unmeasured size or time improvements.

- [ ] **OPT-06 · P2 — Model hardware revisions and compatible build variants.**

  **Type/owner:** Missing hardware evidence and compatibility modeling; hardware team and core maintainers. **Prerequisites:** Authoritative revision/variant documentation or attributable measurements.

  **Evidence:** Sampled [Watcher](../../devices/sensecap-watcher/device.json), [E1001](../../devices/reterminal-e1001/device.json), [E1002](../../devices/reterminal-e1002/device.json) and [XIAO](../../devices/xiao-s3-147/device.json) revisions are unknown. Do not infer compatibility from product names or similar chips.

  **Work:** Record sources first, then design explicit revision/variant selection for real differences such as panel, codec or memory population. Connect selection to Target configuration, project locks and evidence matching; avoid scattered undocumented compile-time branches.

  **Done when:** A documented supported variant selects the correct native inputs; incompatible/unknown combinations are rejected or explicitly unresolved. Physical observations identify the exact revision. Existing unknowns are not replaced with guessed defaults.

  **Software progress (2026-11-18; item remains open):** Pinned Indicator GX/DX vendor definitions now back Device variant facts and explicit Target/native profiles. Variant-bearing Device/Target records use schema v3 so older validators reject unsupported selection semantics; non-variant v2 records remain accepted. Context/new/validate selection, projected source closure, project/import locks, native CMake/compile-command verification and per-variant clean exports are implemented. Physical evidence is variant-scoped; incompatible known revisions are rejected and unknown mappings cannot promote support. The 240-result gate and additional DX public/direct-native export checks pass, preserving all 168 prior host cases and 772 C scenarios while adding 20 DX scenarios. See the [tenth snapshot](../reviews/optimization-hardware-variants-2026-11-18.md). Compatible revision lists and physical observations remain unknown/not_run, so this checkbox stays open.

- [ ] **OPT-07 · P2 — Validate combined peripherals and measure runtime resources.**

  **Type/owner:** Physical verification gap; hardware team and QA/DX. **Dependencies:** Relevant OPT-01–OPT-03 fixes and revision evidence from OPT-06; identified hardware and applicable write/test authorization.

  **Evidence:** The [Watcher acceptance checklist](../../devices/sensecap-watcher/tests/hardware-checklist.md) primarily exercises individual peripherals; [acceptance status](../../devices/sensecap-watcher/tests/acceptance.json) remains not_run. Resource bounds in Target interfaces remain unknown.

  **Work:** Start with one representative board and a documented combination of display, audio and storage/camera appropriate to its real resources. Exercise startup, sustained load and normal reset/sleep recovery where supported. Measure heap, task-stack watermarks, latency, DMA/buffer use and power with the tested configuration recorded. Add Linux OS/kernel and device-interface observations when validating the Linux Target.

  **Done when:** Retained logs identify revision, source/Target/toolchain, workload, duration, stimuli and outcomes, with explicit acceptance thresholds supported by requirements/evidence. Distinguish measured peaks from proven upper bounds. Untested boards and scenarios retain their existing status; one successful run never promotes the entire catalog.

## Architecture and Skill delivery TODOs

- [x] **OPT-08 · P2 — Make Python domain dependencies directional.**

  **Type/owner:** Structural coupling; core maintainers. **Prerequisites:** None.

  **Original review evidence:** [model.py](../../skills/_shared/model.py) loaded CapabilityCatalog, while [catalog.py](../../capabilities/catalog.py) imported domain/load_group from model and constructed a hardware Catalog for optional Target lookup. Cloud-only loading worked, but the modules still knew about each other's orchestration. The completion below records the corrected dependency direction.

  **Work:** Move neutral loading/registry primitives to a lower-level module and inject optional Target resolution from the caller. Keep domain-specific validation with its owning domain. Preserve the current public behavior.

  **Done when:** The cloud domain does not import/construct the concrete hardware Catalog; both domains consume the shared primitives. Cloud-only fixtures, explicit Target rejection, native discovery and exported projects pass. The source graph includes every new implementation module.

  **Completed (2026-11-18):** Neutral registry/loading primitives now have one owner in skills/_shared/registry.py. Hardware and cloud domains consume them; CapabilityCatalog no longer imports or constructs Catalog. Public load_cloud composition lazily injects optional Target resolution, preserving explicit Target rejection. The original implementation fails the prohibited-hardware-import experiment; the changed domain loads/discovers independently. Native/cloud/export graphs include the new module and drift invalidates locks. All eight Targets passed their native checks and clean-export builds; the [sixth snapshot](../reviews/optimization-cloud-policy-2026-11-18.md) retains the regression and evidence.

- [x] **OPT-09 · P2 — Separate stable Capability semantics from Provider-specific policy.**

  **Type/owner:** Contract design improvement; Capability/Provider maintainers. **Prerequisites:** Review actual consumers and current version compatibility.

  **Original review evidence:** The [ASR contract](../../capabilities/asr/capability.json) included quota_per_call=1000, a rule of the current service. [Its Provider](../../capabilities/asr/providers/codecraft-cloud/provider.json) already owned concrete API/model identity. The completion below records the policy migration.

  **Work:** Classify fields into stable operation semantics, genuinely shared restrictions and Provider-specific quota/format/service limits. Move only implementation-specific policy to the Provider; do not indiscriminately remove Capability constraints. Specify version compatibility and update resolution, documentation and tests together.

  **Done when:** A Provider policy change does not unnecessarily change the semantic Capability contract. Constraints still fail closed; existing consumers have a documented compatible or versioned migration, and all four prepared-client contracts pass.

  **Completed (2026-11-18):** Capability 2.0.0 preserves stable operation semantics while separately versioned Provider policy 1.0.0 owns current service limits, declared billing, approved defaults and restrictive schema fragments. All four Skill 1.0.1 packages and original provenance remain unchanged. Selection/preparation expose effective policy/configuration/schemas, reject weakened constraints and preserve explicit archival. Actual isolated-client conformance and service-boundary tests pass; synthetic policy changes preserve semantic contract hashes while invalidating Provider/project fingerprints. The [migration contract](../architecture/capability-provider-policy.md) explains old exports and separate versions; the [sixth snapshot](../reviews/optimization-cloud-policy-2026-11-18.md) records 181 passing checks. Live billing/service acceptance and a real second Provider remain unverified.

- [ ] **OPT-10 · P2 — Test interchangeability using a genuinely different Provider.**

  **Type/owner:** Unverified extensibility; Capability maintainers. **Dependencies:** OPT-09 and an actual additional Provider contract/source.

  **Evidence:** Current registrations bind the four Capabilities to CodeCraft cloud Skills. The additional-Provider regression checks registration/resolution, not a second service's distinct behavior.

  **Work:** Select a real second implementation only when its contract is available; capture differences in input handling, options, output, errors and limits. Keep all service-specific translation inside its Provider/Skill. Start with offline fixtures.

  **Done when:** Both implementations satisfy the same intended Capability semantics, with explicit selection and supported/unknown/unsupported cases, without adding Provider-ID branches to core orchestration. Live execution remains separately authorized and evidenced. Do not invent a Provider to check this box.

- [x] **OPT-11 · P2 — Make standalone Skill packaging and versioning a repeatable workflow.**

  **Type/owner:** Delivery-process improvement; Skill/Capability maintainers. **Prerequisites:** Preserve independent installation and immutable import provenance.

  **Original review evidence:** [Shared helper synchronization](../../skills/_cloud/sync_helpers.py) existed, while the [maintenance workflow](../../skills/README.md) required coordinated package copies, reviewed Provider fingerprints, documentation and version updates.

  **Work:** Produce candidate packages and manifest/hash diffs from maintained sources, run isolated install/conformance tests, review changes, then finalize package/API/contract versions and fingerprints. Distinguish documentation-only and runtime changes. Keep _cloud as the maintenance source and package-local helpers as distribution copies.

  **Done when:** Repeating the same packaging inputs produces identical package contents; unreviewed drift fails instead of being automatically accepted by a hash rewrite. One copied Skill works without sibling packages, import.json retains original provenance, and packaging never implicitly publishes or calls a real API.

  **Completed (2026-11-18):** The [release workflow](skill-releases.md) prepares all packages from maintained sources, emits complete byte/version differences and requires explicit higher package versions for changed inputs. Candidate checks run complete isolated packages and real prepared-client conformance. Apply requires the reviewed digest, rejects source/candidate drift, reruns checks and restores completed writes after failure; failed restoration retains backups. Two actual candidates are byte-identical with 17 passing check rows. Original import provenance and all current package files/versions remain unchanged; release/mutation/failure tests use temporary repositories. The [seventh snapshot](../reviews/optimization-skill-delivery-2026-11-18.md) retains the candidate receipt and complete gate. No installation or publication is implicit.

- [x] **OPT-12 · P2 — Provide a stable public repository-tool entry point.**

  **Type/owner:** Tool-interface/layout improvement; core maintainers and DX. **Dependencies:** Coordinate module boundaries with OPT-08 and export behavior with OPT-11 where relevant.

  **Original review evidence:** The original documented commands directly exposed [skills/_shared/codecraft.py](../../skills/_shared/codecraft.py), an internal implementation path.

  **Work:** Choose and document a stable invocation entry while retaining shared implementation ownership under skills/. Define compatibility for the existing command, including generated projects; avoid requiring a global installation merely to build an exported project.

  **Done when:** The public entry works in the repository and the documented external-project workflow, returns the same result/status contract, and has a tested compatibility or explicit migration path. README, Skills, CI and generated instructions agree.

  **Completed (2026-11-18):** python3 codecraft.py is the stable thin public entry; implementation stays under skills/ and native commands remain in platform adapters. New exports include the entry in their source graph and lock and support verify-project, lock-project and build-project. The internal CLI and build.py commands remain compatible, with tests for matching JSON/errors/exit codes, source drift, missing toolchains and repository-only commands. README pairs, workflow Skills, CI, Agent rules and generated project instructions agree. Existing exports retain their original files; no global installation is needed. All eight native/clean-export validations passed; see the [seventh snapshot](../reviews/optimization-skill-delivery-2026-11-18.md).

## Directory-layout TODOs

- [x] **OPT-13 · P2 — Place tests with the behavior they own.**

  **Type/owner:** Layout/ownership improvement; core, platform and QA/DX maintainers. **Prerequisites:** Capture the current discovered-test inventory; preserve all existing suites.

  **Original review evidence:** [codecraft-validate/tests](../../skills/codecraft-validate/tests/) contained architecture/export/lock and cloud-client regressions; [cloud protocol tests](../../skills/_cloud/tests/test_protocol.py) used a separate unittest entry and wrapper. Component/Target runtime runners needed their own homes.

  **Work:** Put core graph/export/lock tests in skills/_shared/tests/, cloud maintenance tests in skills/_cloud/tests/, native component/Target tests under their owners, and leave validation-entry/gate tests with codecraft-validate. Capability and physical acceptance tests retain their domain ownership. Update discovery to support real nested native test paths and existing suite styles.

  **Done when:** A before/after test-ID mapping proves no case was lost or unintentionally run twice; focused runs and the full gate execute the same preserved coverage plus new tests. Update instructions, wrappers and CI in the same migration.

  **Completed (2026-11-18):** Core, cloud-maintenance, gate/entry and native component/Target suites now live with their owners. The recursive public runner supports ordinary functions and unittest fixtures, reports collection/fixture failures and skips, and provides identical focused/full-gate discovery. An explicit mapping preserves all 133 old entries as 156 current cases, expanding the nine-method wrapper and splitting multi-board functions. All 772 C scenario arguments are unchanged; 94 other function bodies and the protocol class retain identical ASTs. Six new discovery regressions and the complete 222-result gate pass. [The eighth snapshot](../reviews/optimization-test-ownership-2026-11-18.md) retains the mapping, workload comparison, source hashes and per-Target evidence. Rules, Skills, CI and README pairs use the new paths. Physical acceptance remains separate.

- [x] **OPT-14 · P3 — Clarify BSP public headers and private implementation layout where useful.**

  **Type/owner:** Conditional layout improvement; BSP maintainers. **Dependencies:** Prefer doing this alongside actual OPT-04/OPT-05 changes.

  **Original review evidence:** At the original review, BSPs kept public headers in include/ and C/private helper files at the BSP root. This is workable for small BSPs and is not itself a runtime defect.

  **Work:** Adopt include/ for public contracts and src/ for implementation/private helpers on affected, growing BSPs. Keep CMakeLists.txt and idf_component.yml at the native component root, and keep sdkconfig.defaults and complete examples at their documented native locations.

  **Done when:** Include visibility and public APIs remain intentional; CMake, source assertions, metadata paths, generators, exports and documentation links all resolve. No empty hierarchy or duplicate driver tree is introduced solely for visual symmetry.

  **Completed (2026-11-18):** All seven ESP-IDF BSPs now keep public headers in include/ and 45 implementation/private-header files in src/, preserving their bytes and public contracts. Native registration and managed manifest remain at the component root; complete examples and SDK defaults retain their native locations. CMake, Target/source-assertion paths, host runners, export closures, generator inputs, Skills and documentation links were updated together. All 772 native scenarios, 28 example builds and eight default plus two additional clean exports pass; see the [ninth snapshot](../reviews/optimization-native-composition-2026-11-18.md). No duplicate driver tree was introduced.

- [x] **OPT-15 · P3 — Separate enduring documentation from review/execution history.**

  **Type/owner:** Navigation/layout improvement; documentation and core maintainers. **Prerequisites:** Inventory incoming links and Agent routing before moving documents.

  **Evidence:** [docs/development](../README.md) currently routes architecture, development guidance, the retained plan, review findings and execution reports together.

  **Work:** As documentation grows, organize architecture/decisions, daily development guidance and historical reviews/reports distinctly. Keep the retained planning baseline address stable or provide an explicit navigation migration. Root AGENTS retains its two required sections and task routing; generate device navigation from canonical data. Keep Skills flat and classify them through indexes.

  **Done when:** A contributor can find rules, current behavior, open TODOs and historical evidence without treating an old report as current guidance. All reciprocal README language links, English engineering routes and generated indexes pass checks; evidence references remain attributable.

  **Completed (2026-11-18):** Current architecture is in docs/architecture/overview.md; prior reviews/execution reports are in docs/reviews/ with dated snapshot notices. docs/development/ retains the stable planning baseline, development guide and sole TODO ledger. Both documentation READMEs separate these routes. Incoming links, root routing and Skill references were migrated. The user-requested language policy removes 47 non-README translations; generation/export and validation enforce English engineering documents plus paired maintained READMEs. Two missing maintained README translations were supplied; the third-party component README retains its original text. Package versions are 1.0.1 with unchanged runtime hashes and upstream provenance. Language/export regression checks and the 88-result static gate passed; see the [execution snapshot](../reviews/optimization-progress-2026-11-18.md) for subsequent complete-gate results. Reverting this slice must restore rules, generators, manifests and documents together; existing external projects keep their locked source.

## Deferred verification and governance TODOs

- [ ] **OPT-16 · P2 — Establish live cloud acceptance separately from offline conformance.**

  **Type/owner:** External verification gap; cloud service/Skill maintainers and QA. **Prerequisites:** An explicitly authorized live task, configured origin and valid private credentials; source-contract corrections from OPT-09 where applicable.

  **Evidence:** [Retained validation](../reviews/refactor-validation.md) marks live APIs not_run. Imported provenance reports a historical image-generation HTTP 502; offline passing tests do not establish whether the service now succeeds.

  **Work:** Verify the actual selected operations, output/archival behavior and available quota/billing evidence in the authorized environment. Diagnose any image-service failure using sanitized service evidence. Keep credentials and signed URLs out of repository records, and do not automatically repeat charged requests.

  **Done when:** Each tested operation has a dated, scoped live observation or an explicit unresolved failure with evidence. Untested operations remain not_run; local fixture results are not relabeled as live success.

- [x] **OPT-17 · P3 — Decide and document useful simulator coverage.**

  **Type/owner:** Open verification capability; platform maintainers and QA. **Prerequisites:** A concrete scenario and a simulator that can support it.

  **Evidence:** Registered platform manifests explicitly report simulation as not_supported. No implemented simulator is claimed.

  **Work:** Evaluate a narrow useful scenario, its fidelity and limitations before adding any simulator. Keep tests/assets with the owning Platform/Target and state what hardware behavior the simulator cannot verify.

  **Done when:** Either a sourced scope decision retains explicit non-support, or a runnable case, coverage description and gate result are registered together. Simulation never promotes physical verification.

  **Completed (2026-11-18):** The [simulation scope decision](../architecture/simulation-scope.md) evaluates the concrete E1001/E1002 sensor transaction against Espressif's v6.0.2 QEMU documentation, QEMU feature matrix and virtual-parts documentation. It retains explicit platform non-support, distinguishes deterministic host fault tests from emulation/physical evidence, and records missing board models and reopening criteria. No simulator was installed or executed; platform manifests remain consistent with this decision.

- [ ] **OPT-18 · P3 — Supply attributable, revision-matched device imagery/assets.**

  **Type/owner:** Missing evidence/assets; hardware documentation maintainers. **Prerequisites:** Suitable source material and explicit license/provenance.

  **Evidence:** Device imagery remains unverified in the [validation report](../reviews/refactor-validation.md); [asset manifests](../../devices/sensecap-watcher/assets/manifest.json) provide the owning location.

  **Work:** Acquire suitable real-device assets and record revision, origin, license, version, checksum, dimensions and transparency as applicable. Keep assets with the Device and choose large-file storage under OPT-19 when needed.

  **Done when:** Registered assets match the supported revision and pass metadata/file checks; missing rights or unknown identity remain explicit. Do not substitute fabricated hardware imagery for verified reference material.

- [ ] **OPT-19 · P3 — Assign maintenance, HIL cadence and evidence-storage policy.**

  **Type/owner:** Open governance decisions; hardware, core and QA/DX leads. **Prerequisites:** Actual team ownership and available test/storage resources.

  **Evidence:** The [retained plan](codecraft-hardware-distilled.md) leaves HIL resources/retest cadence, large-asset storage and partial-board support open. Current maintenance ownership is unassigned; successful builds do not determine maturity.

  **Work:** Assign real maintainers, define required reviews/retest triggers and partial-board support criteria, and decide durable logs/large-asset retention with hashes and resolvable indexes. Preserve earlier observations when evidence becomes stale. If independent OCR review is adopted, repair its external model configuration separately: the prior optional run failed with model_not_found/unknown provider and produced no review result.

  **Done when:** Ownership, retest/retention decisions and support rules are documented and enforceable without invented personnel or hardware capacity. Historical evidence remains accessible and its scope/status is clear. Optional tooling availability does not silently gate unrelated development.

## Inputs required for the six open items

Read-only audit on 2026-11-18: all eight Device records still have unknown
revisions, unassigned maintainers, empty asset inventories and physical
acceptance marked not_run. The local serial inventory did not identify a
project board; this does not prove that no hardware is available elsewhere.
The current process has neither CODECRAFT_API_ORIGIN nor CODECRAFT_DEVICE_FILE
configured. No credential file was read and no device or service operation
was performed during this audit.

The existing codecraft-gadgets-cloud checkout was also inspected. Its
docs/architecture.md and docs/api-conventions.md at repository HEAD
bec6dd7a64adb9382df01d25212d8887368452f3 distinguish the public Device API from
internal New API/provider adapters. Those server-side adapters are not a second
Agent-consumed Provider contract for OPT-10. Its working-copy Skills README
reports earlier LLM/ASR/TTS observations and an image-generation HTTP 502;
those historical statements do not establish current source-matched acceptance
for this repository. Do not expose internal endpoints as public contracts or
relabel those observations as a new passing run.

| Existing item | Required input | Work unlocked by that input |
| --- | --- | --- |
| OPT-06 | An identified board/assembly and attributable revision mapping, plus access for the intended observations | Match the selected native variant to the actual revision and retain physical evidence |
| OPT-07 | A representative identified board, applicable test authorization, intended combined workload and measurement requirements | Run the combined workload and record resource, timing and recovery measurements |
| OPT-10 | The intended second real Provider's public protocol or client source | Implement its Provider/Skill translation and offline interchangeability cases |
| OPT-16 | Runnable service origin, privately configured credential file and the authorized live operation scope | Execute scoped live acceptance and retain sanitized results, including unresolved failures |
| OPT-18 | Real device assets with revision identity, source and usable license | Register and validate attributable images without inventing hardware details |
| OPT-19 | Named maintainers, available HIL capacity and approved retention/storage decisions | Make ownership, retest triggers and evidence retention enforceable |

These are prerequisites for the existing acceptance criteria, not additional
optimization items. Credentials must remain in private local configuration,
not in this document or chat. The software gate remains source-matched and
passing; none of the six checkboxes is closed by this prerequisite audit.

## Proposed layout after applicable TODOs

This is a destination sketch, not the current complete tree. Add directories only with actual content; README translations and some existing native files are omitted for readability.

```text
devices/<device>/
  device.json, AGENTS.md, reference/, assets/, tests/
platforms/esp-idf/
  platform.json, adapter.py
  components/<component>/
    CMakeLists.txt, include/, src/, tests/
  targets/<device>/
    target.json, sdkconfig.defaults
    bsp/
      CMakeLists.txt, idf_component.yml, include/, src/
    examples/<example>/       # complete native projects
    tests/                   # board-specific runtime/combination tests
  tests/                     # platform adapter/contract tests
capabilities/<capability>/
  capability.json, providers/<provider>/, tests/
skills/
  _shared/                   # repository orchestration and its tests/
  _cloud/                    # client maintenance source and its tests/
  codecraft-<name>/           # independently installable Skill packages
docs/                        # current guidance, planning and scoped history
```

Device facts and stack-specific Target code stay separate. Components own reusable protocols; BSP owns board assembly. Tests follow the behavior owner. Existing evidence paths remain valid until an explicitly implemented migration preserves their references.

## Suggested execution order and closure gate

| Stage | TODO IDs | Concrete outcome |
| --- | --- | --- |
| Runtime correctness | OPT-01, OPT-02, OPT-03 | Recoverable BSP state, documented concurrency and executable failure coverage |
| Source boundaries | OPT-04, OPT-05, OPT-08, OPT-13 | Reusable protocols, scoped dependencies, directional imports and owned tests |
| Cloud contract/delivery | OPT-09, OPT-10, OPT-11, OPT-12 | Stable contracts, a real interchangeability check and repeatable package/tool entry |
| Hardware and live acceptance | OPT-06, OPT-07, OPT-16 | Revision-specific measurements and separately scoped live-service evidence |
| Conditional layout/governance | OPT-14, OPT-15, OPT-17, OPT-18, OPT-19 | Clear navigation, justified simulation/assets and sustainable maintenance |

Source gathering and owner assignment can proceed in parallel with code work. Hardware/service prerequisites are not implied by elapsed time or software test success. Do not delay the known runtime fixes for cosmetic moves.

For implementation slices, run the smallest meaningful regression first, then the applicable checks and the required complete gate:

```sh
python3 codecraft.py generate --check
python3 codecraft.py validate --static
python3 codecraft.py validate --target <platform>/<device> --projects
python3 codecraft.py validate
```

After metadata changes, run generate before generate --check. Each completed TODO records the actual change, compatibility/rollback implications, tests and evidence. Report static/host checks, per-Target native and external-project builds, simulation, physical verification and live cloud execution separately. A passing build cannot close a TODO whose acceptance requires physical observations or a real Provider contract.
