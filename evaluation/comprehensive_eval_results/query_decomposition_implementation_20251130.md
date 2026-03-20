# 查询分解实现报告

**实施时间**: 2025-11-30  
**目标**: 实现真正的查询分解，基于推理步骤检索证据

---

## ✅ 已实施的改进

### 1. 改进推理步骤生成提示词

**修改位置**: `src/core/real_reasoning_engine.py` - `_execute_reasoning_steps_with_prompts`

**改进内容**:
- 要求LLM生成**可执行的子查询**，而不是描述性的推理过程
- 明确要求使用问题格式: "What is...?", "Who is...?", "Where is...?", "How many...?", etc.
- 添加示例: "What is the depth of the New Britain Trench?" 而不是 "Find the depth of New Britain Trench"
- 在JSON格式中添加`sub_query`字段，用于存储可执行的子查询

**关键提示词改进**:
```
**CRITICAL: For multi-hop queries, decompose into EXPLICIT, EXECUTABLE sub-questions**:
- Each step must be a **complete, executable question** that can be used to retrieve evidence
- Use question format: "What is...?", "Who is...?", "Where is...?", "How many...?", etc.
- Example: Instead of "Find the depth of New Britain Trench", use "What is the depth of the New Britain Trench?"
```

### 2. 添加子查询提取方法

**新增方法**: `_extract_executable_sub_query`

**功能**:
- 从推理步骤描述中提取可执行的子查询
- 支持多种模式:
  - "Find X" -> "What is X?"
  - "Identify X" -> "What is X?"
  - "Determine X" -> "What is X?"
  - "Calculate X" -> 保持原样（计算步骤）
  - 包含疑问词的描述 -> 提取问题部分

**位置**: `src/core/real_reasoning_engine.py` (第9774行)

### 3. 改变证据收集流程

**修改位置**: `src/core/real_reasoning_engine.py` - `reason`方法

**改进内容**:
- **之前**: 证据收集和推理步骤生成并行执行，证据收集基于整个查询
- **现在**: 先生成推理步骤（子查询），然后为每个子查询分别检索证据

**关键流程改进**:
```python
# 步骤4: 先生成推理步骤（子查询）
reasoning_steps = await _execute_reasoning_steps_with_prompts(...)

# 步骤5: 基于推理步骤（子查询）检索证据
for step in reasoning_steps:
    sub_query = step.get('sub_query') or step.get('description', query)
    step_evidence = await _gather_evidence_for_step(sub_query, step, ...)
    step['evidence'] = step_evidence  # 为每个步骤分配证据
```

### 4. 新增基于步骤的证据检索方法

**新增方法**: `_gather_evidence_for_step`

**功能**:
- 为单个推理步骤检索证据
- 使用子查询进行检索，而不是整个查询
- 复用`_gather_evidence`的逻辑

**位置**: `src/core/real_reasoning_engine.py` (第3600行)

### 5. 关联推理步骤和证据

**改进内容**:
- 为每个推理步骤分配对应的证据
- 在推理步骤对象中添加`evidence`字段
- 确保每个步骤都有相关证据支持

**关键代码**:
```python
# 为每个步骤分配证据
for i, step_evidences in enumerate(step_evidence_list):
    if i < len(reasoning_steps):
        reasoning_steps[i]['evidence'] = step_evidences
```

---

## 📊 预期效果

### 1. 证据质量提升

**之前**:
- 证据相关性: 0.612（低）
- 证据数量: 1条（不足）
- 证据覆盖: 不完整

**预期**:
- 证据相关性: 0.8+（高）
- 证据数量: 3+条（每个子查询1条）
- 证据覆盖: 覆盖所有推理步骤所需的信息

### 2. LLM调用时间降低

**之前**:
- LLM调用耗时: 3707.44秒（约62分钟）
- 原因: 证据不相关，LLM需要完全依赖自身知识

**预期**:
- LLM调用耗时: 300秒以下（5分钟以内）
- 原因: 提供相关证据，减少LLM推理时间

### 3. 总处理时间降低

**之前**:
- 总处理时间: 4495.51秒（约75分钟）

**预期**:
- 总处理时间: 600秒以下（10分钟以内）
- 原因: 改进证据质量和查询分解，提高整体效率

---

## 🔧 技术细节

### 1. 推理步骤数据结构

**之前**:
```python
{
    'type': 'evidence_gathering',
    'description': 'Find the depth of New Britain Trench',
    'confidence': 0.8,
    'timestamp': 1234567890
}
```

**现在**:
```python
{
    'type': 'evidence_gathering',
    'description': 'Find the depth of New Britain Trench',
    'sub_query': 'What is the depth of the New Britain Trench?',  # 新增
    'evidence': [...],  # 新增：该步骤的证据
    'confidence': 0.8,
    'timestamp': 1234567890
}
```

### 2. 证据收集流程

**之前**:
```
查询 -> 证据收集（基于整个查询） + 推理步骤生成（并行）
```

**现在**:
```
查询 -> 推理步骤生成（子查询） -> 为每个子查询检索证据 -> 为每个步骤分配证据
```

### 3. 子查询提取逻辑

**支持的转换模式**:
- "Find X" -> "What is X?"
- "Identify X" -> "What is X?"
- "Determine X" -> "What is X?"
- "Calculate X" -> "Calculate X"（保持原样）
- 包含疑问词的描述 -> 提取问题部分

---

## 🎯 下一步优化

### 1. 优化子查询提取

**当前**: 使用规则模式匹配
**优化**: 使用LLM提取更准确的子查询

### 2. 优化证据检索策略

**当前**: 为每个子查询分别检索
**优化**: 考虑步骤间的依赖关系，复用前一步的证据

### 3. 优化证据分配

**当前**: 简单分配
**优化**: 根据步骤类型和内容，智能分配最相关的证据

---

**报告生成时间**: 2025-11-30

