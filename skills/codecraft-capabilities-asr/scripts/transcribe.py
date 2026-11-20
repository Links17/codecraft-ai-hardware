#!/usr/bin/env python3
import argparse
import sys
import json

# Keep the installed skill directory free of Python bytecode caches.
sys.dont_write_bytecode = True

from device_api import DeviceAPI, SkillError, decode_json, multipart, read_bytes, run, validate_pcm_wav


def validate_wav(data):
    """Validate the public file ASR format and duration before a billable request."""
    validate_pcm_wav(data, max_seconds=60, max_bytes=10 * 1024 * 1024)


def main():
    parser = argparse.ArgumentParser(description='Transcribe one CodeCraft PCM WAV; 1000 quota per accepted call.')
    parser.add_argument('--file', required=True)
    args = parser.parse_args()
    audio = read_bytes(args.file, 10 * 1024 * 1024)
    validate_wav(audio)
    body, content_type = multipart({}, audio)
    result = decode_json(DeviceAPI().request('/deviceapi/ai-services/v1/audio/transcriptions', data=body, content_type=content_type))
    if not isinstance(result.get('text'), str):
        raise SkillError('ASR returned an invalid transcript.')
    print(json.dumps({'text': result['text']}, ensure_ascii=False))


if __name__ == '__main__':
    run(main)
