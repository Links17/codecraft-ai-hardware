# Standalone Skill release workflow

Use this workflow for changes to the bundled cloud Skill packages. It prepares
reviewable local candidates, checks isolated clients and updates reviewed package
fingerprints. It does not install Skills globally, publish artifacts or call a
real cloud service. Original import provenance in skills/_cloud/import.json and
Provider source fields is preserved.

## Maintained inputs and versions

Edit common client behavior in skills/_cloud/device_api.py. Other package files
remain maintained under their own skills/codecraft-* directories. The candidate
builder copies the common helper into every distribution; it does not rewrite
working package copies or their Provider manifests while preparing a candidate.
The old sync_helpers.py only copies helpers and cannot approve their hashes.

If a distribution helper differs from both its previously pinned bytes and the
maintained helper, preparation fails and preserves the local edit. Reconcile
those sources explicitly before preparing a candidate; packaging must not silently
discard a conflicting edit to a distribution copy.

A candidate covers all registered repository-skill packages together. Its
manifest records the exact maintained source graph, current package inventories,
previous/proposed Providers, file additions/removals/changes and independent
versions. Package changes containing only Markdown files are classified as
documentation; code, assets, Agent configuration or other changes are runtime
changes. This classification does not infer API compatibility.

Any package-byte or API-version change requires an explicit higher numeric
major.minor.patch Skill version. Policy versions cannot decrease. Contract
versions must match the reviewed Capability. A changed semantic contract or
binding must be implemented and reviewed at its owning source; the packager
does not invent operation translations or update the Capability itself.

Version overrides are a JSON object keyed by Provider ID. For example, after a
documentation-only ASR edit from package 1.0.1:

```json
{
  "asr/codecraft-cloud": {
    "skill_version": "1.0.2"
  }
}
```

Optional fields are api_version, contract_version and policy_version. Omitted
versions remain unchanged. A shared-helper edit needs a reviewed version change
for every affected package. Do not change versions or hashes merely to suppress
a failing contract test.

## Prepare and inspect

Save version overrides outside the repository and choose a new output directory:

```sh
python3 codecraft.py skill-release prepare --versions /work/release-versions.json --output /work/skill-candidate
```

For a reproducibility check with unchanged package inputs, omit --versions.
Outputs contain complete skills/<name> packages, proposed Provider JSON files
and manifest.json. Identical source bytes and version overrides produce identical
candidate file bytes and review_sha256 values; no timestamp or absolute source
path participates in the candidate identity. Normal Python caches and .DS_Store
are excluded; package symlinks and private environment files are rejected.
Validation and application copy only the pinned files and verify their copied
bytes against the reviewed hashes. Ignored caches never enter the staged or
applied package, and a file changing during copying causes failure.

Review the actual candidate files, each before/after fingerprint, the proposed
versions, policy and CLI/API behavior. The manifest reports changes relative to
the previously pinned package, including local edits not yet accepted by the
normal repository gate. A clean candidate does not by itself approve a release.

## Validate and apply

```sh
python3 codecraft.py skill-release check --candidate /work/skill-candidate
python3 codecraft.py skill-release apply --candidate /work/skill-candidate --review-sha256 <reviewed-64-character-digest>
```

check stages the candidate in a temporary repository with the exact declared
validation inputs. It checks complete pinned package inventories and CLI flags,
shared-helper equality, the nine offline protocol cases and the twelve current
prepared-client conformance functions. Each client runs alone against a loopback
fixture with synthetic credentials. The explicit release-checks.json registry
must cover registered Providers and their operations. Added Providers require
their own concrete tests; the workflow does not fabricate a substitute service.

apply requires the exact reviewed digest and reruns those checks. A modified
candidate, missing/extra files, changed maintained sources or outdated Provider
inventory fails before application. Validation receipts are not trusted as a
substitute for this rerun. A release lock prevents simultaneous apply operations.

Only changed distribution directories and Provider manifests are replaced.
Unrelated repository files and original provenance are preserved. On a write
failure, completed replacements are restored. If restoring a backup itself
fails, recovery files remain under the reported skills/.release-* directory;
inspect and recover them before retrying. Do not remove a live release lock or
discard retained originals merely to clear an error.

After applying, review the resulting diff and run:

```sh
python3 codecraft.py generate
python3 codecraft.py validate --static
python3 codecraft.py validate
```

The complete gate retains native/export checks separately from cloud client
tests. No command here flashes, publishes or establishes live service acceptance.
Copy an approved complete Skill directory for independent installation; runtime
imports remain inside it. An installed Skill does not require the repository CLI
or a sibling Skill. Existing exported applications keep their locked versions
until an explicitly reviewed application migration or a new export.

The full workflow is repository maintenance. Plain exported applications carry
the public codecraft.py entry and native build support, but do not carry the
release maintainer or its test suite; skill-release reports not_supported there.
