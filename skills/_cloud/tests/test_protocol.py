"""Offline protocol tests. Each Skill is copied alone and run outside this repository."""
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import wave

ROOT = Path(__file__).resolve().parents[3]
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jXioAAAAASUVORK5CYII=')
ASSET = '00112233-4455-6677-8899-aabbccddeeff'


def wav(seconds=1):
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(bytes(32000 * seconds))
    return buffer.getvalue()


class SkillTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.requests = []
        self.mode = 'normal'
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                self.do_POST()

            def do_POST(self):
                data = self.rfile.read(int(self.headers.get('Content-Length', 0)))
                owner.requests.append((self.path, self.headers.get('Authorization'), data))
                status, content_type, response = 200, 'application/json', b''
                if owner.mode == 'redirect':
                    self.send_response(302)
                    self.send_header('Location', owner.origin + '/stolen')
                    self.end_headers()
                    return
                if owner.mode == 'denied':
                    status, response = 401, b'PRIVATE_CANARY_WITH_CREDENTIALS'
                elif self.path.endswith('/chat/completions'):
                    payload = json.loads(data)
                    if payload['stream']:
                        content_type = 'text/event-stream'
                        response = b'data: {"choices":[{"delta":{"content":"hello"}}]}\n\n'
                        if owner.mode != 'incomplete':
                            response += b'data: [DONE]\n\n'
                    else:
                        response = json.dumps({'choices': [{'message': {'content': 'hello'}}], 'usage': {'total_tokens': 2}}).encode()
                elif self.path.endswith('/audio/speech'):
                    content_type, response = 'audio/wav', wav()
                elif self.path.endswith('/audio/transcriptions'):
                    response = b'{"text":"hello"}'
                elif self.path.endswith('/images/generations'):
                    response = json.dumps({'data': [{'b64_json': base64.b64encode(PNG).decode()}]}).encode()
                elif self.path == '/deviceapi/media-assets/v1/files':
                    if owner.mode == 'archive-fail':
                        status, response = 503, b'PRIVATE_CANARY_WITH_CREDENTIALS'
                    else:
                        response = json.dumps({'code': 200, 'data': {'id': ASSET,
                            'content_url': '/deviceapi/media-assets/v1/files/' + ASSET + '/content',
                            'url': 'https://private.example/?signature=SECRET_CANARY'}}).encode()
                elif self.path.endswith('/content'):
                    content_type, response = 'image/png', PNG
                else:
                    status = 404
                self.send_response(status)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(response)))
                self.end_headers()
                self.wfile.write(response)

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.origin = 'http://127.0.0.1:' + str(self.server.server_port)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        credentials = self.directory / 'device.json'
        credentials.write_text(json.dumps({'eui': '0' * 16, 'deviceKey': '1' * 32}))
        self.env = dict(os.environ, CODECRAFT_API_ORIGIN=self.origin, CODECRAFT_DEVICE_FILE=str(credentials))
        self.env.pop('PYTHONPATH', None)
        self.prompt = self.directory / 'prompt.txt'
        self.prompt.write_text('Hello device cloud.')
        self.audio = self.directory / 'input.wav'
        self.audio.write_bytes(wav())

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def invoke(self, skill, script, *arguments, env=None):
        # Only this skill is installed; no sibling skill or repository helper exists.
        destination = self.directory / 'installed' / skill
        if not destination.exists():
            shutil.copytree(ROOT / 'skills' / skill, destination, ignore=shutil.ignore_patterns('__pycache__'))
        result = subprocess.run([sys.executable, str(destination / 'scripts' / script), *map(str, arguments)],
                                env=env or self.env, cwd=self.directory, capture_output=True, text=True, timeout=10)
        self.assertNotIn('PRIVATE_CANARY', result.stdout + result.stderr)
        self.assertNotIn('SECRET_CANARY', result.stdout + result.stderr)
        expected = 'Device ' + base64.b64encode(('0' * 16 + ':' + '1' * 32).encode()).decode()
        self.assertNotIn(expected, result.stdout + result.stderr)
        for _, authorization, _ in self.requests:
            self.assertEqual(authorization, expected)
        return result

    def test_llm_json_and_sse(self):
        result = self.invoke('codecraft-llm', 'llm.py', '--prompt-file', self.prompt)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['text'], 'hello')
        payload = json.loads(self.requests[0][2])
        self.assertEqual(payload['model'], 'qwen-plus')
        self.assertEqual(payload['max_tokens'], 256)
        result = self.invoke('codecraft-llm', 'llm.py', '--prompt-file', self.prompt, '--stream')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'hello')

    def test_incomplete_sse_is_not_retried(self):
        self.mode = 'incomplete'
        result = self.invoke('codecraft-llm', 'llm.py', '--prompt-file', self.prompt, '--stream')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, 'hello')
        self.assertEqual(len(self.requests), 1)

    def test_transcription_and_local_duration_validation(self):
        result = self.invoke('codecraft-asr', 'transcribe.py', '--file', self.audio)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['text'], 'hello')
        self.assertIn(b'qwen-audio-3.0-asr-flash', self.requests[0][2])
        self.assertIn(wav(), self.requests[0][2])
        self.audio.write_bytes(wav(61))
        result = self.invoke('codecraft-asr', 'transcribe.py', '--file', self.audio)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(self.requests), 1)
        self.audio.write_bytes(b'RIFFinvalid')
        result = self.invoke('codecraft-asr', 'transcribe.py', '--file', self.audio)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(self.requests), 1)

    def test_tts_archive_and_existing_output(self):
        output = self.directory / 'speech.wav'
        result = self.invoke('codecraft-tts', 'speak.py', '--text-file', self.prompt, '--output', output, '--archive')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_bytes(), wav())
        self.assertEqual(json.loads(result.stdout)['content_url'], self.origin + '/deviceapi/media-assets/v1/files/' + ASSET + '/content')
        self.assertEqual(json.loads(self.requests[0][2])['response_format'], 'wav')
        result = self.invoke('codecraft-tts', 'speak.py', '--text-file', self.prompt, '--output', output)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(self.requests), 2)
        self.assertEqual(output.read_bytes(), wav())

    def test_archive_failure_retains_generated_file(self):
        self.mode = 'archive-fail'
        output = self.directory / 'speech.wav'
        result = self.invoke('codecraft-tts', 'speak.py', '--text-file', self.prompt, '--output', output, '--archive')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_bytes(), wav())
        self.assertEqual(json.loads(result.stdout)['file'], str(output.resolve()))
        self.assertEqual(len(self.requests), 2)
        self.mode = 'normal'
        result = self.invoke('codecraft-tts', 'device_api.py', 'archive', '--file', output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sum(path.endswith('/audio/speech') for path, _, _ in self.requests), 1)

    def test_image_generation_and_stable_download(self):
        output = self.directory / 'image.png'
        result = self.invoke('codecraft-image-generation', 'generate.py', '--prompt-file', self.prompt, '--output', output, '--archive')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_bytes(), PNG)
        payload = json.loads(self.requests[0][2])
        self.assertEqual((payload['model'], payload['n'], payload['size'], payload['response_format']), ('qwen-image-2.0', 1, '1024x1024', 'b64_json'))
        downloaded = self.directory / 'download.png'
        result = self.invoke('codecraft-image-generation', 'device_api.py', 'download', '--asset-id', ASSET, '--output', downloaded)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(downloaded.read_bytes(), PNG)

    def test_text_limits_reject_before_network(self):
        self.prompt.write_text('字' * 501)
        result = self.invoke('codecraft-tts', 'speak.py', '--text-file', self.prompt, '--output', self.directory / 'speech.wav')
        self.assertNotEqual(result.returncode, 0)
        self.prompt.write_text('字' * 2001)
        result = self.invoke('codecraft-image-generation', 'generate.py', '--prompt-file', self.prompt, '--output', self.directory / 'image.png')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.requests, [])

    def test_unsafe_origins_reject_before_network(self):
        for origin in ['http://remote.example', self.origin + '/other', self.origin + '?key=private', 'https://user:password@example.com']:
            result = self.invoke('codecraft-llm', 'llm.py', '--prompt-file', self.prompt, env=dict(self.env, CODECRAFT_API_ORIGIN=origin))
            self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.requests, [])

    def test_redirect_and_error_body_do_not_leak_credentials(self):
        for mode in ['redirect', 'denied']:
            self.mode = mode
            before = len(self.requests)
            result = self.invoke('codecraft-llm', 'llm.py', '--prompt-file', self.prompt)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(len(self.requests), before + 1)
        self.assertFalse(any(path == '/stolen' for path, _, _ in self.requests))


if __name__ == '__main__':
    unittest.main()
