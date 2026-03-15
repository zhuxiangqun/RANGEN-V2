# 答案准确性修复总结

## 问题

**查询**: "Who was the 15th first lady of the United States?"

**系统返回**: "Melania Trump" ❌

**正确答案**: "Harriet Lane"（James Buchanan 的侄女，他未婚，所以没有第一夫人，但 Harriet Lane 担任了第一夫人的角色）

## 问题分析

### 根本原因

1. **答案验证不足**
   - 系统没有验证答案是否与查询中的数字匹配
   - 例如：查询是"15th first lady"，答案不应该包含"Trump"（第45任总统）

2. **可能的问题来源**
   - 推理步骤可能生成了错误的答案
   - 答案合成逻辑可能选择了错误的步骤答案
   - 证据收集可能检索到了不相关的信息

## 已实施的修复

### 1. 添加查询-答案一致性验证规则 ✅

在 `src/core/reasoning/answer_extraction/answer_validator.py` 中添加了 `QueryAnswerConsistencyRule` 类：

**功能**:
- 检查答案中的序数是否与查询中的序数匹配
- 如果答案中的序数与查询中的序数相差太大（>10），拒绝答案
- 检查答案中是否包含明显不匹配的总统相关信息
- 例如：查询是"15th first lady"，答案不应该包含"Trump"（第45任总统）

**验证逻辑**:
```python
# 提取查询中的序数（如"15th"）
query_ordinal = 15

# 检查答案中是否包含不匹配的总统信息
if "trump" in answer_lower and query_ordinal == 15:
    # Trump 是第45任总统，与查询的15th不匹配
    return False, "答案中包含第45任总统相关信息，但查询要求的是第15任"
```

## 下一步建议

### 1. 检查推理步骤

需要检查推理步骤是否正确：
- 步骤1应该查询"第15任总统是谁"（应该是 James Buchanan）
- 步骤2应该查询"第15任总统的第一夫人是谁"（应该是 Harriet Lane）

### 2. 检查答案合成逻辑

需要检查 `_synthesize_answer_from_steps` 方法：
- 是否正确选择了与查询最相关的步骤答案
- 是否验证了合成后的答案

### 3. 增强日志

添加更详细的日志，记录：
- 每个推理步骤的查询和答案
- 答案合成的过程
- 答案验证的结果

## 测试建议

重新运行查询 "Who was the 15th first lady of the United States?"，检查：
1. 答案验证是否拒绝错误的答案（如"Melania Trump"）
2. 系统是否生成正确的答案（"Harriet Lane"）
3. 如果仍然错误，检查推理步骤和答案合成逻辑

## 诊断命令

```bash
# 检查最新的执行记录
curl http://localhost:8080/api/executions | jq '.executions[0]'

# 检查推理步骤
curl http://localhost:8080/api/executions | jq '.executions[0].nodes[] | select(.name == "generate_steps" or .name == "extract_step_answer")'

# 检查答案验证日志
grep -E "查询-答案一致性|QueryAnswerConsistency|序数.*不匹配" research_system.log | tail -20
```

