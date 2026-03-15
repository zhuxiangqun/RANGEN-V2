---
name: rag-retrieval
version: 1.0.0
description: RAG retrieval skill - retrieves relevant information from knowledge base
author: RANGEN Team
tags: [rag, retrieval, knowledge, vector]
triggers: [rag, retrieval, 检索, 知识库, 查找资料]
dependencies: [query-analysis]
---

# RAG Retrieval Skill

从知识库中检索相关信息，用于增强 AI 回答的准确性。

## 触发条件

当用户请求包含以下关键词时自动触发：
- "检索"、"retrieval"、"RAG"
- "知识库"、"knowledge base"
- "查找资料"、"search"
- "基于文档"、"based on"

## 核心功能

### 1. 向量检索 (Vector Search)
- 使用语义相似度匹配
- 适用于概念理解
- 阈值：0.7-0.85

### 2. 关键词检索 (Keyword Search)
- 精确匹配关键词
- 适用于专有名词、术语

### 3. 混合检索 (Hybrid Search)
- 向量 + 关键词组合
- RRF 融合排序

## 检索流程

```
1. 查询理解
   - 提取核心实体
   - 识别查询意图
   - 扩展相关术语

2. 检索执行
   - 选择合适的检索策略
   - 设置检索数量(通常5-15条)
   - 应用过滤条件

3. 结果处理
   - 相关性排序
   - 去重处理
   - 片段拼接
```

## 使用方法

```python
from src.agents.tools.rag_tool import RAGTool

rag = RAGTool()
result = await rag.retrieve(query="Python 异步编程", top_k=5)
```

## 返回格式

```json
{
  "success": true,
  "data": {
    "query": "查询内容",
    "chunks": [
      {
        "content": "相关文档片段",
        "score": 0.85,
        "source": "document.pdf"
      }
    ],
    "count": 5
  }
}
```

## 质量指标

| 指标 | 说明 |
|------|------|
| Hit Rate @K | 前K个结果包含相关信息 |
| MRR | 平均倒数排名 |
| NDCG | 归一化折损累积增益 |

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| 召回太低 | 降低阈值，添加同义词 |
| 精确太低 | 提高阈值，增加关键词过滤 |
| 无结果 | 扩展查询，尝试不同表述 |

## 与其他 Skill 的关系

- 依赖: `query-analysis` (查询分析)
- 被: `rag_agent`, `retrieval_agent` 调用
- 后续: `answer-generation` (答案生成)
