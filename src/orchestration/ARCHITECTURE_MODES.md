# RANGEN V2 系统架构说明

## 系统双模式架构

RANGEN V2 采用**双模式架构**，满足不同场景需求：

### 模式1: 轻量模式 (默认 - 生产推荐)

```
环境变量: (默认，无需设置)
```

| 组件 | 文件 | 说明 |
|------|------|------|
| 协调器 | `execution_coordinator.py` | LangGraph 状态机，5个节点 |
| 状态 | `AgentState` | 10个字段 |
| 特点 | 轻量、快速 | 适合简单问答 |

**优势**: 启动快、资源占用低、适合生产环境

### 模式2: 完整模式 (可选 - 高级功能)

```
环境变量: RANGEN_USE_UNIFIED_RESEARCH=1
```

| 组件 | 文件 | 说明 |
|------|------|------|
| 协调器 | `langgraph_unified_workflow.py` | 完整工作流，60+节点 |
| 状态 | `ResearchSystemState` | 60+字段 |
| 特点 | 功能完整 | 适合深度研究 |

**功能**:
- 并行执行 (langgraph_parallel_execution)
- 动态工作流 (langgraph_dynamic_workflow)
- 自学习系统 (langgraph_learning_nodes - 12个引用!)
- 性能监控 (langgraph_performance_monitor - 6个引用!)
- 错误恢复 (langgraph_error_recovery)
- 能力扩展 (langgraph_capability_nodes - 3个引用)

---

## 模块使用关系图

```
                    ┌─────────────────────────────────────────┐
                    │        UnifiedResearchSystem            │
                    │   (启用 RANGEN_USE_UNIFIED_RESEARCH=1)  │
                    └──────────────────┬──────────────────────┘
                                       │
           ┌───────────────────────────┼───────────────────────────┐
           │                           │                           │
           ▼                           ▼                           ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│langgraph_unified_    │  │langgraph_unified_   │  │langgraph_unified_   │
│workflow.py           │◀─┤workflow.py           │◀─┤workflow.py           │
│                      │  │                      │  │                      │
│引用的模块:           │  │引用的模块:           │  │引用的模块:           │
│ - learning_nodes (12)│  │ - dynamic_workflow  │  │ - capability_nodes  │
│ - performance_mon (6)│  │   (2)                │  │   (3)                │
│ - parallel_exec (1)  │  │ - error_recovery (2) │  │                      │
│ - ...                │  │ - enhanced_error (1) │  │                      │
└──────────────────────┘  └──────────────────────┘  └──────────────────────┘
           │                           │                           │
           └───────────────────────────┼───────────────────────────┘
                                       │
                    ┌──────────────────┴──────────────────────┐
                    │        ExecutionCoordinator              │
                    │              (默认模式)                   │
                    │                                          │
                    │ 只使用:                                  │
                    │ - ReasoningAgent                         │
                    │ - ToolRegistry                          │
                    │ - QualityEvaluator                      │
                    └─────────────────────────────────────────┘
```

---

## 模块状态一览

| 模块 | 引用数 | 使用模式 | 说明 |
|------|--------|----------|------|
| **核心 (轻量模式必须)** ||||
| execution_coordinator.py | 3+ | 默认 | ✅ 生产使用 |
| AgentState | - | 默认 | ✅ 生产使用 |
| **扩展 (完整模式使用)** ||||
| langgraph_learning_nodes | 12 | 完整模式 | ✅ 大量使用 |
| langgraph_performance_monitor | 6 | 完整模式 | ✅ 大量使用 |
| langgraph_dynamic_workflow | 2 | 完整模式 | ✅ 有使用 |
| langgraph_error_recovery | 2 | 完整模式 | ✅ 有使用 |
| langgraph_capability_nodes | 3 | 完整模式 | ✅ 有使用 |
| langgraph_enhanced_error_recovery | 1 | 完整模式 | ✅ 有使用 |
| langgraph_parallel_execution | 1 | 完整模式 | ✅ 有使用 |
| **可能未使用** ||||
| langgraph_collaboration_nodes | 0 | - | ⚠️ 0引用 |

---

## 选择指南

| 场景 | 推荐模式 | 说明 |
|------|----------|------|
| 简单问答 | 默认 | 快速响应 |
| 生产环境 | 默认 | 稳定可靠 |
| 深度研究 | 完整模式 | RANGEN_USE_UNIFIED_RESEARCH=1 |
| 需要自学习 | 完整模式 | 启用持续学习 |
| 需要 Hook | 增强模式 | RANGEN_USE_ENHANCED=1 |

---

## 状态定义选择

| 状态类 | 字段数 | 使用场景 |
|--------|--------|----------|
| `AgentState` | 10 | ✅ 生产默认 (execution_coordinator) |
| `ExtendedAgentState` | 30+ | 推荐用于新功能开发 |
| `ReActState` | 15 | ReasoningAgent 内部使用 |
| `ResearchSystemState` | 60+ | 完整模式使用 |

---

## 结论

**不是冗余代码，而是双模式架构的体现：**

1. **轻量模式**: 默认使用，资源占用低
2. **完整模式**: 启用环境变量后使用，功能完整

所有之前标记为"弃用"的模块实际上都被**完整模式系统**使用，引用数就是最好的证明（有的高达12次引用！）。
