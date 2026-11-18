#!/usr/bin/env python3
import argparse
import json
import sys

# Keep the installed skill directory free of Python bytecode caches.
sys.dont_write_bytecode = True

from device_api import DeviceAPI, SkillError, decode_json, read_text, run


def main():
    parser = argparse.ArgumentParser(description='Call the CodeCraft device LLM; no automatic retries.')
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--prompt-file')
    inputs.add_argument('--messages-file', help='UTF-8 JSON array of system/user/assistant text messages')
    parser.add_argument('--max-tokens', type=int, default=256)
    parser.add_argument('--stream', action='store_true', help='Write content deltas to stdout; a missing DONE is an error')
    args = parser.parse_args()
    if not 1 <= args.max_tokens <= 2048:
        raise SkillError('--max-tokens must be between 1 and 2048.')
    messages = json.loads(read_text(args.messages_file)) if args.messages_file else [{'role': 'user', 'content': read_text(args.prompt_file)}]
    if not isinstance(messages, list) or not messages or any(
        not isinstance(m, dict) or m.get('role') not in ('system', 'user', 'assistant')
        or not isinstance(m.get('content'), str) or not m['content'].strip() for m in messages
    ):
        raise SkillError('Provide a nonempty list of system/user/assistant text messages.')
    if len(messages) > 64 or sum(len(m['content']) for m in messages) > 8192:
        raise SkillError('Use at most 64 messages and 8192 total Unicode characters.')
    # Project only supported fields; this CLI does not execute tools or support image inputs.
    payload = {'messages': [{'role': m['role'], 'content': m['content']} for m in messages],
               'max_tokens': args.max_tokens, 'stream': args.stream}
    api = DeviceAPI()
    path = '/deviceapi/ai-services/v1/chat/completions'
    if not args.stream:
        result = decode_json(api.request(path, payload=payload))
        text = result['choices'][0]['message']['content']
        if not isinstance(text, str):
            raise SkillError('Model returned no text content.')
        reason = result['choices'][0].get('finish_reason')
        complete = reason == 'stop'
        print(json.dumps({'text': text, 'usage': result.get('usage'),
                          'finish_reason': reason, 'complete': complete}, ensure_ascii=False))
        if not complete:
            raise SkillError('Generation did not finish normally (token limit, filtering, or missing completion status). Partial output is retained; no automatic retry.')
        return
    done = False
    finish_reason = None
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
                if choice.get('finish_reason') is not None:
                    finish_reason = choice['finish_reason']
                text = choice.get('delta', {}).get('content')
                if text is not None:
                    if not isinstance(text, str):
                        raise SkillError('Unexpected streaming content.')
                    sys.stdout.write(text)
                    sys.stdout.flush()
    if not done:
        raise SkillError('SSE ended without DONE; partial output is incomplete. Do not automatically retry.')
    if finish_reason != 'stop':
        raise SkillError('Generation did not finish normally (token limit, filtering, or missing completion status). Partial output is retained; no automatic retry.')
    print()


if __name__ == '__main__':
    run(main)
