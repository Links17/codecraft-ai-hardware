"""Shared standard-library client, copied into each independently installable skill.

Edit this source and run tools/skills/sync_helpers.py; never import across skills.
"""
import argparse
import base64
import contextlib
import http.client
import json
import os
from pathlib import Path
import re
import sys
import struct
import urllib.error
import urllib.parse
import urllib.request
import uuid

MAX_FILE = 20 * 1024 * 1024


class SkillError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_bytes(path, maximum=MAX_FILE):
    with open(Path(path).expanduser(), 'rb') as source:
        data = source.read(maximum + 1)
    if not data or len(data) > maximum:
        raise SkillError(f'Input must contain 1..{maximum} bytes.')
    return data


def read_text(path, maximum=65536):
    try:
        return read_bytes(path, maximum).decode('utf-8')
    except UnicodeError:
        raise SkillError('Input text must be UTF-8.') from None


def decode_json(data):
    try:
        result = json.loads(data)
    except (ValueError, UnicodeError):
        raise SkillError('API returned invalid JSON; no automatic retry.') from None
    if not isinstance(result, dict) or 'error' in result:
        raise SkillError('API reported a failure; no automatic retry.')
    return result


def read_response(response, maximum):
    """Reject incomplete fixed-length bodies as well as oversized responses."""
    expected = None
    length = response.headers.get('Content-Length')
    if length is not None and not getattr(response, 'chunked', False):
        if not re.fullmatch(r'[0-9]+', length.strip()):
            raise SkillError('Invalid response length; no automatic retry.')
        expected = int(length)
        if expected > maximum:
            raise SkillError('API response exceeds the local size limit; no automatic retry.')
    data = response.read(maximum + 1)
    if len(data) > maximum:
        raise SkillError('API response exceeds the local size limit; no automatic retry.')
    if expected is not None and len(data) != expected:
        raise SkillError('Response interrupted; received fewer bytes than declared. Outcome and charge may be uncertain; no automatic retry.')
    return data


def validate_pcm_wav(data, max_seconds=None, max_bytes=MAX_FILE):
    """Validate the complete RIFF container and PCM payload, without repairing it."""
    if (len(data) < 44 or len(data) > max_bytes or data[:4] != b'RIFF'
            or data[8:12] != b'WAVE' or struct.unpack_from('<I', data, 4)[0] + 8 != len(data)):
        raise SkillError('Expected a complete PCM WAV with accurate chunk lengths.')
    offset, formats, chunks, byte_rate, pcm_size = 12, 0, 0, 0, 0
    while offset + 8 <= len(data):
        kind = data[offset:offset + 4]
        size = struct.unpack_from('<I', data, offset + 4)[0]
        start = offset + 8
        end = start + size
        if end > len(data):
            raise SkillError('WAV contains a truncated chunk.')
        if kind == b'fmt ':
            if size < 16:
                raise SkillError('WAV format chunk is incomplete.')
            encoding, channels, frequency, byte_rate, align, bits = struct.unpack_from('<HHIIHH', data, start)
            if encoding != 1 or channels != 1 or bits != 16 or not 8000 <= frequency <= 48000 or byte_rate != frequency * 2 or align != 2:
                raise SkillError('Expected mono PCM 16-bit WAV at 8-48 kHz.')
            formats += 1
        elif kind == b'data':
            pcm_size += size
            chunks += 1
        offset = end + size % 2
    if offset != len(data) or formats != 1 or chunks != 1 or not byte_rate or not pcm_size or pcm_size % 2:
        raise SkillError('WAV requires one complete PCM data chunk with valid sample boundaries.')
    if max_seconds is not None and pcm_size > byte_rate * max_seconds:
        raise SkillError(f'WAV duration exceeds {max_seconds} seconds.')


@contextlib.contextmanager
def new_output(path):
    """Reserve a new output before any paid call; remove incomplete output on failure."""
    target = Path(path).expanduser()
    with open(target, 'xb') as out:
        os.chmod(target, 0o600)
        owned = os.fstat(out.fileno())
        try:
            yield out
        except BaseException:
            # Do not unlink a different file installed concurrently at this path.
            out.close()
            if target.exists() and (target.stat().st_dev, target.stat().st_ino) == (owned.st_dev, owned.st_ino):
                target.unlink()
            raise


def multipart(fields, data, filename='input.wav', content_type='audio/wav'):
    boundary = 'codecraft-' + uuid.uuid4().hex
    parts = []
    for key, value in fields.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\nContent-Type: {content_type}\r\n\r\n'.encode())
    parts.extend([data, f'\r\n--{boundary}--\r\n'.encode()])
    return b''.join(parts), 'multipart/form-data; boundary=' + boundary


class DeviceAPI:
    def __init__(self):
        origin = os.environ.get('CODECRAFT_API_ORIGIN', '')
        parsed = urllib.parse.urlsplit(origin)
        local_http = parsed.scheme == 'http' and parsed.hostname in ('localhost', '127.0.0.1', '::1')
        if (not parsed.hostname or (parsed.scheme != 'https' and not local_http)
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in ('', '/')):
            raise SkillError('CODECRAFT_API_ORIGIN must be an HTTPS origin without path/credentials/query; HTTP is allowed only on loopback.')
        credential_file = os.environ.get('CODECRAFT_DEVICE_FILE')
        if not credential_file:
            raise SkillError('Set CODECRAFT_DEVICE_FILE to a private JSON file containing eui and deviceKey.')
        try:
            credentials = json.loads(read_bytes(credential_file, 16384))
            eui, key = credentials['eui'], credentials['deviceKey']
            valid = isinstance(eui, str) and isinstance(key, str) and re.fullmatch(r'[0-9a-fA-F]{16}', eui) and re.fullmatch(r'[0-9a-fA-F]{32}', key)
        except (ValueError, KeyError, TypeError):
            valid = False
        if not valid:
            raise SkillError('Credential file requires a 16-hex EUI and 32-hex deviceKey.')
        self.eui = eui
        self.origin = origin.rstrip('/')
        self.authorization = 'Device ' + base64.b64encode((eui + ':' + key).encode()).decode()
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def open(self, path, data=None, content_type='application/json'):
        if not path.startswith('/deviceapi/') or '?' in path or '#' in path or '\\' in path:
            raise SkillError('Only fixed CodeCraft device API paths are accepted.')
        request = urllib.request.Request(self.origin + path, data=data,
                                         headers={'Authorization': self.authorization, 'Content-Type': content_type})
        try:
            return self.opener.open(request, timeout=160)
        except urllib.error.HTTPError as error:
            status = error.code
            error.close()
            hints = {401: 'Device credentials are invalid or device quota is exhausted.',
                     402: 'Device quota is unavailable.',
                     403: 'Device access is disabled or forbidden.', 404: 'Asset or API path not found.',
                     400: 'Request parameters are invalid.', 413: 'Input is too large.',
                     429: 'Rate limit or quota limit reached.', 502: 'The service could not complete the request.',
                     503: 'The service is temporarily unavailable.'}
            raise SkillError(f'HTTP {status}: {hints.get(status, "Request failed.")} No automatic retry.') from None
        except (urllib.error.URLError, TimeoutError):
            raise SkillError('Network failure; request outcome and charge may be uncertain. Do not automatically retry.') from None

    def request(self, path, payload=None, data=None, content_type='application/json', maximum=32 * 1024 * 1024):
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode()
        try:
            with self.open(path, data, content_type) as response:
                result = read_response(response, maximum)
        except (OSError, http.client.HTTPException):
            raise SkillError('Response interrupted; request outcome and charge may be uncertain. Do not automatically retry.') from None
        return result

    def archive(self, path):
        body, content_type = multipart({}, read_bytes(path), 'asset', 'application/octet-stream')
        result = decode_json(self.request('/deviceapi/media-assets/v1/files', data=body, content_type=content_type))
        data = result.get('data')
        if result.get('code') != 200 or not isinstance(data, dict):
            raise SkillError('Archive response is invalid; do not regenerate the media.')
        try:
            identifier = str(uuid.UUID(data['id']))
        except (KeyError, ValueError, TypeError, AttributeError):
            raise SkillError('Archive returned an invalid asset ID.') from None
        expected = '/deviceapi/media-assets/v1/files/' + identifier + '/content'
        if data.get('content_url') != expected:
            raise SkillError('Archive returned an unexpected content path.')
        return {'asset_id': identifier, 'content_url': self.origin + expected, 'authentication': 'Device header required'}


def media_result(api, output, archive):
    result = {'file': str(Path(output).expanduser().resolve())}
    if archive:
        try:
            result.update(api.archive(output))
        except SkillError:
            print(json.dumps(result, ensure_ascii=False))
            raise SkillError('Media generation succeeded and the local file is retained, but archival failed. Retry only the archive command, not generation.') from None
    print(json.dumps(result, ensure_ascii=False))


def run(main):
    try:
        main()
    except (SkillError, OSError, ValueError, KeyError, TypeError, IndexError, AttributeError, http.client.HTTPException) as error:
        # Never print low-level exception text: it can contain credentials or signed URLs.
        message = str(error) if isinstance(error, SkillError) else 'Invalid input, output path, or network response; no automatic retry.'
        print(message, file=sys.stderr)
        raise SystemExit(1) from None


def assets_main():
    parser = argparse.ArgumentParser(description='Archive an existing file or download a stable device asset.')
    sub = parser.add_subparsers(dest='command', required=True)
    upload = sub.add_parser('archive')
    upload.add_argument('--file', required=True)
    download = sub.add_parser('download')
    download.add_argument('--asset-id', required=True)
    download.add_argument('--output', required=True)
    args = parser.parse_args()
    api = DeviceAPI()
    if args.command == 'archive':
        print(json.dumps(api.archive(args.file), ensure_ascii=False))
    else:
        identifier = str(uuid.UUID(args.asset_id))
        with new_output(args.output) as out:
            out.write(api.request('/deviceapi/media-assets/v1/files/' + identifier + '/content', maximum=MAX_FILE))
        media_result(api, args.output, False)


if __name__ == '__main__':
    run(assets_main)
