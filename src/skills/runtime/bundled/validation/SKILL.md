---
name: validation
version: 1.0.0
description: Validate inputs, outputs, and intermediate results
author: RANGEN Team
tags: [validation, verification, check, input, output]
triggers: [validate, verify, check, 验证, 检查, 校验]
dependencies: []
---

# Validation Skill

验证技能，验证输入、输出和中间结果。

## 触发条件

当需要进行验证时自动触发。

## 功能

### 1. 输入验证
- 类型检查
- 范围检查
- 格式验证
- 完整性检查

### 2. 输出验证
- 结果正确性
- 格式一致性
- 边界情况

### 3. 规则验证
- 业务规则
- 约束条件
- 依赖关系

### 4. 验证报告
- 验证结果
- 问题列表
- 改进建议

## 输出格式

```json
{
  "success": true,
  "data": {
    "is_valid": true,
    "checks": [{"name": "...", "passed": true}],
    "issues": []
  }
}
```
