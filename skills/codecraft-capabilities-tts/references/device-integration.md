# Native MCU and Linux integration

Use this reference when implementing device firmware or a Linux application. SenseCraft CLI is used on the provisioning workstation; Python scripts in this skill are optional host diagnostics. The device calls the public HTTPS/WebSocket contract directly using its existing networking stack.

## Authentication and first request

Obtain the matching API origin, EUI and DeviceKey using [device onboarding](onboarding.md). Provision all three to the runtime; the device does not query SenseCraft CLI for a URL. For every authenticated HTTP call, send:

```text
Authorization: Device <standard padded Base64 of ASCII(eui + ":" + deviceKey)>
```

Encode the hexadecimal text, not decoded hexadecimal bytes. Do not insert a newline. Preserve the credentials exactly, use the `Device` scheme, and do not substitute `Bearer`. Base64 is reversible and is not encryption. Keep credentials out of URLs, command-line arguments, telemetry, and logs.

Start with `GET /deviceapi/device-management/v1/device`. A successful response has this shape (the EUI below is a schema label):

```json
{"code":200,"data":{"eui":"YOUR_DEVICE_EUI","initial_quota":62500}}
```

Require HTTP success, numeric `code == 200`, and an EUI matching the provisioned identity (case-insensitive hexadecimal comparison). Reject malformed bodies or a different identity. The first valid request may initialize the device quota allocation. Monthly renewal is managed by the service. `initial_quota` is not a balance query; never reset a local balance on boot, on a profile check or from the local calendar. A successful check establishes access at that time, not indefinite access or guaranteed model availability.

Use HTTPS with certificate and hostname validation and an accurate device clock. Do not disable verification to resolve clock or certificate errors. Set connection/read timeouts, bound response sizes, and do not follow authenticated redirects to another origin. The Python helper accepts loopback HTTP for local development only; that exception is not a production device configuration.

## Portable C authentication helper

Copy [device_auth.h](../assets/device_auth.h) into the device project. It is a C99 header with no heap allocation or platform dependencies. It works with an existing HTTP stack; it does not implement TLS or credential storage.

```c
#include "device_auth.h"

/* eui and device_key come from the device's provisioned storage. */
int prepare_device_header(const char *eui, const char *device_key,
                          char authorization[CODECRAFT_AUTH_HEADER_SIZE])
{
    return codecraft_device_authorization(
        eui, device_key, authorization, CODECRAFT_AUTH_HEADER_SIZE);
}
```

Allocate a writable 76-byte buffer in the caller. On return value 1, pass it as the **value** of the `Authorization` header to the platform's HTTP client. On 0, stop before sending. Input strings must be NUL-terminated and must not overlap the output buffer. Keep the buffer alive as required by the HTTP client's copy/ownership rules; clear it after the client has finished using it. Do not print it. The helper validates lengths and ASCII hexadecimal characters and includes standard Base64 padding.

This helper has host-side encoding/bounds tests. Each target still needs validation of its TLS implementation, storage permissions, transport buffering, microphone/display/audio driver, and disconnect handling.

## Native Linux curl

A native application may construct the same header directly. For manual curl diagnostics, optionally generate a private header configuration once on the workstation (Python 3.10+, from this installed skill root, with onboarding environment variables set):

```sh
python3 scripts/device_credentials.py curl-config \
  --output "$CODECRAFT_WORKDIR/device-curl.conf"
```

The output contains credentials and is created owner-readable only. Copy it securely if diagnostics run on a separate Linux device; never print it or include it in a package. It contains no endpoint. The target needs curl and its trusted CA certificates, not Python. Set `CODECRAFT_WORKDIR` to the target directory containing the file and `CODECRAFT_API_ORIGIN` to the supplied HTTPS origin, then run:

```sh
: "${CODECRAFT_WORKDIR:?Set the directory containing device-curl.conf}"
: "${CODECRAFT_API_ORIGIN:?Set the supplied HTTPS origin}"
curl -q --config "$CODECRAFT_WORKDIR/device-curl.conf" \
  --proto '=https' --max-time 30 --fail --silent --show-error \
  "${CODECRAFT_API_ORIGIN%/}/deviceapi/device-management/v1/device"
```

`-q` disables automatic curl configuration loading; keep it as the first argument. Do not add `--insecure`, `--verbose`, `--trace`, `--location`, or shell tracing to credential-bearing requests. An exit code of 0 alone is insufficient: inspect the JSON business code and device identity described above. A native application should do this validation programmatically.

For a JSON capability request, use the same private configuration, the documented method/path and `Content-Type: application/json`, and `--data-binary @request.json` with an actual prepared input file. For file ASR, use multipart form fields and let the HTTP library generate the multipart boundary. See [the capability API](api.md) for exact inputs and responses. Model calls consume quota; do not use all examples as an automatic smoke-test batch.

## Device transport and media handling

| Capability | Device implementation |
|---|---|
| Text generation | Parse `choices[0].message.content` for JSON, or SSE `data:` events and `choices[].delta.content` for streaming. JSON helper output is a projection, not the raw API schema. |
| File ASR/STT | Upload a complete supported WAV as multipart data; parse the returned `text`. Do not substitute raw PCM without a WAV container. |
| Realtime ASR | Create a session over authenticated HTTPS, then use the returned same-origin WebSocket path and short-lived ticket protocol. Follow the realtime reference in the ASR package. |
| TTS | Receive binary WAV, validate its container and sample format, then feed a compatible decoder/player or file. A helper's `{file: ...}` is local metadata, not the HTTP response. |
| Image generation | Parse the image result's `b64_json` or authenticated `url`. Decode incrementally or download to storage if RAM is limited. Check the actual image format and requested dimensions before display. |
| Stored media | Use the authenticated asset content path with the owning device's header. A stable path remains usable while the asset exists and access remains valid. |

HTTP reads, SSE events, JSON objects, and WebSocket messages have different boundaries. A network read may contain only part of a JSON/SSE event or several events. Use a bounded incremental parser rather than assuming one read equals one result. When supplied, verify Content-Length; treat early EOF and missing protocol completion as incomplete. Do not play error JSON as audio or accept a truncated image as success.

For LLM streaming, preserve partial content but require a successful finish reason and `[DONE]` before reporting completion. A token limit or content-filter stop is incomplete under this skill's contract. Avoid allocating a full large Base64 image in MCU RAM. Requesting `response_format=url` stores the image and returns a stable same-origin asset content path. Resolve that path against the configured CodeCraft origin, require the expected `/deviceapi/media-assets/v1/files/` prefix, and authenticate the download with the owning device's header. Do not follow cross-origin redirects or fetch arbitrary URLs. Use Base64 output when persistent storage is not desired.


Handle 400/413 by correcting input, 401/403 by resolving credentials/access, and 429 by respecting the limit. Other capability-specific statuses are in the API reference. Do not automatically replay billable calls after a timeout; completion and charging may be uncertain. Realtime sessions have explicit status and recovery semantics. Record non-secret operation/session identifiers where provided; never rotate identities to evade limits.
