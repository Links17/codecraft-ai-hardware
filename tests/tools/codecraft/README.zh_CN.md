<p align="right"><a href="README.md">English</a> · <strong>简体中文</strong></p>

# CodeCraft 工具测试

本目录覆盖设备解析、依赖图、工程导出与锁文件、证据、公共 CLI 行为、递归主机测试发现、文档规则和测试 ID 唯一性。云端安装、协议与发布测试位于 tests/tools/skill_packages/；独立客户端一致性测试位于 tests/skills/<skill-id>/。平台与板级夹具分别位于 tests/platforms/ 和 tests/devices/<device>/targets/。

使用 `python3 codecraft.py test --path tests/tools/codecraft` 定向运行本目录，或使用 `python3 codecraft.py validate --static` 运行全部主机测试。参见[测试归属与执行](../../../docs/development/testing.md)。测试不访问物理硬件。
