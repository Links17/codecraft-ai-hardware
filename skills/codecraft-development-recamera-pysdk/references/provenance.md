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
The imported runtime scripts, reference pages and SDK locks are preserved from
the submitted package. Local integration changes the package identity and
maintenance commands, adds offline host tests under the central test owner,
and provides repository navigation and licensing. It does not change the SDK
API, builder, target runtime profile or hardware behavior.

## Licensing and limits

The Python tools, builder and documentation use the upstream
[Apache-2.0 license](../LICENSE). The original C client declarations retain the
[SDK notice and BSD-3-Clause terms](api/sdk-license.txt).

Offline checks establish source/package consistency only. No reCamera native
Target, firmware deployment, model accuracy or physical-device acceptance is
established by this import. Device access remains optional and requires the
user's task authorization.
