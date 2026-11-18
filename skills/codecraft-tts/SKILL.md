---
name: codecraft-tts
description: Synthesize text into WAV speech with CodeCraft Gadgets Cloud and optionally archive it as a device-authenticated link. Use for CodeCraft MCU/Linux TTS integration, device announcements, and spoken prompts; not for transcription or voice cloning.
metadata:
  version: "2.0.4"
  api-version: "v1"
---

# CodeCraft Speech Synthesis

## Device integration and onboarding

Use this skill to integrate the public API into MCU firmware or Linux applications, or to run an authorized diagnostic call. The device needs its own EUI/DeviceKey, the supplied API origin, and an HTTPS client. Python, Node.js, SenseCraft CLI, and host helper dependencies are not device runtime requirements.

- Missing API origin, EUI or DeviceKey: read [device onboarding](references/onboarding.md). It explains the gateway source, current CLI discovery limits, existing-device lookup, authorized creation and private credential import. Reuse available configuration; a missing origin does not require a new identity.
- Native device development: read [MCU/Linux integration](references/device-integration.md) and the [capability API](references/api.md). Use the bundled [C header helper](assets/device_auth.h) where appropriate.
- Workstation diagnostics: use the optional scripts below. Installing a skill does not grant access. Invoke only operations included in the user's task; do not expand one call into a batch or automatically provision a device.

The service fixes the implementation for each capability. Do not send a `model`, provider, routing, or endpoint override. Do not disclose or infer underlying model names, provider identities or internal model IDs in explanations, examples, generated applications or logs. Describe the public capabilities, limits and free allowance only. Unsupported request fields are rejected.

## Free allowance

Read the [free allowance table](references/onboarding.md#free-allowance) for monthly per-device usage, monthly totals across five devices and LLM token examples. These features share one monthly device allowance; the listed counts are alternatives, not separate grants.

## Optional workstation helpers

Requires Python 3.10+; file-based calls use only the standard library. These dependencies apply to the helpers only.

Set `CODECRAFT_API_ORIGIN` to the origin without `/deviceapi`, and `CODECRAFT_DEVICE_FILE` to the absolute path of a private JSON file containing `eui` and `deviceKey`. See [authentication and network settings](references/api.md#authentication-and-network). Never place credentials in this package, prompts, command-line arguments, or URLs. Scripts send credentials only to the configured origin and reject redirects.

## Workstation command context

The examples use a POSIX shell on macOS or Linux, with Python 3.10+ available as `python3`. Run them from this installed skill's root directory (the directory containing this `SKILL.md` and `scripts/`). On Windows, use a WSL shell for these commands.

Create a separate working directory for user files:

```sh
export CODECRAFT_WORKDIR="${CODECRAFT_WORKDIR:-$HOME/codecraft-workspace}"
mkdir -p "$CODECRAFT_WORKDIR"
```

Complete [device onboarding](references/onboarding.md) or configure existing credentials using the [authentication setup](references/api.md#authentication-and-network) before making API calls. File names below are example inputs: place the user's actual files at those locations or substitute their existing paths. Output paths must not already exist. Commands do not create input recordings or supply device credentials.

## Generate speech

Prepare the requested UTF-8 text and check the input limit. Generate a WAV file and return its location. Add `--archive` only when the task requires persistent storage or a device download link.

```bash
python3 scripts/speak.py --text-file "$CODECRAFT_WORKDIR/text.txt" --output "$CODECRAFT_WORKDIR/speech.wav"
# Alternative to the command above; do not run both for the same task.
python3 scripts/speak.py --text-file "$CODECRAFT_WORKDIR/text.txt" --output "$CODECRAFT_WORKDIR/speech.wav" --archive
```

The script reserves a new output file before the billable call and prints its path as JSON. Existing files are never overwritten. Complete WAV structure and PCM sample boundaries are validated; corrupt or truncated audio is rejected before archival.

## Limits and quota

- Each call costs 1000 quota units; input is limited to 500 Unicode characters at normal speed.
- WAV output only. MP3, streaming speech, and voice cloning are outside this skill's scope. Do not silently truncate, split, or regenerate text.
- Do not automatically retry billable calls. A timeout or interruption may leave execution and charges uncertain. If archival fails, retain the generated audio and handle archival separately.

## Archive and retrieve assets

Use `--archive` only when the task requires persistent storage or a device download link. It uploads the generated file and returns `asset_id` and a complete `content_url`. Every download requires the same device's Authorization header. The link remains usable while the file exists and the device retains access; it is not a permanent public URL.

If generation succeeds but archival fails, retain the generated file and retry only the archive operation when appropriate. Use its actual path in this command:

```bash
python3 scripts/device_api.py archive --file "$CODECRAFT_WORKDIR/speech.wav"
```

Download an existing asset to a new file. Replace `ASSET_UUID` with the ID returned by a successful archive request; it is not a literal argument:

```bash
python3 scripts/device_api.py download --asset-id ASSET_UUID --output "$CODECRAFT_WORKDIR/downloaded-speech.wav"
```

Browser media elements cannot set an Authorization header directly. Do not promise anonymous access or direct embedding. See the [asset API](references/api.md#asset-api) for response fields and failure handling.
