# Remaining acceptance and maintenance TODOs

This ledger tracks work requiring external facts, physical observations, service
access or maintainer decisions. Source layout, CLI commands and native contracts
are defined by the current [architecture](../architecture/overview.md). Do not
mark an acceptance item complete because its metadata or test fixture exists.

- [ ] **OPT-06 — Confirm hardware revision mappings.** Hardware maintainers must
  identify actual PCB/assembly revisions, source the Indicator GX/DX mapping and
  record observations per selected variant. Software selection, native profiles,
  exported locks and variant-scoped evidence are implemented. Close when sourced
  revision mappings and matching physical cases exist; unknown mappings must not
  promote device support.
- [ ] **OPT-07 — Measure combined peripheral workloads.** Hardware and QA must run
  a representative board workload with its actual display/audio/storage/camera
  combination, then measure memory, task stacks, latency, DMA/buffers and power.
  Record source, revision, toolchain, duration, thresholds, stimuli and recovery.
  Linux acceptance must include OS/kernel/device-interface details. Measured peaks
  do not prove upper bounds; untested scenarios remain unknown.
- [ ] **OPT-10 — Validate a second real Provider.** Capability maintainers need an
  actual additional service/client contract. Bind its differing inputs, outputs,
  options and errors in its Provider/Skill, then run isolated conformance against
  the same semantic Capability. No Provider-ID branching belongs in orchestration.
  A synthetic fixture alone does not establish interchangeability.
- [ ] **OPT-16 — Perform scoped live cloud acceptance.** Cloud maintainers and QA
  need an authorized task, configured origin and private credentials. Record
  actual operations, output/archival behavior and available quota/billing evidence.
  Retain sanitized failures and avoid automatic charged retries. Offline tests do
  not certify service availability; each untested operation stays not_run.
- [ ] **OPT-18 — Register licensed device imagery.** Hardware documentation owners
  must supply real revision-matched images with source, license, checksum,
  dimensions and transparency metadata. Validate the files against the manifest.
  Missing rights or hardware identity must remain explicit; generated imagery is
  not verified hardware evidence.
- [ ] **OPT-19 — Assign maintainers and physical retest resources.** Team leads
  must assign real owners, define partial-board support, required review/retest
  triggers, HIL cadence and durable evidence/large-asset retention. Record actual
  resources and enforceable decisions without inventing personnel or capacity.

Each item closes only with its named evidence and an owner review. Build, host,
simulator, service and physical results remain distinct. Peripheral implementations
outside the registered native interfaces are outside current support; adding one
requires sourced hardware facts, native code, tests and its own acceptance.
