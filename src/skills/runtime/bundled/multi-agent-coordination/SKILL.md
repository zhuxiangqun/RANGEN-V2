---
name: multi-agent-coordination
version: 1.0.0
description: Coordinate multiple agents for complex collaborative tasks
author: RANGEN Team
tags: [multi-agent, coordination, collaboration, team]
triggers: [coordinat, team, collaborate, multi-agent, 协调, 协作, 团队]
dependencies: [query-analysis]
---

# Multi-Agent Coordination Skill

多智能体协调技能，协调多个智能体完成复杂协作任务。

## 触发条件

当需要协调多个智能体时触发：
- 复杂任务分解
- 并行任务执行
- 结果聚合

## 功能

### 1. 任务分解
- 识别可并行子任务
- 评估依赖关系
- 分配执行角色

### 2. 协调执行
- 同步/异步执行
- 状态监控
- 冲突处理

### 3. 结果聚合
- 结果收集
- 冲突解决
- 统一输出

## 输出格式

```json
{
  "success": true,
  "data": {
    "task_id": "...",
    "subtasks": [{"id": "...", "status": "completed"}],
    "aggregated_result": {...}
  }
}
```
