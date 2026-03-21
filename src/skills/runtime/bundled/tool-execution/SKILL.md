---
name: tool-execution
version: 1.0.0
description: Execute tools and manage tool calling lifecycle
author: RANGEN Team
tags: [tool, execution, function-call, api]
triggers: [execute, tool, function, call, 执行, 工具, 函数]
dependencies: []
---

# Tool Execution Skill

工具执行技能，执行工具并管理工具调用生命周期。

## 触发条件

当需要执行工具时触发。

## 功能

### 1. 工具发现
- 可用工具列表
- 工具能力描述
- 参数规范

### 2. 工具调用
- 参数验证
- 安全检查
- 执行调度

### 3. 结果处理
- 结果格式化
- 错误处理
- 日志记录

### 4. 工具管理
- 工具注册
- 权限控制
- 版本管理

## 输出格式

```json
{
  "success": true,
  "data": {
    "tool_name": "...",
    "parameters": {...},
    "result": {...},
    "execution_time_ms": 100
  }
}
```
