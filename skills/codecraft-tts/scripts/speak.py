#!/usr/bin/env python3
import argparse

from device_api import DeviceAPI, SkillError, media_result, new_output, read_text, run


def main():
    parser = argparse.ArgumentParser(description='Generate CodeCraft WAV speech; 1000 quota per accepted call.')
    parser.add_argument('--text-file', required=True)
    parser.add_argument('--output', required=True, help='New WAV path; existing files are never overwritten')
    parser.add_argument('--voice', default='Cherry')
    parser.add_argument('--archive', action='store_true', help='Upload the generated audio and return a stable Device-authenticated URL')
    args = parser.parse_args()
    text = read_text(args.text_file).strip()
    if not text or len(text) > 500 or not args.voice or len(args.voice) > 64:
        raise SkillError('TTS requires 1–500 Unicode characters and a nonempty voice of at most 64 characters.')
    api = DeviceAPI()
    with new_output(args.output) as out:
        audio = api.request('/deviceapi/ai-services/v1/audio/speech',
                            payload={'model': 'qwen3-tts-flash', 'input': text, 'voice': args.voice, 'response_format': 'wav'},
                            maximum=20 * 1024 * 1024)
        if len(audio) < 44 or audio[:4] != b'RIFF' or audio[8:12] != b'WAVE':
            raise SkillError('TTS returned an unexpected audio format; no automatic retry.')
        out.write(audio)
    media_result(api, args.output, args.archive)


if __name__ == '__main__':
    run(main)
