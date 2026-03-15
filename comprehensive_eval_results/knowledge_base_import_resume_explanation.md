# 知识库导入断点续传功能说明

**创建时间**: 2025-11-13

---

## ✅ 支持断点续传

**是的，如果终端知识库创建进程，再次执行会继续而不是重头再来！**

---

## 🔍 断点续传机制

### 1. 进度文件

**位置**: `data/knowledge_management/import_progress.json`

**内容结构**:
```json
{
  "processed_item_indices": [0, 1, 2, ...],  // 已处理的item索引列表
  "total_items": 1000,                        // 总数据项数
  "start_time": "2025-11-13T06:19:02",       // 开始时间
  "last_update": "2025-11-13T09:22:15"       // 最后更新时间
}
```

### 2. 进度保存时机

脚本会在以下时机保存进度：

1. **每个批次处理完成后**（Line 404-406）
   - 无论成功还是失败，都会保存进度
   - 确保即使中断也不会丢失已处理的进度

2. **单个item处理失败时**（Line 295-296, 304-305）
   - 即使单个item失败，也会记录为已处理
   - 避免重复处理失败的item

### 3. 断点续传逻辑

**代码位置**: `import_wikipedia_from_frames.py` Line 208-220

```python
# 加载进度
progress = load_progress() if resume else {
    'processed_item_indices': [],
    'total_items': len(frames_data),
    'start_time': datetime.now().isoformat()
}
processed_indices = set(progress.get('processed_item_indices', []))

# 过滤已处理的item
items_to_process = []
for i, item in enumerate(frames_data):
    if resume and i in processed_indices:
        continue  # 跳过已处理的item
    items_to_process.append((i, item))
```

**工作流程**:
1. 加载进度文件（如果存在）
2. 获取已处理的item索引列表
3. 过滤掉已处理的item
4. 只处理未处理的item

---

## 📋 使用方法

### 默认行为（断点续传）

```bash
python knowledge_management_system/scripts/import_wikipedia_from_frames.py \
    data/frames_dataset.json \
    --batch-size 5 \
    --wikipedia-full-text
```

**说明**: 
- 默认 `resume=True`
- 会自动加载进度文件
- 跳过已处理的item
- 继续处理未完成的item

### 从头开始（不使用断点续传）

```bash
python knowledge_management_system/scripts/import_wikipedia_from_frames.py \
    data/frames_dataset.json \
    --batch-size 5 \
    --wikipedia-full-text \
    --no-resume
```

**说明**:
- 使用 `--no-resume` 参数
- 会忽略进度文件
- 从头开始处理所有item

---

## 🔍 检查进度

### 方法1: 查看进度文件

```bash
cat data/knowledge_management/import_progress.json
```

### 方法2: 使用进度检查脚本

```bash
python scripts/check_import_progress.py
```

### 方法3: 查看日志

```bash
tail -f import_wikipedia_after_cleaning.log
```

---

## ⚠️ 注意事项

### 1. 进度文件位置

- **路径**: `data/knowledge_management/import_progress.json`
- **自动创建**: 脚本会自动创建和更新
- **自动清理**: 所有item处理完成后会自动删除

### 2. 中断恢复

- ✅ **支持中断恢复**: 可以随时中断进程，再次运行会继续
- ✅ **进度保存**: 每个批次完成后都会保存进度
- ✅ **失败处理**: 即使单个item失败，也会记录进度

### 3. 数据一致性

- ✅ **已处理item**: 不会重复处理
- ✅ **失败item**: 会记录为已处理，避免重复尝试
- ⚠️ **部分完成**: 如果批次中部分item成功，部分失败，已成功的会保留

### 4. 重新开始

如果需要重新开始（例如修改了清理逻辑），可以：

1. **删除进度文件**:
   ```bash
   rm data/knowledge_management/import_progress.json
   ```

2. **使用--no-resume参数**:
   ```bash
   python ... --no-resume
   ```

---

## 📊 示例场景

### 场景1: 正常中断和恢复

1. **开始导入**: 运行导入脚本
2. **处理了100个item**: 进度文件记录 `[0, 1, 2, ..., 99]`
3. **中断进程**: Ctrl+C 或关闭终端
4. **再次运行**: 运行相同的导入命令
5. **自动继续**: 脚本会跳过前100个item，从第101个开始处理

### 场景2: 网络中断恢复

1. **开始导入**: 运行导入脚本
2. **网络中断**: 导致Wikipedia抓取失败
3. **失败item记录**: 失败的item也会记录为已处理
4. **再次运行**: 网络恢复后再次运行
5. **继续处理**: 跳过已处理的item，继续处理剩余的

### 场景3: 修改清理逻辑后重新导入

1. **修改清理逻辑**: 改进了HTML清理代码
2. **删除进度文件**: `rm data/knowledge_management/import_progress.json`
3. **重新运行**: 使用 `--no-resume` 或删除进度文件后运行
4. **重新处理**: 所有item会重新处理，应用新的清理逻辑

---

## ✅ 总结

**断点续传功能**:
- ✅ **默认启用**: `resume=True`（默认）
- ✅ **自动保存**: 每个批次完成后自动保存进度
- ✅ **自动恢复**: 再次运行自动从断点继续
- ✅ **失败处理**: 失败的item也会记录，避免重复尝试

**使用方法**:
- **继续导入**: 直接运行脚本（默认会继续）
- **重新开始**: 使用 `--no-resume` 或删除进度文件

---

*创建时间: 2025-11-13*

