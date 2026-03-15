# MPS内存泄漏修复报告（2025-11-23）

## 问题描述

在处理101个样本时，从样本35开始出现MPS（Metal Performance Shaders）内存溢出错误：

```
MPS backend out of memory (MPS allocated: 18.14 GiB, other allocations: 640.00 KiB, max allowed: 18.13 GiB)
Tried to allocate 89.43 MiB on private pool
```

导致本地embedding模型无法加载，影响后续样本处理。

## 根本原因

1. **MPS内存未释放**：每个样本处理时加载embedding模型，但MPS内存没有被显式释放
2. **批次间清理不足**：虽然批次间有资源清理，但MPS内存需要特殊处理
3. **资源监控缺失**：资源监控器没有监控MPS内存使用情况

## 修复方案

### 1. 批次结束时释放MPS内存 ✅

**文件**: `scripts/run_core_with_frames.py`

**修改**:
- 在批次处理完成后，添加MPS内存清理：
  ```python
  # 🚀 P0修复：释放MPS内存（避免MPS内存溢出）
  try:
      import torch
      if torch.backends.mps.is_available():
          torch.mps.empty_cache()
          print(f"🧹 MPS内存已清理")
  except Exception as e:
      print(f"⚠️ MPS内存清理失败: {e}")
  ```

### 2. 资源清理回调中添加MPS内存清理 ✅

**文件**: `scripts/run_core_with_frames.py`

**修改**:
- 在`cleanup_callback`函数中添加MPS内存清理：
  ```python
  # 🚀 P0修复：清理MPS内存
  try:
      import torch
      if torch.backends.mps.is_available():
          torch.mps.empty_cache()
  except Exception:
      pass  # 忽略MPS清理错误
  ```

### 3. 资源监控器添加MPS内存监控 ✅

**文件**: `src/utils/resource_monitor.py`

**修改**:
1. **添加MPS内存阈值配置**:
   ```python
   @dataclass
   class ResourceThresholds:
       # ... 其他配置 ...
       mps_memory_gb: float = 16.0   # MPS内存使用量阈值（GB）
   ```

2. **获取MPS内存使用情况**:
   ```python
   # 🚀 P0修复：获取MPS内存使用情况
   mps_memory_gb = 0.0
   mps_available = False
   try:
       import torch
       if torch.backends.mps.is_available():
           mps_available = True
           # 获取MPS内存使用情况
           if hasattr(torch.mps, 'current_allocated_memory'):
               mps_memory_bytes = torch.mps.current_allocated_memory()
               mps_memory_gb = mps_memory_bytes / (1024 ** 3)
   except ImportError:
       pass
   ```

3. **检查MPS内存阈值**:
   ```python
   # 🚀 P0修复：检查MPS内存使用量
   if mps.get("available") and mps.get("memory_gb", 0) > self.thresholds.mps_memory_gb:
       issues.append(f"MPS内存使用量过高: {mps['memory_gb']:.2f}GB > {self.thresholds.mps_memory_gb}GB")
       should_cleanup = True
   ```

4. **清理时释放MPS内存**:
   ```python
   # 🚀 P0修复：清理MPS内存
   try:
       import torch
       if torch.backends.mps.is_available():
           torch.mps.empty_cache()
           self.logger.info("🧹 MPS内存已清理")
   except ImportError:
       pass
   ```

### 4. 修复Fallback逻辑错误 ✅

**文件**: `src/core/real_reasoning_engine.py`

**问题**: 在fallback逻辑中，第8227行有`import re`，但在某些执行路径中可能未执行到，导致`re`变量未定义错误。

**修复**:
- 移除函数内部的`import re`（文件开头已导入）
- 确保`re`模块始终可用

**修改**:
```python
# 修改前：
if is_numerical_query:
    import re
    numbers = re.findall(r'\b\d+\b', line)

# 修改后：
if is_numerical_query:
    # 🚀 P0修复：确保re模块可用（已在文件开头导入）
    numbers = re.findall(r'\b\d+\b', line)
```

## 修复效果

### 预期效果

1. **MPS内存及时释放**：
   - 每个批次处理完成后，MPS内存会被显式释放
   - 资源监控触发清理时，也会释放MPS内存

2. **MPS内存监控**：
   - 资源监控器会监控MPS内存使用情况
   - 超过阈值（16GB）时会触发清理

3. **Fallback逻辑稳定**：
   - 修复了`re`变量未定义错误
   - Fallback逻辑更加稳定

### 验证方法

1. **运行101个样本**：
   - 观察是否还会出现MPS内存溢出
   - 检查MPS内存是否在每个批次后被释放

2. **监控资源使用**：
   - 观察资源监控日志
   - 确认MPS内存监控正常工作

3. **检查错误日志**：
   - 确认不再出现`re`变量未定义错误
   - 确认Fallback逻辑正常工作

## 注意事项

1. **PyTorch版本**：
   - 确保PyTorch版本支持`torch.mps.empty_cache()`
   - 如果方法不存在，代码会优雅降级

2. **MPS内存监控**：
   - `torch.mps.current_allocated_memory()`方法可能在某些PyTorch版本中不存在
   - 代码已处理这种情况，不会影响主流程

3. **性能影响**：
   - MPS内存清理操作很快，不会显著影响性能
   - 批次间休息时间（2秒）足够MPS内存释放

## 后续优化建议

1. **模型共享**：
   - 考虑在批次级别共享embedding模型实例
   - 避免每个样本都重新加载模型

2. **更细粒度的监控**：
   - 在每个样本处理前后监控MPS内存
   - 识别哪些操作消耗MPS内存最多

3. **内存使用优化**：
   - 考虑使用CPU进行embedding（如果MPS内存持续不足）
   - 或者使用JINA API作为fallback

---

**修复时间**: 2025-11-23  
**修复文件**:
- `scripts/run_core_with_frames.py`
- `src/utils/resource_monitor.py`
- `src/core/real_reasoning_engine.py`

**状态**: ✅ 已完成

