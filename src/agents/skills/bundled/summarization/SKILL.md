---
name: summarization
version: 1.0.0
description: Summarize long content into concise summaries
author: RANGEN Team
tags: [summarization, summary, compress, nlg]
triggers: [summarize, 总结, 摘要, 概括, summary, 简短]
dependencies: [query-analysis]
---

# Summarization Skill

总结技能，将长内容压缩为简洁的摘要。

## 触发条件

当用户请求包含以下关键词时自动触发：
- "summarize"、"总结"
- "摘要"、"abstract"
- "概括"、"概括"
- "简短"、"brief"
- "核心观点"、"key points"

## 摘要类型

| 类型 | 长度 | 适用场景 |
|------|------|----------|
| Headline | 1句话 | 新闻标题 |
| Brief | 50字 | 快速预览 |
| Standard | 200字 | 一般总结 |
| Detailed | 500字+ | 深度理解 |

## 摘要方法

### 1. 抽取式 (Extractive)
- 直接从原文提取关键句子
- 保留原文措辞
- 快速但可能不够连贯

### 2. 生成式 (Abstractive)
- 理解内容后重新组织语言
- 更自然流畅
- 需要更强的语言模型

### 3. 指针网络 (Pointer-Generator)
- 结合抽取和生成
- 可以复制原文词汇
- 可以生成新内容

## 使用方法

```python
from src.agents.tools.answer_generation_tool import AnswerGenerationTool

tool = AnswerGenerationTool()
result = await tool.generate(
    query="总结以下内容",
    context=[{"content": "长篇内容..."}],
    style="brief"  # brief/standard/detailed
)
```

## 输出格式

```json
{
  "success": true,
  "data": {
    "original_length": 5000,
    "summary_length": 200,
    "summary": "摘要内容...",
    "compression_ratio": 0.04,
    "key_points": [
      "要点1",
      "要点2",
      "要点3"
    ]
  }
}
```

## 与其他 Skill 的关系

- 依赖: `query-analysis` (查询分析)
- 被: `rag_agent`, `expert_agent` 调用
- 配合: `answer-generation` (答案生成)
