# Refactor validation

Historical execution report: the results and package inventories below apply to the source digests recorded here. They do not certify later changes. Current implementation and progress are in [architecture](../architecture/overview.md) and the [optimization ledger](../development/optimization-plan.md). Package 1.0.1 subsequently removed engineering-document translations without changing runtime code.

Executed 2026-11-17T15:58:03.171514+00:00. The complete local software gate **passed 127/127 checks**: 86 static/host results (67 host tests), 33 native build/source results and 8 clean external generated-project builds. The current scope is seven ESP-IDF Targets, one Linux Target and the Arduino adapter. The remote GitHub workflow was updated and parsed locally; it was not dispatched in this session.

| Target | Native checks | Clean generated project | Current v2 evidence |
| --- | --- | --- | --- |
| esp-idf/respeaker-lite | 3 passed | passed | [record](../../devices/respeaker-lite/tests/records/build-v2-b7a6907b7fb2d655.json) |
| esp-idf/reterminal-e1001 | 4 passed | passed | [record](../../devices/reterminal-e1001/tests/records/build-v2-5861aea35ae8108d.json) |
| esp-idf/reterminal-e1002 | 4 passed | passed | [record](../../devices/reterminal-e1002/tests/records/build-v2-0f5156647a3ceb80.json) |
| esp-idf/reterminal-sticky | 3 passed | passed | [record](../../devices/reterminal-sticky/tests/records/build-v2-8e1ba46d8b6378b1.json) |
| esp-idf/sensecap-indicator | 3 passed | passed | [record](../../devices/sensecap-indicator/tests/records/build-v2-447ee83216e68ac2.json) |
| esp-idf/sensecap-watcher | 8 passed | passed | [record](../../devices/sensecap-watcher/tests/records/build-v2-133b4d75eeb64843.json) |
| esp-idf/xiao-s3-147 | 3 passed | passed | [record](../../devices/xiao-s3-147/tests/records/build-v2-4bdab7501ed61e16.json) |
| linux/reterminal | 5 passed | passed | [record](../../devices/reterminal/tests/records/build-v2-d14cd9f8c4a6ad96.json) |

ESP-IDF: all 28 examples passed using the actual SDK **v6.0.2-dirty**. The pre-existing SDK modification was retained; the records contain the exact SDK commit, submodule state, change digest, compiler and Python provenance. This is evidence for that recorded environment, not an untouched SDK checkout. Linux: four Python syntax checks and one DTS compilation passed, using Python **3.14.6** and **Version: DTC 1.8.1**. No Linux demo was executed against device interfaces. Arduino: adapter contract tests passed; no hardware Target is registered and no Arduino firmware build is claimed.

Each of the 8 Targets also passed a native build from a newly generated project outside this repository, with source-lock and actual-toolchain verification. The corrected independent cloud catalog, package verification and project export pipeline are included in the tested source digest. The six resolved review findings are documented in [the architecture review](capability-review.md). Earlier evidence remains historical; only records matching the current source graph establish build-verified status. Device status remains not_run independently of build status.

## Cloud Skill contracts

The four standalone packages from codecraft-gadgets-cloud are now maintained under skills/: [LLM](../../skills/codecraft-llm/SKILL.md), [ASR](../../skills/codecraft-asr/SKILL.md), [TTS](../../skills/codecraft-tts/SKILL.md) and [image generation](../../skills/codecraft-image-generation/SKILL.md). Each includes bilingual instructions/API references, UI metadata, its entry script and an independent HTTP helper. All four passed complete-package hash and isolated offline CLI checks. Their previously validated Skill package files are unchanged in this review.

The imported suite passed **9 offline protocol tests** using isolated package installs, a loopback mock service and synthetic credentials. It is included in the static/full gate. Provider checks enforce complete local package fingerprints and declared export dependencies; regression tests exercise selected-package export, execution outside the repository and rejection of unreviewed client changes. Eight new Capability-to-client tests also execute prepared arguments through isolated clients and validate real output schemas/exit status against loopback fixtures. Six additional regressions cover cloud-only loading, malformed selections/mappings, complete installed inventories, bytecode isolation and pinned binary exports. All tests avoid real cloud API calls.

Import provenance is retained in [skills/_cloud/import.json](../../skills/_cloud/import.json). The original checkout was at bec6dd7a64adb9382df01d25212d8887368452f3 with uncommitted Skill files; their original hashes are recorded. Its contents were not edited. Entry scripts and UI metadata were copied unchanged; helper runtime logic is unchanged, with only its maintenance path comment adapted. Cloud services and device/account provisioning remain external. Current contract observations: [asr](../../capabilities/asr/tests/evidence/repository-contract-09fbaf981dc1e4bc.json), [image-generation](../../capabilities/image-generation/tests/evidence/repository-contract-0d3915cc6900f9a6.json), [llm](../../capabilities/llm/tests/evidence/repository-contract-b354b57ab1697191.json), [tts](../../capabilities/tts/tests/evidence/repository-contract-c2bce4460a2d88f2.json).

## Preservation and remaining verification

All **270 remaining native source/configuration inputs** matched the pre-refactor working-tree SHA-256 snapshot, including existing user edits; all **18 configuration symlinks** were preserved. This review additionally compared all 317 Platform files and all 28 imported cloud package files against its starting snapshot; none changed. Paths and entry commands changed as documented in [the migration map](../architecture/overview.md). No commit, push, publication or device write was performed.

Flashing, physical acceptance and live cloud API checks are **not_run**. Simulation is **not_supported** by the registered adapters because no simulator is registered. Board revisions, physical behavior, Linux OS/kernel compatibility and licensed device images remain unverified where evidence is absent. Maintenance ownership remains unassigned and maturity remains experimental, independently of successful software builds. Source packaging does not imply firmware publication or end-to-end device/cloud integration.
