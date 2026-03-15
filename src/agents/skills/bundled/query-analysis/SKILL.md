---
name: query-analysis
version: 1.0.0
description: Analyze and understand user queries for better processing
author: RANGEN Team
tags: [query, analysis, nlu, understanding]
triggers: [分析, query, 理解, analyze, 意图]
dependencies: []
---

# Query Analysis Skill

查询分析技能，理解用户查询的意图和关键信息。

## 触发条件

当系统处理任何查询时自动触发（基础技能）

## 分析维度

### 1. 意图识别 (Intent Classification)
- informational: 寻求信息
- transactional: 执行操作
- navigational: 导航查询
- conversational: 对话闲聊

### 2. 实体提取 (Entity Extraction)
- 人名、地名、机构名
- 时间表达式
- 数值、数量
- 专业术语

### 3. 关键词提取
- 核心关键词
- 扩展关键词
- 同义词

### 4. 查询类型判断
- 简单事实型
- 解释型
- 比较型
- 原因型
- 方法型

## 使用方法

```python
# 作为独立工具使用
from src.agents.tools.search_tool import SearchTool

search = SearchTool()
# search 内部会调用 query-analysis
result = await search.call("Python 异步编程教程")
```

## 输出格式

```json
{
  "success": true,
  "data": {
    "original_query": "Python 异步编程教程",
    "intent": "informational",
    "entities": [
      {"type": "topic", "value": "Python"},
      {"type": "topic", "value": "异步编程"},
      {"type": "type", "value": "教程"}
    ],
    "keywords": ["Python", "异步编程", "教程"],
    "query_type": "方法型",
    "expanded_queries": [
      "Python 异步编程 教程",
      "Python asyncio 入门",
      "Python async await"
    ],
    "language": "zh"
  }
}
```

## 与其他 Skill 的关系

- 基础技能：被大多数其他 Skills 依赖
- 被: 所有需要处理用户查询的 Agent 调用
