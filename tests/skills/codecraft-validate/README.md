<p align="right"><strong>English</strong> · <a href="README.zh_CN.md">简体中文</a></p>

# Validation entry and gate tests

These tests own public CLI behavior, recursive host discovery, documentation policy and unique current test IDs. Core graph/export/lock/evidence integration tests live in tests/skills/_shared; cloud installation/protocol/release tests live in tests/skills/_cloud. Shared component scenarios live in tests/platforms/<stack>/components/<component>/. Board-specific scenarios live in tests/devices/<device>/targets/, with shared compiler helpers in tests/platforms/<stack>/.

Run `python3 codecraft.py test --path tests/skills/codecraft-validate` for this owner, or `python3 codecraft.py validate --static` for every host suite. See [test ownership and execution](../../../docs/development/testing.md). Tests do not access hardware.
