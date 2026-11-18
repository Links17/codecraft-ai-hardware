# Device onboarding

Use this guide on a developer workstation to obtain the API origin and one device's EUI/DeviceKey. The MCU or Linux runtime needs those three values and its native HTTPS client; SenseCraft CLI, Node.js and the optional Python helpers run on the workstation.

## Free allowance

Each device receives the following free allowance every month, shared by the AI features below. Each row assumes the entire unused monthly device allowance is spent on that feature; **the rows are alternatives and must not be added together**.

| Feature | Per device per month | Per user per month, total across 5 devices |
| --- | --- | --- |
| File ASR / STT (up to 60 seconds per call) | **62 calls** | **310 calls** |
| Realtime ASR (up to 60 seconds per session) | **62 sessions** | **310 sessions** |
| TTS (up to 500 input characters per call) | **62 calls** | **310 calls** |
| Image generation | **6 images** | **30 images** |
| LLM: 100 input + 50 output tokens | **About 41 calls** | **About 205 calls** |
| LLM: 100 input + 100 output tokens | **About 31 calls** | **About 155 calls** |
| LLM: 200 input + 100 output tokens | **About 20 calls** | **About 100 calls** |

The five-device column adds the complete calls available on five separate devices; it is not a pooled account balance. LLM counts are estimates for the stated token usage. Actual usage includes the full request context and generated output; longer conversations or replies reduce the number of calls. Using one feature reduces the allowance available for the others. The service manages monthly renewal; checking device access again does not replenish the allowance.

## Choose the missing setup

| Input | Where to obtain it | Local use |
| --- | --- | --- |
| CodeCraft API origin | The selected service environment's published Device API configuration; see [origin lookup](#obtain-the-api-origin) | `CODECRAFT_API_ORIGIN`; HTTPS origin without `/deviceapi` |
| EUI | An existing development device's `device_eui`, or the `eui` returned by authorized creation | `eui` in the private device file |
| DeviceKey | `device devkit key` or authorized creation returns `device_key` | Import as `deviceKey` in the private device file |

- All three are available: reuse them and go to [access checking](#check-device-api-access); no account login or device creation is needed.
- Only the origin is missing: follow [origin lookup](#obtain-the-api-origin), preserving the existing identity and key.
- Credentials are missing: use the configured CLI environment to [select an existing device](#select-or-create-one-development-device). Sign in only if that environment has no suitable active profile.

The origin and credentials must belong to the same service environment. A missing CodeCraft origin blocks Device API requests, not local credential import or an already configured SenseCraft provisioning task. Never create another identity just to resolve an unknown URL.

## Workstation context

Run shell examples from this installed skill's root (containing `SKILL.md`) in a POSIX shell on macOS/Linux or WSL. Python 3.10+ is needed only for the optional import/check helpers. Create a private workspace outside the skill package:

```sh
export CODECRAFT_WORKDIR="${CODECRAFT_WORKDIR:-$HOME/codecraft-workspace}"
umask 077
mkdir -p "$CODECRAFT_WORKDIR"
```

The CLI command reference for this guide is [SenseCraft CLI 0.5.0](https://www.npmjs.com/package/@seeed-studio/sensecraft-cli/v/0.5.0). Reuse the existing installation and its official bundled Skill when they support these commands. Check the actual executable before using it:

```sh
sensecraft-cli --version
sensecraft-cli --help
```

If the CLI is missing and provisioning is part of the task, install the selected release with Node.js 16+:

```sh
npm install --global @seeed-studio/sensecraft-cli@0.5.0
sensecraft-cli --version
```

Stop if installation fails. Preserve an existing installation unless changing it is part of setup. Keep the CLI's account configuration outside the skill package and version control. Reuse the configuration for the intended environment; do not automatically replace `SENSECRAFT_CLI_PATH` or reset an active profile. For an explicitly separate environment, use its operator-supplied CLI configuration and a separate private configuration directory.

## Obtain the API origin

1. Reuse an explicitly configured `CODECRAFT_API_ORIGIN` or obtain the Device API origin from the selected service environment's official onboarding/deployment configuration. It must explicitly identify the CodeCraft `/deviceapi` service and match the environment that issued the credentials. EUI and DeviceKey do not encode a gateway URL.
2. To inspect what the installed CLI supports, use its `--version`, `--help` and bundled official Skill. In the 0.5.0 reference, `auth info --json` reports profile metadata, and `devkit` returns credentials; neither returns a CodeCraft origin. There is no documented endpoint-discovery command in that release. Do not invent one or read private account configuration to guess a service URL. A future release's documented endpoint query may be used only after checking its actual output contract and selected environment.
3. The published CLI 0.5.0 documentation identifies `https://api-gateway.seeed.cc` as the production SenseCraft AI/Hub gateway for `/openapi` calls with an account Access Key. This is a known platform gateway, not confirmation that CodeCraft `/deviceapi` is deployed there. Use that same origin for CodeCraft only when the service's published configuration explicitly confirms the mapping. A CLI host override, account login URL, Console URL or SenseCAP Data URL alone does not establish that mapping.
4. Export the confirmed value as `CODECRAFT_API_ORIGIN`: HTTPS scheme, hostname and optional port only. Do not include `/deviceapi`, `/openapi`, credentials, a query or a fragment. Plain HTTP is accepted by the helpers only for an explicitly configured loopback fixture. The skill has no built-in public origin or automatic domain fallback.

If no matching Device API origin is published or supplied, ask for that environment's CodeCraft API origin and report it as the missing input. Preserve available credentials and continue independent work. Selecting a CLI site alone does not configure a test environment; do not combine credentials from one environment with another origin. Actual Device API access is established by the [profile check](#check-device-api-access), not by a domain name or a successful account login.

## Sign in on the workstation

Inspect the configured CLI profile without calling a cloud API:

```sh
sensecraft-cli auth info --json
```

If the intended environment already has a suitable active profile, skip login. Otherwise use the environment's supplied `SENSECRAFT_SITE` and configuration with the official CLI Skill's split login flow. CodeCraft's API origin is not needed for this account login:

```sh
: "${SENSECRAFT_SITE:?Set the site from the selected environment onboarding instructions}"
sensecraft-cli auth init --site "$SENSECRAFT_SITE" --no-wait
```

Show the returned verification URL and wait for the user to complete login. Do not invent a URL or ask for their account password in chat. Set `SENSECRAFT_DEVICE_CODE` locally to the returned device code, then complete the same login:

```sh
: "${SENSECRAFT_DEVICE_CODE:?Set the code returned by auth init}"
sensecraft-cli auth init --device-code "$SENSECRAFT_DEVICE_CODE"
```

If the continuation returns key choices rather than a completed login, select an existing key with the permissions needed for the task by setting `SENSECRAFT_KEY_ID` to its returned ID:

```sh
: "${SENSECRAFT_KEY_ID:?Select a returned access key ID with the required permissions}"
sensecraft-cli auth init --device-code "$SENSECRAFT_DEVICE_CODE" --key-id "$SENSECRAFT_KEY_ID"
```

Creating a new device requires write access. When the authorized provisioning task also needs a new account Access Key, the CLI supports `--label` with `--access-level read-write`. After login, run `sensecraft-cli auth info --json` and `unset SENSECRAFT_DEVICE_CODE SENSECRAFT_KEY_ID`. Do not loop login attempts or switch accounts to bypass permission errors. Account Access Keys authorize platform operations; never install them in firmware or use them as DeviceKey values.

## Select or create one development device

Prefer the intended existing identity. List development devices when the EUI is unknown:

```sh
sensecraft-cli device list --device-type 3
```

List results use `device_eui` and `device_name`. Set `DEVICE_EUI` to the intended device's EUI; if it is already known, skip listing. Retrieve a missing DeviceKey into a new private file:

```sh
: "${DEVICE_EUI:?Select the intended development device EUI}"
(
  umask 077
  set -C
  sensecraft-cli device devkit key --eui "$DEVICE_EUI" > "$CODECRAFT_WORKDIR/devkit-response.json"
)
```

**Alternative: create a new identity only when the user's task includes provisioning a new device.** Do not run this after successfully retrieving an existing identity:

```sh
(
  umask 077
  set -C
  sensecraft-cli device devkit create --sku blank_device --name "my-linux-device" > "$CODECRAFT_WORKDIR/devkit-response.json"
)
```

`blank_device` is the generic development identity option for a custom MCU/Linux project where supported by the selected environment. CLI 0.5.0 also lists `xiao` and `grove_vision_ai`, with up to five development kits per SKU per organization. `devkit key` supports development kits; it does not establish a credential-retrieval method for every physical product. Use the product's approved provisioning process for other devices.

Check the command's exit status before importing its output. The new-file redirection prevents overwriting an existing response. On a timeout or ambiguous creation result, list devices and recover the existing identity; do not blindly create again. Retain any incomplete response privately for investigation and choose a new output filename for recovery. A missing route or permission error means the environment/account needs correction, not that a fabricated EUI will work.

## Import credentials locally

Create/key responses use `eui` and `device_key`; key responses can also contain `token`. Import only the identity and DeviceKey:

```sh
python3 scripts/device_credentials.py import \
  --input "$CODECRAFT_WORKDIR/devkit-response.json" \
  --output "$CODECRAFT_WORKDIR/device.json"
export CODECRAFT_DEVICE_FILE="$CODECRAFT_WORKDIR/device.json"
```

The import needs no API origin and makes no network call. It writes a new owner-only file, discards extra fields and never prints secrets. The JSON contains `eui` (16 hexadecimal characters) and `deviceKey` (32 hexadecimal characters). The CLI's `token` is not the DeviceKey. EUI is assigned by the service; it is not automatically a MAC address or MCU chip ID. Once imported successfully, remove the raw CLI response when it is no longer needed.

If a private `eui`/`deviceKey` JSON file already exists, set `CODECRAFT_DEVICE_FILE` to its absolute path and skip CLI retrieval/import. Keep it outside version control; never paste credentials into chat or a shell command.

## Check Device API access

After the matching origin and credential file are configured, run the profile check when access verification is part of the task:

```sh
: "${CODECRAFT_API_ORIGIN:?Obtain the matching Device API origin before making a request}"
: "${CODECRAFT_DEVICE_FILE:?Set the absolute path of the private device JSON file}"
test -r "$CODECRAFT_DEVICE_FILE" && python3 scripts/device_credentials.py check
```

`check` calls `GET /deviceapi/device-management/v1/device`, requires both HTTP and business success, verifies the returned EUI and prints no credentials. First valid access may initialize the device allocation; it does not invoke an AI model. The monthly allowance is 62500 shared quota units, with renewal managed by the service. Returned `initial_quota` is the configured allocation, **not remaining balance**; the response must not be used to reset a local balance. Treat the profile response as authoritative for the selected environment.

A failed check does not authorize changing the origin, creating another identity or retrying a paid operation. For a route error, verify the published Device API mapping; for an authentication error, verify the selected environment and credential source. Without Python, implement the same request and response validation in the [native client](device-integration.md).

## Provision the runtime

Transfer only the matching API origin, EUI and DeviceKey using the device's approved provisioning channel. Keep them associated with the same environment and use one identity per device. Store the key in protected device storage or an owner-readable Linux file; never compile a shared fleet key or account Access Key into distributable firmware. Do not log the key, encoded Authorization value or credential file.

Use [device integration](device-integration.md) for TLS, header construction, native Linux calls and MCU streaming. Credential rotation/revocation requires the approved account or product management process; this API package does not define a public rotation endpoint. After replacing credentials, check access again. Do not create another identity to bypass quota or a revoked key.
