# Bug修复报告：query_analysis类型错误

**修复时间**: 2025-11-08  
**错误信息**: `❌ 推理失败: 'str' object has no attribute 'get'`

---

## 🔍 问题分析

### 错误原因
在 `src/core/real_reasoning_engine.py` 中，代码期望 `query_analysis` 是一个字典对象，但 `_analyze_query_type_with_ml()` 方法实际返回的是字符串类型（查询类型）。

### 错误位置
1. **第780-781行**:
   ```python
   query_analysis = self._analyze_query_type_with_ml(query)
   query_type = query_analysis.get('type', 'general')  # ❌ 错误：对字符串调用.get()
   ```

2. **第849行**:
   ```python
   evidence_task = asyncio.create_task(self._gather_evidence(query, enhanced_context, {'type': query_analysis}))
   # ❌ 错误：query_analysis 是字符串，不是字典
   ```

---

## ✅ 修复方案

### 修复1: 正确处理查询类型返回值
**文件**: `src/core/real_reasoning_engine.py` (第778-786行)

**修复前**:
```python
query_analysis = self._analyze_query_type_with_ml(query)
query_type = query_analysis.get('type', 'general')
```

**修复后**:
```python
query_type = self._analyze_query_type_with_ml(query)  # 返回字符串，不是字典
# 🚀 修复：_analyze_query_type_with_ml 返回的是字符串类型，不是字典
if isinstance(query_type, dict):
    query_type = query_type.get('type', 'general')
elif not isinstance(query_type, str):
    query_type = str(query_type) if query_type else 'general'
```

### 修复2: 修复_gather_evidence调用参数
**文件**: `src/core/real_reasoning_engine.py` (第849行)

**修复前**:
```python
evidence_task = asyncio.create_task(self._gather_evidence(query, enhanced_context, {'type': query_analysis}))
```

**修复后**:
```python
# 🚀 修复：query_type 现在是字符串，需要包装成字典传递给 _gather_evidence
evidence_task = asyncio.create_task(self._gather_evidence(query, enhanced_context, {'type': query_type}))
```

---

## 📝 技术细节

### `_analyze_query_type_with_ml` 方法签名
```python
def _analyze_query_type_with_ml(self, query: str) -> str:
    """返回查询类型字符串（factual, numerical, temporal, etc.）"""
    # 返回字符串，不是字典
    return classification_service.classify(...)
```

### 为什么会出现这个错误？
1. **历史遗留**: 可能之前 `_analyze_query_type_with_ml` 返回的是字典，后来改为返回字符串，但调用代码没有更新
2. **类型不一致**: 方法签名明确返回 `str`，但调用代码期望字典

---

## ✅ 验证

- [x] 修复了类型错误
- [x] 添加了类型检查（兼容字典和字符串）
- [x] 修复了 `_gather_evidence` 调用参数
- [x] 通过了linter检查

---

## 🎯 预期效果

修复后，推理引擎应该能够：
1. ✅ 正确分析查询类型（不再出现类型错误）
2. ✅ 正确传递查询类型给证据收集方法
3. ✅ 正常执行推理流程

---

*修复完成，可以重新运行测试验证*

