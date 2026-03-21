---
name: error-handling
version: 1.0.0
description: Handle errors gracefully and provide helpful recovery suggestions
author: RANGEN Team
tags: [error, exception, recovery, debugging]
triggers: [error, exception, fail, 错误, 异常, 失败]
dependencies: []
---

# Error Handling Skill

错误处理技能，优雅地处理错误并提供恢复建议。

## 触发条件

当系统发生错误时自动触发。

## 功能

### 1. 错误分类
- 网络错误
- 权限错误
- 格式错误
- 业务逻辑错误

### 2. 错误分析
- 错误原因分析
- 影响范围评估
- 错误上下文记录

### 3. 恢复建议
- 自动重试
- 参数调整
- 替代方案

### 4. 用户反馈
- 友好错误信息
- 解决步骤指引
- 支持联系方式

## 输出格式

```json
{
  "success": false,
  "error": {
    "type": "network_error",
    "message": "友好错误信息",
    "suggestion": "恢复建议",
    "can_retry": true
  }
}
```
