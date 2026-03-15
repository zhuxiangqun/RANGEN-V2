---
name: fact-check
version: 1.0.0
description: Verify claims and facts against reliable sources
author: RANGEN Team
tags: [fact-check, verification, validation]
triggers: [fact-check, 核实, 验证, 确认, verify, 是否真实]
dependencies: [web-search, query-analysis]
---

# Fact-Check Skill

事实核查技能，验证声明和事实的准确性。

## 触发条件

当用户请求包含以下关键词时自动触发：
- "fact-check"、"核实"
- "验证"、"verify"
- "是否真实"、"是真的吗"
- "确认"、"confirm"
- "查证"、"validate"

## 核查流程

```
1. 声明提取
   - 识别需要核查的内容
   - 分解为可验证的声明
   - 提取关键事实点

2. 证据搜集
   - 网络搜索相关来源
   - 查找权威资料
   - 交叉比对多个来源

3. 评估判断
   - 来源可靠性评估
   - 证据充分性分析
   - 给出核查结论
```

## 使用方法

```python
from src.agents.tools.search_tool import SearchTool

# 基础核查
search = SearchTool()
result = await search.call("地球是平的吗", max_results=5)

# 使用专门的核查工具
from src.agents.tools.citation_tool import CitationTool
citation = CitationTool()
result = await citation.verify_claims(claims=["声明1", "声明2"])
```

## 结论类型

| 结论 | 说明 | 颜色标识 |
|------|------|----------|
| TRUE | 声明正确，有充分证据支持 | 🟢 绿色 |
| MOSTLY_TRUE | 大部分正确，部分需要澄清 | 🟡 黄色 |
| PARTIALLY_TRUE | 部分正确，部分错误 | 🟠 橙色 |
| FALSE | 声明错误 | 🔴 红色 |
| UNVERIFIABLE | 无法验证 | ⚪ 灰色 |

## 输出格式

```json
{
  "success": true,
  "data": {
    "claim": "待核查声明",
    "verdict": "FALSE",
    "confidence": 0.95,
    "sources": [
      {
        "title": "来源标题",
        "url": "https://...",
        "reliability": "high",
        "evidence": "相关证据"
      }
    ],
    "explanation": "解释说明"
  }
}
```

## 与其他 Skill 的关系

- 依赖: `web-search` (网络搜索), `query-analysis` (查询分析)
- 被: `citation_agent`, `validation_agent` 调用
- 配合: `citation-generation` (引用生成)
