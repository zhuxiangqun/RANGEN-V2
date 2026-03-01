# 推理链串行执行修复计划

## 问题
用户指出：推理链应该是一环套一环的，不能并行处理。上一个推理的结果可能在下一个推理里使用，应该要用到上下文工程的能力。

## 当前问题

### 问题1：证据检索并行执行 ⚠️ P0

**当前实现**：
```python
# 为每个推理步骤检索证据
evidence_tasks = []
for i, step in enumerate(reasoning_steps):
    evidence_task = asyncio.create_task(
        self._gather_evidence_for_step(sub_query, step, ...)
    )
    evidence_tasks.append(evidence_task)

# 等待所有证据检索完成（并行执行）
step_evidence_list = await asyncio.gather(*evidence_tasks, return_exceptions=True)
```

**问题**：
- 所有推理步骤的证据检索是并行执行的
- 后续步骤无法使用前一步的检索结果
- 无法实现真正的多跳推理（一环套一环）

---

### 问题2：缺少上下文传递 ⚠️ P0

**问题**：
- 前一步的推理结果没有传递给下一步
- 后续步骤无法使用前一步的答案来构建新的查询
- 缺少上下文工程的能力

---

## 修复方案

### 修复1：改为串行执行推理步骤 ✅

**位置**：`src/core/real_reasoning_engine.py` 第2945-3063行

**修复**：
```python
# 修复前：并行执行
evidence_tasks = []
for i, step in enumerate(reasoning_steps):
    evidence_task = asyncio.create_task(...)
    evidence_tasks.append(evidence_task)
step_evidence_list = await asyncio.gather(*evidence_tasks, ...)

# 修复后：串行执行
evidence = []
previous_step_evidence = []
previous_step_result = None  # 存储前一步的推理结果

for i, step in enumerate(reasoning_steps):
    # 1. 获取子查询
    sub_query = step.get('sub_query') or step.get('description', query)
    
    # 2. 如果前一步有结果，使用上下文工程增强子查询
    if previous_step_result:
        sub_query = self._enhance_sub_query_with_context(
            sub_query, previous_step_result, step, query
        )
    
    # 3. 为当前步骤检索证据
    step_evidence = await self._gather_evidence_for_step(
        sub_query, step, enhanced_context, query_analysis, previous_step_evidence
    )
    
    # 4. 使用上下文工程处理证据，提取推理结果
    step_result = self._extract_step_result_with_context(
        step_evidence, step, previous_step_result, query
    )
    
    # 5. 更新上下文
    previous_step_evidence = step_evidence
    previous_step_result = step_result
    step['evidence'] = step_evidence
    step['result'] = step_result
    
    # 6. 合并证据
    for ev in step_evidence:
        if ev not in evidence:
            evidence.append(ev)
```

---

### 修复2：使用上下文工程增强子查询 ✅

**新增方法**：`_enhance_sub_query_with_context`

**功能**：
- 使用前一步的推理结果替换子查询中的占位符
- 例如："What is [previous_result]'s mother?" → "What is Edith Wilson's mother?"

---

### 修复3：使用上下文工程提取步骤结果 ✅

**新增方法**：`_extract_step_result_with_context`

**功能**：
- 从证据中提取当前步骤的推理结果
- 考虑前一步的上下文
- 为下一步提供可用的结果

---

## 实施步骤

1. **修改证据检索逻辑**：从并行改为串行
2. **添加上下文传递**：在步骤间传递推理结果
3. **使用上下文工程**：增强子查询和提取结果
4. **测试验证**：确保多跳推理正确工作

