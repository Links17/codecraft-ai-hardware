# Optimization and acceptance TODOs

This ledger tracks tooling completion and remaining acceptance requiring external
facts, physical observations, service access or maintainer decisions.
Source layout, CLI commands and native contracts
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
- [ ] **OPT-10 — Validate a second real Provider.** Skill maintainers need an
  actual additional service/client contract. Bind its differing inputs, outputs,
  options and errors in its standalone Skill, then run isolated conformance against
  the required semantic contract. Do not add generic service routing until real consumers and conformance need it.
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
- [x] **OPT-20 — Export complete workflow context.** Platform rules, hardware
  workflow Skills and portable application guidance share the export graph and
  lock. Isolated checks pass for all 10 Targets / 11 Target-variant combinations,
  with native-only and explicit cloud Skill selections and all eight workflow
  contexts. No guidance is borrowed from the reference checkout. See the
  [acceptance results](cli-boundaries-review.md#verification-scope).
- [x] **OPT-21 — Consolidate CLI and Skill contract ownership.** Local hardware
  and maintenance commands remain in the repository; external platform operations
  remain in sensecraft-cli. Four standalone Skills own their contracts and direct
  clients, with separate pinned release records. CLI-01 through CLI-07 are complete,
  the reviewed candidate was applied and static/host acceptance is recorded with
  the current source in
  [command ownership and implementation acceptance](cli-boundaries-review.md).

- [ ] **OPT-22 — Publish CodeCraft Device API endpoint discovery.** The external
  sensecraft-cli and cloud service maintainers must confirm the public /deviceapi
  origin for each supported environment, then expose it through a documented
  read-only CLI query with a versioned JSON contract, environment/site identity
  and service identity. The response must contain no credentials and must not
  infer a Device API origin from the account, Data or platform /openapi endpoint.
  Once released, update all four standalone onboarding references with the actual
  command and supported CLI version. Check explicit origin precedence, environment
  mismatches, absent mappings and secret-free output with offline fixtures. Keep
  URL discovery on the workstation; devices receive the matching origin, EUI and
  DeviceKey. Existing credentials and local import must work without discovery.
  Current [onboarding](../../skills/codecraft-capabilities-llm/references/onboarding.md) describes
  the verified credential flow and explicit origin source; it does not claim
  automatic endpoint lookup. Live routing acceptance remains OPT-16.

Each item closes only with its named evidence and an owner review. Build, host,
simulator, service and physical results remain distinct. Peripheral implementations
outside the registered native interfaces are outside current support; adding one
requires sourced hardware facts, native code, tests and its own acceptance.
