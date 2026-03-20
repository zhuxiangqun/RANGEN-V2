# Superpowers 与 RANGEN V2 集成对比分析

## 分析日期
2026-03-20

## Superpowers 概述

| 指标 | 数据 |
|------|------|
| Stars | 101k ⭐ |
| Forks | 8k |
| 创建时间 | 2025-10-09 |
| 最新版本 | v5.0.5 |
| 支持工具 | Claude Code, Cursor, Codex, Gemini CLI, OpenCode |

---

## 一、Superpowers 核心 Skills 清单

### 1.1 核心工作流 Skills

| Skill | 功能 | 关键特性 |
|-------|------|----------|
| **brainstorming** | 苏格拉底式需求讨论 | 设计先行、追问澄清、多方案对比 |
| **using-git-worktrees** | 隔离工作区 | 新分支、独立工作区 |
| **writing-plans** | 任务拆解 | 2-5分钟任务、精确文件路径 |
| **subagent-driven-development** | 子Agent驱动开发 | 双阶段审查、spec→quality |
| **test-driven-development** | 严格TDD | RED-GREEN-REFACTOR铁律 |
| **requesting-code-review** | 代码审查 | 严重程度分级、阻塞机制 |
| **finishing-a-development-branch** | 收尾合并 | 全量测试、多种选项 |

### 1.2 辅助 Skills

| Skill | 功能 |
|-------|------|
| **systematic-debugging** | 4阶段根因定位 |
| **verification-before-completion** | 修复验证 |
| **executing-plans** | 批量执行+检查点 |
| **dispatching-parallel-agents** | 并行Agent |
| **receiving-code-review** | 响应审查反馈 |
| **writing-skills** | 创建新Skill |

---

## 二、RANGEN V2 已有集成

### 2.1 已实现的组件

| 组件 | 文件 | 对应 Superpowers Skill |
|-------|------|----------------------|
| **TDDEnforcer** | `src/agents/tdd_enforcer.py` | test-driven-development |
| **TwoStageReviewer** | `src/agents/two_stage_reviewer.py` | requesting-code-review |
| **TaskPlanner** | `src/agents/task_planner.py` | writing-plans |
| **RequirementDiscovery** | `src/agents/requirement_discovery.py` | brainstorming |
| **MiddlewareChain** | `src/core/middleware.py` | (基础架构) |
| **AgentHUD** | `src/ui/agent_hud.py` | (可观测性) |

### 2.2 新增组件 (2026-03-20)

| 组件 | 文件 | 功能 |
|------|------|------|
| **HARD_GATE** | `src/agents/hard_gate.py` | 设计先行门控机制 |
| **StrictTDDEnforcer** | `src/agents/strict_tdd_enforcer.py` | 不可绕过TDD强制 |
| **BlockingReviewer** | `src/agents/blocking_reviewer.py` | Critical问题阻塞 |
| **SubagentDispatcher** | `src/agents/subagent_dispatcher.py` | 精确上下文构造 |
| **SpecReviewer** | `src/agents/spec_reviewer.py` | 规范合规检查 |
| **集成测试** | `tests/test_superpowers_enforcement.py` | 21个测试 |

### 2.2 已有实现分析

#### TDDEnforcer (376行)
```python
# 核心铁律
"NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST"

# 状态机
- RED: 写失败测试
- GREEN: 写最小实现
- REFACTOR: 重构
```

**与 Superpowers 对比**:
| 特性 | Superpowers | RANGEN |
|------|-------------|--------|
| 铁律执行 | Hard-gate | ✅ 已有 |
| 状态持久化 | .tdd_state.json | ✅ 已有 |
| 人类绕过 | 需要明确批准 | ✅ 已有 |
| 测试反模式检查 | @testing-anti-patterns | ⚠️ 缺失 |

#### TwoStageReviewer (481行)
```python
# 两阶段审查
Stage 1: Spec Compliance Review
Stage 2: Code Quality Review
```

**与 Superpowers 对比**:
| 特性 | Superpowers | RANGEN |
|------|-------------|--------|
| 双阶段审查 | ✅ | ✅ 已有 |
| 严重程度分级 | Critical/Important/Suggestion | ⚠️ 需完善 |
| 阻塞机制 | Critical阻塞 | ⚠️ 需完善 |
| 最大迭代限制 | 3次 | ⚠️ 需完善 |

#### TaskPlanner (484行)
```python
# 任务规划
- Bite-sized tasks (2-5 min)
- 精确文件路径
- 验证步骤
```

**与 Superpowers 对比**:
| 特性 | Superpowers | RANGEN |
|------|-------------|--------|
| 任务粒度 | 2-5分钟 | ✅ 已有 |
| 文件映射 | ✅ | ✅ 已有 |
| TDD步骤 | 失败→通过→提交 | ⚠️ 需完善 |
| 依赖追踪 | ✅ | ⚠️ 需完善 |

---

## 三、缺失的组件

### 3.1 高优先级缺失

| 组件 | 优先级 | 说明 |
|------|--------|------|
| **Spec Document Reviewer** | P1 | spec-document-reviewer 子Agent |
| **implementer Prompt** | P1 | 子Agent实现者Prompt模板 |
| **HARD-GATE 机制** | P1 | 强制设计阶段先行 |
| **Git Worktree 隔离** | P1 | 隔离工作区管理 |

### 3.2 中优先级缺失

| 组件 | 优先级 | 说明 |
|------|--------|------|
| **Parallel Dispatching** | P2 | 并行Agent分发 |
| **Spec Writer** | P2 | 设计文档自动生成 |
| **Feelings Journal** | P3 | AI情绪记录 |
| **Visual Companion** | P3 | 视觉辅助设计 |

---

## 四、Superpowers 关键创新点

### 4.1 HARD-GATE 机制

Superpowers 使用 `<HARD-GATE>` 标签强制执行：

```
<HARD-GATE>
Do NOT invoke any implementation skill... until you have presented a design and the user has approved it.
</HARD-GATE>
```

**RANGEN 可借鉴**: 在 `RequirementDiscovery` 中添加 HARD-GATE

### 4.2 子Agent 精确上下文

Superpowers 的子Agent从不继承父会话历史，而是接收精确构造的上下文：

```python
# Superpowers 模式
implementer_prompt = f"""
[Exact task description]
[File paths to work on]
[Verification steps]
[Context: why this matters]
"""

# 问题: 子Agent不应读取计划文件
# 解决: 主Agent提取并提供完整文本
```

### 4.3 两阶段审查顺序

Superpowers 强调 **先Spec合规，后代码质量**：

```
实现 → Stage1(Spec合规) → 修复 → Stage2(代码质量) → 修复
```

### 4.4 模型选择策略

| 任务类型 | 模型选择 |
|----------|----------|
| 机械实现 (1-2文件) | 快速/便宜模型 |
| 集成/判断 (多文件) | 标准模型 |
| 架构/设计/审查 | 最强模型 |

---

## 五、建议集成方案

### 5.1 Phase 1: 补齐核心 (P1)

| 任务 | 文件 | 说明 |
|------|------|------|
| 添加 SpecReviewer | `src/agents/spec_reviewer.py` | 规范审查子Agent |
| 添加 ImplementerPrompt | `src/prompts/implementer.py` | 子Agent实现者模板 |
| 完善 HARD-GATE | `src/agents/requirement_discovery.py` | 强制设计先行 |
| 添加 Worktree隔离 | `src/swarm/worktree.py` | 隔离工作区 |

### 5.2 Phase 2: 增强功能 (P2)

| 任务 | 文件 | 说明 |
|------|------|------|
| 完善严重程度分级 | `src/agents/two_stage_reviewer.py` | Critical阻塞 |
| 添加最大迭代限制 | `src/agents/two_stage_reviewer.py` | 3次上限 |
| 添加并行分发 | `src/agents/parallel_dispatcher.py` | 并行Agent |
| 完善TDD步骤 | `src/agents/task_planner.py` | 失败→通过→提交 |

### 5.3 Phase 3: 高级特性 (P3)

| 任务 | 文件 | 说明 |
|------|------|------|
| 添加 FeelingsJournal | `src/agents/feelings_journal.py` | 情绪记录 |
| 添加 VisualCompanion | `src/ui/visual_companion.py` | 视觉辅助 |
| 模型自动选择 | `src/agents/model_selector.py` | 基于任务复杂度 |

---

## 六、结论

### 6.1 已集成度

| Superpowers Skill | RANGEN 状态 |
|-------------------|-------------|
| brainstorming | ✅ 部分实现 (RequirementDiscovery) |
| test-driven-development | ✅ 完整实现 (TDDEnforcer) |
| writing-plans | ✅ 完整实现 (TaskPlanner) |
| requesting-code-review | ✅ 完整实现 (TwoStageReviewer) |
| subagent-driven-development | ⚠️ 需完善 (缺少SpecReviewer) |
| using-git-worktrees | ✅ 已实现 (WorktreeManager) |

### 6.2 差距分析

**优势**:
- RANGEN 有完整的 Agent 架构
- RANGEN 有 LangGraph 工作流引擎
- RANGEN 有 Skills 触发系统

**差距**:
- 缺少 Spec Document Reviewer 子Agent
- 缺少 HARD-GATE 强制机制
- 缺少 implementer prompt 模板
- 缺少 feelings journal

### 6.3 建议

**短期 (1-2周)**:
1. 添加 SpecReviewer 子Agent
2. 完善 HARD-GATE 机制
3. 添加 implementer prompt 模板

**中期 (1个月)**:
1. 完善严重程度分级和阻塞机制
2. 添加并行分发
3. 完善 TDD 步骤

**长期**:
1. 模型自动选择
2. Feelings Journal
3. Visual Companion
