# RANGEN 文档分类架构设计

## 📋 概述

本文档定义了RANGEN系统的文档分类架构，旨在解决文档分散、维护困难的问题。通过统一的分类体系，提高文档的可查找性、可维护性和用户体验。

## 🎯 设计原则

1. **用户导向**：按用户角色和使用场景组织文档
2. **渐进式学习**：从入门到精通，形成完整学习路径
3. **易于维护**：清晰的目录结构，便于更新和扩展
4. **一致性**：统一的命名约定和文档格式

## 📁 文档分类架构

### 1. 📚 **入门指南** (`docs/getting-started/`)
针对新用户的快速入门文档，帮助用户在最短时间内了解和使用系统。

```
getting-started/
├── README.md                    # 入门指南索引
├── quick-start.md               # 5分钟快速启动
├── installation/                # 安装部署
│   ├── basic-installation.md    # 基础安装
│   ├── docker-installation.md   # Docker安装
│   └── configuration.md         # 环境配置
└── first-steps/                 # 初次使用
    ├── basic-usage.md           # 基本使用
    ├── examples/                # 示例教程
    └── common-tasks.md          # 常见任务
```

### 2. 🏗️ **架构设计** (`docs/architecture/`)
系统架构、设计理念和组件说明，面向架构师和高级开发者。

```
architecture/
├── README.md                    # 架构设计索引
├── system-overview/             # 系统概览
│   ├── core-concepts.md         # 核心概念
│   ├── design-philosophy.md     # 设计理念
│   └── version-history.md       # 版本演进
├── component-design/            # 组件设计
│   ├── agents/                  # 智能体组件
│   ├── services/                # 服务组件
│   ├── core-engine/             # 核心引擎
│   └── interfaces/              # 接口设计
└── patterns/                    # 设计模式
    ├── reflection-pattern.md    # 反思型架构
    ├── routing-pattern.md       # 路由模式
    └── training-pattern.md      # 训练模式
```

### 3. 🔧 **开发指南** (`docs/development/`)
面向开发者的技术文档，包括API参考、开发规范和扩展开发。

```
development/
├── README.md                    # 开发指南索引
├── api-reference/               # API参考
│   ├── rest-api.md              # REST API
│   ├── client-sdks.md           # 客户端SDK
│   └── webhooks.md              # Webhooks
├── extending-system/            # 系统扩展
│   ├── custom-agents.md         # 自定义智能体
│   ├── custom-tools.md          # 自定义工具
│   └── plugin-development.md    # 插件开发
└── testing/                     # 测试
    ├── unit-testing.md          # 单元测试
    ├── integration-testing.md   # 集成测试
    └── performance-testing.md   # 性能测试
```

### 4. 🚀 **运维部署** (`docs/operations/`)
系统部署、监控、维护和故障排除，面向运维人员和系统管理员。

```
operations/
├── README.md                    # 运维指南索引
├── deployment/                  # 部署
│   ├── production-deployment.md # 生产部署
│   ├── scaling-guide.md         # 扩缩容指南
│   └── backup-recovery.md       # 备份恢复
├── monitoring/                  # 监控
│   ├── metrics-dashboard.md     # 监控面板
│   ├── logging-config.md        # 日志配置
│   └── alerting.md              # 告警配置
└── troubleshooting/             # 故障排除
    ├── common-issues.md         # 常见问题
    ├── performance-troubleshooting.md # 性能问题
    └── emergency-procedures.md  # 应急流程
```

### 5. 📖 **技术参考** (`docs/reference/`)
详细的技术规格、配置参数和实现细节，供需要深入了解系统的用户参考。

```
reference/
├── README.md                    # 技术参考索引
├── configuration/               # 配置参考
│   ├── env-variables.md         # 环境变量
│   ├── config-files.md          # 配置文件
│   └── security-config.md       # 安全配置
├── models/                      # 模型参考
│   ├── llm-providers.md         # LLM提供商
│   ├── model-capabilities.md    # 模型能力
│   └── training-framework.md    # 训练框架
└── technical-specs/             # 技术规格
    ├── performance-specs.md     # 性能指标
    ├── security-specs.md        # 安全规格
    └── compatibility.md         # 兼容性
```

### 6. 💡 **最佳实践** (`docs/best-practices/`)
使用经验、优化建议和实战技巧，帮助用户更高效地使用系统。

```
best-practices/
├── README.md                    # 最佳实践索引
├── usage-patterns/              # 使用模式
│   ├── efficient-routing.md     # 高效路由
│   ├── cost-optimization.md     # 成本优化
│   └── performance-tuning.md    # 性能调优
├── security-practices/          # 安全实践
│   ├── access-control.md        # 访问控制
│   ├── data-protection.md       # 数据保护
│   └── compliance.md            # 合规性
└── advanced-techniques/         # 高级技巧
    ├── reflection-optimization.md # 反思优化
    ├── custom-training.md       # 自定义训练
    └── integration-patterns.md  # 集成模式
```

### 7. 📝 **变更日志** (`docs/changelog/`)
版本更新、迁移指南和未来路线图，帮助用户了解系统演进。

```
changelog/
├── README.md                    # 变更日志索引
├── releases/                    # 版本发布
│   ├── v1.0.0.md                # 版本1.0.0
│   ├── v2.0.0.md                # 版本2.0.0
│   └── upcoming.md              # 即将发布
├── migration-guides/            # 迁移指南
│   ├── v1-to-v2.md              # V1到V2迁移
│   ├── breaking-changes.md      # 重大变更
│   └── compatibility.md         # 兼容性指南
└── roadmap/                     # 路线图
    ├── 2025-q1.md               # 2025年Q1
    ├── 2025-q2.md               # 2025年Q2
    └── long-term.md             # 长期规划
```

## 🔄 现有文档映射

### docs目录现有结构映射
- `docs/agent_architecture/` → `architecture/component-design/agents/`
- `docs/analysis/` → `operations/troubleshooting/` + `reference/technical-specs/`
- `docs/architecture/` → `architecture/`（主要）
- `docs/development/` → `development/`
- `docs/diagrams/` → `architecture/diagrams/`
- `docs/fixes/` → `operations/troubleshooting/`
- `docs/guide/` → `best-practices/` + `getting-started/`
- `docs/guides/` → `getting-started/examples/`
- `docs/implementation/` → `development/extending-system/`
- `docs/installation/` → `getting-started/installation/`
- `docs/migration/` → `changelog/migration-guides/`
- `docs/refactoring/` → `architecture/patterns/`
- `docs/testing/` → `development/testing/`
- `docs/tools/` → `operations/monitoring/`
- `docs/troubleshooting/` → `operations/troubleshooting/`
- `docs/usage/` → `getting-started/first-steps/`
- `docs/visualization/` → `operations/monitoring/`

### 根目录文档处理
- `AGENTS.md` → 拆分为多个文档：`architecture/component-design/agents/` + `development/extending-system/custom-agents.md`
- `RANGEN_V3_SYSTEM_ANALYSIS_REPORT.md` → `architecture/system-overview/design-philosophy.md` + `architecture/patterns/reflection-pattern.md`
- `SYSTEM_SPEC.md` → `architecture/system-overview/core-concepts.md` + `reference/technical-specs/`
- `README.md` → 保持为项目主README，链接到`docs/getting-started/quick-start.md`

## 🚀 实施计划

### 第一阶段：创建新目录结构
1. 在docs目录下创建新的分类目录
2. 创建每个分类的README.md索引文件
3. 更新docs/README.md指向新结构

### 第二阶段：文档迁移
1. 将现有文档按映射关系移动到新目录
2. 更新文档内的链接引用
3. 创建重定向或符号链接（如需要）

### 第三阶段：更新根目录文档
1. 拆分AGENTS.md等大文档
2. 更新项目主README.md
3. 创建文档导航页面

### 第四阶段：完善和优化
1. 填补缺失的文档
2. 优化文档格式和内容
3. 建立文档维护流程

## 📊 维护指南

### 文档更新流程
1. **新增文档**：根据分类放入对应目录，更新README.md索引
2. **修改文档**：在对应目录中直接编辑
3. **删除文档**：从目录中移除，更新索引，考虑存档
4. **移动文档**：更新所有引用链接

### 版本控制
- 文档与代码一起版本控制
- 重大变更时更新`changelog/`
- 保持向后兼容性说明

### 质量检查
- 定期检查死链接
- 确保示例代码可运行
- 保持与代码实现同步

## 📞 反馈与贡献

欢迎通过以下方式改进文档：
1. 报告文档问题
2. 提交改进建议
3. 贡献新的文档内容
4. 翻译为其他语言

---

*最后更新：2026-03-07*  
*文档版本：1.0.0*  
*维护团队：RANGEN文档工作组*