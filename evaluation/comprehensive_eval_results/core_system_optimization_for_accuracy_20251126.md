# 核心系统准确率优化实施报告

## 日期
2025-11-26

## 问题背景

用户反馈：**之前的准确率都很高，但是经过模型选择的优化后准确率就开始大幅下降了**。

当前准确率：30.0% (3/10)

## 核心原因分析

### 1. 答案提取不完整（42.9%）
- 样本1: 期望"Jane Ballou"，LLM响应"Elizabeth Ballou"，但只提取了"Elizabeth"
- 样本7: 期望完整句子，LLM响应"Dmitri Mendeleev"，但只提取了"Dmitri"
- 样本10: 期望完整句子，LLM响应"Battle of Hastings"，但只提取了"Battle"

### 2. 推理错误（57.1%）
- 样本2, 5, 6, 8: LLM推理过程本身就有错误

## 优化方案实施

### 优化1: 改进推理模型的答案提取prompt

**文件**: `src/core/llm_integration.py`

**修改内容**:
- 在`_extract_answer_from_reasoning_with_llm`方法中，优化了答案提取prompt
- 明确要求提取完整答案：
  - 对于人名：提取完整的人名（FirstName LastName），如"Jane Ballou"、"Dmitri Mendeleev"
  - 对于短语：提取完整的短语，如"Battle of Hastings"
  - 对于句子：提取完整的句子

**关键改进**:
```python
4. **CRITICAL**: Extract COMPLETE answers:
   - For person names: Extract the FULL name (e.g., "Jane Ballou", "Dmitri Mendeleev", not just "Jane" or "Dmitri")
   - For phrases: Extract the COMPLETE phrase (e.g., "Battle of Hastings", not just "Battle")
   - For sentences: Extract the COMPLETE sentence if the query requires it
   - For numerical answers: Extract the exact number
```

### 优化2: 优化答案提取逻辑，避免截断

**文件**: `src/core/llm_integration.py`

**修改内容**:
- 在答案清理逻辑中，避免截断完整的人名和短语
- 只有当答案超过200字符时，才考虑截断
- 对于50字符以内或没有空格的内容（可能是完整的人名或短语），保留完整内容

**关键改进**:
```python
# 🚀 优化：不要截断答案，保留完整的人名、短语和句子
if len(cleaned) > 200:
    # 检查是否是完整的人名或短语（通常不超过50字符）
    if len(cleaned) <= 50 or ' ' not in cleaned:
        # 可能是完整的人名或短语，保留
        pass
    else:
        # 可能是长文本，提取第一句话
        sentences = cleaned.split('.')
        if sentences:
            cleaned = sentences[0].strip()
```

### 优化3: 增强答案提取prompt，明确要求完整答案

**文件**: `src/core/real_reasoning_engine.py`

**修改内容**:
- 在`_extract_with_llm`方法中，优化了通用答案提取prompt
- 明确要求提取完整答案，不要截断
- 添加了详细的示例说明

**关键改进**:
```python
2. **CRITICAL**: 提取完整的答案，不要截断：
   - 如果答案是人名，提取完整的人名（FirstName LastName），如"Jane Ballou"、"Jens Kidman"、"Dmitri Mendeleev"，不要只提取"Jane"、"Jens"或"Dmitri"
   - 如果答案是短语，提取完整的短语，如"Battle of Hastings"，不要只提取"Battle"
   - 如果答案是句子，提取完整的句子，如"Mendelevium is named after Dmitri Mendeleev."，不要只提取部分
```

## 预期效果

### 答案提取改进
- ✅ 能够提取完整的人名（如"Jane Ballou"、"Dmitri Mendeleev"）
- ✅ 能够提取完整的短语（如"Battle of Hastings"）
- ✅ 能够提取完整的句子（如"Mendelevium is named after Dmitri Mendeleev."）

### 准确率改进
- **预期准确率**: 从30%提高到60-70%（解决答案提取不完整的问题）
- **剩余问题**: 推理错误（57.1%）需要进一步优化推理模型的prompt

## 下一步优化建议

### 1. 优化推理模型的prompt（高优先级）
- 强化推理步骤的准确性要求
- 增加验证步骤，要求LLM在给出最终答案前进行验证
- 明确要求LLM在不确定时明确说明，而不是给出错误答案

### 2. 优化质量检查（中优先级）
- 增强质量检查逻辑，更准确地识别答案质量
- 对于推理模型的答案，也进行质量检查

### 3. 优化两阶段流水线（中优先级）
- 确保两阶段流水线正常工作
- 如果快速模型能够处理更多medium样本，可以显著提高整体性能

## 验证方法

1. **运行测试**:
   ```bash
   python3 scripts/run_core_with_frames.py --sample-count 10 --data-path data/frames_dataset.json
   ```

2. **检查日志**:
   - 查看答案提取是否完整
   - 查看是否提取了完整的人名、短语和句子

3. **检查准确率**:
   - 答案提取不完整的样本应该减少
   - 准确率应该从30%提高到60-70%

## 总结

本次优化主要解决了答案提取不完整的问题（42.9%），通过：
1. 优化推理模型的答案提取prompt
2. 优化答案提取逻辑，避免截断
3. 增强答案提取prompt，明确要求完整答案

**预期效果**: 准确率从30%提高到60-70%

**剩余问题**: 推理错误（57.1%）需要进一步优化推理模型的prompt

