# 知识图谱构建程序断点续传和错误重试功能说明

**更新时间**: 2025-11-15  
**状态**: ✅ 完全支持

---

## ✅ 功能确认

**知识图谱构建程序完全支持以下功能**：

1. ✅ **断点续传** - 程序中断后可以从上次停止的地方继续
2. ✅ **错误后重新导入** - 失败的条目可以重新处理
3. ✅ **进度自动保存** - 每个条目处理完后立即保存进度
4. ✅ **失败条目记录** - 自动记录处理失败的条目

---

## 📋 功能详解

### 1. 断点续传功能 ✅

#### 工作原理
- **进度文件**: `data/knowledge_management/graph_progress.json`
- **记录内容**:
  - `processed_entry_ids`: 已成功处理的条目ID列表
  - `failed_entry_ids`: 处理失败的条目ID列表
  - `total_entries`: 总条目数
  - `start_time`: 开始时间
  - `last_update`: 最后更新时间

#### 自动保存机制
- **每个条目处理完后立即保存进度**
- **失败时也保存进度**（记录失败条目）
- **每批处理完后再次保存**（作为备份）

#### 使用方式

**方式1: 自动启用（推荐）**
```bash
# 如果检测到进度文件，自动启用断点续传
python build_knowledge_graph.py --batch-size 100
```

**方式2: 显式启用**
```bash
# 显式指定断点续传
python build_knowledge_graph.py --resume --batch-size 100
```

**方式3: 禁用断点续传（从头开始）**
```bash
# 从头开始，忽略之前的进度
python build_knowledge_graph.py --no-resume
```

#### 断点续传逻辑
```python
if resume:
    if retry_failed:
        # 重新处理失败的条目
        entries_to_process = [kid for kid in all_knowledge_ids if kid in failed_entry_ids]
    else:
        # 跳过已处理的条目，只处理未处理的
        entries_to_process = [kid for kid in all_knowledge_ids if kid not in processed_entry_ids]
```

---

### 2. 错误后重新导入功能 ✅

#### 工作原理
- **失败条目记录**: 处理失败的条目ID会被记录到`failed_entry_ids`
- **重新处理**: 使用`--retry-failed`参数可以重新处理失败的条目

#### 使用方式

**重新处理失败的条目**
```bash
# 只处理之前失败的条目
python build_knowledge_graph.py --retry-failed
```

**断点续传 + 重新处理失败条目**
```bash
# 继续处理未完成的条目，同时重新处理失败的条目
python build_knowledge_graph.py --resume --retry-failed
```

#### 失败条目处理逻辑
```python
if retry_failed:
    # 重新处理失败的条目
    entries_to_process = [kid for kid in all_knowledge_ids if kid in failed_entry_ids]
    logger.info(f"🔄 断点续传模式：重新处理 {len(entries_to_process)} 个失败条目")
```

---

## 📊 进度文件结构

### 进度文件位置
```
data/knowledge_management/graph_progress.json
```

### 进度文件内容示例
```json
{
  "processed_entry_ids": [
    "knowledge_id_1",
    "knowledge_id_2",
    ...
  ],
  "failed_entry_ids": [
    "knowledge_id_10",
    "knowledge_id_20",
    ...
  ],
  "total_entries": 18265,
  "start_time": "2025-11-15T14:23:38.123456",
  "last_update": "2025-11-15T14:48:11.789012"
}
```

---

## 🔍 使用场景

### 场景1: 程序意外中断
```bash
# 程序运行中断后，重新启动会自动从上次停止的地方继续
python build_knowledge_graph.py --batch-size 100
# 或显式指定
python build_knowledge_graph.py --resume --batch-size 100
```

### 场景2: 网络错误导致部分条目失败
```bash
# 网络恢复后，重新处理失败的条目
python build_knowledge_graph.py --retry-failed
```

### 场景3: 优化后重新处理失败的条目
```bash
# 应用优化后（如重试机制），重新处理之前失败的条目
python build_knowledge_graph.py --retry-failed
```

### 场景4: 从头开始（清除进度）
```bash
# 从头开始，忽略之前的进度
python build_knowledge_graph.py --no-resume
```

---

## 📝 进度保存机制

### 保存时机
1. **每个条目处理成功后** - 立即保存
2. **每个条目处理失败后** - 立即保存（记录失败）
3. **每批处理完成后** - 再次保存（作为备份）

### 保存内容
- `processed_entry_ids`: 已成功处理的条目ID
- `failed_entry_ids`: 处理失败的条目ID
- `last_update`: 最后更新时间

### 代码位置
```python
# 处理成功后保存
progress['processed_entry_ids'] = list(processed_entry_ids)
progress['failed_entry_ids'] = list(failed_entry_ids)
save_graph_progress(progress)

# 处理失败后也保存
failed_entry_ids.add(knowledge_id)
progress['failed_entry_ids'] = list(failed_entry_ids)
save_graph_progress(progress)
```

---

## 🎯 实际使用示例

### 示例1: 正常断点续传
```bash
# 第一次运行（处理100条后中断）
python build_knowledge_graph.py --batch-size 100

# 第二次运行（自动从第101条开始）
python build_knowledge_graph.py --batch-size 100
# 输出: 🔄 断点续传模式：已处理 100 条，剩余 18165 条
```

### 示例2: 重新处理失败条目
```bash
# 查看失败条目数量
cat data/knowledge_management/graph_progress.json | grep failed_entry_ids

# 重新处理失败的条目
python build_knowledge_graph.py --retry-failed
# 输出: 🔄 断点续传模式：重新处理 5 个失败条目
```

### 示例3: 应用优化后重新处理
```bash
# 1. 停止当前程序
kill <PID>

# 2. 应用优化（代码已更新）

# 3. 重新启动，继续处理未完成的条目
python build_knowledge_graph.py --resume --batch-size 100

# 4. 重新处理之前失败的条目（使用新的重试机制）
python build_knowledge_graph.py --retry-failed
```

---

## ⚠️ 注意事项

1. **进度文件位置**: `data/knowledge_management/graph_progress.json`
2. **不要手动删除进度文件**: 除非想从头开始
3. **失败条目**: 使用`--retry-failed`重新处理，不要手动修改进度文件
4. **并发安全**: 不要同时运行多个构建程序实例

---

## 🔧 故障排除

### 问题1: 进度文件损坏
```bash
# 备份进度文件
cp data/knowledge_management/graph_progress.json graph_progress.json.backup

# 从头开始
python build_knowledge_graph.py --no-resume
```

### 问题2: 想清除失败条目记录
```bash
# 编辑进度文件，清空failed_entry_ids
# 或从头开始
python build_knowledge_graph.py --no-resume
```

### 问题3: 查看当前进度
```bash
# 查看进度文件
cat data/knowledge_management/graph_progress.json | python -m json.tool

# 或使用检查脚本
python scripts/check_import_progress.py
```

---

## 📊 功能总结

| 功能 | 支持状态 | 使用方式 |
|------|---------|---------|
| 断点续传 | ✅ 完全支持 | `--resume` 或自动启用 |
| 错误重试 | ✅ 完全支持 | `--retry-failed` |
| 进度保存 | ✅ 自动保存 | 每个条目处理完后立即保存 |
| 失败记录 | ✅ 自动记录 | 自动记录到`failed_entry_ids` |
| 从头开始 | ✅ 支持 | `--no-resume` |

---

## 🎯 最佳实践

1. **正常使用**: 直接运行，程序会自动处理断点续传
2. **网络错误**: 等待网络恢复后，使用`--retry-failed`重新处理
3. **应用优化**: 重启程序后，使用`--retry-failed`重新处理失败的条目
4. **监控进度**: 定期查看进度文件，了解处理状态

---

*更新时间: 2025-11-15*

