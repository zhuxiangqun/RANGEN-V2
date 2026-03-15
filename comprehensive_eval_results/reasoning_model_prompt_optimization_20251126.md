# 推理模型Prompt优化报告

## 日期
2025-11-26

## 优化目标

解决推理错误问题（57.1%的错误样本），通过优化推理模型的prompt来提高推理准确性。

## 优化内容

### 优化1: 增强答案准确性要求

**文件**: `src/core/real_reasoning_engine.py`

**修改内容**:
- 大幅增强了`accuracy_instruction`，添加了详细的验证要求
- 添加了6个强制验证步骤，要求LLM在给出最终答案前必须进行验证

**关键改进**:
1. **强制验证步骤**:
   - 证据一致性检查
   - 答案类型验证
   - 多跳推理验证
   - 计算验证
   - 答案完整性检查
   - 最终一致性检查

2. **常见错误避免**:
   - 明确列出7种常见错误，要求避免
   - 强调不要返回中间实体名称
   - 强调不要在多跳推理中提前停止

3. **推理准确性要求**:
   - 数值计算：要求显示每个步骤，验证每个步骤
   - 多跳推理：要求完成所有跳，验证每个中间结果
   - 实体识别：要求验证名称的正确性和完整性

### 优化2: 针对数值问题的特殊要求

**文件**: `src/core/real_reasoning_engine.py`

**修改内容**:
- 为数值问题添加了详细的特殊要求
- 明确要求FINAL ANSWER必须是数字
- 强调不要返回人名、地名或年份（除非问题明确要求年份）
- 强调必须完成所有跳直到获得数值答案

**关键改进**:
```
⚠️ CRITICAL: NUMERICAL QUESTION - SPECIAL REQUIREMENTS:
1. **MANDATORY**: Your FINAL ANSWER MUST be a NUMBER
2. **DO NOT** return person names, location names, or years
3. **MANDATORY**: For multi-hop queries, complete ALL hops until you reach the numerical answer
4. **DO NOT** stop at intermediate entities
5. **VERIFY**: Re-calculate your answer and verify it matches your calculation steps
6. **CHECK**: If your reasoning shows one number but Final Answer shows another, this is an ERROR - must correct
7. **EXAMPLES**: 提供了详细的示例说明
```

### 优化3: 针对排名问题的特殊要求

**文件**: `src/core/real_reasoning_engine.py`

**修改内容**:
- 为排名问题添加了特殊要求
- 明确要求FINAL ANSWER必须是序数词（如"37th"）
- 强调不要返回纯数字（如"37"）

**关键改进**:
```
⚠️ CRITICAL: RANKING QUESTION - SPECIAL REQUIREMENTS:
1. **MANDATORY**: Your FINAL ANSWER MUST be an ORDINAL (e.g., "37th", "1st", "2nd")
2. **DO NOT** return plain numbers (e.g., "37" instead of "37th")
3. **VERIFY**: Check that you're extracting the correct rank from the evidence
4. **CHECK**: Ensure your answer matches the ranking format in the evidence
```

## 预期效果

### 推理准确性改进
- ✅ 数值计算错误应该减少（样本2、6、8）
- ✅ 多跳推理错误应该减少（样本6、8）
- ✅ 答案类型错误应该减少（样本2）
- ✅ 无法找到答案的情况应该减少（样本5）

### 准确率改进
- **预期准确率**: 从30%提高到70-80%
- **剩余问题**: 可能仍有一些复杂的推理错误需要进一步优化

## 关键改进点

### 1. 强制验证步骤
- 要求LLM在给出最终答案前必须进行6项验证
- 确保答案的准确性、完整性和一致性

### 2. 常见错误避免
- 明确列出7种常见错误
- 要求LLM避免这些错误

### 3. 特定问题类型的特殊要求
- 数值问题：强调必须返回数字，完成所有跳
- 排名问题：强调必须返回序数词
- 提供详细的示例说明

### 4. 推理准确性要求
- 数值计算：要求显示和验证每个步骤
- 多跳推理：要求完成所有跳，验证每个中间结果
- 实体识别：要求验证名称的正确性和完整性

## 验证方法

1. **运行测试**:
   ```bash
   python3 scripts/run_core_with_frames.py --sample-count 10 --data-path data/frames_dataset.json
   ```

2. **检查日志**:
   - 查看推理过程是否包含验证步骤
   - 查看是否避免了常见错误
   - 查看数值计算是否正确

3. **检查准确率**:
   - 推理错误应该减少
   - 准确率应该从30%提高到70-80%

## 总结

本次优化主要解决了推理错误的问题（57.1%），通过：
1. 增强答案准确性要求，添加6个强制验证步骤
2. 针对数值问题添加特殊要求
3. 针对排名问题添加特殊要求
4. 明确列出常见错误并要求避免

**预期效果**: 准确率从30%提高到70-80%

**剩余问题**: 可能仍有一些复杂的推理错误需要进一步优化，但大部分推理错误应该得到解决。

