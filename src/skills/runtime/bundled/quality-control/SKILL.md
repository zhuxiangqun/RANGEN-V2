---
name: quality-control
version: 1.0.0
description: Control and assure output quality across all operations
author: RANGEN Team
tags: [quality, control, assurance, validation]
triggers: [quality, check, validate, assurance, 质量, 检查, 验证]
dependencies: [fact-check, query-analysis]
---

# Quality Control Skill

质量控制技能，控制和保证所有操作的输出质量。

## 触发条件

当需要质量控制时自动触发。

## 功能

### 1. 质量评估
- 完整性检查
- 准确性验证
- 一致性检查

### 2. 质量改进
- 问题识别
- 改进建议
- 迭代优化

### 3. 质量报告
- 质量评分
- 问题汇总
- 改进跟踪

## 输出格式

```json
{
  "success": true,
  "data": {
    "quality_score": 0.95,
    "checks": [{"name": "...", "passed": true}],
    "issues": [{"severity": "low", "description": "..."}]
  }
}
```
