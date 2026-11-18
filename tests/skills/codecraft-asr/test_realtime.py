#!/usr/bin/env python3
"""Offline HTTP+WebSocket contract tests against a separately installed ASR skill.

Run with the Python environment containing the skill's requirements-realtime.txt.
"""
import base64
import io
import json
import os
from pathlib import Path
import select
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import uuid
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from websockets.sync.server import serve
from websockets.exceptions import ConnectionClosed

ROOT = Path(__file__).resolve().parents[3]
BASE = '/deviceapi/ai-services/v1/audio/transcriptions/realtime/sessions'
SID = str(uuid.uuid4())
TICKET = 'PRIVATE_TICKET_CANARY'
AUTH = 'Device ' + base64.b64encode(('0' * 16 + ':' + '1' * 32).encode()).decode()


def wav(rate=16000, duration=0.2):
    output = io.BytesIO()
    with wave.open(output, 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(b'\x01\x00' * int(rate * duration))
    return output.getvalue()


class RealtimeSkillTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.installed = self.directory / 'codecraft-asr'
        shutil.copytree(ROOT / 'skills/codecraft-asr', self.installed, ignore=shutil.ignore_patterns('__pycache__'))
        self.mode = 'normal'
        self.requests, self.frames, self.frame_times = [], [], []
        self.ws_requests = []
        self.server_errors = []
        owner = self

        def websocket(ws):
            try:
                owner.ws_requests.append((ws.request.path, dict(ws.request.headers)))
                auth = json.loads(ws.recv(timeout=2))
                owner.assertEqual(auth, {'type': 'session.authenticate', 'ticket': TICKET})
                if owner.mode == 'auth-error':
                    ws.send(json.dumps({'type': 'session.error', 'code': 2020, 'reason': 'invalid_ticket', 'ticket': TICKET}))
                    return
                ws.send(json.dumps({'type': 'session.ready', 'session_id': SID}))
                while True:
                    frame = ws.recv(timeout=3)
                    if isinstance(frame, bytes):
                        owner.frames.append(frame)
                        owner.frame_times.append(time.monotonic())
                        if owner.mode == 'disconnect':
                            ws.close(1011, 'PRIVATE_ERROR_CANARY')
                            return
                        if len(owner.frames) == 1:
                            for revision, text in [(2, '你好'), (1, '旧文本')]:
                                ws.send(json.dumps({'type': 'transcript.partial', 'segment_id': 1, 'revision': revision, 'text': text}))
                        continue
                    owner.assertEqual(json.loads(frame), {'type': 'input.finish'})
                    for event in [
                        {'type': 'transcript.final', 'segment_id': 1, 'revision': 3, 'text': '你好世界'},
                        {'type': 'transcript.final', 'segment_id': 1, 'revision': 3, 'text': '重复'},
                    ]:
                        ws.send(json.dumps(event))
                    # Final result must be drained after input.finish, not closed early.
                    time.sleep(0.03)
                    ws.send(json.dumps({'type': 'session.error' if owner.mode == 'error' else 'session.finished',
                                        'session_id': SID, 'code': 7020 if owner.mode == 'error' else 200,
                                        'charged_quota': 1000, 'billing_status': 'pending' if owner.mode == 'pending' else 'committed',
                                        'reason': 'completed', 'ticket': TICKET}))
                    return
            except ConnectionClosed:
                pass
            except Exception as error:
                owner.server_errors.append(error)

        self.wsserver = serve(websocket, '127.0.0.1', 0)
        self.wsthread = threading.Thread(target=self.wsserver.serve_forever, daemon=True)
        self.wsthread.start()
        wsport = self.wsserver.socket.getsockname()[1]

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def reply(self, data, status=200):
                body = json.dumps(data).encode()
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                data = self.rfile.read(int(self.headers.get('Content-Length', 0)))
                owner.requests.append(('POST', self.path, dict(self.headers), json.loads(data)))
                if owner.mode == 'http-error':
                    return self.reply({'message': 'PRIVATE_ERROR_CANARY'}, 503)
                if owner.mode == 'http-redirect':
                    self.send_response(307)
                    self.send_header('Location', owner.origin + '/stolen')
                    self.end_headers()
                    return
                session = {'session_id': SID, 'state': 'pending', 'billing_status': 'reserved', 'reserved_quota': 1000,
                           'charged_quota': 0, 'ticket': TICKET, 'stream_path': BASE + '/' + SID + '/stream'}
                if owner.mode == 'unsafe-path':
                    session['stream_path'] = 'ws://evil.invalid/steal?ticket=' + TICKET
                self.reply({'code': 200, 'data': session})

            def do_GET(self):
                if self.path.endswith('/stream'):
                    if owner.mode == 'ws-redirect':
                        self.send_response(302)
                        self.send_header('Location', 'ws://127.0.0.1:' + str(wsport) + '/stolen')
                        self.end_headers()
                        return
                    # Proxy the upgrade on the same origin to a real WS library server.
                    with socket.create_connection(('127.0.0.1', wsport)) as upstream:
                        upstream.sendall((self.requestline + '\r\n' + ''.join(f'{key}: {value}\r\n' for key, value in self.headers.items()) + '\r\n').encode())
                        while True:
                            readable, _, _ = select.select([upstream, self.connection], [], [], 5)
                            if not readable:
                                return
                            for source in readable:
                                data = source.recv(65536)
                                if not data:
                                    return
                                destination = self.connection if source is upstream else upstream
                                destination.sendall(data)
                    return
                owner.requests.append(('GET', self.path, dict(self.headers), None))
                self.reply({'code': 200, 'data': {'session_id': SID, 'state': 'finished', 'billing_status': 'committed',
                                                'charged_quota': 1000, 'ticket': TICKET}})

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.origin = 'http://127.0.0.1:' + str(self.server.server_port)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        credentials = self.directory / 'device.json'
        credentials.write_text(json.dumps({'eui': '0' * 16, 'deviceKey': '1' * 32}))
        self.env = dict(os.environ, CODECRAFT_API_ORIGIN=self.origin, CODECRAFT_DEVICE_FILE=str(credentials),
                        HTTP_PROXY='http://127.0.0.1:1', WS_PROXY='http://127.0.0.1:1')
        self.env.pop('PYTHONPATH', None)
        self.audio = self.directory / 'input.wav'
        self.audio.write_bytes(wav())

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.wsserver.shutdown()
        self.wsthread.join()
        self.temp.cleanup()
        self.assertEqual(self.server_errors, [])

    def invoke(self, *args, isolated=False):
        command = [sys.executable]
        if isolated:
            command += ['-S']  # status/recover/help must work without optional packages.
        result = subprocess.run(command + [str(self.installed / 'scripts/realtime.py'), *map(str, args)],
                                cwd=self.directory, env=self.env, capture_output=True, text=True, timeout=10)
        self.assertEqual(list(self.installed.rglob('__pycache__')), [])
        for private in (TICKET, AUTH, 'PRIVATE_ERROR_CANARY'):
            self.assertNotIn(private, result.stdout + result.stderr)
        for _, _, headers, _ in self.requests:
            self.assertEqual(headers['Authorization'], AUTH)
        for path, headers in self.ws_requests:
            self.assertEqual(path, BASE + '/' + SID + '/stream')
            self.assertNotIn('authorization', headers)
        return result

    def start(self, **kwargs):
        return self.invoke('stream', '--file', self.audio, **kwargs)

    def test_paced_stream_final_drain_revisions_and_independent_install(self):
        result = self.start()
        self.assertEqual(result.returncode, 0, result.stderr)
        events = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(events[-1], {'type': 'transcript.result', 'text': '你好世界'})
        self.assertEqual(sum(e['type'] == 'transcript.partial' for e in events), 1)
        self.assertEqual(sum(e['type'] == 'transcript.final' for e in events), 1)
        self.assertEqual(b''.join(self.frames), b'\x01\x00' * 3200)
        self.assertEqual([len(frame) for frame in self.frames], [3200, 3200])
        self.assertGreater(self.frame_times[1] - self.frame_times[0], 0.075)
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(self.requests[0][3], {'audio': {'format': 'pcm_s16le', 'sample_rate': 16000, 'channels': 1}, 'max_audio_seconds': 60})
        key = json.loads(result.stderr.splitlines()[0])['idempotency_key']
        self.assertEqual(self.requests[0][2]['Idempotency-Key'], key)

    def test_raw_pcm(self):
        self.audio.write_bytes(b'\x02\x00' * 160)
        result = self.invoke('stream', '--file', self.audio, '--raw-pcm')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(b''.join(self.frames), self.audio.read_bytes())

    def test_status_and_recover_without_websocket_dependency(self):
        result = self.invoke('status', '--session-id', SID, isolated=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['charged_quota'], 1000)
        result = self.invoke('recover', '--idempotency-key', 'original-key-123', isolated=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.requests[-1][2]['Idempotency-Key'], 'original-key-123')
        self.assertEqual(self.ws_requests, [])
        self.assertEqual([r[0] for r in self.requests], ['GET', 'POST'])

    def test_validation_before_reservation(self):
        for data in [wav(8000), wav(duration=61), b'RIFFinvalid']:
            self.audio.write_bytes(data)
            self.assertNotEqual(self.start().returncode, 0)
        self.audio.write_bytes(b'odd')
        self.assertNotEqual(self.invoke('stream', '--file', self.audio, '--raw-pcm').returncode, 0)
        self.audio.write_bytes(wav())
        self.assertNotEqual(self.start(isolated=True).returncode, 0)
        self.assertNotEqual(self.invoke('stream', '--file', self.audio, '--idempotency-key', 'bad\nheader').returncode, 0)
        self.assertNotEqual(self.invoke('status', '--session-id', '../escape').returncode, 0)
        self.assertEqual(self.requests, [])

    def test_no_retry_or_replay_on_network_and_terminal_failures(self):
        for mode in ['disconnect', 'error', 'pending', 'auth-error']:
            with self.subTest(mode=mode):
                self.mode = mode
                before = len(self.requests)
                connections = len(self.ws_requests)
                result = self.start()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(len(self.ws_requests), connections + 1)
                self.assertNotIn('transcript.result', result.stdout)
                self.assertEqual(len(self.requests), before + 1)

    def test_redirects_and_untrusted_stream_paths_rejected(self):
        for mode in ['http-error', 'http-redirect', 'ws-redirect', 'unsafe-path']:
            with self.subTest(mode=mode):
                self.mode = mode
                before = len(self.requests)
                result = self.start()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(len(self.requests), before + 1)
        self.assertEqual(self.ws_requests, [])
        self.assertEqual(self.frames, [])


if __name__ == '__main__':
    unittest.main()
