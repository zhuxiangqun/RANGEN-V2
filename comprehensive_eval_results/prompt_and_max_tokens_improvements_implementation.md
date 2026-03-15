# 提示词和max_tokens改进实施总结

**实施时间**: 2025-11-09  
**优先级**: P1  
**状态**: ✅ 已完成

---

## ✅ 已实施的改进

### 改进1：改进提示词，引导LLM优先输出答案（P1）

**位置**: `templates/templates.json` - `reasoning_with_evidence` 和 `reasoning_without_evidence`

**改进内容**:

1. **在 "Reasoning Transparency" 部分添加**:
```
✅ **IMPORTANT**: If the reasoning process is long, you can provide a preliminary answer in Step 3 (Answer Synthesis), then confirm it in Final Answer
✅ **CRITICAL**: Ensure the answer is provided even if the reasoning process is truncated
```

2. **在 "Step 3: Answer Synthesis" 部分添加**:
```
- **IMPORTANT**: If reasoning process is long, provide preliminary answer here to ensure it's not lost if truncated
```

3. **在 "Final Answer" 部分添加**:
```
**CRITICAL**: Ensure the answer is provided even if the reasoning process is truncated. If you provided a preliminary answer in Step 3, confirm it here.
```

**预期效果**:
- LLM会在推理过程中优先输出答案（在Step 3中提供初步答案）
- 即使推理过程被截断，答案也可能已经输出
- 减少截断的影响

---

### 改进2：动态调整 max_tokens（P1）

**位置**: `src/core/llm_integration.py`

**改进内容**:

1. **修改 `_get_max_tokens` 方法**:
```python
def _get_max_tokens(self, model: str, query_complexity: Optional[str] = None) -> int:
    """根据查询复杂度动态调整max_tokens"""
    base_tokens = 6000 if "reasoner" in model.lower() else 2000
    
    if query_complexity:
        if query_complexity == "complex":
            adjusted_tokens = int(base_tokens * 1.5)  # 复杂问题：推理模型9000，其他3000
        elif query_complexity == "simple":
            adjusted_tokens = int(base_tokens * 0.8)  # 简单问题：推理模型4800，其他1600
        else:
            adjusted_tokens = base_tokens  # 中等问题：推理模型6000，其他2000
    else:
        adjusted_tokens = base_tokens
    
    return int(adjusted_tokens)
```

2. **实现 `_estimate_query_complexity` 方法**:
```python
def _estimate_query_complexity(self, prompt: str) -> str:
    """估算查询复杂度
    
    简单启发式方法：
    - 简单问题：短查询，单一事实问题
    - 中等问题：中等长度，需要一些推理
    - 复杂问题：长查询，多步骤推理，复杂逻辑
    """
    prompt_length = len(prompt)
    word_count = len(prompt.split())
    
    # 检查复杂查询的关键词
    complexity_keywords = ["compare", "analyze", "explain", "why", "how", ...]
    has_complexity_keywords = any(keyword in prompt.lower() for keyword in complexity_keywords)
    
    # 检查是否包含多步骤推理的指示
    has_multi_step = any(indicator in prompt.lower() for indicator in [
        "step 1", "step 2", "first", "then", "next", "finally", ...
    ])
    
    # 简单启发式判断
    if prompt_length < 100 and word_count < 20 and not has_complexity_keywords:
        return "simple"
    elif prompt_length > 500 or word_count > 100 or has_multi_step or (has_complexity_keywords and word_count > 30):
        return "complex"
    else:
        return "medium"
```

3. **在 `_call_deepseek` 中调用**:
```python
# 🚀 P1改进：根据查询复杂度动态调整max_tokens
query_complexity = self._estimate_query_complexity(prompt)
max_tokens = self._get_max_tokens(self.model, query_complexity)
```

**预期效果**:
- 简单问题使用较少tokens（推理模型4800，其他1600）- 节省成本和时间
- 中等问题使用默认tokens（推理模型6000，其他2000）
- 复杂问题使用更多tokens（推理模型9000，其他3000）- 避免截断
- 提高资源利用效率

---

## 📊 改进效果预估

### 改进前

**提示词**:
- 要求按 "Step 1 → Step 2 → Step 3 → Final Answer" 顺序输出
- 如果推理过程很长，答案在最后，可能被截断

**max_tokens**:
- 所有查询使用相同的max_tokens（推理模型6000，其他2000）
- 简单问题浪费tokens
- 复杂问题可能仍然不够

---

### 改进后（预期）

**提示词**:
- LLM会在Step 3中提供初步答案
- 即使推理过程被截断，答案也可能已经输出
- 减少截断的影响

**max_tokens**:
- 简单问题：推理模型4800，其他1600（节省20%）
- 中等问题：推理模型6000，其他2000（保持不变）
- 复杂问题：推理模型9000，其他3000（增加50%）
- 提高资源利用效率

---

## 🎯 核心改进点

### 1. 引导LLM优先输出答案

**改进前**:
- 答案在推理过程的最后
- 如果推理过程被截断，答案可能丢失

**改进后**:
- LLM在Step 3中提供初步答案
- 即使推理过程被截断，答案也可能已经输出
- 减少截断的影响

---

### 2. 动态调整 max_tokens

**改进前**:
- 所有查询使用相同的max_tokens
- 简单问题浪费，复杂问题可能不够

**改进后**:
- 根据查询复杂度动态调整
- 简单问题节省tokens，复杂问题增加tokens
- 提高资源利用效率

---

## 📝 实施细节

### 提示词改进

**修改的模板**:
- `reasoning_with_evidence`
- `reasoning_without_evidence`

**添加的指令**:
1. 在推理过程中优先输出答案
2. 如果推理过程很长，在Step 3中提供初步答案
3. 确保即使推理过程被截断，答案也已经输出

---

### max_tokens动态调整

**修改的方法**:
- `_get_max_tokens`: 添加 `query_complexity` 参数
- `_estimate_query_complexity`: 新增方法，估算查询复杂度
- `_call_deepseek`: 调用时传入查询复杂度

**复杂度判断逻辑**:
- 简单：短查询（<100字符，<20词），无复杂关键词
- 复杂：长查询（>500字符，>100词），或多步骤推理，或复杂关键词+长查询
- 中等：其他情况

---

## ✅ 总结

**已完成的改进**:
- ✅ 改进提示词，引导LLM优先输出答案
- ✅ 动态调整 max_tokens

**预期效果**:
- 减少截断的影响（LLM优先输出答案）
- 提高资源利用效率（动态调整max_tokens）
- 简单问题节省tokens，复杂问题避免截断

**设计理念**:
- ✅ 解决根本问题，而不是依赖截断后的提取
- ✅ 提高资源利用效率
- ✅ 保持系统的智能性和扩展性

---

*本总结基于2025-11-09的改进实施生成*

