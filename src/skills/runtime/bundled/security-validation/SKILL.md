---
name: security-validation
version: 1.0.0
description: Validate security aspects of inputs and operations
author: RANGEN Team
tags: [security, validation, safety, protection]
triggers: [security, validate, safe, protect, 安全, 验证, 保护]
dependencies: []
---

# Security Validation Skill

安全验证技能，验证输入和操作的安全性。

## 触发条件

当需要安全验证时自动触发：
- 用户输入验证
- 权限检查
- 敏感操作确认

## 功能

### 1. 输入验证
- 恶意代码检测
- 注入攻击防护
- 格式校验

### 2. 权限检查
- 身份验证
- 授权检查
- 审计日志

### 3. 安全建议
- 风险评估
- 安全加固
- 合规检查

## 输出格式

```json
{
  "success": true,
  "data": {
    "is_safe": true,
    "risks": [],
    "recommendations": []
  }
}
```
