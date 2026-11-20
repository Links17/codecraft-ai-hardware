---
name: codecraft-development-recamera-pysdk
description: Develop, validate and package reCamera Pro (RV1126B) Python SDK apps. Use for Kit/App Center applications, ONNX-to-RKNN conversion and authorized app delivery; firmware and BSP development use the device's native workflow.
---

# reCamera Pro Python Development

Turn the requested behavior into Python source or an installable App Center
archive. This package is an independently installable SDK workflow. It does not
register a hardware Target or establish board-revision compatibility.

The authoritative SDK is
[Seeed-Studio/recamera-pro-ext-api](https://github.com/Seeed-Studio/recamera-pro-ext-api).
The package includes an offline API snapshot and a pinned official builder;
ordinary validation and packaging need no SDK checkout, repository CLI or
sibling Skill. See [provenance](references/provenance.md) for their identities.
Run the commands below from this Skill's installed directory.

## Select the outcome and required context

Read [capability-routing.md](references/capability-routing.md) first. Classify
the requested behavior as supported, supported with preconditions, or not
supported through this SDK. A documented API does not prove the device has its
extension runtime, compatible model, service or permissions. Keep those
preconditions explicit; offline application development can proceed without a
device. For unsupported behavior, explain the missing capability without
creating placeholder implementations.

| Task | Read when selected | Deliverable |
| --- | --- | --- |
| Direct SDK demo | [SDK contracts](references/sdk-contracts.md), selected [API module](references/api/index.md) | Python source and relevant offline checks |
| Managed Kit/App Center app | [Kit patterns](references/kit-app-patterns.md), [manifest contract](references/manifest-contract.md) | A real Kit entry and manifest; a verified archive when packaging is requested |
| New model or ONNX conversion | [Model conversion](references/model-conversion.md) | Conversion artifact and separate numerical/runtime results |
| Inference output/overlay | [Result overlay](references/result-overlay.md) | Matching output, coordinates and renderer declarations |
| Recording or speaker output | [Recording](references/recording.md) or [audio playback](references/audio-playback.md) | The supported SDK/firmware path and its actual acceptance status |
| Runtime failure | [Managed runtime](references/managed-runtime.md) | Diagnosis tied to the current App instance |
| Host smoke test or device delivery | [Runtime validation](references/runtime-validation.md) | Separate archive, loader, upload, installation and device observations |

Use [doc-router.md](references/doc-router.md) for deeper API/source lookup.
Load only the selected references and API modules. Keep API and builder pins
separate: `scripts/api-reference-lock.json` identifies the documentation;
`scripts/sdk-contract-lock.json` identifies the bundled builder and watched
contracts. Newer APIs require an explicit revision and contract comparison.
Do not refresh either pin during ordinary application development.

## Implement against the selected contract

Start from the closest compatible official example. Direct SDK demos may use
`recamera_ext`; App Center apps need a `kit.app.App` entry, `owns_loop = True`
and `run(self)`. A plain script is not launchable by `kit.run`. Keep application
code separate from the installed Skill and SDK.

The routed references own the detailed contracts. In particular:

- Read the Kit and manifest references before selecting NPU/resource modes,
  model artifacts, wheel dependencies or result routing. Declaring a model
  alone does not grant inference access.
- Frame/zero-copy views belong to the current iteration. Copy before retaining
  or queuing them; keep coordinate and timestamp conventions consistent with
  the selected SDK layer.
- For inference apps, follow the default browser-overlay policy in the overlay
  reference. Stream/recording OSD is a separate, explicitly selected output.
- RKIPC/AppMgr own media pipelines, installation and lifecycle. Do not open a
  competing camera pipeline, invent private RPC calls, modify shared Python,
  or change firmware/Buildroot/AppMgr to make an app work.

## Validate and package the requested deliverable

Run the non-executing source/manifest validator and fix its errors:

```text
python scripts/validate_app.py --app-dir <app> --mode demo
```

For an App Center archive, read [app-packaging.md](references/app-packaging.md)
and run the official-builder wrapper:

```text
python scripts/package_app.py --app-dir <app> --out <dist>
```

This performs package-mode validation, builds the archive and reopens the
final bytes to verify the manifest, lock, payload and hashes. It does not run
the application, install dependencies or contact a device. Supply an explicit
target-compatible wheelhouse for private dependencies; missing wheels remain
a packaging prerequisite. Do not substitute host site-packages or a handwritten
tar archive. Source-only tasks and standalone demos do not require packaging.

For a requested public release candidate, also run the documented `publish`
validation mode. Signing and channel acceptance remain AppMgr/platform policy;
structural validity alone does not establish installation acceptance.

## Test or deliver only within the requested scope

Follow [runtime-validation.md](references/runtime-validation.md) to smoke-test
the final archive with the real Kit loader and a bounded, app-specific hook.
This executes trusted application code and is separate from static inspection.
Missing compatible host dependencies leave that stage unperformed; do not
replace native target wheels with incompatible host packages.

For authorized delivery, `scripts/deploy_app.py` defaults to upload only.
Select `--action install`, `--action verify` or `--replace` only when covered by
the user's request. Reuse existing authorization and access; do not embed
credentials or device addresses in application source or this package.

Report the selected SDK/runtime assumptions, source or artifact paths and
actual results separately: offline validation/package integrity, host loader,
model numerical comparison, upload/install/lifecycle, result delivery and task
behavior. A PID, socket, successful upload or successful build does not prove
device behavior. Keep unknown hardware revision and runtime compatibility
explicit.
