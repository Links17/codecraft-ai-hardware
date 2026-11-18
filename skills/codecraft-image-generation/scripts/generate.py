#!/usr/bin/env python3
import argparse
import base64

from device_api import DeviceAPI, SkillError, decode_json, media_result, new_output, read_text, run


def main():
    parser = argparse.ArgumentParser(description='Generate one 1024x1024 CodeCraft image; 10000 quota per accepted call.')
    parser.add_argument('--prompt-file', required=True)
    parser.add_argument('--output', required=True, help='New image path; existing files are never overwritten')
    parser.add_argument('--archive', action='store_true', help='Return a stable Device-authenticated URL after uploading the local image')
    args = parser.parse_args()
    prompt = read_text(args.prompt_file).strip()
    if not prompt or len(prompt) > 2000:
        raise SkillError('Image prompts must contain 1–2000 Unicode characters.')
    api = DeviceAPI()
    with new_output(args.output) as out:
        result = decode_json(api.request('/deviceapi/ai-services/v1/images/generations',
                             payload={'model': 'qwen-image-2.0', 'prompt': prompt, 'n': 1, 'size': '1024x1024', 'response_format': 'b64_json'}))
        items = result.get('data')
        if not isinstance(items, list) or len(items) != 1 or not isinstance(items[0].get('b64_json'), str):
            raise SkillError('Image response must contain exactly one base64 image.')
        try:
            image = base64.b64decode(items[0]['b64_json'], validate=True)
        except ValueError:
            raise SkillError('Image response contains invalid base64.') from None
        valid = image.startswith(b'\x89PNG\r\n\x1a\n') or image.startswith(b'\xff\xd8\xff') or (image[:4] == b'RIFF' and image[8:12] == b'WEBP')
        if not valid or len(image) > 20 * 1024 * 1024:
            raise SkillError('Image response is not a supported PNG/JPEG/WebP within 20 MiB.')
        out.write(image)
    media_result(api, args.output, args.archive)


if __name__ == '__main__':
    run(main)
