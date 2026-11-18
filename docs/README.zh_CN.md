<p align="right"><a href="README.md">English</a> · <strong>简体中文</strong></p>

# 文档

仅 README 保留中文版。工程指南、规则、Skills 和报告统一维护英文。

## 当前规则与实现

- [仓库与贡献约束](../AGENTS.md)
- [架构与迁移](architecture/overview.md)
- [Capability 与 Provider 策略迁移](architecture/capability-provider-policy.md)
- [仿真范围决策](architecture/simulation-scope.md)
- [AI 开发指南](development/ai-guide.md)
- [独立 Skill 打包与版本工作流](development/skill-releases.md)
- [主机测试归属与定向执行](development/testing.md)
- [ESP-IDF BSP 组合与布局](development/native-compositions.md)
- [硬件变体与原生构建选择](development/hardware-variants.md)
- [生成的设备/能力清单](inventory.md)
- [生成的厂商索引](vendor-sources.md)
- [设备验收](on-device-validation.md)

## 规划与待办

- [精简规划基线](development/codecraft-hardware-distilled.md) — 保持稳定的规划地址；当前实现见架构指南。
- [优化方案与 TODO](development/optimization-plan.md) — OPT-01 至 OPT-19 的唯一状态清单。

硬件事实与原始来源记录位于 devices/<device>/reference/。

## 历史审查与执行证据

报告仅描述所标明日期的源码与环境，不覆盖当前规则，也不将变更后的源码自动视为已验证。

- [重构验证记录](reviews/refactor-validation.md)
- [Capability 与云端 Skill 审查](reviews/capability-review.md)
- [优化执行记录，2026-11-18](reviews/optimization-progress-2026-11-18.md)
- [原生驱动优化记录，2026-11-18](reviews/optimization-drivers-2026-11-18.md)
- [BSP 生命周期优化记录，2026-11-18](reviews/optimization-lifecycle-2026-11-18.md)
- [原生 I/O 契约优化记录，2026-11-18](reviews/optimization-io-contracts-2026-11-18.md)
- [BSP 外设与调用方契约记录，2026-11-18](reviews/optimization-peripheral-contracts-2026-11-18.md)
- [云端领域与 Provider 策略记录，2026-11-18](reviews/optimization-cloud-policy-2026-11-18.md)
- [Skill 交付与公共入口记录，2026-11-18](reviews/optimization-skill-delivery-2026-11-18.md)
- [测试归属与发现记录，2026-11-18](reviews/optimization-test-ownership-2026-11-18.md)
- [原生组合与 BSP 布局记录，2026-11-18](reviews/optimization-native-composition-2026-11-18.md)
- [有来源的硬件变体记录，2026-11-18](reviews/optimization-hardware-variants-2026-11-18.md)
- [提交前验证记录，2026-11-18](reviews/submission-validation-2026-11-18.md)
