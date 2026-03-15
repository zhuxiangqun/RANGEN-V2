# 知识图谱构建自动重试失败条目优化

**实施时间**: 2025-11-15  
**状态**: ✅ 已完成

---

## 📋 优化内容

### 问题
- **之前**: 失败的条目需要显式使用`--retry-failed`参数才能重新处理
- **用户需求**: 希望程序自动记录失败的条目，下次执行时自动重试

### 解决方案
- **默认行为**: 断点续传时自动包含失败的条目（自动重试）
- **灵活控制**: 提供参数控制是否自动重试

---

## 🚀 新的行为逻辑

### 默认行为（推荐）✅

**断点续传时自动重试失败的条目**

```bash
# 默认行为：自动重试失败的条目
python build_knowledge_graph.py --batch-size 100
```

**处理逻辑**:
- 处理未处理的条目
- **自动重试之前失败的条目**
- 跳过已成功处理的条目

**日志输出**:
```
🔄 断点续传模式：已处理 200 条，剩余 18065 条（其中 5 个失败条目将自动重试）
```

---

### 选项1: 只处理失败的条目

```bash
# 只重新处理失败的条目（不处理未处理的条目）
python build_knowledge_graph.py --retry-failed
```

**处理逻辑**:
- 只处理之前失败的条目
- 不处理未处理的条目

**日志输出**:
```
🔄 断点续传模式：只重新处理 5 个失败条目
```

---

### 选项2: 不自动重试失败的条目

```bash
# 不自动重试失败的条目（只处理未处理的条目）
python build_knowledge_graph.py --no-retry-failed
```

**处理逻辑**:
- 只处理未处理的条目
- 不重试之前失败的条目

**日志输出**:
```
🔄 断点续传模式：已处理 200 条，剩余 18065 条（不重试失败的条目）
```

---

## 📊 行为对比

| 场景 | 命令 | 处理内容 |
|------|------|---------|
| **默认（推荐）** | `python build_knowledge_graph.py` | 未处理的条目 + **自动重试失败的条目** |
| 只重试失败 | `python build_knowledge_graph.py --retry-failed` | 只处理失败的条目 |
| 不重试失败 | `python build_knowledge_graph.py --no-retry-failed` | 只处理未处理的条目 |

---

## 🎯 使用场景

### 场景1: 正常使用（推荐）
```bash
# 第一次运行（处理100条后中断，其中5条失败）
python build_knowledge_graph.py --batch-size 100

# 第二次运行（自动处理剩余的条目 + 自动重试5个失败的条目）
python build_knowledge_graph.py --batch-size 100
# 输出: 🔄 断点续传模式：已处理 100 条，剩余 18160 条（其中 5 个失败条目将自动重试）
```

### 场景2: 网络错误后恢复
```bash
# 网络错误导致部分条目失败
# 网络恢复后，重新运行（自动重试失败的条目）
python build_knowledge_graph.py --batch-size 100
# 自动重试失败的条目，无需额外操作
```

### 场景3: 应用优化后重新处理
```bash
# 1. 停止当前程序
kill <PID>

# 2. 应用优化（代码已更新）

# 3. 重新运行（自动重试失败的条目，使用新的重试机制）
python build_knowledge_graph.py --batch-size 100
# 自动重试失败的条目，使用优化后的重试机制
```

---

## 📝 代码实现

### 修改位置
- `knowledge_management_system/scripts/build_knowledge_graph.py`

### 关键逻辑
```python
# 默认自动重试失败的条目
if auto_retry_failed:
    entries_to_process = [
        kid for kid in all_knowledge_ids 
        if kid not in processed_entry_ids  # 未处理的条目
        or kid in failed_entry_ids  # 或之前失败的条目（自动重试）
    ]
```

### 参数说明
- `auto_retry_failed`: 默认`True`，自动重试失败的条目
- `retry_failed`: 如果为`True`，只处理失败的条目
- `--no-retry-failed`: 显式禁用自动重试

---

## ✅ 优势

1. **自动化**: 无需手动指定参数，自动重试失败的条目
2. **智能**: 合并未处理和失败的条目，一次性处理
3. **灵活**: 提供参数控制，满足不同需求
4. **用户友好**: 默认行为符合用户期望

---

## 📊 预期效果

### 优化前
- 需要显式使用`--retry-failed`才能重试失败的条目
- 用户需要记住使用特定参数

### 优化后
- **默认自动重试失败的条目**
- 用户无需额外操作
- 更符合直觉的行为

---

*实施时间: 2025-11-15*

