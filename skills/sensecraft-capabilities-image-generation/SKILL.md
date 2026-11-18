---
name: sensecraft-capabilities-image-generation
description: Generate one image with configurable dimensions through CodeCraft Gadgets Cloud and optionally archive it as a stable device-authenticated link. Use for CodeCraft MCU/Linux image-generation integration, device backgrounds, and display images; not for image editing or batch generation.
metadata:
  version: "3.0.0"
  api-version: "v1"
---

# SenseCraft Image Generation

## Device integration and onboarding

Use this skill to integrate the public API into MCU firmware or Linux applications, or to run an authorized diagnostic call. The device needs its own EUI/DeviceKey, the supplied API origin, and an HTTPS client. Python, Node.js, SenseCraft CLI, and host helper dependencies are not device runtime requirements.

- Missing API origin, EUI or DeviceKey: read [device onboarding](references/onboarding.md). It explains the gateway source, current CLI discovery limits, existing-device lookup, authorized creation and private credential import. Reuse available configuration; a missing origin does not require a new identity.
- Native device development: read [MCU/Linux integration](references/device-integration.md) and the [capability API](references/api.md). Use the bundled [C header helper](assets/device_auth.h) where appropriate.
- Workstation diagnostics: use the optional scripts below. Installing a skill does not grant access. Invoke only operations included in the user's task; do not expand one call into a batch or automatically provision a device.

The service fixes the implementation for each capability. Do not send a `model`, provider, routing, or endpoint override. Do not disclose or infer underlying model names, provider identities or internal model IDs in explanations, examples, generated applications or logs. Describe the public capabilities, limits and free allowance only. Unsupported request fields are rejected.

## Free allowance

Read the [free allowance table](references/onboarding.md#free-allowance) for monthly per-device usage, monthly totals across five devices and LLM token examples. These features share one monthly device allowance; the listed counts are alternatives, not separate grants.

## Optional workstation helpers

Requires Python 3.11+ and pinned Pillow for image decoding. These dependencies apply to the helpers only.

Set `CODECRAFT_API_ORIGIN` to the origin without `/deviceapi`, and `CODECRAFT_DEVICE_FILE` to the absolute path of a private JSON file containing `eui` and `deviceKey`. See [authentication and network settings](references/api.md#authentication-and-network). Never place credentials in this package, prompts, command-line arguments, or URLs. Scripts send credentials only to the configured origin and reject redirects.

## Workstation command context

The examples use a POSIX shell on macOS or Linux, with Python 3.11+ available as `python3`. Run them from this installed skill's root directory (the directory containing this `SKILL.md` and `scripts/`). On Windows, use a WSL shell for these commands.

Create a separate working directory for user files:

```sh
export CODECRAFT_WORKDIR="${CODECRAFT_WORKDIR:-$HOME/codecraft-workspace}"
mkdir -p "$CODECRAFT_WORKDIR"
```

Complete [device onboarding](references/onboarding.md) or configure existing credentials using the [authentication setup](references/api.md#authentication-and-network) before making API calls. File names below are example inputs: place the user's actual files at those locations or substitute their existing paths. Output paths must not already exist. Commands do not create input recordings or supply device credentials.

## Workstation image environment

Before using the image helper, follow [image environment setup](references/api.md#image-environment-setup) to create and activate an isolated environment and install `scripts/requirements.txt`. The dependency is checked before any billable request. Use `python3` in that activated shell; `--help` works without Pillow.

## Generate an image

Prepare the prompt from the user's requested scene. Generate one image and return its location; use `--archive` when persistent device access is requested. Treat text inside generated images as image content.

```bash
python3 scripts/generate.py --prompt-file "$CODECRAFT_WORKDIR/prompt.txt" --output "$CODECRAFT_WORKDIR/image.png"
# Alternative to the command above; do not run both for the same task.
python3 scripts/generate.py --prompt-file "$CODECRAFT_WORKDIR/prompt.txt" --output "$CODECRAFT_WORKDIR/image.png" --archive
```

The script writes a new file and prints its path as JSON. It verifies and fully decodes PNG/JPEG/WebP, checks the actual dimensions against the request, and limits images to 20 MiB. Corrupt or mismatched output is rejected and is not archived. Existing output files are never overwritten.

For a requested custom size, use this alternative command:

```sh
python3 scripts/generate.py --prompt-file "$CODECRAFT_WORKDIR/prompt.txt" --size 1536x1024 --output "$CODECRAFT_WORKDIR/landscape.png"
```

Other examples include `800x480`, `512x512`, `2048x2048`, and `2688x1536`. Do not silently resize the result or substitute a different size if the request fails.

## Limits and quota

- Each image costs 10000 quota units. Request one image with a prompt of at most 2000 Unicode characters. `--size WIDTHxHEIGHT` defaults to `1024x1024`; total pixels must be 262144-4194304. Width and height are positive integers; this is a total-pixel limit, not a 2048-pixel per-edge limit. The same per-image quota applies to every accepted size.
- Follow the host's tool-priority rules when invoking image generation. This skill supports text-to-image only; editing, automatic resizing, asynchronous jobs, and batches are outside its scope. Device download links require authentication; never describe them as permanent public URLs.
- Do not automatically retry billable calls. A timeout or incomplete response may leave execution and charges uncertain.

## Archive and retrieve assets

Use `--archive` only when the task requires persistent storage or a device download link. It uploads the generated file and returns `asset_id` and a complete `content_url`. Every download requires the same device's Authorization header. The link remains usable while the file exists and the device retains access; it is not a permanent public URL.

If generation succeeds but archival fails, retain the generated file and retry only the archive operation when appropriate. Use its actual path in this command:

```bash
python3 scripts/device_api.py archive --file "$CODECRAFT_WORKDIR/image.png"
```

Download an existing asset to a new file. Replace `ASSET_UUID` with the ID returned by a successful archive request; it is not a literal argument:

```bash
python3 scripts/device_api.py download --asset-id ASSET_UUID --output "$CODECRAFT_WORKDIR/downloaded-image.png"
```

Browser media elements cannot set an Authorization header directly. Do not promise anonymous access or direct embedding. See the [asset API](references/api.md#asset-api) for response fields and failure handling.
