---
name: research-workflow
version: 1.0.0
description: Guide agents through structured research process
author: RANGEN Team
tags: [research, workflow, investigation, study]
triggers: [research, 研究, 调查, 研究报告, investigate, 研究]
dependencies: [query-analysis, web-search, rag-retrieval, fact-check, answer-generation]
---

# Research Workflow Skill

研究工作流技能，指导结构化研究和报告生成。

## 触发条件

当用户请求包含以下关键词时自动触发：
- "research"、"研究"
- "调查"、"investigate"
- "研究报告"、"analysis"
- "深度分析"、"comprehensive"

## 研究流程

```
┌─────────────────────────────────────────────────────────────┐
│                    研究工作流 (6 阶段)                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 规划阶段                                                │
│     - 明确研究目标                                           │
│     - 制定研究计划                                           │
│     - 识别关键问题                                           │
│                          ↓                                   │
│  2. 信息搜集                                                │
│     - 网络搜索                                               │
│     - 知识库检索                                             │
│     - 多角度查询                                             │
│                          ↓                                   │
│  3. 来源分析                                                │
│     - 评估可靠性                                             │
│     - 交叉验证                                               │
│     - 提取关键信息                                           │
│                          ↓                                   │
│  4. 综合分析                                                │
│     - 主题聚合                                               │
│     - 观点对比                                               │
│     - 趋势识别                                               │
│                          ↓                                   │
│  5. 报告生成                                                │
│     - 结构化输出                                             │
│     - 添加引用                                               │
│     - 质量检查                                               │
│                          ↓                                   │
│  6. 审核优化                                                │
│     - 事实核查                                               │
│     - 逻辑验证                                               │
│     - 完善补充                                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 使用方法

```python
# 研究工作流通常由 expert_agent 或 chief_agent 调用
from src.agents.expert_agent import ExpertAgent

agent = ExpertAgent()
result = await agent.conduct_research(
    topic="人工智能在医疗领域的应用",
    depth="comprehensive"  # brief/detailed/comprehensive
)
```

## 输出格式

```json
{
  "success": true,
  "data": {
    "topic": "人工智能在医疗领域的应用",
    "executive_summary": "执行摘要...",
    "sections": [
      {
        "title": "诊断辅助",
        "content": "详细内容...",
        "sources": ["source1", "source2"]
      }
    ],
    "conclusions": ["结论1", "结论2"],
    "sources_count": 15,
    "quality_score": 0.9
  }
}
```

## 与其他 Skill 的关系

- 依赖: 
  - `query-analysis` (查询分析)
  - `web-search` (网络搜索)
  - `rag-retrieval` (知识检索)
  - `fact-check` (事实核查)
  - `answer-generation` (答案生成)
- 被: `expert_agent` 调用
