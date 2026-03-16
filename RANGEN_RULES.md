# RANGEN Harness 架构

> 基于 Harness Engineering 最佳实践
> 本文件是入口，指向详细文档

---

## 目录结构

```
RANGEN_RULES.md          # 本文件 - 精简入口 (~100行)
└── docs/harness/
    ├── ARCHITECTURE.md  # 架构原则
    ├── DESIGN.md        # 设计模式
    ├── QUALITY.md       # 质量标准
    └── SECURITY.md      # 安全约束
```

---

## 快速索引

```
IF 任务 = "编码"      → 阅读 docs/harness/ARCHITECTURE.md
IF 任务 = "设计"      → 阅读 docs/harness/DESIGN.md
IF 任务 = "验证"      → 阅读 docs/harness/QUALITY.md
IF 任务 = "安全"      → 阅读 docs/harness/SECURITY.md
```

---

## 核心原则

### 1. 渐进式披露

Agent 不需要一开始知道所有事，只在正确时机获取正确粒度的信息。

### 2. 三大维度

| 维度 | 负责 | 文件 |
|------|------|------|
| 上下文工程 | 知道什么 | RANGEN_RULES.md |
| 架构约束 | 边界内行事 | docs/harness/ARCHITECTURE.md |
| 熵管理 | 不随时间腐化 | src/core/harness_entropy_manager.py |

### 3. 四大组成部分 (Harness Engineering)

| 组件 | 功能 | 文件 |
|------|------|------|
| 信息喂送 | 渐进式文档披露 | docs/harness/ |
| 约束拦截 | Agent 友好的 Linter | src/core/agent_linter.py |
| 自我验证 | Agent ↔ Agent 评审 | src/core/agent_reviewer.py |
| 可观测性 | Agent 查询运行时数据 | src/core/agent_observability_client.py |

### 4. 任务契约

使用 `TaskContract` 定义任务完成标准：
- 契约存储: `.rangen/contracts/`
- 查看状态: `check_contract_status(task_id)`

---

## 更新日志

- 2026-03-16: 初始版本，迁移自 RANGEN_RULES.md
