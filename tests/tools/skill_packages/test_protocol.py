"""Offline protocol tests. Each Skill is copied alone and run outside this repository."""
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import struct
import zlib
import sys
import tempfile
import threading
import unittest
import wave

ROOT = Path(__file__).resolve().parents[3]
def png(width=1024, height=1024):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    header = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    pixels = (b'\0' + b'\x20\x80\xc0' * width) * height
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header) + chunk(b'IDAT', zlib.compress(pixels)) + chunk(b'IEND', b'')


PNG = png()

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
                        reason = {'llm-length': 'length', 'llm-filter': 'content_filter', 'llm-no-finish': None}.get(owner.mode, 'stop')
                        response = ('data: ' + json.dumps({'choices': [{'delta': {'content': 'hello'}, 'finish_reason': reason}]}) + '\n\n').encode()
                        if owner.mode != 'incomplete':
                            response += b'data: [DONE]\n\n'
                    else:
                        response = json.dumps({'choices': [{'message': {'content': 'hello'}, 'finish_reason': {'llm-length': 'length', 'llm-filter': 'content_filter', 'llm-no-finish': None}.get(owner.mode, 'stop')}], 'usage': {'total_tokens': 2}}).encode()
                elif self.path.endswith('/audio/speech'):
                    content_type, response = 'audio/wav', wav()
                    if owner.mode in ('short-body', 'truncated-wav'):
                        response = response[:100]
                    elif owner.mode == 'bad-pcm':
                        response = bytearray(response)
                        struct.pack_into('<I', response, 28, 1)
                        response = bytes(response)
                elif self.path.endswith('/audio/transcriptions'):
                    response = b'{"text":"hello"}'
                elif self.path.endswith('/images/generations'):
                    payload = json.loads(data)
                    size = tuple(map(int, payload['size'].split('x')))
                    content = png(*size)
                    if owner.mode == 'image-header':
                        content = content[:8]
                    elif owner.mode == 'image-truncated':
                        content = content[:-20]
                    elif owner.mode == 'image-corrupt':
                        content = content[:-16] + bytes([content[-16] ^ 1]) + content[-15:]
                    elif owner.mode == 'image-wrong-size':
                        content = png(512, 512)
                    elif owner.mode in ('image-jpeg', 'image-webp', 'image-jpeg-truncated', 'image-webp-truncated'):
                        from PIL import Image
                        buffer = io.BytesIO()
                        Image.new('RGB', size, 'blue').save(buffer, format=owner.mode.split('-')[1].upper())
                        content = buffer.getvalue()
                        if owner.mode.endswith('-truncated'):
                            content = content[:-20]
                    response = json.dumps({'data': [{'b64_json': base64.b64encode(content).decode()}]}).encode()
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
                self.send_header('Content-Length', str(len(response) + (1000 if owner.mode == 'short-body' else 0)))
                self.send_header('Connection', 'close')
                self.close_connection = True
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

    def invoke(self, skill, script, *arguments, env=None, python_flags=()):
        # Only this skill is installed; no sibling skill or repository helper exists.
        destination = self.directory / 'installed' / skill
        if not destination.exists():
            shutil.copytree(ROOT / 'skills' / skill, destination, ignore=shutil.ignore_patterns('__pycache__'))
        result = subprocess.run([sys.executable, *python_flags, str(destination / 'scripts' / script), *map(str, arguments)],
                                env=env or self.env, cwd=self.directory, capture_output=True, text=True, timeout=10)
        self.assertEqual(list(destination.rglob('__pycache__')), [])
        self.assertNotIn('PRIVATE_CANARY', result.stdout + result.stderr)
        self.assertNotIn('SECRET_CANARY', result.stdout + result.stderr)
        expected = 'Device ' + base64.b64encode(('0' * 16 + ':' + '1' * 32).encode()).decode()
        self.assertNotIn(expected, result.stdout + result.stderr)
        for _, authorization, _ in self.requests:
            self.assertEqual(authorization, expected)
        return result

    def test_public_packages_do_not_disclose_implementations(self):
        forbidden = re.compile(r'qwen|paraformer|dashscope|cosyvoice|z-image|Cherry|APISIX|Bifrost|New API', re.I)
        packages = [path.parent for path in (ROOT / 'skills').glob('*/contract.json')]
        self.assertTrue(packages, 'No public packages were scanned')
        for path in (path for package in packages for path in package.rglob('*')):
            if path.is_file():
                self.assertNotIn(path.suffix, ('.pyc', '.pyo'))
                self.assertNotIn('__pycache__', path.parts)
                self.assertIsNone(forbidden.search(path.read_text()), str(path))

    def test_llm_json_and_sse(self):
        result = self.invoke('codecraft-capabilities-llm', 'llm.py', '--prompt-file', self.prompt)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['text'], 'hello')
        payload = json.loads(self.requests[0][2])
        self.assertNotIn('model', payload)
        self.assertEqual(payload['max_tokens'], 256)
        result = self.invoke('codecraft-capabilities-llm', 'llm.py', '--prompt-file', self.prompt, '--stream')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'hello')

    def test_incomplete_sse_is_not_retried(self):
        self.mode = 'incomplete'
        result = self.invoke('codecraft-capabilities-llm', 'llm.py', '--prompt-file', self.prompt, '--stream')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, 'hello')
        self.assertEqual(len(self.requests), 1)

    def test_transcription_and_local_duration_validation(self):
        result = self.invoke('codecraft-capabilities-asr', 'transcribe.py', '--file', self.audio)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['text'], 'hello')
        self.assertNotIn(b'name="model"', self.requests[0][2])
        self.assertIn(wav(), self.requests[0][2])
        self.audio.write_bytes(wav(61))
        result = self.invoke('codecraft-capabilities-asr', 'transcribe.py', '--file', self.audio)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(self.requests), 1)
        self.audio.write_bytes(b'RIFFinvalid')
        result = self.invoke('codecraft-capabilities-asr', 'transcribe.py', '--file', self.audio)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(self.requests), 1)

    def test_tts_archive_and_existing_output(self):
        output = self.directory / 'speech.wav'
        result = self.invoke('codecraft-capabilities-tts', 'speak.py', '--text-file', self.prompt, '--output', output, '--archive')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_bytes(), wav())
        self.assertEqual(json.loads(result.stdout)['content_url'], self.origin + '/deviceapi/media-assets/v1/files/' + ASSET + '/content')
        self.assertEqual(json.loads(self.requests[0][2])['response_format'], 'wav')
        result = self.invoke('codecraft-capabilities-tts', 'speak.py', '--text-file', self.prompt, '--output', output)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(self.requests), 2)
        self.assertEqual(output.read_bytes(), wav())

    def test_archive_failure_retains_generated_file(self):
        self.mode = 'archive-fail'
        output = self.directory / 'speech.wav'
        result = self.invoke('codecraft-capabilities-tts', 'speak.py', '--text-file', self.prompt, '--output', output, '--archive')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_bytes(), wav())
        self.assertEqual(json.loads(result.stdout)['file'], str(output.resolve()))
        self.assertEqual(len(self.requests), 2)
        self.mode = 'normal'
        result = self.invoke('codecraft-capabilities-tts', 'device_api.py', 'archive', '--file', output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sum(path.endswith('/audio/speech') for path, _, _ in self.requests), 1)

    def test_image_generation_and_stable_download(self):
        output = self.directory / 'image.png'
        result = self.invoke('codecraft-capabilities-image-generation', 'generate.py', '--prompt-file', self.prompt, '--output', output, '--archive')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_bytes(), PNG)
        payload = json.loads(self.requests[0][2])
        self.assertNotIn('model', payload)
        self.assertEqual((payload['n'], payload['size'], payload['response_format']), (1, '1024x1024', 'b64_json'))
        downloaded = self.directory / 'download.png'
        result = self.invoke('codecraft-capabilities-image-generation', 'device_api.py', 'download', '--asset-id', ASSET, '--output', downloaded)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(downloaded.read_bytes(), PNG)

    def test_text_limits_reject_before_network(self):
        self.prompt.write_text('字' * 501)
        result = self.invoke('codecraft-capabilities-tts', 'speak.py', '--text-file', self.prompt, '--output', self.directory / 'speech.wav')
        self.assertNotEqual(result.returncode, 0)
        self.prompt.write_text('字' * 2001)
        result = self.invoke('codecraft-capabilities-image-generation', 'generate.py', '--prompt-file', self.prompt, '--output', self.directory / 'image.png')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.requests, [])

    def test_unsafe_origins_reject_before_network(self):
        for origin in ['http://remote.example', self.origin + '/other', self.origin + '?key=private', 'https://user:password@example.com']:
            result = self.invoke('codecraft-capabilities-llm', 'llm.py', '--prompt-file', self.prompt, env=dict(self.env, CODECRAFT_API_ORIGIN=origin))
            self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.requests, [])

    def test_redirect_and_error_body_do_not_leak_credentials(self):
        for mode in ['redirect', 'denied']:
            self.mode = mode
            before = len(self.requests)
            result = self.invoke('codecraft-capabilities-llm', 'llm.py', '--prompt-file', self.prompt)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(len(self.requests), before + 1)
        self.assertFalse(any(path == '/stolen' for path, _, _ in self.requests))


    def test_llm_incomplete_finish_status_preserves_text_but_fails(self):
        for mode in ('llm-length', 'llm-filter', 'llm-no-finish'):
            self.mode = mode
            for flags in ((), ('--stream',)):
                before = len(self.requests)
                result = self.invoke('codecraft-capabilities-llm', 'llm.py', '--prompt-file', self.prompt, *flags)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('hello', result.stdout)
                if not flags:
                    self.assertFalse(json.loads(result.stdout)['complete'])
                self.assertEqual(len(self.requests), before + 1)

    def test_short_http_body_rejects_output_and_archive_without_retry(self):
        self.mode = 'short-body'
        for skill, script, arguments in (
            ('codecraft-capabilities-tts', 'speak.py', ('--text-file', self.prompt, '--archive')),
            ('codecraft-capabilities-image-generation', 'generate.py', ('--prompt-file', self.prompt, '--archive')),
            ('codecraft-capabilities-tts', 'device_api.py', ('download', '--asset-id', ASSET)),
        ):
            output = self.directory / (skill + script + '.bin')
            before = len(self.requests)
            result = self.invoke(skill, script, *arguments, '--output', output)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())
            self.assertEqual(len(self.requests), before + 1)
        self.assertFalse(any(path == '/deviceapi/media-assets/v1/files' for path, _, _ in self.requests))

    def test_tts_corrupt_wav_rejected_with_complete_http_body(self):
        for mode in ('truncated-wav', 'bad-pcm'):
            self.mode = mode
            output = self.directory / (mode + '.wav')
            before = len(self.requests)
            result = self.invoke('codecraft-capabilities-tts', 'speak.py', '--text-file', self.prompt, '--output', output, '--archive')
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())
            self.assertEqual(len(self.requests), before + 1)

    def test_image_corruption_and_dimension_mismatch_do_not_archive(self):
        for mode in ('image-header', 'image-truncated', 'image-corrupt', 'image-wrong-size', 'image-jpeg-truncated', 'image-webp-truncated'):
            self.mode = mode
            output = self.directory / (mode + '.png')
            before = len(self.requests)
            result = self.invoke('codecraft-capabilities-image-generation', 'generate.py', '--prompt-file', self.prompt, '--output', output, '--archive')
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())
            self.assertEqual(len(self.requests), before + 1)

    def test_custom_image_sizes_and_decoders(self):
        for size in ('800x480', '512x512', '2048x2048', '2688x1536', '1536x2688'):
            output = self.directory / (size + '.png')
            result = self.invoke('codecraft-capabilities-image-generation', 'generate.py', '--prompt-file', self.prompt, '--size', size, '--output', output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(self.requests[-1][2])['size'], size)
            self.assertEqual(output.read_bytes(), png(*map(int, size.split('x'))))
        for mode in ('image-jpeg', 'image-webp'):
            self.mode = mode
            result = self.invoke('codecraft-capabilities-image-generation', 'generate.py', '--prompt-file', self.prompt, '--output', self.directory / mode)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_image_invalid_size_and_missing_decoder_fail_before_billing(self):
        for size in ('0x512', '-512x512', '1x1', '4096x4096', '1024*1024', '1024X1024', ' 512x512', '0512x512', '99999999999999999999x1'):
            result = self.invoke('codecraft-capabilities-image-generation', 'generate.py', '--prompt-file', self.prompt, '--size=' + size, '--output', self.directory / 'never.png')
            self.assertNotEqual(result.returncode, 0)
        result = self.invoke('codecraft-capabilities-image-generation', 'generate.py', '--prompt-file', self.prompt, '--output', self.directory / 'never.png', python_flags=('-S',))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.requests, [])
        self.assertFalse((self.directory / 'never.png').exists())


if __name__ == '__main__':
    unittest.main()
