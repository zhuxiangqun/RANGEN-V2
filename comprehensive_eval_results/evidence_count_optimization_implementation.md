# 证据数量动态调整优化实施总结

**实施时间**: 2025-11-18  
**优化目标**: 根据查询复杂度动态调整证据数量，提高复杂查询的准确率

---

## ✅ 已实施的优化

### P0（最高优先级）- 修复动态调整逻辑

#### 1. 改进查询复杂度评估方法 ✅

**位置**: `src/core/real_reasoning_engine.py` - `_assess_query_complexity_for_evidence()`

**优化内容**:
- ✅ 新增 `_assess_query_complexity_for_evidence()` 方法
- ✅ 考虑6个因素评估查询复杂度：
  1. 查询长度（权重：1-2）
  2. 查询类型（权重：2）
  3. 查询语义复杂度（权重：1）
  4. 多实体/多关系查询（权重：1）
  5. 时间/数值推理（权重：1）
  6. 当前证据数量（权重：1）

**代码**:
```python
def _assess_query_complexity_for_evidence(self, query: str, query_type: str, current_evidence_count: int) -> int:
    """评估查询复杂度（用于动态调整证据数量）"""
    complexity_score = 0
    
    # 1. 查询长度
    if len(query) > 200:
        complexity_score += 2
    elif len(query) > 100:
        complexity_score += 1
    
    # 2. 查询类型
    complex_types = ['temporal', 'multi_hop', 'complex', 'numerical', 'spatial']
    if query_type in complex_types:
        complexity_score += 2
    elif query_type in ['causal', 'comparative', 'analytical']:
        complexity_score += 1
    
    # 3. 查询语义复杂度
    complex_keywords = ['compare', 'analyze', 'explain', 'why', 'how', ...]
    if any(keyword in query.lower() for keyword in complex_keywords):
        complexity_score += 1
    
    # ... (更多因素)
    
    return min(complexity_score, 5)  # 限制最大评分为5
```

**预期效果**:
- 更准确地评估查询复杂度
- 复杂查询能够被正确识别

---

#### 2. 在推理引擎中应用动态调整 ✅

**位置**: `src/core/real_reasoning_engine.py` - `_gather_evidence()`

**优化内容**:
- ✅ 使用新的复杂度评估方法
- ✅ 根据复杂度评分动态调整 `max_evidence`：
  - 复杂度评分 ≥ 3: `max_evidence = 8`（复杂查询）
  - 复杂度评分 ≥ 2: `max_evidence = 6`（中等查询）
  - 复杂度评分 < 2: `max_evidence = 5`（简单查询）

**代码变更**:
```python
# 🚀 P0优化：改进的查询复杂度评估（考虑更多因素）
complexity_score = self._assess_query_complexity_for_evidence(query, query_type_str, len(evidence))

# 根据复杂度评分动态确定最大证据数量
if complexity_score >= 3:
    max_evidence = 8  # 复杂查询：允许更多证据
elif complexity_score >= 2:
    max_evidence = 6  # 中等查询：中等数量证据
else:
    max_evidence = 5  # 简单查询：最少证据
```

**预期效果**:
- 复杂查询可以使用8个证据
- 中等查询可以使用6个证据
- 简单查询保持5个证据

---

#### 3. 在知识检索智能体中应用动态调整 ✅

**位置**: `src/agents/enhanced_knowledge_retrieval_agent.py` - `_retrieve_knowledge()`

**优化内容**:
- ✅ 根据查询复杂度动态调整第一层检索的 `top_k_initial`：
  - 复杂度评分 ≥ 3: `top_k_initial = 30`（复杂查询）
  - 复杂度评分 ≥ 2: `top_k_initial = 25`（中等查询）
  - 复杂度评分 < 2: `top_k_initial = 20`（简单查询，保持原值）

**代码变更**:
```python
# 🚀 P0优化：根据查询复杂度动态调整第一层检索的top_k
context_query_type = context.get('query_type', 'general') if isinstance(context, dict) else 'general'
query_length = len(query)

# 评估查询复杂度（简化版，与推理引擎保持一致）
complexity_score = 0
if query_length > 200:
    complexity_score += 2
elif query_length > 100:
    complexity_score += 1
if context_query_type in ['temporal', 'multi_hop', 'complex', 'numerical', 'spatial']:
    complexity_score += 2
complex_keywords = ['compare', 'analyze', 'explain', 'why', 'how', 'relationship']
if any(keyword in query.lower() for keyword in complex_keywords):
    complexity_score += 1

# 根据复杂度动态调整top_k_initial
if complexity_score >= 3:
    top_k_initial = 30  # 复杂查询：检索更多候选
elif complexity_score >= 2:
    top_k_initial = 25  # 中等查询：检索中等数量候选
```

**预期效果**:
- 复杂查询检索更多候选结果（30个）
- 中等查询检索中等数量候选（25个）
- 简单查询保持原值（20个）

---

#### 4. 在主动知识检索中应用动态调整 ✅

**位置**: `src/core/real_reasoning_engine.py` - `_gather_evidence()` (主动检索部分)

**优化内容**:
- ✅ 在主动知识检索时，根据查询复杂度动态调整 `top_k`
- ✅ 将动态 `top_k` 传递给知识检索智能体

**代码变更**:
```python
# 🚀 P0优化：根据查询复杂度动态调整知识检索的top_k参数
complexity_score = self._assess_query_complexity_for_evidence(query, query_type_str, 0)
# 根据复杂度动态调整top_k
if complexity_score >= 3:
    dynamic_top_k = 8  # 复杂查询：检索更多证据
elif complexity_score >= 2:
    dynamic_top_k = 6  # 中等查询：检索中等数量证据
else:
    dynamic_top_k = 5  # 简单查询：最少证据

# 将动态top_k传递给知识检索智能体
knowledge_agent.top_k = dynamic_top_k
log_info(f"证据收集: 根据查询复杂度动态调整top_k={dynamic_top_k}（复杂度评分: {complexity_score}）")
```

**预期效果**:
- 主动知识检索时也能根据查询复杂度调整检索数量
- 复杂查询能够检索到更多证据

---

#### 5. 在知识检索智能体中使用动态top_k ✅

**位置**: `src/agents/enhanced_knowledge_retrieval_agent.py` - `_retrieve_knowledge()`

**优化内容**:
- ✅ 在最终结果筛选时，使用动态调整的 `top_k`（如果已设置）

**代码变更**:
```python
# 🚀 P0优化：使用动态调整的top_k（如果已设置）
final_top_k = getattr(self, 'top_k', top_k_for_search)
if final_top_k and final_top_k != top_k_for_search:
    log_info(f"知识检索: 使用动态调整的top_k={final_top_k}（原值: {top_k_for_search}）")
results = validated_results[:final_top_k]
```

**预期效果**:
- 知识检索智能体能够使用动态调整的 `top_k`
- 确保最终返回的证据数量符合复杂度要求

---

## 📊 优化效果预期

### 证据数量变化

| 查询复杂度 | 优化前 | 优化后 | 变化 |
|-----------|--------|--------|------|
| **简单查询** | 5个 | 5个 | 无变化 |
| **中等查询** | 5个 | 6个 | +1个 |
| **复杂查询** | 5个 | 8个 | +3个 |

### 知识检索候选数量变化

| 查询复杂度 | 优化前 | 优化后 | 变化 |
|-----------|--------|--------|------|
| **简单查询** | 20个 | 20个 | 无变化 |
| **中等查询** | 20个 | 25个 | +5个 |
| **复杂查询** | 20个 | 30个 | +10个 |

---

## 🎯 预期改进

### 1. 复杂查询准确率提升

**预期**:
- 复杂查询的准确率提升5-10%
- 多跳推理、时间推理等复杂查询能够获得更多证据支持

**原因**:
- 复杂查询现在可以使用8个证据（原来只有5个）
- 知识检索阶段检索更多候选（30个，原来20个）

---

### 2. 动态调整逻辑生效

**预期**:
- 动态调整逻辑真正生效
- 不同复杂度的查询使用不同数量的证据

**原因**:
- 改进了查询复杂度评估方法
- 在多个阶段应用动态调整

---

### 3. 知识库利用率提升

**预期**:
- 知识库利用率从0.027%提升到0.044%（复杂查询）
- 更多知识被检索和利用

**原因**:
- 复杂查询检索更多候选（30个）
- 最终使用更多证据（8个）

---

## 📝 实施总结

### 已完成的优化

1. ✅ **改进查询复杂度评估方法** - 考虑6个因素
2. ✅ **在推理引擎中应用动态调整** - 根据复杂度调整max_evidence
3. ✅ **在知识检索智能体中应用动态调整** - 根据复杂度调整top_k_initial
4. ✅ **在主动知识检索中应用动态调整** - 传递动态top_k
5. ✅ **在知识检索智能体中使用动态top_k** - 确保最终结果符合要求

### 优化效果

- **简单查询**: 保持5个证据（无变化）
- **中等查询**: 使用6个证据（+1个）
- **复杂查询**: 使用8个证据（+3个）

### 下一步

1. **测试验证**: 运行测试，验证动态调整是否生效
2. **性能监控**: 监控复杂查询的准确率和处理时间
3. **持续优化**: 根据实际效果调整复杂度评估逻辑

---

*实施时间: 2025-11-18*

