# 查询分解优化完成报告

**完成时间**: 2025-11-30  
**目标**: 完成所有查询分解相关的优化任务

---

## ✅ 已完成的优化任务

### 1. 优化子查询提取 ✅

**实施内容**:
- 添加了`_extract_sub_query_with_llm`方法，使用LLM提取更准确的子查询
- 优化了`_extract_executable_sub_query`方法，先使用规则匹配（快速），失败时使用LLM（更准确）
- 所有调用点都已更新，传入`query`参数以支持LLM提取

**技术细节**:
- 规则匹配：快速，适用于常见模式（"Find X" -> "What is X?"）
- LLM提取：更准确，适用于复杂描述，但较慢（5秒超时保护）

**位置**: `src/core/real_reasoning_engine.py`
- `_extract_executable_sub_query` (第9781行)
- `_extract_sub_query_with_llm` (第10008行)

### 2. 优化证据检索策略 ✅

**实施内容**:
- 添加了`_can_reuse_previous_evidence`方法，判断是否可以复用前一步的证据
- 添加了`_enhance_sub_query_with_previous_results`方法，基于前一步的结果增强子查询
- 添加了`_filter_relevant_previous_evidence`方法，过滤出与当前步骤相关的前一步证据
- 更新了`_gather_evidence_for_step`方法，支持复用前一步的证据
- 更新了证据收集流程，考虑步骤间的依赖关系

**技术细节**:
- 可复用步骤类型：`logical_deduction`, `causal_reasoning`, `pattern_recognition`, `answer_synthesis`
- 增强子查询：从前一步证据中提取关键实体，用于增强当前步骤的子查询
- 相关证据过滤：基于关键词匹配，过滤出与当前步骤相关的前一步证据

**位置**: `src/core/real_reasoning_engine.py`
- `_can_reuse_previous_evidence` (第3690行)
- `_enhance_sub_query_with_previous_results` (第3715行)
- `_filter_relevant_previous_evidence` (第3750行)
- `_gather_evidence_for_step` (第3619行，已更新)

### 3. 优化证据分配 ✅

**实施内容**:
- 添加了`_allocate_evidence_for_step`方法，根据步骤类型和内容智能分配最相关的证据
- 更新了证据合并流程，使用智能分配方法为每个步骤分配证据

**技术细节**:
- 相关性评分：基于证据的原始相关性、关键词匹配、步骤类型权重
- 证据数量限制：根据步骤类型决定返回的证据数量
  - `evidence_gathering`: 5条
  - `logical_deduction`: 3条
  - `causal_reasoning`: 3条
  - `pattern_recognition`: 3条
  - `answer_synthesis`: 2条
  - `query_analysis`: 2条

**位置**: `src/core/real_reasoning_engine.py`
- `_allocate_evidence_for_step` (第3787行)

---

## 📊 优化效果预期

### 1. 子查询提取准确性提升

**之前**: 仅使用规则匹配，可能无法处理复杂描述
**现在**: 规则匹配 + LLM提取，准确性更高

### 2. 证据检索效率提升

**之前**: 每个步骤独立检索，可能重复检索相同内容
**现在**: 考虑步骤依赖关系，复用前一步的证据，减少重复检索

### 3. 证据分配质量提升

**之前**: 简单分配，所有证据都分配给每个步骤
**现在**: 智能分配，根据步骤类型和内容选择最相关的证据

---

## 🔧 技术实现细节

### 1. 子查询提取流程

```
描述性文本 -> 规则匹配（快速） -> 成功？ -> 返回子查询
                ↓ 失败
                LLM提取（准确但较慢） -> 返回子查询或None
```

### 2. 证据检索流程

```
步骤1: 检索证据 -> 存储为previous_step_evidence
步骤2: 检查是否可以复用 -> 可以？ -> 复用 + 增强子查询 -> 检索证据
                                ↓ 不可以
                                直接检索证据
步骤3: 合并前一步的相关证据 -> 智能分配 -> 分配给步骤
```

### 3. 证据分配流程

```
证据列表 -> 计算相关性分数（原始相关性 + 关键词匹配 + 步骤类型权重）
         -> 按分数排序
         -> 根据步骤类型选择前N条最相关的证据
         -> 分配给步骤
```

---

## 🎯 下一步建议

### 1. 性能优化

- 考虑缓存LLM提取的子查询结果
- 优化证据相关性评分算法
- 考虑使用向量相似度进行证据匹配

### 2. 功能增强

- 支持更复杂的步骤依赖关系（多步骤依赖）
- 支持证据的增量更新（基于前一步的结果）
- 支持证据的置信度传播（前一步的高置信度证据影响当前步骤）

---

**报告生成时间**: 2025-11-30

