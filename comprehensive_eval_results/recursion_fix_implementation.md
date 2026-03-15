# 递归问题修复实施总结

**修复时间**: 2025-11-09  
**问题**: maximum recursion depth exceeded  
**优先级**: P0（最高优先级）

---

## 🔍 问题分析

### 递归调用链

**问题**:
```
_call_deepseek(prompt)
  → _estimate_query_complexity(prompt)  (第445行)
    → _estimate_query_complexity_with_llm(query)  (第240行)
      → self._call_llm(complexity_prompt)  (第300行)
        → self._call_deepseek(complexity_prompt)  (第472行)
          → _estimate_query_complexity(complexity_prompt)  (第445行)
            → ... (无限递归)
```

**根本原因**:
- `_estimate_query_complexity_with_llm` 调用 `_call_llm`
- `_call_llm` 调用 `_call_deepseek`
- `_call_deepseek` 调用 `_estimate_query_complexity`
- 形成无限递归循环

---

## 🚀 修复方案

### 修复1：添加 skip_complexity_estimation 参数

**位置**: `src/core/llm_integration.py` - `_call_deepseek` 方法

**修改**:
```python
def _call_deepseek(self, prompt: str, skip_complexity_estimation: bool = False) -> str:
    """Call DeepSeek API with retry mechanism and improved SSL error handling
    
    Args:
        prompt: 提示词内容
        skip_complexity_estimation: 是否跳过复杂度估算（用于避免递归调用）
    """
```

**作用**:
- 允许在调用 `_call_deepseek` 时跳过复杂度估算
- 避免递归调用

---

### 修复2：在 _call_deepseek 中条件性调用复杂度估算

**位置**: `src/core/llm_integration.py` - `_call_deepseek` 方法

**修改**:
```python
# 🚀 P1改进：根据查询复杂度动态调整max_tokens（如果未跳过）
if not skip_complexity_estimation:
    query_complexity = self._estimate_query_complexity(prompt)
    max_tokens = self._get_max_tokens(self.model, query_complexity)
else:
    # 跳过复杂度估算，使用默认值
    max_tokens = self._get_max_tokens(self.model, None)
```

**作用**:
- 只有在未跳过时才进行复杂度估算
- 如果跳过，使用默认的max_tokens值

---

### 修复3：在 _estimate_query_complexity_with_llm 中跳过复杂度估算

**位置**: `src/core/llm_integration.py` - `_estimate_query_complexity_with_llm` 方法

**修改**:
```python
# 🚀 修复：直接调用 _call_deepseek，跳过复杂度估算以避免递归
# 使用当前LLM实例判断（快速且准确），但跳过复杂度估算以避免无限递归
response = self._call_deepseek(complexity_prompt, skip_complexity_estimation=True)
```

**作用**:
- 直接调用 `_call_deepseek`，跳过复杂度估算
- 避免递归调用

---

## 📊 修复效果

### 修复前

**问题**:
- 无限递归：`_call_deepseek` → `_estimate_query_complexity` → `_estimate_query_complexity_with_llm` → `_call_llm` → `_call_deepseek` → ...
- 导致 "maximum recursion depth exceeded" 错误
- 程序无法正常运行

---

### 修复后（预期）

**效果**:
- ✅ 递归问题解决：`_estimate_query_complexity_with_llm` 调用 `_call_deepseek` 时跳过复杂度估算
- ✅ 程序可以正常运行
- ✅ 复杂度估算功能仍然可用（在主调用中）

**调用流程**:
```
主调用: _call_deepseek(prompt, skip_complexity_estimation=False)
  → _estimate_query_complexity(prompt)
    → _estimate_query_complexity_with_llm(query)
      → _call_deepseek(complexity_prompt, skip_complexity_estimation=True)
        → 跳过复杂度估算，直接调用API
```

---

## ✅ 总结

**修复内容**:
- ✅ 添加 `skip_complexity_estimation` 参数到 `_call_deepseek`
- ✅ 在 `_call_deepseek` 中条件性调用复杂度估算
- ✅ 在 `_estimate_query_complexity_with_llm` 中跳过复杂度估算

**预期效果**:
- ✅ 解决递归问题
- ✅ 程序可以正常运行
- ✅ 复杂度估算功能仍然可用

---

*本修复基于2025-11-09的错误日志分析生成*

