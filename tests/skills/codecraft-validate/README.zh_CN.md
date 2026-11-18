<p align="right"><a href="README.md">English</a> · <strong>简体中文</strong></p>

# 验证入口与检查流程测试

此目录负责公共 CLI 行为、递归主机测试发现、文档规则和当前测试 ID 唯一性。核心依赖图、导出、锁与证据集成测试位于 tests/skills/_shared；云端安装、协议与发布测试位于 tests/skills/_cloud。共享组件场景位于 tests/platforms/<stack>/components/<component>/；板级场景位于 tests/devices/<device>/targets/，共用编译辅助逻辑位于 tests/platforms/<stack>/。

使用 `python3 codecraft.py test --path tests/skills/codecraft-validate` 定向运行本目录，或使用 `python3 codecraft.py validate --static` 运行全部主机测试。参见[测试归属与执行](../../../docs/development/testing.md)。测试不访问硬件。
