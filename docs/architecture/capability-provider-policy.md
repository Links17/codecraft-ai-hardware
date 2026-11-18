# Capability contracts and Provider policy

Capability defines the operation consumed by a cloud Skill. Provider binds that
operation to a concrete, pinned standalone client and its service policy. Device
peripherals remain native Target interfaces. These contracts do not implement a
cloud service or certify integration with a physical device.

## Domain dependencies

The cloud catalog imports neutral loading primitives from
`skills/_shared/registry.py`, graph primitives from `skills/_shared/graph.py`,
and its own schema. It never imports or constructs the hardware Catalog.
Hardware discovery consumes the same registry primitives. The composition
entry `model.load_cloud(root, target_lookup=None)` injects a lazy hardware lookup, used only for an explicit Target. A direct
`CapabilityCatalog` consumer must inject its own lookup when supplying a Target;
an unchecked Target is rejected. No Target is needed for cloud-only work.

Cloud graphs explicitly include the registry, graph, I/O helpers and this
document. Native runtime resources also declare the registry. Context, exports
and locks therefore include the implementation that actually loads the domains.

## Ownership and versions

All four current semantic contracts and their Providers' `contract_version`
are **2.0.0**. Their metadata container remains `schema_version: 2`. Each
Provider's `policy` has its own `schema_version: 1` and `version: 1.0.0`.
Standalone Skill versions and complete file inventories are pinned in each
Provider. The current API is **v1**. These version numbers describe different boundaries.

| Owner | Fields and responsibility |
| --- | --- |
| Capability | Named operations; typed inputs, outputs and configuration; stable semantic restrictions; errors, risk and resource dimensions |
| Provider policy | Service limits, approved configuration defaults, restrictive schema fragments, declared billing units and pinned sources |
| Provider binding | API/model identity, CLI mappings, prerequisites, resource estimates, package inventory and source provenance |
| Standalone Skill | Input-file content checks, authentication, HTTP, wire format, streaming, local media and optional archival |

All Capabilities prohibit automatic retries. LLM retains text-only messages,
the permitted roles and complete-stream semantics. Image generation retains one
image per operation. ASR retains single-recording transcription without speaker
identification or silent conversion/splitting. Archival remains an explicit
caller decision; a Provider cannot introduce an archive default.

The current CodeCraft policy is derived from the pinned API reference and client
entrypoint listed in `policy.sources`. Service declarations are not observed
billing, measured resource bounds or live-service acceptance. A second real
Provider has not been validated.

## Policy contracts

`policy.billing.status` is `declared` or `unknown`. Declared amounts are
nonnegative accounting units, not currency; a null amount allows usage-dependent
billing, such as tokens. Unknown billing has null unit, basis and amount. Do not
invent prices or infer authorization from a billing declaration.

A policy-only change increments the policy version as appropriate without
changing an unchanged Capability contract. The Provider document participates
in the source graph, so the change invalidates its fingerprint and project lock.
A changed operation meaning requires a Capability version and matching Provider
contract versions. Changes to packaged bytes require a separately reviewed
Skill version/inventory update. Original import provenance remains immutable.

## Resolution, preparation and enforcement

Resolution validates optional Target context, environment prerequisites and
resource constraints. Candidates expose `contract_limits` and `provider_policy`.
An eligible candidate does not prove file validity, live availability, quota or
physical-device integration.

Selection retains the caller's raw `configuration` and returns
`effective_configuration`, formed from permitted Provider defaults followed by
caller overrides. Only configuration properties explicitly annotated
`provider_default: true` by the Capability may have Provider defaults. The current
properties are LLM `max_tokens` and TTS `voice`. Other choices, especially
`archive`, cannot be defaulted by a Provider.

Provider schema fragments can only narrow existing fields, enum values, ranges,
lengths, required fields or additional-property policy. They cannot add fields,
change types, replace an existing pattern or weaken a bound. Unknown constraint
keys, malformed defaults, missing operations and incompatible contract versions
fail validation. Provider service-limit keys cannot override Capability semantic
limit keys. Capability definitions are not mutated while applying constraints.

Preparation validates effective configuration and input schemas, returns effective
input/configuration/output schemas, and maps the effective values to an argument
array. LLM explicitly receives `--max-tokens 256` when omitted; TTS receives
`--voice Cherry`. These are the approved Provider defaults. Explicit
caller values take precedence. Execution remains `not_run`.

Preparation does not open user input files, read credentials, call an API or
perform automatic retries. File sizes, WAV encoding/duration, prompt contents,
wire completion and media signatures are checked by the selected pinned client.
`policy.limits` declares those service facts; it is not a generic file-validation
engine. Use the returned effective output schema and process exit status after
authorized client execution. Partial text or retained media on a failed request
does not turn it into success. Image dimensions describe the requested size;
offline signature checks do not verify decoded output pixel dimensions.

## Project locks and acceptance

Exports contain the selected runtime, metadata and complete pinned Skill package.
Verify the lock before building or packaging. A new source or environment requires
review and an explicit lock-project operation; a lock refresh is not a substitute
for reviewing changes. Provider and Capability versions must match.

Offline acceptance covers cloud loading with hardware imports prohibited,
explicit Target rejection, native discovery/export, unchanged semantic-contract
hashes across synthetic policy changes, restrictive schema failures, package
isolation, effective defaults, all four actual prepared clients and their service
boundaries, and lock invalidation. Loopback fixtures use synthetic credentials.
They do not establish a second real Provider, measured billing or live API success.
