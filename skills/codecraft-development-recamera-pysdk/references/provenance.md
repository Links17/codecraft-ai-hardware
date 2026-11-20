# reCamera SDK Skill provenance

This package imports the standalone reCamera Python SDK Skill submitted in
[upstream PR #9](https://github.com/Seeed-Solution/codecraft-ai-hardware/pull/9),
from [the original package snapshot](https://github.com/zhousizhao/codecraft-ai-hardware/tree/cc188ba3d1d5f0a6b112f7d93f9ab766eae14306/linux/recamera/recamera-pro-skills).
The repository records the original file hashes in `docs/recamera-skill-import.json`;
that maintenance record is not a runtime dependency of an installed Skill.

## SDK and documentation identity

The official source is [Seeed-Studio/recamera-pro-ext-api at 635ffc3c](https://github.com/Seeed-Studio/recamera-pro-ext-api/tree/635ffc3c51d596dd2e8139f297798162e6be62b9).
The three bundled builder files and watched SDK contracts are pinned by
`scripts/sdk-contract-lock.json`. The separate API snapshot records its source
files, signatures, routes and generated-page hashes in
`scripts/api-reference-lock.json`. The imported Skill includes reviewed updates
to the SDK repository's earlier Skill snapshot; these locks identify the actual
SDK revision consumed. They must not be refreshed merely to accept drift.

Original third-party API reference text and SDK docstrings retain their source
language and attribution, including Chinese text. These are imported reference
snapshots, not translated copies of this repository's engineering rules.
The initial integration preserved the submitted runtime and reference snapshots
and adapted package identity, maintenance guidance, host tests and licensing.
Subsequent optimization keeps the application execution helpers, SDK API,
builder and target runtime profile unchanged while shortening the Agent entry
and moving the API-reference producer/editorial notes to the repository's
`tools/skill_packages/recamera/`. The generated API index documents the public
maintenance command; upstream descriptions retain their original attribution.

The current package inventory/version is reviewed separately in
`tools/skill_packages/recamera/release.json`. Original import hashes remain in
`docs/recamera-skill-import.json`; these repository records are not runtime
dependencies. Candidate/check/review/apply uses the repository public CLI with
explicit `--skill codecraft-development-recamera-pysdk` selection. An installed
copy needs neither the generator nor the repository's maintenance sources.

## Licensing and limits

The Python tools, builder and documentation use the upstream
[Apache-2.0 license](../LICENSE). The original C client declarations retain the
[SDK notice and BSD-3-Clause terms](api/sdk-license.txt).

Offline checks establish source/package consistency only. No reCamera native
Target, firmware deployment, model accuracy or physical-device acceptance is
established by this import. Device access remains optional and requires the
user's task authorization.
