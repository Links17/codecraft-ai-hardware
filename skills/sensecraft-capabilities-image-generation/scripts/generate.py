#!/usr/bin/env python3
import argparse
import sys
import base64
import io
import re
import warnings

# Keep the installed skill directory free of Python bytecode caches.
sys.dont_write_bytecode = True

from device_api import DeviceAPI, SkillError, decode_json, media_result, new_output, read_text, run


def parse_size(value):
    if not re.fullmatch(r'[1-9][0-9]{0,6}x[1-9][0-9]{0,6}', value):
        raise SkillError('--size must be WIDTHxHEIGHT using positive integers, for example 1536x1024.')
    width, height = map(int, value.split('x'))
    if not 262144 <= width * height <= 4194304:
        raise SkillError('Image size must contain 262144..4194304 total pixels.')
    return width, height


def image_decoder():
    # Resolve dependencies before reserving output or invoking a billable API.
    try:
        from PIL import Image, ImageFile
    except ImportError:
        raise SkillError('Image generation requires Pillow. Follow references/api.md#image-environment-setup before calling the service.') from None
    ImageFile.LOAD_TRUNCATED_IMAGES = False
    Image.MAX_IMAGE_PIXELS = 4194304
    return Image


def validate_image(data, expected_size, decoder):
    if not data or len(data) > 20 * 1024 * 1024:
        raise SkillError('Image response must contain a complete image within 20 MiB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', decoder.DecompressionBombWarning)
            with decoder.open(io.BytesIO(data), formats=('PNG', 'JPEG', 'WEBP')) as image:
                if image.size != expected_size or getattr(image, 'n_frames', 1) != 1:
                    raise SkillError('Image dimensions or frame count do not match the request; no automatic retry.')
                # Verify container checksums, then reopen to decode all pixel data.
                image.verify()
            with decoder.open(io.BytesIO(data), formats=('PNG', 'JPEG', 'WEBP')) as image:
                image.load()
    except SkillError:
        raise
    except Exception:
        raise SkillError('Image response is incomplete or corrupt; no automatic retry.') from None


def main():
    parser = argparse.ArgumentParser(description='Generate one CodeCraft image; 10000 quota per accepted call.')
    parser.add_argument('--prompt-file', required=True)
    parser.add_argument('--output', required=True, help='New image path; existing files are never overwritten')
    parser.add_argument('--size', default='1024x1024', help='WIDTHxHEIGHT, 262144..4194304 total pixels (default: 1024x1024)')
    parser.add_argument('--archive', action='store_true', help='Return a stable Device-authenticated URL after uploading the local image')
    args = parser.parse_args()
    expected_size = parse_size(args.size)
    prompt = read_text(args.prompt_file).strip()
    if not prompt or len(prompt) > 2000:
        raise SkillError('Image prompts must contain 1-2000 Unicode characters.')
    decoder = image_decoder()
    api = DeviceAPI()
    with new_output(args.output) as out:
        result = decode_json(api.request('/deviceapi/ai-services/v1/images/generations',
                             payload={'prompt': prompt, 'n': 1, 'size': args.size, 'response_format': 'b64_json'}))
        items = result.get('data')
        if not isinstance(items, list) or len(items) != 1 or not isinstance(items[0], dict) or not isinstance(items[0].get('b64_json'), str):
            raise SkillError('Image response must contain exactly one base64 image.')
        try:
            image = base64.b64decode(items[0]['b64_json'], validate=True)
        except ValueError:
            raise SkillError('Image response contains invalid base64.') from None
        validate_image(image, expected_size, decoder)
        out.write(image)
    media_result(api, args.output, args.archive)


if __name__ == '__main__':
    run(main)
