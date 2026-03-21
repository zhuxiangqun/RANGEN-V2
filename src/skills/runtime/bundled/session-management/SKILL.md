---
name: session-management
version: 1.0.0
description: Manage conversation sessions and maintain state across interactions
author: RANGEN Team
tags: [session, conversation, state, history]
triggers: [session, history, conversation, 会话, 历史, 对话]
dependencies: [context-management]
---

# Session Management Skill

会话管理技能，管理对话会话并维护交互状态。

## 触发条件

当需要管理会话状态时触发。

## 功能

### 1. 会话创建
- 初始化会话
- 配置参数
- 上下文设置

### 2. 会话存储
- 历史记录
- 状态持久化
- 元数据管理

### 3. 会话恢复
- 历史检索
- 上下文重建
- 状态恢复

### 4. 会话清理
- 历史归档
- 资源释放
- 隐私处理

## 输出格式

```json
{
  "success": true,
  "data": {
    "session_id": "...",
    "created_at": "...",
    "message_count": 10,
    "last_message": "..."
  }
}
```
