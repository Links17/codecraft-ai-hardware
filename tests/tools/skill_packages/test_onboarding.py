"""Offline onboarding behavior and portable C authentication tests."""
import base64
import ctypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[3]
SKILLS = ('codecraft-capabilities-llm', 'codecraft-capabilities-asr', 'codecraft-capabilities-tts', 'codecraft-capabilities-image-generation')
EUI = '0123456789ABCDEF'
KEY = 'abcdef0123456789ABCDEF0123456789'
AUTH = 'Device ' + base64.b64encode((EUI + ':' + KEY).encode()).decode()


class OnboardingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='codecraft onboarding ')
        self.directory = Path(self.temp.name)
        self.response = {'code': 200, 'data': {'eui': EUI, 'initial_quota': 500000}}
        self.status = 200
        self.calls = []
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                owner.calls.append((self.path, self.headers.get('Authorization')))
                data = json.dumps(owner.response).encode()
                self.send_response(owner.status)
                if owner.status == 302:
                    self.send_header('Location', owner.origin + '/unexpected')
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.origin = 'http://127.0.0.1:' + str(self.server.server_port)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.credentials = self.directory / 'device.json'
        self.credentials.write_text(json.dumps({'eui': EUI, 'deviceKey': KEY}))
        self.env = dict(os.environ, CODECRAFT_API_ORIGIN=self.origin,
                        CODECRAFT_DEVICE_FILE=str(self.credentials))
        self.env.pop('PYTHONPATH', None)
        for name in SKILLS:
            shutil.copytree(ROOT / 'skills' / name, self.directory / name,
                            ignore=shutil.ignore_patterns('__pycache__'))

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def invoke(self, *args, skill=SKILLS[0], env=None):
        result = subprocess.run([sys.executable, '-S', 'scripts/device_credentials.py', *args],
                                cwd=self.directory / skill, env=self.env if env is None else env,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(list((self.directory / skill).rglob('__pycache__')), [])
        for secret in (KEY, AUTH, 'EXTRA_SECRET_CANARY'):
            self.assertNotIn(secret, result.stdout + result.stderr)
        return result

    def test_each_standalone_package_import_and_check(self):
        source = self.directory / 'cli.json'
        source.write_text(json.dumps({'eui': EUI, 'device_key': KEY, 'token': 'EXTRA_SECRET_CANARY'}))
        for name in SKILLS:
            with self.subTest(skill=name):
                dest = self.directory / (name + '.json')
                result = self.invoke('import', '--input', str(source), '--output', str(dest), skill=name)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(dest.read_text()), {'eui': EUI, 'deviceKey': KEY})
                self.assertEqual(dest.stat().st_mode & 0o777, 0o600)
                self.assertEqual(len(self.calls), SKILLS.index(name))
                result = self.invoke('check', skill=name, env=dict(self.env, CODECRAFT_DEVICE_FILE=str(dest)))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), {'authenticated': True, 'identity_matches': True,
                    'initial_quota': 500000, 'initial_quota_is_remaining_balance': False})
                self.assertEqual(self.calls[-1], ('/deviceapi/device-management/v1/device', AUTH))

    def test_import_rejects_bad_inputs_and_existing_output(self):
        source = self.directory / 'cli.json'
        destination = self.directory / 'new.json'
        for data in ([], {}, {'eui': EUI, 'deviceKey': KEY}, {'eui': 'X' * 16, 'device_key': KEY},
                     {'eui': EUI, 'device_key': 'short'}, {'eui': EUI, 'device_key': None}):
            source.write_text(json.dumps(data))
            result = self.invoke('import', '--input', str(source), '--output', str(destination))
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(destination.exists())
        source.write_text('{"eui":')
        self.assertNotEqual(self.invoke('import', '--input', str(source), '--output', str(destination)).returncode, 0)
        source.write_text(json.dumps({'eui': EUI, 'device_key': KEY}))
        destination.write_text('preserve')
        self.assertNotEqual(self.invoke('import', '--input', str(source), '--output', str(destination)).returncode, 0)
        self.assertEqual(destination.read_text(), 'preserve')
        self.assertEqual(self.calls, [])

    def test_check_rejects_business_failure_identity_and_invalid_profile(self):
        for response in ({'code': 11201, 'msg': 'EXTRA_SECRET_CANARY'},
                         {'code': '200', 'data': {'eui': EUI, 'initial_quota': 500000}},
                         {'code': 200, 'data': {'eui': 'F' * 16, 'initial_quota': 500000}},
                         {'code': 200, 'data': {'eui': EUI, 'initial_quota': True}},
                         {'code': 200, 'data': {'eui': EUI, 'initial_quota': -1}},
                         {'code': 200, 'data': {'eui': EUI}}, []):
            self.response = response
            count = len(self.calls)
            self.assertNotEqual(self.invoke('check').returncode, 0)
            self.assertEqual(len(self.calls), count + 1)

    def test_check_no_redirect_or_retry_or_error_body_leak(self):
        self.response = {'error': 'EXTRA_SECRET_CANARY'}
        for status in (302, 401, 403, 429, 503):
            self.status = status
            count = len(self.calls)
            self.assertNotEqual(self.invoke('check').returncode, 0)
            self.assertEqual(len(self.calls), count + 1)

    def test_curl_config_is_private_local_and_usable(self):
        destination = self.directory / 'device-curl.conf'
        result = self.invoke('curl-config', '--output', str(destination))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls, [])
        self.assertEqual(destination.stat().st_mode & 0o777, 0o600)
        self.assertEqual(destination.read_text(), 'header = "Authorization: ' + AUTH + '"\n')
        self.assertNotEqual(self.invoke('curl-config', '--output', str(destination)).returncode, 0)
        # HTTP is used only against this isolated loopback test server.
        result = subprocess.run(['curl', '-q', '--config', str(destination), '--noproxy', '*',
                                 '--max-time', '3', '--fail', '--silent', '--show-error',
                                 self.origin + '/deviceapi/device-management/v1/device'],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls, [('/deviceapi/device-management/v1/device', AUTH)])
        self.assertEqual(json.loads(result.stdout), self.response)

    def test_help_and_import_do_not_require_api_configuration_or_dependencies(self):
        env = dict(os.environ)
        for key in ('CODECRAFT_API_ORIGIN', 'CODECRAFT_DEVICE_FILE', 'PYTHONPATH'):
            env.pop(key, None)
        for name in SKILLS:
            self.assertEqual(self.invoke('--help', skill=name, env=env).returncode, 0)
        source = self.directory / 'cli.json'
        source.write_text(json.dumps({'eui': EUI, 'device_key': KEY}))
        self.assertEqual(self.invoke('import', '--input', str(source), '--output',
                                    str(self.directory / 'imported.json'), env=env).returncode, 0)
        self.assertEqual(self.calls, [])


class PortableAuthTests(unittest.TestCase):
    def test_c_and_cpp_encoding_vectors_and_bounds(self):
        with tempfile.TemporaryDirectory(prefix='codecraft C auth ') as directory:
            root = Path(directory)
            shutil.copy(ROOT / 'skills/codecraft-capabilities-llm/assets/device_auth.h', root)
            source = root / 'auth.c'
            source.write_text('''#include "device_auth.h"
#ifdef __cplusplus
extern "C"
#endif
int encode(const char *eui, const char *key, char *out, size_t size) {
    return codecraft_device_authorization(eui, key, out, size);
}
''')
            rng = random.Random(42)
            for compiler, language, standard in (('cc', 'c', 'c99'), ('c++', 'c++', 'c++11')):
                library = root / ('auth-' + language + '.so')
                subprocess.run([compiler, '-x', language, '-std=' + standard, '-Wall', '-Wextra',
                                '-Werror', '-pedantic', '-shared', '-fPIC', str(source), '-o', str(library)],
                               check=True, capture_output=True, text=True)
                lib = ctypes.CDLL(str(library))
                encode = lib.encode
                encode.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_size_t]
                encode.restype = ctypes.c_int
                for i in range(100):
                    eui = ''.join(rng.choice('0123456789aAbBcCdDeEfF') for _ in range(16)).encode()
                    key = ''.join(rng.choice('0123456789aAbBcCdDeEfF') for _ in range(32)).encode()
                    out = ctypes.create_string_buffer(b'!' * 80, 81)
                    self.assertEqual(encode(eui, key, out, 76), 1)
                    self.assertEqual(out.value, b'Device ' + base64.b64encode(eui + b':' + key))
                    self.assertEqual(out.raw[76:80], b'!!!!')
                for eui, key in ((None, KEY.encode()), (b'', KEY.encode()), (b'F' * 15, KEY.encode()),
                                 (b'F' * 17, KEY.encode()), (EUI.encode(), None),
                                 (EUI.encode(), b'Z' * 32), (EUI.encode(), b'F' * 31),
                                 (EUI.encode(), b'F' * 33)):
                    out = ctypes.create_string_buffer(76)
                    self.assertEqual(encode(eui, key, out, 76), 0)
                    self.assertEqual(out.value, b'')
                for capacity in (0, 1, 75):
                    out = ctypes.create_string_buffer(b'!' * 80, 81)
                    self.assertEqual(encode(EUI.encode(), KEY.encode(), out, capacity), 0)
                    self.assertEqual(out.raw[max(1, capacity):80], b'!' * (80 - max(1, capacity)))
                    self.assertEqual(out.raw[0:1], b'!' if capacity == 0 else b'\0')
                self.assertEqual(encode(EUI.encode(), KEY.encode(), None, 76), 0)


if __name__ == '__main__':
    unittest.main()
