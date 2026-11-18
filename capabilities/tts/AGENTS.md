# Speech synthesis

Consumed through the bundled [codecraft-tts](../../skills/codecraft-tts/SKILL.md) Skill, with its package version pinned by the Provider and API v1. Native peripheral interfaces belong to Targets.

Read [contract](capability.json), [Provider](providers/codecraft-cloud/provider.json) and [Provider policy](../../docs/architecture/capability-provider-policy.md). Capability 2.0.0 defines semantics; Provider policy 1.0.0 owns current service limits, billing and approved defaults. The Provider pins the current Skill package version and full file inventory; the API version is v1. Consume the effective schemas and configuration returned by preparation. File-content and protocol checks remain in the standalone client. The Provider pins the local Skill package and records its upstream import provenance. Selected Capability exports include the complete standalone package; native projects without a Capability selection do not import it. No sibling checkout is required.

Use `cloud-catalog`, `resolve-capability` and `prepare-capability` through the repository CLI. Preparation produces an invocation envelope only. Use `check-cloud-skills` to check the repository packages; pass `--skills-root <installed-skill-parent>` to check an installed copy. No Target is required for cloud-only work; --target adds optional hardware context, not a firmware integration claim. Checks compare the complete package inventory and verify CLI flags from a fresh copy of pinned source. Capability tests prepare the mapped invocation, run the isolated Skill against a loopback fixture, and validate its actual output schema and exit status. Actual API execution belongs to the installed Skill and requires the user’s authorized operation. Never read credentials for validation, auto-retry a charged request, or infer device verification.

- No MP3, streaming speech or voice cloning.
- After archival failure retain local media and retry only the archive workflow when authorized.
