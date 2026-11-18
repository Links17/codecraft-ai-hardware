#!/usr/bin/env python3
"""Standalone, one-shot realtime ASR client. Never reconnect or replay audio."""
import argparse
import io
import json
import logging
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
import wave

# Keep the installed skill directory free of Python bytecode caches.
sys.dont_write_bytecode = True

from device_api import DeviceAPI, SkillError, decode_json, read_bytes, run, read_response
from transcribe import validate_wav

BASE = '/deviceapi/ai-services/v1/audio/transcriptions/realtime/sessions'
REQUEST = {'audio': {'format': 'pcm_s16le', 'sample_rate': 16000, 'channels': 1}, 'max_audio_seconds': 60}
STATUS_FIELDS = ('session_id', 'state', 'billing_status', 'reserved_quota', 'charged_quota', 'audio_duration_ms', 'outcome')


def emit(value):
    print(json.dumps(value, ensure_ascii=False), flush=True)


def identifier(value):
    try:
        return str(uuid.UUID(value))
    except (ValueError, TypeError, AttributeError):
        raise SkillError('Expected a valid session UUID.') from None


def idempotency_key(value):
    # Intentionally narrower than the server contract; safe for headers/logs.
    if not re.fullmatch(r'[A-Za-z0-9_-]{8,128}', value):
        raise SkillError('Idempotency key requires 8..128 letters, digits, underscores or hyphens.')
    return value


def audio_bytes(path, raw=False):
    audio = read_bytes(path, 1920000 if raw else 10 * 1024 * 1024)
    if not raw:
        validate_wav(audio)
        with wave.open(io.BytesIO(audio), 'rb') as source:
            if source.getframerate() != 16000:
                raise SkillError('Realtime WAV requires 16000 Hz; convert explicitly before calling.')
            audio = source.readframes(source.getnframes())
    if not audio or len(audio) % 2 or len(audio) > 1920000:
        raise SkillError('Realtime input requires nonempty, even-length PCM16 mono at 16000 Hz, at most 60 seconds.')
    return audio


def session_request(api, session_id=None, key=None):
    path = BASE + '/' + identifier(session_id) if session_id else BASE
    headers = {'Authorization': api.authorization, 'Content-Type': 'application/json'}
    body = None
    if key is not None:
        headers['Idempotency-Key'] = idempotency_key(key)
        body = json.dumps(REQUEST).encode()
    request = urllib.request.Request(api.origin + path, data=body, headers=headers)
    try:
        with api.opener.open(request, timeout=15) as response:
            data = read_response(response, 65536)
        result = decode_json(data)
        if result.get('code') != 200 or not isinstance(result.get('data'), dict):
            raise SkillError('Session API reported failure; no automatic retry.')
        session = result['data']
        sid = identifier(session.get('session_id'))
        if session_id and sid != identifier(session_id):
            raise SkillError('Session response has an unexpected ID.')
        return session
    except urllib.error.HTTPError as error:
        status = error.code
        error.close()
        raise SkillError(f'Session HTTP {status}; no automatic retry. For uncertain creation, retain the same idempotency key.') from None
    except (urllib.error.URLError, OSError):
        raise SkillError('Session network failure; outcome may be uncertain. Retain the same idempotency key; do not create a replacement session.') from None


def public_status(session):
    # Never print ticket, URL or unrecognized response fields.
    return {name: session[name] for name in STATUS_FIELDS if name in session}


def websocket_connect():
    try:
        import websockets
        from websockets.sync.client import connect
    except ImportError:
        raise SkillError('Realtime requires websockets==15.0.1; install scripts/requirements-realtime.txt in a virtual environment.') from None
    if websockets.__version__ != '15.0.1':
        raise SkillError('Use websockets==15.0.1 from scripts/requirements-realtime.txt; other versions have unverified redirect behavior.')
    return connect


def event_message(raw):
    if not isinstance(raw, str):
        raise SkillError('Unexpected binary server event; query session status.')
    event = decode_json(raw)
    kind = event.get('type')
    if kind not in ('session.ready', 'transcript.partial', 'transcript.final', 'session.finished', 'session.error'):
        raise SkillError('Unknown realtime event; query session status.')
    return event


def stream(api, session, audio, connect):
    sid = identifier(session.get('session_id'))
    path = BASE + '/' + sid + '/stream'
    ticket = session.get('ticket')
    if session.get('stream_path') != path or not isinstance(ticket, str) or not ticket:
        raise SkillError('Session is not connectable. Query its status; do not automatically create another.')
    uri = ('wss' if api.origin.startswith('https:') else 'ws') + api.origin[api.origin.index(':'):] + path
    # A private silent logger prevents websocket debug logging from exposing tickets.
    logger = logging.Logger('sensecraft-capabilities-asr-private')
    logger.addHandler(logging.NullHandler())
    logger.disabled = True
    revisions, finals = {}, {}
    with connect(uri, proxy=None, compression=None, open_timeout=10, close_timeout=2,
                 max_size=65536, max_queue=16, logger=logger) as ws:
        ws.send(json.dumps({'type': 'session.authenticate', 'ticket': ticket}))
        event = event_message(ws.recv(timeout=15))
        if event['type'] != 'session.ready' or event.get('session_id') != sid:
            raise SkillError('Realtime authentication/start failed; query session status. No automatic retry.')
        emit({'type': 'session.ready', 'session_id': sid})
        offset, finished_input = 0, False
        started = next_send = time.monotonic()
        deadline = started + 110
        while True:
            now = time.monotonic()
            if now >= deadline:
                raise SkillError('Realtime result timed out; query session status. No automatic retry.')
            if not finished_input and now >= next_send:
                if offset < len(audio):
                    chunk = audio[offset:offset + 3200]
                    ws.send(chunk)
                    offset += len(chunk)
                    # Never burst to catch up after a slow send.
                    next_send = time.monotonic() + len(chunk) / 32000
                else:
                    ws.send(json.dumps({'type': 'input.finish'}))
                    finished_input = True
            timeout = deadline - time.monotonic()
            if not finished_input:
                timeout = min(timeout, max(0, next_send - time.monotonic()))
            try:
                event = event_message(ws.recv(timeout=max(0, timeout)))
            except TimeoutError:
                continue
            kind = event['type']
            if kind in ('transcript.partial', 'transcript.final'):
                segment, revision, text = event.get('segment_id'), event.get('revision'), event.get('text', '')
                if type(segment) is not int or segment < 0 or type(revision) is not int or revision < 1 or not isinstance(text, str):
                    raise SkillError('Invalid transcript event; query session status.')
                if segment in finals or revision <= revisions.get(segment, 0):
                    continue
                revisions[segment] = revision
                if kind == 'transcript.final':
                    finals[segment] = text
                emit({'type': kind, 'segment_id': segment, 'revision': revision, 'text': text,
                      **{field: event[field] for field in ('start_ms', 'end_ms') if type(event.get(field)) is int}})
            elif kind in ('session.finished', 'session.error'):
                if event.get('session_id') not in (None, sid) or type(event.get('code')) is not int:
                    raise SkillError('Invalid terminal event; query session status.')
                emit({field: event[field] for field in ('type', 'session_id', 'audio_duration_ms', 'charged_quota', 'billing_status', 'code', 'reason') if field in event})
                if (kind != 'session.finished' or event['code'] != 200 or event.get('billing_status') != 'committed'
                        or offset != len(audio)):
                    raise SkillError('Realtime session failed, ended early or billing is unresolved. Query status; do not replay audio.')
                emit({'type': 'transcript.result', 'text': ''.join(finals[key] for key in sorted(finals))})
                return
            else:
                raise SkillError('Unexpected repeated ready event; query session status.')


def main():
    parser = argparse.ArgumentParser(description='CodeCraft realtime ASR: paced file streaming, no automatic reconnect/replay.')
    sub = parser.add_subparsers(dest='command', required=True)
    start = sub.add_parser('stream', help='Create one session and send one recording as paced PCM.')
    start.add_argument('--file', required=True)
    start.add_argument('--raw-pcm', action='store_true', help='Input is raw S16LE, mono, 16000 Hz, without WAV header.')
    start.add_argument('--idempotency-key', help='Reuse the original key only for the same logical operation.')
    status = sub.add_parser('status', help='Read status without sending audio or creating a session.')
    status.add_argument('--session-id', required=True)
    recover = sub.add_parser('recover', help='Repeat creation with its original key; print status only, never reconnect.')
    recover.add_argument('--idempotency-key', required=True)
    args = parser.parse_args()
    if args.command == 'status':
        emit(public_status(session_request(DeviceAPI(), session_id=identifier(args.session_id))))
        return
    if args.command == 'recover':
        emit(public_status(session_request(DeviceAPI(), key=idempotency_key(args.idempotency_key))))
        return
    audio = audio_bytes(args.file, args.raw_pcm)
    connect = websocket_connect()  # Dependency validation precedes quota reservation.
    api = DeviceAPI()
    key = idempotency_key(args.idempotency_key or str(uuid.uuid4()))
    print(json.dumps({'idempotency_key': key}), file=sys.stderr, flush=True)
    session = session_request(api, key=key)
    print(json.dumps({'session_id': identifier(session.get('session_id'))}), file=sys.stderr, flush=True)
    try:
        stream(api, session, audio, connect)
    except SkillError:
        raise
    except (Exception, KeyboardInterrupt):
        # Low-level WS exceptions may contain headers, tickets or signed URLs.
        raise SkillError('Realtime connection interrupted; query status with the session ID. No automatic reconnect or audio replay.') from None


if __name__ == '__main__':
    run(main)
