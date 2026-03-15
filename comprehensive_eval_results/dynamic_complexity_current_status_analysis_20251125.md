# 动态复杂度当前状态分析（2025-11-25）

**分析时间**: 2025-11-25  
**数据来源**: 终端运行日志（样本1-3）

---

## 📊 当前状态

### 从终端日志分析

**样本1**:
- LLM判断查询复杂度: **complex**
- 动态复杂度: **complex**
- 使用模型: **deepseek-reasoner**（推理模型）
- 处理时间: 331.78秒

**样本2**:
- LLM判断查询复杂度: **complex**
- 动态复杂度: **complex**
- 使用模型: **deepseek-reasoner**（推理模型）
- 处理时间: 308.47秒

**样本3**:
- LLM判断查询复杂度: **complex**
- 动态复杂度: **complex**
- 使用模型: **deepseek-reasoner**（推理模型）

**关键发现**:
- ⚠️ **所有样本都被LLM判断为"complex"**
- ⚠️ **所有样本都使用了推理模型（deepseek-reasoner）**
- ⚠️ **没有使用快速模型（deepseek-chat）的样本**

---

## 🔍 问题分析

### 问题1：所有样本都是"complex" ⚠️

**表现**:
- 从日志看，所有3个样本都被LLM判断为"complex"
- 与之前的50个样本都是"medium"不同，现在是所有样本都是"complex"

**可能原因**:

#### 原因1：LLM判断逻辑过于严格

**LLM判断提示词**（`_estimate_query_complexity_with_llm`）:
- 要求区分"multi-hop"和"complex reasoning"
- 但可能LLM将所有多跳查询都判断为"complex"

**分析**:
- FRAMES数据集中的查询大多是复杂查询
- LLM可能将所有需要多步推理的查询都判断为"complex"
- 导致所有样本都使用推理模型

#### 原因2：LLM判断的复杂度被直接使用

**代码逻辑**:
```python
llm_complexity_for_log = getattr(self, '_last_llm_complexity', None)
if llm_complexity_for_log:
    dynamic_complexity = llm_complexity_for_log  # 直接使用LLM判断的复杂度
```

**分析**:
- 如果LLM判断为"complex"，就直接使用"complex"
- 没有结合其他因素（如处理时间、证据数量等）进行综合判断
- 导致所有样本都是"complex"

---

### 问题2：所有样本都使用推理模型 ⚠️

**表现**:
- 所有样本都使用`deepseek-reasoner`（推理模型）
- 没有样本使用`deepseek-chat`（快速模型）

**影响**:
- 性能问题严重：推理模型响应时间280-306秒
- 所有查询都使用慢速模型，无法利用快速模型提升性能

**根本原因**:
- LLM判断所有查询都是"complex"
- 系统强制使用推理模型（"✅ LLM判断为complex，强制使用推理模型"）

---

## 🎯 根本原因

### 根本原因1：LLM判断过于严格

**问题**:
- LLM将所有多跳查询都判断为"complex"
- 但实际上很多多跳查询应该使用快速模型（"medium"）

**LLM提示词问题**:
- 提示词要求区分"multi-hop"和"complex reasoning"
- 但LLM可能无法准确区分，将所有多跳查询都判断为"complex"

### 根本原因2：缺少综合判断

**问题**:
- 直接使用LLM判断的复杂度，没有结合其他因素
- 应该结合处理时间、证据数量等因素进行综合判断

**当前逻辑**:
```python
if llm_complexity_for_log:
    dynamic_complexity = llm_complexity_for_log  # 直接使用
else:
    dynamic_complexity = self._assess_complexity_progressively(...)  # 规则判断
```

**问题**:
- 如果LLM判断为"complex"，就直接使用，不再考虑其他因素
- 应该结合LLM判断和规则判断，进行综合评估

---

## 💡 优化建议

### 建议1：改进LLM判断提示词 ⭐⭐⭐⭐⭐

**问题**: LLM判断过于严格，将所有多跳查询都判断为"complex"

**优化方案**:
```python
# 优化提示词，更明确地区分multi-hop和complex reasoning
complexity_prompt = f"""Analyze the complexity of the following query and return ONLY one word: "simple", "medium", or "complex".

**CRITICAL: Multi-hop fact chaining is MEDIUM, not COMPLEX**

**Multi-hop query (MEDIUM)**:
- Requires multiple steps of fact lookup
- Each step is a DIRECT fact lookup (no complex reasoning)
- Example: "Who released album X? What school did they attend? Who else attended that school?"
- Example: "The artist who released X went to the same school as Y, how many teams did Y participate on?"

**Complex reasoning (COMPLEX)**:
- Requires logical deduction, calculation, analysis, or inference
- Example: "Calculate the total population of all cities that meet condition X and Y"
- Example: "If X happened, what would be the result?"

**Simple query (SIMPLE)**:
- Single step, direct fact lookup
- Example: "What is the capital of France?"

Query: {query[:500]}

Return ONLY one word: "simple", "medium", or "complex".
"""
```

**预期效果**:
- 更多多跳查询被判断为"medium"
- 只有真正需要复杂推理的查询被判断为"complex"

---

### 建议2：结合LLM判断和规则判断 ⭐⭐⭐⭐⭐

**问题**: 直接使用LLM判断，没有结合其他因素

**优化方案**:
```python
# 结合LLM判断和规则判断
llm_complexity = getattr(self, '_last_llm_complexity', None)
rule_complexity = self._assess_complexity_progressively("evidence_retrieval", evidence_context)

# 综合判断
if llm_complexity == "complex" and rule_complexity == "complex":
    dynamic_complexity = "complex"  # 两者都判断为complex，使用complex
elif llm_complexity == "simple" and rule_complexity == "simple":
    dynamic_complexity = "simple"  # 两者都判断为simple，使用simple
else:
    # 不一致时，使用更保守的判断（选择更复杂的）
    if llm_complexity == "complex" or rule_complexity == "complex":
        dynamic_complexity = "complex"
    elif llm_complexity == "medium" or rule_complexity == "medium":
        dynamic_complexity = "medium"
    else:
        dynamic_complexity = "simple"
```

**预期效果**:
- 更准确的复杂度判断
- 减少误判（所有都是complex）

---

### 建议3：添加处理时间反馈机制 ⭐⭐⭐⭐

**问题**: 没有根据实际处理时间调整复杂度判断

**优化方案**:
```python
# 在最终答案推导后，根据实际处理时间调整复杂度
actual_processing_time = time.time() - derive_start_time

if actual_processing_time < 30:  # 处理时间短
    # 如果处理时间短，说明查询可能不是complex
    if dynamic_complexity == "complex":
        # 降级为medium
        dynamic_complexity = "medium"
        self.logger.info(f"⚠️ 根据处理时间调整复杂度: complex → medium (处理时间: {actual_processing_time:.2f}秒)")
elif actual_processing_time > 300:  # 处理时间长
    # 如果处理时间长，说明查询确实是complex
    if dynamic_complexity != "complex":
        # 升级为complex
        dynamic_complexity = "complex"
        self.logger.info(f"⚠️ 根据处理时间调整复杂度: {previous_complexity} → complex (处理时间: {actual_processing_time:.2f}秒)")
```

**预期效果**:
- 根据实际处理表现调整复杂度判断
- 处理时间短的查询使用快速模型
- 处理时间长的查询使用推理模型

---

### 建议4：降低LLM判断的权重 ⭐⭐⭐

**问题**: LLM判断的权重过高，直接决定复杂度

**优化方案**:
```python
# 降低LLM判断的权重，增加规则判断的权重
llm_complexity = getattr(self, '_last_llm_complexity', None)
rule_complexity = self._assess_complexity_progressively("evidence_retrieval", evidence_context)

# 如果LLM判断为complex，但规则判断为simple/medium，使用规则判断
if llm_complexity == "complex" and rule_complexity in ["simple", "medium"]:
    # 规则判断更保守，使用规则判断
    dynamic_complexity = rule_complexity
    self.logger.info(f"⚠️ LLM判断为complex，但规则判断为{rule_complexity}，使用规则判断")
else:
    # 其他情况，使用LLM判断
    dynamic_complexity = llm_complexity or rule_complexity
```

**预期效果**:
- 减少LLM误判的影响
- 更多查询使用快速模型

---

## 📊 预期优化效果

### 优化前

| 复杂度等级 | 样本数 | 占比 | 使用模型 |
|-----------|--------|------|---------|
| complex | 3/3 | 100% | deepseek-reasoner |
| medium | 0 | 0% | - |
| simple | 0 | 0% | - |

### 优化后（预期）

| 复杂度等级 | 样本数 | 占比 | 使用模型 |
|-----------|--------|------|---------|
| complex | 10-20% | 10-20% | deepseek-reasoner |
| medium | 60-70% | 60-70% | deepseek-chat |
| simple | 10-20% | 10-20% | deepseek-chat |

**预期效果**:
- 更多查询使用快速模型（deepseek-chat）
- 平均处理时间从300秒降至50-100秒
- 性能提升：60-80%

---

## 🎯 结论

### 当前问题

1. ⚠️ **所有样本都被LLM判断为"complex"** - LLM判断过于严格
2. ⚠️ **所有样本都使用推理模型** - 无法利用快速模型提升性能
3. ⚠️ **处理时间过长** - 280-306秒，远超正常范围

### 优化优先级

1. **P0（最高）**: 改进LLM判断提示词，更明确地区分multi-hop和complex reasoning
2. **P1（高）**: 结合LLM判断和规则判断，进行综合评估
3. **P2（中）**: 添加处理时间反馈机制，根据实际处理表现调整复杂度
4. **P3（低）**: 降低LLM判断的权重，增加规则判断的权重

### 下一步行动

1. **立即优化LLM判断提示词**（P0）:
   - 更明确地区分multi-hop（medium）和complex reasoning（complex）
   - 强调多跳查询应该判断为"medium"

2. **结合LLM判断和规则判断**（P1）:
   - 不要直接使用LLM判断
   - 结合规则判断进行综合评估

3. **添加处理时间反馈**（P2）:
   - 根据实际处理时间调整复杂度判断
   - 处理时间短的查询使用快速模型

---

**报告生成时间**: 2025-11-25  
**数据来源**: 终端运行日志（样本1-3）  
**关键发现**: 所有样本都被LLM判断为"complex"，都使用推理模型

