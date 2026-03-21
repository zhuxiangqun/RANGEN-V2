---
name: citation-generation
version: 1.0.0
description: Generate citations and references for provided information
author: RANGEN Team
tags: [citation, reference, source]
triggers: [citation, 引用, 来源, reference, cite, 参考]
dependencies: [fact-check]
---

# Citation Generation Skill

引用生成技能，为回答添加来源和引用。

## 触发条件

当用户请求包含以下关键词时自动触发：
- "citation"、"引用"
- "来源"、"source"
- "参考"、"reference"
- "cite"、"cite"

## 引用格式

| 格式 | 说明 |
|------|------|
| APA | 作者, (年份). 标题. 来源 |
| MLA | 作者. "标题." 来源, 日期 |
| Chicago | 作者. "标题." 来源 (日期) |
| 简洁 | [来源1] |

## 使用方法

```python
from src.agents.tools.citation_tool import CitationTool

tool = CitationTool()

# 生成引用
result = await tool.generate_citations(
    content="人工智能是计算机科学的一个分支。",
    sources=["doc1.pdf", "doc2.pdf"],
    format="简洁"
)
```

## 输出格式

```json
{
  "success": true,
  "data": {
    "content": "原文内容",
    "citations": [
      {
        "text": "人工智能是计算机科学的一个分支[1]。",
        "references": [
          {"id": "1", "source": "doc1.pdf", "page": 5}
        ]
      }
    ]
  }
}
```

## 与其他 Skill 的关系

- 依赖: `fact-check` (事实核查)
- 被: `citation_agent` 调用
- 配合: `answer-generation` (答案生成)
