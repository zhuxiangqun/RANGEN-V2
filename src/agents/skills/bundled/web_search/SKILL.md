---
name: web_search
version: 1.0.0
description: Web search capability using multiple search engines
author: RANGEN Team
tags: [search, web, retrieval]
triggers: [search, web_search, 搜索, 联网搜索]
dependencies: []
---

# Web Search Skill

提供网络搜索能力，支持多种搜索引擎。

## 触发条件

当用户请求包含以下关键词时自动触发：
- "搜索"、"search"
- "查找"、"find"
- "联网"、"web"
- "最新消息"、"recent"

## 支持的搜索引擎

| 引擎 | 优先级 | API 需要 | 说明 |
|------|--------|----------|------|
| Tavily | 1 | ✅ API Key | 实时搜索，AI 摘要 |
| DuckDuckGo | 2 | ❌ | 浏览器自动化 |
| Bing | 3 | ✅ API Key | 微软搜索 |

## 使用方法

### 1. Tavily API (推荐)

```python
# 设置环境变量
export TAVILY_API_KEY="your-api-key"

# 调用
from src.agents.tools.real_search_tool import RealSearchTool

tool = RealSearchTool()
result = await tool.call("Python 教程", max_results=5)
```

### 2. DuckDuckGo (无需 API)

```python
from src.agents.tools.web_search_tool import WebSearchTool

tool = WebSearchTool()
result = await tool.call("machine learning", max_results=5)
```

## 返回格式

```json
{
  "success": true,
  "data": {
    "query": "搜索关键词",
    "answer": "AI 生成的摘要",
    "results": [
      {
        "title": "结果标题",
        "url": "https://...",
        "content": "内容摘要"
      }
    ],
    "count": 5
  }
}
```

## 配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| query | string | 必填 | 搜索关键词 |
| max_results | int | 5 | 返回结果数量 |
| include_answer | bool | true | 是否包含 AI 摘要 |
| take_screenshot | bool | false | 是否截图 (仅 DuckDuckGo) |

## 错误处理

- `TAVILY_API_KEY 未设置`: 使用 DuckDuckGo 备用
- `网络超时`: 返回空结果并记录日志
- `API 限流`: 自动重试 3 次

## 与其他 Skill 的关系

- 依赖: `query-analysis` (查询分析)
- 被: `retrieval_agent`, `react_agent` 调用
