<p align="right"><strong>English</strong> · <a href="README.zh_CN.md">简体中文</a></p>

# Validation entry and gate tests

These tests own public CLI behavior, recursive host discovery, documentation policy and unique current test IDs. Core graph/export/lock/evidence integration tests live in skills/_shared/tests; cloud installation/protocol/release tests live in skills/_cloud/tests. Native scenarios live with their component or Target, with shared compiler helpers at the platform.

Run `python3 codecraft.py test --path skills/codecraft-validate/tests` for this owner, or `python3 codecraft.py validate --static` for every host suite. See [test ownership and execution](../../../docs/development/testing.md). Tests do not access hardware.
