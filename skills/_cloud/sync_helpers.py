"""Keep standalone skill bundles in sync without runtime cross-folder imports."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ('codecraft-llm', 'codecraft-asr', 'codecraft-tts', 'codecraft-image-generation')

if __name__ == '__main__':
    source = Path(__file__).with_name('device_api.py').read_bytes()
    for name in SKILLS:
        (ROOT / 'skills' / name / 'scripts/device_api.py').write_bytes(source)
        print('Updated bundled helper:', name)
