# Skill ownership and maintenance

This directory owns hardware workflows, host orchestration and independently
installable cloud clients. Read the root contract before changes. Native build
commands stay in Platforms; board implementations and physical facts stay in
Devices. SenseCraft platform authentication, telemetry, Hub and upload commands
remain in the external official CLI and Skill.

Each cloud client owns contract.json, SKILL.md, API references and package-local
runtime code. Stable semantics, service policy and API versions remain distinct.
Policy constraints may only narrow the semantic schema; defaults require explicit
policy_default permission. Archival is never an implicit default. Unknown
resource bounds and missing execution prerequisites must remain explicit.

Release records in _cloud/packages/<skill-id>.json own distribution versions,
complete file hashes and original import provenance. Keep these records outside
packages to avoid self-hashing. Never refresh hashes to accept unreviewed edits.
Follow [release maintenance](../docs/development/skill-releases.md) and apply only
the reviewed candidate digest. Packaging is not installation or publication.

Runtime imports must stay inside the copied package. Shared repository contract
checks must not import the hardware Catalog or call a service. Native-only
operations must not load or export cloud records, contracts or clients. An explicit
Skill selection adds only that package and its actual verification dependencies.
See [contract ownership](../docs/architecture/skill-contracts.md).

Tests belong under tests/skills/, with client cases under their Skill IDs,
repository schema/export checks under _shared and protocol/release cases under
_cloud. Run actual isolated clients against loopback fixtures with synthetic
credentials. Preserve input/output, default, privacy/TLS, failure and no-retry
coverage; --help checks alone do not establish integration.
