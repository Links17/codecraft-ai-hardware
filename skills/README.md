<p align="right"><strong>English</strong> · <a href="README.zh_CN.md">简体中文</a></p>

# Agent Skills

This directory contains hardware development workflows and standalone clients that consume CodeCraft cloud Capability contracts. Device facts live in devices/, native implementations in platforms/, and cloud contracts in capabilities/.

## Hardware development

The five required workflows are codecraft-develop, codecraft-setup, codecraft-build, codecraft-device-test and codecraft-debug. Use codecraft-discover and codecraft-validate when needed. Generic orchestration lives in _shared/; each platform owns its native commands and toolchain probe.

## Cloud API clients

| Skill | Operation | Default model | Platform quota |
| --- | --- | --- | --- |
| [codecraft-llm](codecraft-llm/SKILL.md) | Text generation and SSE | qwen-plus | By token |
| [codecraft-asr](codecraft-asr/SKILL.md) | WAV transcription; ASR/STT | qwen-audio-3.0-asr-flash | 1000 per call |
| [codecraft-tts](codecraft-tts/SKILL.md) | WAV synthesis and optional archival | qwen3-tts-flash | 1000 per call |
| [codecraft-image-generation](codecraft-image-generation/SKILL.md) | One 1024×1024 image and optional archival | qwen-image-2.0 | 10000 per image |

Each directory contains English-only SKILL.md and references/api.md documents, agents/openai.yaml, an entry script and its own scripts/device_api.py. Copy the entire desired directory into an Agent Skills discovery directory. The package runs independently with Python 3.10+ standard library; no sibling Skill or cloud repository checkout is needed. Automatic discovery remains enabled. Installation alone grants no API permission.

Set CODECRAFT_API_ORIGIN and CODECRAFT_DEVICE_FILE only when performing an authorized API task; credential format and limits are in each API reference. Inputs, generated files and credentials belong outside the installed Skill. TTS and image generation save local files by default. Use --archive only when the task requires a stable device-authenticated asset link; it is not a public URL. A failed archive does not require another generation request.

repository-skill Providers pin these local package files and declare them as dependencies. `new --capabilities <selection.json>` exports the selected package into the external project and includes it in codecraft.lock. Plain native projects do not include cloud clients. `prepare-capability` returns a handoff envelope and never invokes an API. Cloud discovery, resolution and preparation work without a hardware Target; --target adds optional validated context. Device integration remains unknown.

Capability contracts are version 2.0.0; each current Provider has policy 1.0.0. Stable semantics remain in Capability. Service bounds, billing and approved defaults belong to the selected Provider. Preparation returns both raw and effective configuration and effective input/output schemas; defaults reach the unchanged client as explicit arguments. The table above describes the current CodeCraft Provider, not universal Capability restrictions or measured billing. See [policy ownership and migration](../docs/architecture/capability-provider-policy.md). Existing locked exports retain their original metadata/runtime; create a new export to adopt this migration.

## Repository call chain

For an authorized cloud task, read the selected Skill and API reference, resolve its Capability prerequisites, then prepare the handoff. For example, an ASR selection file contains:

```json
{
  "capability": "asr",
  "provider": "asr/codecraft-cloud",
  "configuration": {},
  "environment": {
    "network": true,
    "tls": true,
    "privacy_approved": true,
    "environment_refs": ["CODECRAFT_API_ORIGIN"],
    "secret_refs": ["CODECRAFT_DEVICE_FILE"]
  },
  "limits": {}
}
```

The environment describes confirmed conditions and reference names, never credential values; unknown conditions must remain unknown. An input file contains `{"file":"/work/recording.wav"}`. Run:

```sh
python3 codecraft.py prepare-capability --selection /work/selection.json --operation transcribe --input /work/input.json
```

Use the successful envelope's entrypoint and arguments array to run the selected, checked Skill with the authorized environment. Pass arguments as separate process arguments, without shell evaluation. The Skill owns file validation, authentication, HTTP, streaming and optional archival. Treat a nonzero exit as failure even if partial text or a retained local file exists; on success consume the declared output schema. Preparation itself reads no credentials and makes no request. Standalone Skill installation remains independent of this repository CLI.

## Maintenance and validation

Imported source provenance and checksums are in [_cloud/import.json](_cloud/import.json). The original cloud repository remains unchanged. Runtime logic was retained. Only README documents have English and Simplified Chinese versions; all other engineering documents use English. The shared client maintenance source is _cloud/device_api.py. Use the [candidate release workflow](../docs/development/skill-releases.md): `python3 codecraft.py skill-release prepare`, then check the candidate, review its file/version differences and apply the exact reviewed digest. Apply reruns isolated client conformance and rejects source drift. The legacy sync_helpers.py only copies helpers and does not approve new fingerprints. Runtime imports always use the package copy; packaging never installs or publishes automatically.

Package version 1.0.1 removes translated Skill/API documents; its five pinned files preserve the runtime and API contract. Replace an installed package directory as a whole: overlay copying leaves obsolete translations and intentionally fails the exact-inventory check. Existing exported projects retain their locked imported package; create a new export to adopt this documentation migration.

Repository tooling uses the public `python3 codecraft.py` entry. The old internal command and exported build.py remain compatible. The gate also tests deterministic release candidates, explicit version changes, tamper rejection, rollback/recovery and public-entry/lock compatibility. These maintenance tests do not change the current Skill package versions or establish live API acceptance.

From the repository root:

```sh
python3 codecraft.py check-cloud-skills
python3 codecraft.py test --path skills/_cloud/tests/test_protocol.py
python3 codecraft.py validate --static
```

check-cloud-skills verifies the complete repository package inventory by default; --skills-root can check separately installed copies. Missing, extra or symlink files fail. Python caches and .DS_Store are excluded from the inventory, and --help runs from a fresh copy of pinned files without installed bytecode or PYTHONPATH. Binary assets explicitly pinned in skill.files remain in context, exports and locks. The static gate includes all four package/CLI checks, the nine offline protocol tests and twelve Capability-to-client conformance tests plus seven common Provider-policy tests. Each offline test installs an individual package into a temporary directory and uses a loopback mock service with synthetic credentials. Tests cover JSON/SSE, incomplete streams, audio limits, image decoding, archival/download, output preservation, redirect rejection, redacted errors and no automatic retries. No real cloud API is called.

The upstream source reported prior live LLM/ASR/TTS success and an unresolved image-generation HTTP 502. These are historical upstream observations, not a current live-service acceptance claim. See the [retained validation report](../docs/reviews/refactor-validation.md) and [current optimization ledger](../docs/development/optimization-plan.md). This repository does not host the cloud service or publish the Skills automatically.
