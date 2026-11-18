# CodeCraft Text generation API v1

## Request and result

`POST /deviceapi/ai-services/v1/chat/completions`

JSON fields: `model=qwen-plus`, `messages=[{role,content}]`, `max_tokens`, and optional `stream=true`. Choose exactly one UTF-8 `--prompt-file` or JSON `--messages-file` input.

Non-streaming output is `{text,usage}` JSON; streaming writes text deltas to stdout. SSE `[DONE]` is required for success. Incomplete streams retain partial text and exit nonzero.

Only system/user/assistant text messages are supported; no vision, tool execution or model listing. Usage consumes shared device quota by token. `--max-tokens` defaults to 256 and must be positive.

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
