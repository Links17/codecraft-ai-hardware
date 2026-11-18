<p align="right"><a href="README.md">English</a> · <strong>简体中文</strong></p>

# Agent Skills

本目录同时包含硬件开发工作流与消费 CodeCraft 云端 Capability 合同的独立客户端。设备事实归 devices/，原生实现归 platforms/，云端合同归 capabilities/。

## 硬件开发

五个必需工作流为 codecraft-develop、codecraft-setup、codecraft-build、codecraft-device-test、codecraft-debug，使用 [codecraft-ideate](codecraft-ideate/SKILL.md) 梳理应用意图和项目说明，按需使用 codecraft-discover 与 codecraft-validate。`context --task ideate` 包含构思与发现指南。通用编排位于 _shared/；各平台拥有原生命令与工具链探测逻辑。

## 云 API 客户端

| Skill | 操作 | 默认模型 | 平台额度 |
| --- | --- | --- | --- |
| [codecraft-llm](codecraft-llm/SKILL.md) | 文本生成与 SSE | qwen-plus | 按 token |
| [codecraft-asr](codecraft-asr/SKILL.md) | WAV 转写；ASR/STT | qwen-audio-3.0-asr-flash | 每次 1000 |
| [codecraft-tts](codecraft-tts/SKILL.md) | WAV 合成与可选归档 | qwen3-tts-flash | 每次 1000 |
| [codecraft-image-generation](codecraft-image-generation/SKILL.md) | 单张 1024×1024 图片与可选归档 | qwen-image-2.0 | 每张 10000 |

每个目录包含仅英文的 SKILL.md 与 references/api.md、agents/openai.yaml、入口脚本和自己的 scripts/device_api.py。把所需完整目录复制到 Agent Skills 发现目录即可安装。仅依赖 Python 3.10+ 标准库，无需其他 Skill 或云端仓库检出，可独立运行。保持自动发现开启；安装本身不授予 API 权限。

仅在执行已授权 API 任务时配置 CODECRAFT_API_ORIGIN 和 CODECRAFT_DEVICE_FILE，凭据格式与限制见各 API 参考。输入、生成文件和凭据保存在安装目录之外。TTS 和生图默认保存本地文件；任务需要稳定的设备鉴权资产链接时才使用 --archive，该链接不是公开 URL。归档失败不需要再次生成。

repository-skill Provider 固定本地包文件并声明依赖。new --capabilities <selection.json> 将所选包导出到私有项目并纳入 codecraft.lock；纯原生项目不包含云客户端。prepare-capability 只返回调用参数信封，不执行 API。云端发现、解析和准备无需硬件 Target；--target 增加可选且经过校验的上下文，设备集成仍保持 unknown。

Capability 合同版本为 2.0.0，当前各 Provider 的策略版本为 1.0.0。稳定语义保留在 Capability；服务边界、计费声明和获准的默认值归所选 Provider。准备阶段返回原始与有效配置以及有效输入/输出 schema，并通过显式参数把默认值交给客户端。上表描述当前 CodeCraft Provider，不代表通用 Capability 限制或实测计费。参见[策略职责](../docs/architecture/capability-provider-policy.md)。

## 仓库调用链

对于已授权的云端任务，先阅读所选 Skill 与 API 参考，解析 Capability 前置条件，再准备调用信封。例如 ASR 选择文件为：

```json
{
  "capability": "asr",
  "provider": "asr/codecraft-cloud",
  "configuration": {},
  "environment": {
    "network": true,
    "tls": true,
    "privacy_approved": true,
    "environment_refs": ["CODECRAFT_API_ORIGIN"],
    "secret_refs": ["CODECRAFT_DEVICE_FILE"]
  },
  "limits": {}
}
```

environment 仅描述已确认条件与引用名，禁止放入凭据值；未知条件仍须保持未知。输入文件为 `{"file":"/work/recording.wav"}`。执行：

```sh
python3 codecraft.py prepare-capability --selection /work/selection.json --operation transcribe --input /work/input.json
```

使用成功信封中的 entrypoint 与 arguments 数组，在已授权环境中运行所选且已校验的 Skill；参数应作为独立进程参数传递，不经 shell 求值。Skill 负责文件校验、鉴权、HTTP、流式处理和可选归档。非零退出视为失败，即使已有部分文本或保留的本地文件；成功时按声明的输出 schema 消费结果。准备阶段不读取凭据、不发请求。独立 Skill 安装仍不依赖本仓库 CLI。

## 维护与验证

来源和已检查文件的哈希在 [_cloud/import.json](_cloud/import.json)。仅 README 维护英文与简体中文，其余工程文档统一英文。共用客户端源码位于 _cloud/device_api.py，请使用[候选包工作流](../docs/development/skill-releases.md)：准备候选，审查文件和版本差异，执行检查，再应用已审查的确切摘要。应用会重跑隔离一致性测试并拒绝源码漂移。运行时始终导入包内副本；Provider 固定完整包清单和版本，独立安装的包必须与该清单完全一致。

仓库命令统一使用 `python3 codecraft.py`。门禁检查候选包可重复性、显式版本变更、源码和候选篡改拒绝、事务回滚及锁定导出项目。打包不会自动安装或发布；离线检查不代表真实 API 已验收。

从仓库根执行：

```sh
python3 codecraft.py check-cloud-skills
python3 codecraft.py test --path skills/_cloud/tests/test_protocol.py
python3 codecraft.py validate --static
```

check-cloud-skills 默认校验仓库内完整包清单，也可用 --skills-root 校验单独安装的副本。缺失、多余或符号链接文件均失败。清单排除 Python 缓存与 .DS_Store，--help 从固定文件的全新副本运行，不使用已安装字节码或 PYTHONPATH。skill.files 显式固定的二进制素材保留在上下文、导出和锁中。静态门禁包含四个包/CLI 检查、九项离线协议测试，以及十二项 Capability 到真实客户端的一致性测试与七项共用 Provider 策略测试。离线测试把单个包安装到临时目录，使用本机回环模拟服务与合成凭据，覆盖 JSON/SSE、断流、音频限制、图片解码、归档/下载、输出保留、重定向拒绝、错误脱敏和失败不自动重试，不调用真实云 API。

真实 API 验收仍是独立的[待办事项](../docs/development/optimization-plan.md)。本仓库不托管云服务，也不自动发布 Skill。
