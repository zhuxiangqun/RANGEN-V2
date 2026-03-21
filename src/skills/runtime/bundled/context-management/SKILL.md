---
name: context-management
version: 1.0.0
description: Manage conversation context and maintain state across interactions
author: RANGEN Team
tags: [context, memory, state, conversation]
triggers: [context, remember, 上下文, 记住, state]
dependencies: []
---

# Context Management Skill

上下文管理技能，维护对话状态和上下文信息。

## 触发条件

当需要管理对话上下文时触发：
- 多轮对话
- 状态维护
- 上下文压缩

## 功能

### 1. 上下文存储
- 保存对话历史
- 维护实体状态
- 跟踪对话目标

### 2. 上下文检索
- 语义检索
- 关键词检索
- 时间范围检索

### 3. 上下文压缩
- 摘要生成
- 关键信息提取
- 历史裁剪

### 4. 状态管理
- 用户偏好
- 任务进度
- 临时变量

## 使用方法

```python
from src.orchestration.context_engineering.context_manager import ContextManager

ctx = ContextManager()
ctx.add_message("user", "我想学习Python")
ctx.get_context()
```
