# 模板统一规范 v2.0

生成时间: 2025-12-04

## 一、统一输出格式规范

### 1.1 标准输出结构

所有推理模板必须返回以下统一格式：

```json
{
  "metadata": {
    "template_used": "template_name",
    "template_version": "2.0",
    "timestamp": "ISO8601格式",
    "workflow_id": "unique_id（可选）"
  },
  "reasoning": {
    "steps": [],
    "confidence": {
      "score": 0.85,
      "level": "high|medium|low"
    },
    "evidence_quality": "high|medium|low|none"
  },
  "answer": {
    "content": "具体答案",
    "format": "numerical|name|location|ranking|text",
    "validation_status": "verified|unverified|contradictory"
  }
}
```

### 1.2 置信度统一格式

**统一为**：
```json
{
  "confidence": {
    "score": 0.85,  // 0.0-1.0 数值
    "level": "high"  // high (>0.8), medium (0.5-0.8), low (<0.5)
  }
}
```

**映射规则**：
- `high` → `{"score": 0.9, "level": "high"}`
- `medium` → `{"score": 0.7, "level": "medium"}`
- `low` → `{"score": 0.3, "level": "low"}`

### 1.3 Final Answer 格式

**统一格式**：
```
---
FINAL ANSWER: [答案内容]
---
```

**要求**：
- 必须使用 `---` 作为分隔符
- 必须使用 `FINAL ANSWER:` 标记（英文）或 `最终答案:`（中文）
- 答案必须单独一行，不包含推理过程
- 最大长度：20个词

## 二、统一参数名称

### 2.1 参数映射表

| 旧参数名 | 新参数名 | 说明 |
|---------|---------|------|
| `{question}` | `{query}` | 统一使用 query |
| `{context_summary}` | `{context}` | 统一使用 context |
| `{evidence}` | `{evidence}` | 保持不变 |

### 2.2 必需参数

所有模板必须支持：
- `{query}` - 查询内容
- `{context}` - 上下文（可选）
- `{evidence}` - 证据（可选）
- `{query_type}` - 查询类型（可选）

## 三、简化步骤类型系统

### 3.1 步骤类型分类（4大类）

```json
{
  "step_categories": {
    "information": ["retrieve", "extract", "summarize"],
    "processing": ["deduce", "calculate", "compare", "causal_analyze"],
    "creative": ["brainstorm", "generate", "design"],
    "validation": ["verify", "cross_check", "sensitivity_analyze"]
  }
}
```

### 3.2 步骤类型映射

| 旧类型 | 新类型 | 类别 |
|--------|--------|------|
| `evidence_gathering` | `retrieve` | information |
| `knowledge_query` | `retrieve` | information |
| `logical_deduction` | `deduce` | processing |
| `calculation` | `calculate` | processing |
| `numerical_reasoning` | `calculate` | processing |
| `brainstorming` | `brainstorm` | creative |
| `validation` | `verify` | validation |

## 四、证据质量评估

### 4.1 证据质量等级

- `high`: 证据直接相关，来源可靠，信息完整
- `medium`: 证据部分相关，来源一般，信息部分完整
- `low`: 证据相关性低，来源不可靠，信息不完整
- `none`: 无证据

### 4.2 证据验证规则

1. **相关性检查**：证据是否与查询相关
2. **一致性检查**：证据之间是否一致
3. **完整性检查**：证据是否包含足够信息
4. **可靠性检查**：证据来源是否可靠

## 五、模板优先级链

### 5.1 选择规则

```json
{
  "template_selection_rules": [
    {
      "condition": "has_evidence AND evidence_quality > 0.7",
      "primary": "reasoning_with_evidence",
      "fallback": "reasoning_without_evidence"
    },
    {
      "condition": "query_type == 'creative'",
      "primary": "creative_writing",
      "fallback": "general_query"
    },
    {
      "condition": "default",
      "primary": "reasoning_without_evidence",
      "fallback": "general_query"
    }
  ]
}
```

## 六、实施优先级

### 第一阶段（立即修复）
1. ✅ 统一所有模板的 `final_answer` 格式
2. ✅ 统一置信度格式
3. ✅ 统一参数名称

### 第二阶段（架构优化）
1. 实现模板选择器
2. 添加证据质量评估层
3. 建立置信度校准系统

### 第三阶段（测试验证）
1. 测试用例设计
2. 性能监控
3. 持续优化

---

**规范版本**: 2.0
**最后更新**: 2025-12-04

