# 超时和截断问题修复总结

**修复时间**: 2025-11-16

---

## 🔍 问题分析

### 问题1: 读取超时5秒

**现象**:
```
ReadTimeoutError("HTTPSConnectionPool(host='api.deepseek.com', port=443): Read timed out. (read timeout=5.0)")
```

**根本原因**:
- HTTPAdapter的Retry策略在重试时可能使用默认的5秒超时
- 即使我们在`requests.post()`中设置了`timeout=(5.0, 240)`，HTTPAdapter的重试机制可能没有正确传递这个timeout

**修复方案**:
1. ✅ 禁用HTTPAdapter级别的重试（`max_retries=0`）
2. ✅ 在代码层面手动处理重试（`for attempt in range(max_retries)`）
3. ✅ 设置session级别的默认timeout作为fallback

---

### 问题2: 推理内容被截断

**现象**:
- 32436字符 ≈ 8109 tokens
- 34791字符 ≈ 8697 tokens
- 40436字符 ≈ 10109 tokens

**根本原因**:
- max_tokens设置太小（之前是8000，后来增加到10000）
- 知识图谱构建等场景需要更长的推理过程

**修复方案**:
- ✅ 增加基础max_tokens：10000 → 12000
- ✅ 复杂问题max_tokens：15000 → 18000（12000 * 1.5）

---

## ✅ 修复内容

### 1. 超时修复

**文件**: `src/core/llm_integration.py`

**修改**:
```python
# 修复前
adapter = HTTPAdapter(
    max_retries=retry_strategy,  # 使用Retry策略，可能使用默认timeout
    ...
)

# 修复后
session.timeout = timeout  # 设置session级别的默认timeout作为fallback
adapter = HTTPAdapter(
    max_retries=0,  # 禁用HTTPAdapter级别的重试，避免使用默认timeout
    ...
)
```

**为什么这样修复**:
1. 代码中已有手动重试逻辑（`for attempt in range(max_retries)`）
2. 手动重试可以完全控制timeout参数
3. 设置session级别的timeout作为fallback，确保即使HTTPAdapter有问题也能使用正确的timeout

---

### 2. max_tokens增加

**文件**: `src/core/llm_integration.py`

**修改**:
```python
# 修复前
base_tokens = 10000 if "reasoner" in model.lower() else 2000
# 复杂问题：15000 tokens

# 修复后
base_tokens = 12000 if "reasoner" in model.lower() else 2000
# 复杂问题：18000 tokens (12000 * 1.5)
```

**新的max_tokens设置**:
- 基础值：12000 tokens（推理模型）
- 简单问题：9600 tokens（12000 * 0.8）
- 中等问题：12000 tokens
- 复杂问题：18000 tokens（12000 * 1.5）

---

## 📊 预期效果

### 超时修复后
- ✅ 不会再出现"read timeout=5.0"的错误
- ✅ timeout设置会正确传递（240秒）
- ✅ 重试逻辑仍然正常工作（在代码层面手动处理）

### max_tokens增加后
- ✅ 可以覆盖10109 tokens的场景（基础值12000）
- ✅ 复杂问题可以覆盖更长的推理过程（18000 tokens）
- ✅ 减少推理内容被截断的情况

---

## ⚠️ 注意事项

1. **需要重启进程**：修复后需要重启知识图谱构建进程，新代码才会生效

2. **如果仍有5秒超时**：
   - 检查是否重启了进程
   - 检查是否有其他地方的代码设置了超时
   - 查看日志中的"使用超时设置"信息，确认timeout是否正确传递

3. **如果仍有截断**：
   - 检查查询复杂度判断是否正确（是否识别为"complex"）
   - 如果仍然超过18000 tokens，可能需要进一步增加max_tokens

---

*修复时间: 2025-11-16*

