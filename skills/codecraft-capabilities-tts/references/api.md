# CodeCraft Speech Synthesis API v1

## Request and result

`POST /deviceapi/ai-services/v1/audio/speech`

JSON fields: `input` and `response_format=wav`. Voice is fixed by the service; omit `voice` or send the neutral value `default`. There is no voice-selection CLI option.

The raw successful HTTP response is binary WAV, not JSON. Parse its RIFF/WAVE format and data chunks before playback; do not assume a fixed 44-byte header or a sample rate without reading the metadata.

The script reserves a new `--output` path before the billable request, writes the WAV file, and prints its path as JSON. Existing files are not overwritten.

Each call costs 1000 quota units. Input is limited to 500 Unicode characters at normal speed. WAV output only; MP3, streaming speech, and voice cloning are outside the skill's scope. Do not silently truncate, split, or regenerate. Preserve generated audio if archival fails and handle archival separately.

## Fixed capability policy

Omit `model` and all provider, routing, endpoint, and thinking-mode overrides. The service selects one fixed implementation per capability and rejects unsupported request fields. No model discovery or client selection API is exposed. Responses expose documented capability fields without implementation metadata.

## Authentication and network

For first-time setup, follow [SenseCraft CLI onboarding](onboarding.md). For firmware or native Linux applications, read [device integration](device-integration.md); the Python configuration below is for optional workstation helpers.

Obtain `CODECRAFT_API_ORIGIN` through [origin lookup](onboarding.md#obtain-the-api-origin). Use the confirmed HTTPS Device API origin for the same environment as the EUI/DeviceKey; a platform `/openapi` gateway is not sufficient evidence of the `/deviceapi` mapping. The helpers do not discover or default this value. Plain HTTP is accepted only for an explicitly configured loopback fixture. Do not include `/deviceapi`, user information, a query, a fragment or another non-root path. Configure the actual origin before any Device API request.

After creating `CODECRAFT_WORKDIR` as shown in SKILL.md, point the client to a private credential file:

```sh
export CODECRAFT_DEVICE_FILE="$CODECRAFT_WORKDIR/device.json"
```

Create that file using a local editor, or point this variable to an existing credential file instead. The following JSON is a schema example, not usable credentials. Replace both values with the user's actual credentials before saving:

```json
{"eui":"REPLACE_WITH_16_HEX_EUI","deviceKey":"REPLACE_WITH_32_HEX_DEVICE_KEY"}
```

After saving the file, restrict access and verify that the required configuration exists without printing its contents:

```sh
chmod 600 "$CODECRAFT_DEVICE_FILE"
: "${CODECRAFT_API_ORIGIN:?Set CODECRAFT_API_ORIGIN to your actual service origin}"
test -r "$CODECRAFT_DEVICE_FILE"
```

Keep the credential file out of version control. Obtain new device credentials through the onboarding workflow only when provisioning is part of the user's task. Capability calls must not automatically create identities, alter accounts, or add quota.

The request header is `Authorization: Device <Base64(EUI:DeviceKey)>`. Base64 is encoding, not encryption. The scheme is `Device`, not `Bearer`; do not pass a DeviceKey as an SDK's `api_key`. Only the public API origin and device credentials are required.

## Errors and retries

- HTTP 400/413: check input format and limits. Validation that fails before transmission does not invoke the service.
- HTTP 401: credentials may be invalid or quota may be exhausted. Do not infer the cause from an "invalid token" message alone.
- HTTP 402: device quota is unavailable. Do not create another identity or replenish quota automatically.
- HTTP 403: the device is disabled or access is forbidden. Do not switch identities to bypass restrictions.
- HTTP 404: the API or asset is unavailable. Assets belonging to other devices also return 404.
- HTTP 429: rate or quota limit reached. Respect the limit.
- HTTP 502/503: the service is temporarily unable to complete the request.
- A timeout, interrupted stream, or missing response can leave execution and charges uncertain. Report the uncertainty; do not automatically resend a billable request or switch models.

Scripts do not retry automatically, follow redirects, or print raw error bodies, request headers, or credentials. Report success only when the command exits with code 0. On failure, check stderr and retain valid existing output. A single call already authorized by the user does not require another confirmation just because this skill is used; an uncertain outcome does not authorize a repeated operation.

AI capabilities share the device's monthly free allowance. Allocation and monthly renewal are controlled by the service; this skill does not replenish quota. Quota units are not currency or an invoice amount. See [free allowance estimates](onboarding.md#free-allowance) for monthly per-device calls and monthly totals across five devices.

## Asset API

`POST /deviceapi/media-assets/v1/files` accepts multipart field `file`, up to 20 MiB. A successful response has `code=200`, `data.id` as a UUID, and `data.content_url=/deviceapi/media-assets/v1/files/{id}/content`. The script returns the asset ID and stable content link, without printing temporary signed URLs.

`GET /deviceapi/media-assets/v1/files/{id}/content` uses the same Device header and returns binary content without a redirect, with `Cache-Control: private, no-store`. Invalid credentials return 401, disabled devices return 403, and missing or other-device files return 404. Only full GET is supported; do not assume Range or HEAD support.

`--archive` explicitly makes a second request. If generation succeeds but archival fails, the command prints the local file path and exits nonzero. Never regenerate media just to obtain a link. `device_api.py archive --file` uploads an existing file; an upload timeout can also mean the asset was already created, so do not retry automatically.

`content_url` has no built-in signature expiry, but the file must still exist and the device must retain access. It contains no DeviceKey and is not anonymously accessible. Optional temporary `url` and `expires_at` response fields do not describe the stable content link's lifetime.

The client checks the declared response length, complete RIFF chunk boundaries, PCM format, byte rate, and sample alignment before saving. A truncated or corrupt WAV causes a nonzero exit and is not archived. No automatic repair or regeneration is performed.

When Content-Length is provided, the received byte count must match it. Oversized or interrupted responses fail without an automatic retry. The client removes incomplete output files it created and never overwrites an existing file.
