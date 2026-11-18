#!/usr/bin/env python3
import argparse
import json
import sys

from device_api import DeviceAPI, SkillError, decode_json, read_text, run


def main():
    parser = argparse.ArgumentParser(description='Call the CodeCraft device LLM; no automatic retries.')
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--prompt-file')
    inputs.add_argument('--messages-file', help='UTF-8 JSON array of system/user/assistant text messages')
    parser.add_argument('--max-tokens', type=int, default=256)
    parser.add_argument('--stream', action='store_true', help='Write content deltas to stdout; a missing DONE is an error')
    args = parser.parse_args()
    if args.max_tokens <= 0:
        raise SkillError('--max-tokens must be positive.')
    messages = json.loads(read_text(args.messages_file)) if args.messages_file else [{'role': 'user', 'content': read_text(args.prompt_file)}]
    if not isinstance(messages, list) or not messages or any(
        not isinstance(m, dict) or m.get('role') not in ('system', 'user', 'assistant')
        or not isinstance(m.get('content'), str) or not m['content'].strip() for m in messages
    ):
        raise SkillError('Provide a nonempty list of system/user/assistant text messages.')
    # Project only supported fields; this CLI does not execute tools or support image inputs.
    payload = {'model': 'qwen-plus', 'messages': [{'role': m['role'], 'content': m['content']} for m in messages],
               'max_tokens': args.max_tokens, 'stream': args.stream}
    api = DeviceAPI()
    path = '/deviceapi/ai-services/v1/chat/completions'
    if not args.stream:
        result = decode_json(api.request(path, payload=payload))
        text = result['choices'][0]['message']['content']
        if not isinstance(text, str):
            raise SkillError('Model returned no text content.')
        print(json.dumps({'text': text, 'usage': result.get('usage')}, ensure_ascii=False))
        return
    done = False
    total = 0
    with api.open(path, json.dumps(payload, ensure_ascii=False).encode()) as response:
        if 'text/event-stream' not in response.headers.get('Content-Type', ''):
            raise SkillError('Expected an SSE response; no automatic retry.')
        while True:
            line = response.readline(1024 * 1024 + 1)
            if not line:
                break
            total += len(line)
            if len(line) > 1024 * 1024 or total > 32 * 1024 * 1024:
                raise SkillError('SSE response exceeded the client limit; partial text is incomplete.')
            if not line.startswith(b'data:'):
                continue
            event = line[5:].strip()
            if event == b'[DONE]':
                done = True
                break
            result = decode_json(event)
            for choice in result.get('choices', []):
                text = choice.get('delta', {}).get('content')
                if text is not None:
                    if not isinstance(text, str):
                        raise SkillError('Unexpected streaming content.')
                    sys.stdout.write(text)
                    sys.stdout.flush()
    if not done:
        raise SkillError('SSE ended without DONE; partial output is incomplete. Do not automatically retry.')
    print()


if __name__ == '__main__':
    run(main)
