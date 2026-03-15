---
name: answer-generation
version: 1.0.0
description: Generate comprehensive answers from retrieved information
author: RANGEN Team
tags: [answer, generation, nlg, synthesis]
triggers: [answer, 生成回答, 总结, summarize, 回答]
dependencies: [rag-retrieval, citation-generation]
---

# Answer Generation Skill

答案生成技能，基于检索到的信息生成完整、准确的回答。

## 触发条件

当用户请求包含以下关键词时自动触发：
- "answer"、"回答"
- "生成"、"generate"
- "总结"、"summarize"
- "说明"、"explain"

## 生成流程

```
1. 信息整合
   - 整理检索结果
   - 识别关键信息
   - 去除冗余内容

2. 回答构建
   - 组织答案结构
   - 填充关键信息
   - 添加必要解释

3. 质量保证
   - 检查事实准确性
   - 添加引用来源
   - 确保回答完整
```

## 使用方法

```python
from src.agents.tools.answer_generation_tool import AnswerGenerationTool

tool = AnswerGenerationTool()
result = await tool.generate(
    query="什么是机器学习？",
    context=[
        {"content": "机器学习是AI的一个分支...", "source": "doc1"},
        {"content": "机器学习使用算法...", "source": "doc2"}
    ],
    style="comprehensive"  # brief/detailed/comprehensive
)
```

## 回答风格

| 风格 | 说明 | 适用场景 |
|------|------|----------|
| brief | 简洁明了 | 快速问答 |
| detailed | 详细解释 | 学习理解 |
| comprehensive | 全面完整 | 报告撰写 |

## 输出格式

```json
{
  "success": true,
  "data": {
    "query": "原始问题",
    "answer": "生成的回答内容...",
    "sources": [
      {"source": "doc1", "relevance": 0.9},
      {"source": "doc2", "relevance": 0.7}
    ],
    "style": "comprehensive",
    "word_count": 350
  }
}
```

## 与其他 Skill 的关系

- 依赖: `rag-retrieval` (检索), `citation-generation` (引用)
- 前置: `query-analysis` (查询分析)
- 被: `rag_agent`, `expert_agent` 调用
