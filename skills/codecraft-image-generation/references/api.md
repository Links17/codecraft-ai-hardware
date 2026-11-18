# CodeCraft Image generation API v1

## Request and result

`POST /deviceapi/ai-services/v1/images/generations`

JSON fields: `model=qwen-image-2.0`, `prompt`, `n=1`, `size=1024x1024`, `response_format=b64_json`. The script decodes the gateway response without following provider result URLs.

Writes to a new output path and returns its path as JSON. Checks PNG/JPEG/WebP headers and a 20 MiB maximum. Existing files are never overwritten.

One 1024×1024 image per request, at most 2000 Unicode prompt characters, 10000 quota per image. Follow the host environment’s generation-tool priority rules. Editing, adaptive sizes, asynchronous jobs and batch calls are not implemented. Temporary provider URLs are not stable asset links.

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

## Asset API

`POST /deviceapi/media-assets/v1/files` accepts multipart `file`, up to 20 MiB. A successful business envelope has `code=200`; `data.id` is a UUID and `data.content_url=/deviceapi/media-assets/v1/files/{id}/content`. Scripts expose these business fields, not temporary signed OSS URLs.

`GET /deviceapi/media-assets/v1/files/{id}/content` uses the same Device Header and returns binary content without redirects, with `Cache-Control: private, no-store`. Unauthorized access returns 401, a disabled device 403, and missing or other-device assets 404. Only full GET is supported; Range/HEAD are not promised.

`--archive` is an explicit second request. If generation succeeds but archival fails, the script reports the local file and exits nonzero. Never regenerate media to obtain a link. `device_api.py archive --file` uploads an existing file. An upload timeout may still have created an asset; do not automatically upload again.

`content_url` has no signed expiry but requires an existing file and current device permission. It contains no DeviceKey and need not work in an anonymous browser. Temporary `url` / `expires_at` fields remain server compatibility fields and do not describe the stable content_url.
