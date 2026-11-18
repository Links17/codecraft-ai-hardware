<p align="right"><a href="README.md">English</a> · <strong>简体中文</strong></p>

# CodeCraft AI Hardware

Seeed 设备的开发参考仓库，包含设备知识、原生 BSP 与示例、云端 Skill 合同和独立 Agent 工作流。四个云 API 客户端 Skill 在 [skills/](skills/README.zh_CN.md) 中维护，云端服务和账户基础设施仍由外部项目负责。

从 [AGENTS.md](AGENTS.md) 开始。[设备入口](devices/AGENTS.md)和[能力矩阵](docs/inventory.md)由来源清单生成。

## 快速开始

```sh
python3 codecraft.py catalog
python3 codecraft.py discover --interface display
python3 codecraft.py cloud-catalog
python3 codecraft.py check-cloud-skills
python3 codecraft.py resolve-capability --capability asr
python3 codecraft.py context --target esp-idf/reterminal-e1001
python3 codecraft.py validate --static
python3 codecraft.py validate --target esp-idf/reterminal-e1001
```

构建前激活 Target 声明的工具链。生成可移植的私有项目工作区：

```sh
python3 codecraft.py new --target esp-idf/reterminal-e1001 --example epd_hello --output projects/my-e1001-project
python3 codecraft.py build-project projects/my-e1001-project
```

输出目录必须尚不存在。`project.yaml` 记录选择，`codecraft.lock` 记录导入文件摘要、仓库版本与工具链。生成项目和构建日志不提交。`projects/` 已忽略，仍支持显式指定仓库外路径。使用 codecraft-ideate 与 `new --brief <file.json>`，将用途、目标用户、场景和 BOM 写入 project.yaml，并生成应用 AGENTS 的对应区域。参见[项目工作区](docs/development/project-workspaces.md)。

新导出项目也包含公共入口；在应用目录运行 `python3 codecraft.py build-project .`。无需全局安装 CLI。独立云端 Skill 仍可单独运行；包版本维护使用[候选包工作流](docs/development/skill-releases.md)。

## 结构与贡献

`devices/` 负责事实和来源，`platforms/` 负责原生实现，`capabilities/` 负责云端 Skill 消费合同，`skills/` 负责流程、脚本与合同测试。阅读[架构](docs/architecture/overview.md)和[贡献规则](.github/CONTRIBUTING.md)。

元数据修改后执行 `python3 codecraft.py generate`，再执行 `python3 codecraft.py generate --check`。CI 与发现使用同一份 Target 记录。完整软件门禁为 `python3 codecraft.py validate`，物理验证单独记录，在获得真实证据前仍属于未执行。

采用 Apache License 2.0，第三方归属保留在 [NOTICE](NOTICE)。

V0.2 实施进度见 [TODO 清单](docs/development/v0.2-todo.md)；[CONTRIBUTION.md](CONTRIBUTION.md) 提供维护规则入口。云端 CLI 集成、仿真和实机验收仍是独立待办。
