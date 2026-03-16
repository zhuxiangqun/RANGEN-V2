# RANGEN 架构原则

> 详细说明 RANGEN 系统的架构约束和边界

---

## 分层架构

```
Types → Config → Repo → Service → Runtime → UI
```

任何违反依赖方向的代码都会被机械化拦截。

---

## 核心组件

### ExecutionCoordinator (生产核心)

- 位置: `src/core/execution_coordinator.py`
- 状态: `AgentState` (10字段)
- 节点: 5个 (router, direct_executor, reasoning_engine, quality_evaluator, error_handler)

### ProductionWorkflow (备用)

- 位置: `src/core/production_workflow.py`
- 状态: `ProductionState` (30字段)

---

## 架构约束机制

### 1. 确定性 Linter

- 输出格式专为 Agent 设计
- 包含修复建议
- 可自动修复

### 2. Tool Policy

- 风险等级评估
- 策略引擎控制
- 权限管理

### 3. 依赖检查

```
禁止:
- Service 层调用 UI 层
- Runtime 层调用 Config 层
- 直接修改外部状态
```

---

## 禁止模式

| 模式 | 说明 | 处罚 |
|------|------|------|
| 硬编码配置 | 禁止在代码中写死配置 | Linter 警告 |
| 循环依赖 | 禁止 A→B→A | 构建失败 |
| 未捕获异常 | 禁止 bare except | 测试失败 |

---

## 更新原则

- 每次 Agent 犯新类型错误 → 回头加约束
- 日积月累，Harness 越来越健壮
- "让 Agent 永远不再犯同样的错误"
