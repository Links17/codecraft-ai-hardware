<p align="right"><strong>English</strong> · <a href="README.zh_CN.md">简体中文</a></p>

# CodeCraft tool tests

These tests cover Device parsing, source graphs, project exports and locks, evidence, public CLI behavior, recursive host discovery, documentation rules and unique test identities. Cloud installation/protocol/release tests live in tests/tools/skill_packages/. Standalone-client conformance lives under tests/skills/<skill-id>/. Platform and board fixtures remain under tests/platforms/ and tests/devices/<device>/targets/.

Run `python3 codecraft.py test --path tests/tools/codecraft` for this owner, or `python3 codecraft.py validate --static` for every host suite. See [test ownership and execution](../../../docs/development/testing.md). Tests do not access physical hardware.
