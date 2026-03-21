---
name: knowledge-graph
version: 1.0.0
description: Build and query knowledge graphs for structured information
author: RANGEN Team
tags: [knowledge, graph, entities, relationships]
triggers: [knowledge, graph, entities, 知识图谱, 实体, 关系]
dependencies: [query-analysis]
---

# Knowledge Graph Skill

知识图谱技能，构建和查询结构化知识图谱。

## 触发条件

当需要构建或查询知识图谱时触发：
- 实体识别
- 关系抽取
- 知识问答

## 功能

### 1. 图谱构建
- 实体识别
- 关系抽取
- 属性提取

### 2. 图谱查询
- 路径查询
- 邻居查询
- 聚合查询

### 3. 推理
- 关系推理
- 属性推理
- 类型推理

## 输出格式

```json
{
  "success": true,
  "data": {
    "entities": [{"id": "...", "type": "...", "name": "..."}],
    "relations": [{"source": "...", "relation": "...", "target": "..."}]
  }
}
```
