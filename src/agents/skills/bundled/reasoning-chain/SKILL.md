---
name: reasoning-chain
version: 1.0.0
description: Chain-of-thought reasoning skill for complex problem solving
author: RANGEN Team
tags: [reasoning, chain-of-thought, cot, logic]
triggers: [reasoning, 分析, 推理, think, chain, 思考过程]
dependencies: [query-analysis]
---

# Reasoning Chain Skill

思维链推理技能，用于复杂问题的分析和解决。

## 触发条件

当用户请求包含以下关键词时自动触发：
- "reasoning"、"分析"
- "推理"、"think"
- "怎么来的"、"why"
- "思考过程"、"chain"
- "逻辑"

## 核心推理类型

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| Deductive | 演绎推理 | 从一般到特殊 |
| Inductive | 归纳推理 | 从特殊到一般 |
| Abductive | 溯因推理 | 最佳解释推理 |
| Analogical | 类比推理 | 相似问题迁移 |
| Causal | 因果推理 | 原因结果分析 |

## 推理流程

```
1. 问题分解
   - 识别核心问题
   - 拆分子问题
   - 明确约束条件

2. 推理执行
   - 选择推理类型
   - 逐步推导
   - 记录中间结论

3. 结论验证
   - 检查逻辑一致性
   - 评估置信度
   - 识别潜在问题
```

## 使用方法

```python
from src.agents.tools.reasoning_tool import ReasoningTool

tool = ReasoningTool()
result = await tool.reason(
    query="为什么太阳是热的？",
    reasoning_type="causal"
)
```

## 置信度评估

| 级别 | 值 | 说明 |
|------|-----|------|
| VERY_HIGH | 0.9-1.0 | 充分证据支持 |
| HIGH | 0.7-0.9 | 较多证据支持 |
| MEDIUM | 0.5-0.7 | 部分证据支持 |
| LOW | 0.3-0.5 | 少量证据支持 |
| VERY_LOW | 0.0-0.3 | 推测性结论 |

## 输出格式

```json
{
  "success": true,
  "data": {
    "query": "原始问题",
    "reasoning_type": "causal",
    "steps": [
      {
        "step_id": "1",
        "description": "第一步推理",
        "premise": ["前提1", "前提2"],
        "inference": "推理结论",
        "confidence": 0.85
      }
    ],
    "final_conclusion": "最终结论",
    "overall_confidence": 0.82
  }
}
```

## 与其他 Skill 的关系

- 依赖: `query-analysis` (查询分析)
- 被: `reasoning_agent`, `react_agent` 调用
- 配合: `fact-check` (事实核查)
