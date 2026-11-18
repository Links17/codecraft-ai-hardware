# CodeCraft Speech recognition API v1

## Request and result

`POST /deviceapi/ai-services/v1/audio/transcriptions`

Multipart fields: `model=qwen-audio-3.0-asr-flash` and binary `file`. Before requesting, the script parses RIFF/fmt/data and validates format, actual byte lengths and duration.

Returns `{text}` JSON. Empty text can mean no recognized speech and does not justify automatic resubmission. ASR and STT use the same API.

Accepts mono PCM 16-bit WAV at 8–48 kHz, at most 60 seconds and 10 MiB. Other formats require an explicit conversion plan that preserves the original. Do not silently truncate or split into multiple paid requests. Each call consumes 1000 shared device quota.

## Authentication and network

`CODECRAFT_API_ORIGIN` is a user-provided HTTPS origin such as `https://your-codecraft-api.example`. Development port forwarding may use `http://127.0.0.1:18083`; plaintext HTTP is allowed only on loopback. User information, query strings, fragments and non-root paths are rejected. Do not guess an unconfigured public origin.

`CODECRAFT_DEVICE_FILE` points to the user's private configuration outside the Skill. Replace these placeholders with the user's own device credentials:

```json
{"eui":"REPLACE_WITH_16_HEX_EUI","deviceKey":"REPLACE_WITH_32_HEX_DEVICE_KEY"}
```

Use mode 0600 on POSIX and keep the file outside version control. Use existing credentials; do not automatically create devices, modify accounts, add quota or request provider keys.

The header is `Authorization: Device <Base64(EUI:DeviceKey)>`. Base64 is encoding, not encryption. This is not Bearer authentication; do not use DeviceKey as an OpenAI SDK api_key. The gateway validates device credentials and maps them to an internal token. The Skill does not access internal tokens, OSS AccessKeys or databases.

## Errors and retries

- HTTP 400/413: check input and API limits. Local rejection before transmission makes no model call.
- HTTP 401: can indicate invalid device credentials or exhausted device quota; the error text alone may not distinguish them.
- HTTP 403: device disabled or permission denied; do not change identity to bypass it.
- HTTP 404: API or asset absent; assets belonging to another device also return 404.
- HTTP 429: rate or quota limit; respect the existing limit.
- HTTP 502/503: provider, authentication, provisioning or storage dependency failure.
- Timeout, interrupted stream or missing complete response: execution and charge may be uncertain. Report failure or uncertainty; do not automatically resend charged requests or switch models to retry.

Scripts neither retry automatically nor follow redirects. They do not print raw server error bodies, request headers or credentials. Report success only on exit code 0; otherwise inspect stderr and preserve valid existing results. An already-authorized single call needs no additional confirmation merely because a Skill is used. An uncertain result does not authorize another call.

All AI capabilities share device quota. The server provisions quota on first access by a valid device; the Skill does not replenish it. Quota units here are platform accounting, not provider invoices or currency charges.
