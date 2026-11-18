# CodeCraft Text Generation API v1

## Request and result

`POST /deviceapi/ai-services/v1/chat/completions`

JSON fields: `messages=[{role,content}]`, `max_tokens`, and optional `stream=true`. The script accepts either a UTF-8 `--prompt-file` or a JSON message array in `--messages-file`.

The raw non-streaming response contains `choices[0].message.content`, `choices[0].finish_reason`, and `usage`. SSE responses contain JSON `data:` events with `choices[].delta.content` and `finish_reason`, followed by `data: [DONE]`. Network chunks are not event boundaries.

Without streaming, the script prints `{text,usage,finish_reason,complete}` JSON. With `--stream`, it writes content increments to stdout and requires both `finish_reason=stop` and SSE `[DONE]` for completion. Interrupted output is retained, but the command exits nonzero and must not be reported as a complete response.

Only text system/user/assistant messages are supported. Vision, tool calls, and model discovery are outside the script's scope. Usage is charged by token against shared device quota; `--max-tokens` defaults to 256 and accepts 1-2048. Requests support at most 64 messages and 8192 total Unicode characters.

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

A token-limit stop (`finish_reason=length`), content filtering, or missing completion status is incomplete even when transport finishes successfully. The script retains generated text and exits nonzero. Non-streaming JSON sets `complete=false`; streaming preserves its already printed text. Do not automatically continue or retry a billable generation.

When Content-Length is provided, the received byte count must match it. Oversized or interrupted responses fail without an automatic retry. The client removes incomplete output files it created and never overwrites an existing file.
