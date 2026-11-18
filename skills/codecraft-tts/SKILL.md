---
name: codecraft-tts
description: Generate WAV speech from text with CodeCraft Gadgets Cloud and optionally archive it behind device authentication. Use for CodeCraft device announcements, voice prompts and TTS API integration; not for recording transcription or voice cloning.
metadata:
  version: "1.0.0"
  api-version: "v1"
---

# CodeCraft Speech synthesis

## Prerequisites

Requires Python 3.10+ standard library, a reachable APISIX origin and the user's existing device credentials. Installation does not grant API access. Invoke the service only within the authorized task; one request does not authorize a batch.

Set `CODECRAFT_API_ORIGIN` to the origin without `/deviceapi`, and `CODECRAFT_DEVICE_FILE` to the absolute path of a private JSON file containing `eui` and `deviceKey`. Read the [API reference](references/api.md) for the format and error semantics. Keep real credentials out of the Skill, prompts, command-line arguments and URLs. The script sends credentials only to the configured origin and refuses redirects.

Commands below are relative to the installed Skill directory. Use absolute script paths from other directories. Store inputs and outputs in the user's workspace, outside the installed package.

## Workflow

Prepare the requested UTF-8 text and check its length. Generate a WAV file and return its location. Add `--archive` when the task requires long-term storage or a device download link.

```bash
python3 scripts/speak.py --text-file /absolute/path/text.txt --output /absolute/path/speech.wav
```

Writes WAV to a new `--output` path and returns its path as JSON. Existing files are never overwritten; the output is checked and exclusively created before the charged request.

## Limits and quota

- Model: `qwen3-tts-flash`; 1000 quota per call, normal speed, at most 500 Unicode characters.
- WAV only; MP3, streaming speech and voice cloning are not implemented. Do not silently truncate, segment or regenerate. If archival fails, retain the generated audio and retry only archival when authorized.
- Never automatically retry a charged request. On timeout or interruption, explain that output may be incomplete and charge status uncertain.

## Additional usage

```bash
python3 scripts/speak.py --text-file /absolute/path/text.txt --output /absolute/path/speech.wav --archive
```

## Archival and stable links

`--archive` uploads the generated file and returns `asset_id` and a complete `content_url`. Every access requires the same device's Device Header. The link remains usable while the file exists and permission remains valid; it is not publicly accessible.

If generation succeeds but archival fails, keep the local file. Do not regenerate to obtain a link. Archive the existing file with:

```bash
python3 scripts/device_api.py archive --file /absolute/path/generated-file
```

Download an existing asset to a new file with:

```bash
python3 scripts/device_api.py download --asset-id ASSET_UUID --output /absolute/path/downloaded-file
```

A browser `<img src>` cannot add the required Authorization header itself. Do not promise direct embedding of an authenticated link. See the [API reference](references/api.md) for archival fields and behavior.
