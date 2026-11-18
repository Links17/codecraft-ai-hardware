#!/usr/bin/env python3
import argparse
import json
import struct

from device_api import DeviceAPI, SkillError, decode_json, multipart, read_bytes, run


def validate_wav(data):
    """Match the gateway's PCM/time limits before a billable network request."""
    if len(data) < 44 or data[:4] != b'RIFF' or data[8:12] != b'WAVE' or struct.unpack_from('<I', data, 4)[0] + 8 != len(data):
        raise SkillError('ASR requires a complete PCM WAV with accurate chunk lengths.')
    offset, formats, chunks, rate, samples_size = 12, 0, 0, 0, 0
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
            encoding, channels, frequency, rate, align, bits = struct.unpack_from('<HHIIHH', data, start)
            if encoding != 1 or channels != 1 or bits != 16 or not 8000 <= frequency <= 48000 or rate != frequency * 2 or align != 2:
                raise SkillError('ASR requires mono PCM 16-bit WAV at 8–48 kHz.')
            formats += 1
        elif kind == b'data':
            samples_size += size
            chunks += 1
        offset = end + size % 2
    if offset != len(data) or formats != 1 or chunks != 1 or not rate or not samples_size or samples_size % 2 or samples_size > rate * 60:
        raise SkillError('ASR requires one complete PCM data chunk lasting at most 60 seconds.')


def main():
    parser = argparse.ArgumentParser(description='Transcribe one CodeCraft PCM WAV; 1000 quota per accepted call.')
    parser.add_argument('--file', required=True)
    args = parser.parse_args()
    audio = read_bytes(args.file, 10 * 1024 * 1024)
    validate_wav(audio)
    body, content_type = multipart({'model': 'qwen-audio-3.0-asr-flash'}, audio)
    result = decode_json(DeviceAPI().request('/deviceapi/ai-services/v1/audio/transcriptions', data=body, content_type=content_type))
    if not isinstance(result.get('text'), str):
        raise SkillError('ASR returned an invalid transcript.')
    print(json.dumps({'text': result['text']}, ensure_ascii=False))


if __name__ == '__main__':
    run(main)
