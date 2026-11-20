# Realtime ASR / STT v1

For MCU/Linux clients, implement the public session and WebSocket protocol below using the device networking stack. The Python environment in the next section is only for the optional workstation client.

## Running the client

Use the same [device authentication settings](api.md#authentication-and-network). File uploads and realtime sessions are separate billable operations; choose the mode requested by the user.

The workstation streaming helper requires Python 3.10+ and `websockets==15.0.1`. The tested synchronous client does not follow redirects. Revalidate that behavior before changing the dependency version. The package works independently of the source repository or other skills.

Run the following from the installed ASR skill root in a POSIX shell on macOS or Linux (or WSL). These setup commands make no recognition requests. They use a real directory under the user's home directory, or preserve a previously selected `CODECRAFT_WORKDIR`:

```sh
export CODECRAFT_WORKDIR="${CODECRAFT_WORKDIR:-$HOME/codecraft-workspace}"
mkdir -p "$CODECRAFT_WORKDIR"
python3 -m venv "$CODECRAFT_WORKDIR/.venv-asr"
. "$CODECRAFT_WORKDIR/.venv-asr/bin/activate"
python3 -m pip install -r scripts/requirements-realtime.txt
python3 -m pip check
python3 scripts/realtime.py --help
```

Stop if any setup command fails. `python3 -m venv` and pip must be available; use the operating system's Python installation instructions if either is missing. Do not use `sudo pip` or install this dependency into the system Python environment. The pinned package requires network access to the configured package index unless already available locally.

Activation makes `python3` use this environment in the current shell. In each new shell, set the same working directory and activate the existing environment again; creation and installation are not needed on every invocation:

```sh
export CODECRAFT_WORKDIR="${CODECRAFT_WORKDIR:-$HOME/codecraft-workspace}"
. "$CODECRAFT_WORKDIR/.venv-asr/bin/activate"
```

Complete [authentication setup](api.md#authentication-and-network), provide a recording, and choose exactly one input command. Replace the example file name with the user's existing file if different:

```sh
python3 scripts/realtime.py stream --file "$CODECRAFT_WORKDIR/recording-16k.wav"
```

For raw PCM, use this alternative instead. The caller must guarantee the sample format because raw PCM has no container metadata:

```sh
python3 scripts/realtime.py stream --file "$CODECRAFT_WORKDIR/input.pcm" --raw-pcm
```

These streaming commands each start a billable operation. They are alternatives, not consecutive setup steps. Use `deactivate` when finished with the virtual environment.

WAV input must be mono PCM16 at 16000 Hz. The client validates the entire file and strips the WAV container before transmission. Raw PCM must be S16LE / mono / 16000 Hz, nonempty, even-length, and no larger than 1,920,000 bytes (60 seconds). Its sample rate cannot be inferred from raw bytes. The script does not resample or truncate automatically. It streams existing files; it does not capture a microphone or certify a device's audio capture.

stdout contains realtime JSON Lines. Before creation, stderr prints `idempotency_key`; after successful creation it prints `session_id`. Retain these non-credential identifiers for recovery. Tickets are never printed or saved. To save transcripts, redirect stdout to a private file after setting `umask 077` and shell no-clobber mode with `set -C`. Keep recordings and transcripts out of version control.

The client filters stale revisions and duplicate events for finalized segments. On success it appends `{"type":"transcript.result","text":"Final segments joined in segment ID order"}`. Partial text is excluded from this summary. A nonzero exit code means failure or incomplete execution; do not report partial text as complete success.

## Creation and recovery

Base path: `/deviceapi/ai-services/v1/audio/transcriptions/realtime/sessions`.

`POST` the base path with `Authorization: Device <Base64(eui:deviceKey)>` and `Idempotency-Key: <unique value of 8-128 characters>`.

```json
{"audio":{"format":"pcm_s16le","sample_rate":16000,"channels":1},"max_audio_seconds":60}
```

No model or external endpoint parameter is accepted. The response envelope is `{code:200,msg,data,detail}`. Its `data` includes `session_id`, `state`, `billing_status`, `reserved_quota`, `charged_quota`, and `audio_duration_ms`. While the session is connectable, it also includes `stream_path`, `ticket`, and `ticket_expires_in`. This envelope differs from the file transcription response `{text}`.

Repeating the same request with the same device and idempotency key returns the original session. A changed request returns 409. Repetition does not extend the ticket lifetime or create a second charge. The client generates a UUID by default; optionally specify `stream --idempotency-key ORIGINAL_KEY` before the first request. Never replace the key when recovering that operation.

```bash
# With a session ID: read-only query using the standard library.
python3 scripts/realtime.py status --session-id SESSION_UUID
# Only after uncertain creation without an ID: explicitly recover with the original key.
python3 scripts/realtime.py recover --idempotency-key ORIGINAL_KEY
```

Replace `SESSION_UUID` with the returned session ID, or `ORIGINAL_KEY` with the original creation key. These uppercase labels are required user values, not literal arguments.

`status` sends `GET base-path/{id}` and returns the same device's session state, outcome, and billing status. It returns no ticket, audio, or transcript. Other-device and nonexistent IDs return 404. Audio duration may remain 0 while a session is active.

`recover` repeats POST with the original key and prints only status; it does not connect or send audio. If the original request never arrived, this creates a pending session and reserves quota. An unused ticket eventually expires and its reservation is released. Recovery is not read-only and must not be used with a new key as a probe. The client never recovers automatically or replays audio into an ended or uncertain session. Status queries cannot recover lost transcripts.

## WebSocket and events

Convert the configured HTTPS origin to WSS (explicit loopback HTTP may use WS), then append `base-path/{id}/stream`. Validate that the returned path is exactly this session's relative path. Reject external URLs, query strings, and fragments. Do not attach DeviceKey to the upgrade request or place a ticket in the URL.

1. Within 3 seconds of connection, send the first text message: `{"type":"session.authenticate","ticket":"<ticket>"}`.
2. Wait for `{"type":"session.ready","session_id":"<id>","max_audio_seconds":60,"charged_quota":0}` before sending audio.
3. Send binary raw PCM frames, preferably 100 ms / 3200 bytes, at most 200 ms / 6400 bytes. Frames must be nonempty and even-length. Pace transmission in realtime and keep send buffers bounded. Do not send WAV headers, MP3, or WebM.
4. Send `{"type":"input.finish"}` after the audio and continue receiving until a terminal session event. At the 60-second audio limit the service finishes input automatically.

Transcript examples:

```json
{"type":"transcript.partial","segment_id":1,"revision":1,"text":"Hello","start_ms":0}
{"type":"transcript.final","segment_id":1,"revision":2,"text":"Hello world","start_ms":0,"end_ms":2080}
```

A partial contains replacement text for the entire segment, not an append-only delta. Replace by `segment_id`, ignore stale `revision` values, and freeze a segment after finalization. Zero-valued time fields may be omitted. `transcript.final` ends an utterance, not the session; keep the connection open.

Terminal examples:

```json
{"type":"session.finished","session_id":"<id>","audio_duration_ms":2080,"charged_quota":1000,"billing_status":"committed","code":200,"reason":"completed"}
{"type":"session.error","code":2020,"reason":"invalid_ticket","charged_quota":0}
```

`code` is numeric; `reason` is a classification string. Errors before authentication may omit session ID and billing status. Confirm completion only after a successful terminal event with `billing_status=committed`. A pending status requires a query and does not mean no charge. On an error, timeout, disconnect, or final transcript without a terminal event, do not automatically reconnect, replay, or fall back to file ASR.

## Limits, quota, and capture integration

- Tickets expire after 60 seconds and can be consumed only once. They are not long-lived device credentials.
- Each device may have one pending, active, or settling session, with at most six new sessions per minute.
- No audio for 20 seconds ends the session; pings do not extend that limit. Final results may take up to 10 seconds after finish. Allow up to 90 seconds for audio processing and another 12 seconds for settlement.
- Each session costs 1000 quota units from the existing shared device balance. Creation reserves quota; charging is confirmed before the first valid audio is accepted for recognition.
- No-audio sessions, expired unused tickets, and startup failures release reservations. Disconnecting after audio transmission does not cancel the charge. Confirmed recognition failures without a final segment may be refunded. An uncertain committed charge remains charged; query the final session state instead of calculating a presumed refund.
- HTTP 400/413 means invalid input; 401 authentication failure; 402 insufficient quota; 403 disabled device or disallowed Origin; 404 missing session; 409 device busy or idempotency conflict; 429 rate limit; 503 service unavailable. After upgrade, errors use `session.error`. Raw error bodies and low-level exceptions are not printed.
- Native device clients may omit Origin. Browser clients require an approved exact Origin and user permission to capture a microphone. Produce PCM with a suitable capture implementation such as AudioWorklet; do not send MediaRecorder WebM directly. Resolve access issues through the service administrator.
- Audio and transcripts are not archived by default. Persistent storage requires a separate explicit task.

Client dependency reference: [websockets 15.0.1 synchronous client](https://websockets.readthedocs.io/en/15.0.1/reference/sync/client.html).
