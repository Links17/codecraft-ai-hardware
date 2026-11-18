#!/usr/bin/env python3
import argparse
import sys

# Keep the installed skill directory free of Python bytecode caches.
sys.dont_write_bytecode = True

from device_api import DeviceAPI, SkillError, media_result, new_output, read_text, run, validate_pcm_wav


def main():
    parser = argparse.ArgumentParser(description='Generate CodeCraft WAV speech; 1000 quota per accepted call.')
    parser.add_argument('--text-file', required=True)
    parser.add_argument('--output', required=True, help='New WAV path; existing files are never overwritten')
    parser.add_argument('--archive', action='store_true', help='Upload the generated audio and return a stable Device-authenticated URL')
    args = parser.parse_args()
    text = read_text(args.text_file).strip()
    if not text or len(text) > 500:
        raise SkillError('TTS requires 1–500 Unicode characters.')
    api = DeviceAPI()
    with new_output(args.output) as out:
        audio = api.request('/deviceapi/ai-services/v1/audio/speech',
                            payload={'input': text, 'response_format': 'wav'},
                            maximum=20 * 1024 * 1024)
        validate_pcm_wav(audio)
        out.write(audio)
    media_result(api, args.output, args.archive)


if __name__ == '__main__':
    run(main)
