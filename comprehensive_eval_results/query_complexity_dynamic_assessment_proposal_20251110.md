# 查询复杂度动态评估方案（2025-11-10）

**分析时间**: 2025-11-10  
**问题**: 当前系统通过查询文本本身判断复杂度，这是不正确的

---

## 🔍 当前问题分析

### 当前实现方式

#### 1. LLM判断（`_estimate_query_complexity_with_llm`）

**方法**: 通过LLM分析查询文本本身来判断复杂度

**问题**:
- 只基于查询文本，不考虑实际处理情况
- 一个看似简单的问题可能需要复杂的处理
- 一个看似复杂的问题可能处理很简单

**示例**:
- 查询: "What is the capital of France?"（看似简单）
- 但如果没有相关证据，可能需要重新检索、多次验证，实际处理很复杂

---

#### 2. 特征提取（`_estimate_query_complexity_with_features`）

**方法**: 通过查询长度、词数、句子数等特征判断

**问题**:
- 只基于查询文本特征，不考虑实际处理情况
- 短查询可能很复杂（需要多步推理）
- 长查询可能很简单（只是描述详细）

**示例**:
- 查询: "Who?"（很短，但如果没有证据，处理很复杂）
- 查询: "Please provide a detailed explanation of..."（很长，但如果有完整证据，处理很简单）

---

#### 3. 硬编码规则（`_assess_complexity`）

**方法**: 基于查询长度、约束数量、关键词判断

**问题**:
- 完全基于查询文本特征
- 不考虑实际处理表现
- 无法适应动态情况

---

## 🎯 正确的复杂度判断方式

### 核心观点

> **问题的复杂度应该通过实际处理过程中的表现来判断，而不是通过问题本身**

### 判断依据

复杂度应该基于以下**实际处理表现**：

1. **证据检索情况**
   - 需要多少证据？
   - 证据相关性如何？
   - 是否需要重新检索？

2. **推理过程**
   - 需要多少推理步骤？
   - 推理步骤的复杂度如何？
   - 是否需要多次验证？

3. **处理时间**
   - 实际处理时间多长？
   - 各步骤耗时如何？
   - 是否有性能瓶颈？

4. **答案质量**
   - 答案验证是否通过？
   - 是否需要重试？
   - 是否需要fallback？

5. **资源消耗**
   - LLM调用次数？
   - 缓存命中率？
   - 内存/CPU使用？

---

## 💡 动态复杂度评估方案

### 方案1: 基于处理历史的动态评估

**思路**: 在处理过程中收集实际表现数据，动态评估复杂度

**实现**:
```python
def _assess_complexity_dynamically(
    self,
    query: str,
    evidence_count: int,
    evidence_relevance: float,
    reasoning_steps: int,
    processing_time: float,
    retry_count: int,
    fallback_triggered: bool,
    validation_passed: bool
) -> str:
    """基于实际处理表现动态评估复杂度"""
    
    complexity_score = 0
    
    # 1. 证据检索复杂度
    if evidence_count == 0:
        complexity_score += 3  # 无证据，需要重新检索
    elif evidence_relevance < 0.3:
        complexity_score += 2  # 证据相关性低，需要重新检索
    elif evidence_count > 5:
        complexity_score += 1  # 证据多，处理复杂
    
    # 2. 推理复杂度
    if reasoning_steps > 5:
        complexity_score += 2
    elif reasoning_steps > 3:
        complexity_score += 1
    
    # 3. 处理时间复杂度
    if processing_time > 600:  # 10分钟
        complexity_score += 3
    elif processing_time > 300:  # 5分钟
        complexity_score += 2
    elif processing_time > 120:  # 2分钟
        complexity_score += 1
    
    # 4. 重试/fallback复杂度
    if fallback_triggered:
        complexity_score += 2  # 触发了fallback，说明处理复杂
    if retry_count > 0:
        complexity_score += 1  # 需要重试，说明处理复杂
    
    # 5. 验证复杂度
    if not validation_passed:
        complexity_score += 1  # 验证失败，说明处理复杂
    
    # 转换为复杂度等级
    if complexity_score >= 6:
        return "complex"
    elif complexity_score >= 3:
        return "medium"
    else:
        return "simple"
```

---

### 方案2: 基于处理阶段的渐进评估

**思路**: 在处理的不同阶段，根据实际表现逐步调整复杂度评估

**实现**:
```python
def _assess_complexity_progressively(
    self,
    stage: str,  # "evidence_retrieval", "reasoning", "validation", "final"
    context: Dict[str, Any]
) -> str:
    """基于处理阶段的渐进评估复杂度"""
    
    if stage == "evidence_retrieval":
        # 证据检索阶段
        evidence_count = context.get('evidence_count', 0)
        evidence_relevance = context.get('evidence_relevance', 0.0)
        
        if evidence_count == 0 or evidence_relevance < 0.3:
            return "complex"  # 需要重新检索
        elif evidence_count > 5:
            return "medium"
        else:
            return "simple"
    
    elif stage == "reasoning":
        # 推理阶段
        reasoning_steps = context.get('reasoning_steps', 0)
        reasoning_time = context.get('reasoning_time', 0.0)
        
        if reasoning_steps > 5 or reasoning_time > 300:
            return "complex"
        elif reasoning_steps > 3 or reasoning_time > 120:
            return "medium"
        else:
            return "simple"
    
    elif stage == "validation":
        # 验证阶段
        validation_time = context.get('validation_time', 0.0)
        retry_count = context.get('retry_count', 0)
        
        if retry_count > 0 or validation_time > 200:
            return "complex"
        elif validation_time > 100:
            return "medium"
        else:
            return "simple"
    
    elif stage == "final":
        # 最终评估
        total_time = context.get('total_time', 0.0)
        fallback_triggered = context.get('fallback_triggered', False)
        
        if fallback_triggered or total_time > 600:
            return "complex"
        elif total_time > 300:
            return "medium"
        else:
            return "simple"
```

---

### 方案3: 基于历史数据的预测评估

**思路**: 基于相似查询的历史处理数据，预测当前查询的复杂度

**实现**:
```python
def _assess_complexity_from_history(
    self,
    query: str,
    query_type: str,
    historical_data: List[Dict[str, Any]]
) -> str:
    """基于历史数据预测复杂度"""
    
    # 查找相似查询的历史数据
    similar_queries = [
        h for h in historical_data
        if h.get('query_type') == query_type
        and self._calculate_similarity(query, h.get('query', '')) > 0.7
    ]
    
    if not similar_queries:
        return "medium"  # 无历史数据，使用默认值
    
    # 计算平均复杂度指标
    avg_time = sum(h.get('processing_time', 0) for h in similar_queries) / len(similar_queries)
    avg_steps = sum(h.get('reasoning_steps', 0) for h in similar_queries) / len(similar_queries)
    avg_retries = sum(h.get('retry_count', 0) for h in similar_queries) / len(similar_queries)
    
    # 基于历史数据评估
    if avg_time > 600 or avg_retries > 1:
        return "complex"
    elif avg_time > 300 or avg_steps > 3:
        return "medium"
    else:
        return "simple"
```

---

## 🎯 推荐方案

### 混合方案：动态评估 + 渐进调整

**核心思路**:
1. **初始评估**: 使用简单的启发式规则（基于查询类型、长度等）给出初始复杂度
2. **动态调整**: 在处理过程中，根据实际表现动态调整复杂度
3. **最终评估**: 基于完整处理过程的表现，给出最终复杂度评估

**优势**:
- 不依赖查询文本本身
- 基于实际处理表现
- 可以动态调整
- 适应性强

---

## 📊 实施步骤

### P0优化（立即实施）

1. **移除基于查询文本的复杂度判断**
   - 移除`_estimate_query_complexity_with_llm`中的查询文本分析
   - 移除`_estimate_query_complexity_with_features`中的特征提取

2. **实现基于处理表现的动态评估**
   - 在处理过程中收集实际表现数据
   - 基于实际表现动态评估复杂度
   - 用于调整`max_tokens`、证据长度等参数

3. **实现渐进式复杂度调整**
   - 在不同处理阶段评估复杂度
   - 根据阶段表现调整后续处理策略

---

### P1优化（后续实施）

1. **实现历史数据学习**
   - 记录查询处理历史
   - 基于历史数据预测复杂度
   - 提高评估准确性

2. **实现自适应调整**
   - 根据处理表现自动调整参数
   - 优化处理策略

---

## 🎯 总结

### 核心改进

1. **从静态判断改为动态评估**: 不再基于查询文本，而是基于实际处理表现
2. **从预测改为观察**: 不再预测复杂度，而是观察实际复杂度
3. **从固定改为自适应**: 根据实际表现动态调整处理策略

### 预期效果

1. **更准确的复杂度评估**: 基于实际表现，而非文本特征
2. **更合理的资源分配**: 根据实际复杂度调整`max_tokens`、证据长度等
3. **更好的性能优化**: 根据实际表现优化处理策略

---

*提案完成时间: 2025-11-10*

