# 知识图谱构建内存问题分析

**分析时间**: 2025-11-15  
**问题**: 知识图谱构建过程中数据一直放在内存中

---

## 🔍 当前实现分析

### 数据存储流程

1. **收集阶段**（所有批次处理）：
   ```python
   graph_data = []  # 第182行：在内存中创建列表
   
   # 每个批次处理完后
   if extracted_data:
       graph_data.extend(extracted_data)  # 第319/346行：添加到内存列表
   ```

2. **构建阶段**（所有批次处理完成后）：
   ```python
   # 第391-397行：所有批次处理完成后才构建
   if graph_data:
       graph_result = service.graph_builder.build_from_structured_data(graph_data)
   ```

3. **保存阶段**（构建过程中）：
   ```python
   # 在 build_from_structured_data 中
   entity_manager.create_entity(...)  # 每次创建时调用 _save_entities()
   relation_manager.create_relation(...)  # 每次创建时调用 _save_relations()
   ```

---

## ⚠️ 潜在问题

### 1. 内存占用问题

- **数据量估算**：
  - 总条目数：18265 条
  - 每个条目可能提取多个实体和关系
  - 假设每个条目平均提取 2 个实体和 1 条关系
  - 总数据量：约 18265 * 3 = 54795 条数据

- **内存占用**：
  - 每条数据约 200-500 字节（JSON格式）
  - 总内存占用：约 10-27 MB（仅数据）
  - 加上Python对象开销：可能达到 50-100 MB

### 2. 数据丢失风险

- **进程崩溃**：如果构建过程中进程崩溃，所有收集的数据都会丢失
- **内存不足**：如果数据量过大，可能导致内存不足（OOM）

### 3. 无法查看中间结果

- 在构建完成前，无法查看已处理的数据
- 无法进行增量分析

---

## ✅ 优化方案

### 方案1：每批处理完后立即保存（推荐）

**优点**：
- 降低内存占用
- 降低数据丢失风险
- 可以查看中间结果
- 支持增量构建

**实现**：
```python
# 每批处理完后立即构建和保存
for batch_idx in range(total_batches):
    # ... 处理批次 ...
    
    if graph_data:
        # 立即构建和保存当前批次的数据
        service.graph_builder.build_from_structured_data(graph_data)
        graph_data = []  # 清空，释放内存
```

### 方案2：定期保存（每N批）

**优点**：
- 平衡内存占用和性能
- 减少文件I/O次数

**实现**：
```python
SAVE_INTERVAL = 10  # 每10批保存一次

for batch_idx in range(total_batches):
    # ... 处理批次 ...
    
    if (batch_idx + 1) % SAVE_INTERVAL == 0:
        if graph_data:
            service.graph_builder.build_from_structured_data(graph_data)
            graph_data = []
```

### 方案3：流式处理（最优）

**优点**：
- 内存占用最小
- 实时保存
- 支持断点续传

**实现**：
```python
# 每个条目处理完后立即构建和保存
for entry in entries:
    extracted_data = extract_entities_and_relations(entry)
    if extracted_data:
        service.graph_builder.build_from_structured_data(extracted_data)
```

---

## 📊 方案对比

| 方案 | 内存占用 | 数据丢失风险 | 性能 | 实现复杂度 |
|------|---------|------------|------|-----------|
| **当前实现** | 高（所有数据在内存） | 高（进程崩溃丢失所有数据） | 高（批量构建） | 低 |
| **方案1：每批保存** | 低（只保留当前批次） | 低（每批保存） | 中（多次构建） | 中 |
| **方案2：定期保存** | 中（保留N批数据） | 中（定期保存） | 中（多次构建） | 中 |
| **方案3：流式处理** | 最低（只保留当前条目） | 最低（实时保存） | 低（频繁构建） | 高 |

---

## 🎯 推荐方案

**推荐使用方案1（每批处理完后立即保存）**，因为：
1. 内存占用低
2. 数据丢失风险低
3. 实现相对简单
4. 性能影响可接受（构建过程本身很快）

---

*分析时间: 2025-11-15*

