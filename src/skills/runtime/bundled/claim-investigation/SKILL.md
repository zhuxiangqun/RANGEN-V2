---
name: claim-investigation
version: 1.0.0
description: Investigate and verify claims against reliable sources
author: RANGEN Team
tags: [fact-check, verification, research]
triggers: [claim, verify, investigate, 声称, 验证, 调查]
dependencies: [fact-check, web_search]
---

# Claim Investigation Skill

主张调查技能，验证和调查各种声明的真实性。

## 触发条件

当用户提出需要验证的主张时触发：
- "验证这个说法"
- "这是真的吗"
- "调查这个声称"

## 调查流程

### 1. 主张提取
- 识别核心主张
- 提取关键断言
- 确定验证方向

### 2. 信息收集
- 网络搜索
- 知识库检索
- 多源交叉验证

### 3. 分析评估
- 事实核查
- 来源评估
- 逻辑分析

### 4. 结论输出
- 明确结论（真/假/不确定）
- 证据支持
- 不确定原因说明

## 输出格式

```json
{
  "success": true,
  "data": {
    "claim": "原始主张",
    "verdict": "true|false|uncertain",
    "confidence": 0.85,
    "evidence": [
      {"source": "来源", "content": "证据内容", "reliability": "high|medium|low"}
    ],
    "reasoning": "推理过程"
  }
}
```
