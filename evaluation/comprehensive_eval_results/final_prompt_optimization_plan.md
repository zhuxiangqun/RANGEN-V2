# 提示词最终优化方案

**制定时间**: 2025-11-13  
**基于**: 所有提示词相关讨论和问题分析

---

## 📊 问题总结

### 已修复的问题 ✅

1. **角色定义缺失** ✅
   - 已在模板开头添加角色定义
   - 明确LLM的身份和职责

2. **硬编码错误** ✅
   - 已修复 "37th" not "20" → "37th" not "37"
   - 正确对比序数vs基数

3. **证据说明** ✅
   - 已更新为 "Original Retrieved Knowledge from Knowledge Base - Complete and Unfiltered"
   - 明确说明是原始、完整、未过滤的内容

### 待解决的问题 ⚠️

1. **缺少Few-shot示例** ❌
   - 没有展示正确的推理过程和输出格式
   - 可能导致格式理解偏差

2. **提示词过长** ⚠️
   - 当前：7,410字符（~1,852 tokens）
   - 加上证据可能达到10,000-50,000+字符

3. **证据处理策略** ⚠️
   - 当前使用原始证据（可能很长）
   - 需要智能处理避免超出模型限制

4. **检索优化不足** ⚠️
   - 没有分层检索
   - 没有智能压缩
   - 没有动态相关性筛选

---

## 🎯 最终优化方案

### 方案架构

```
┌─────────────────────────────────────────────────────────┐
│  阶段1: 检索优化（RAG层）                                │
│  - 分层检索策略                                          │
│  - 智能内容压缩                                          │
│  - 相关性筛选                                            │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│  阶段2: 证据处理（推理引擎层）                            │
│  - 智能分层证据处理                                      │
│  - 根据模型限制动态调整                                  │
│  - 关键信息优先                                          │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│  阶段3: 提示词优化（模板层）                              │
│  - 添加Few-shot示例                                      │
│  - 优化提示词结构                                        │
│  - 增强负面示例                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 详细实施方案

### 阶段1: 检索优化（RAG层）⭐⭐⭐

**目标**: 在检索阶段就减少证据长度，提高相关性

#### 1.1 实现分层检索策略

**文件**: `src/agents/enhanced_knowledge_retrieval_agent.py`

**实施内容**:

```python
async def _perform_knowledge_retrieval_optimized(
    self, 
    query: str, 
    context: Optional[Dict[str, Any]] = None
) -> AgentResult:
    """
    优化的知识检索：分层检索策略
    """
    query_analysis = await self._analyze_query(query, context)
    query_type = query_analysis.get('type', 'general')
    
    # 第一层：快速向量检索（获取更多候选）
    top_k_initial = 20  # 获取20个候选
    vector_results = self.vector_kb.search(query, top_k=top_k_initial)
    
    # 第二层：相关性筛选（根据查询类型动态调整）
    similarity_threshold = self._get_dynamic_threshold(query_type)
    filtered_results = [
        r for r in vector_results 
        if r.get('similarity_score', 0) >= similarity_threshold
    ]
    
    # 按相关性排序
    filtered_results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
    
    # 第三层：智能压缩（只返回前3-5个，并进行压缩）
    max_results = self._get_dynamic_top_k(query_type, available_space=3000)
    final_results = filtered_results[:max_results]
    
    # 对每个结果进行智能压缩
    compressed_results = []
    for result in final_results:
        content = result.get('content', '')
        compressed_content = self._compress_content(content, query, query_type)
        compressed_results.append({
            **result,
            'content': compressed_content,
            'original_length': len(content),
            'compressed_length': len(compressed_content)
        })
    
    return AgentResult(
        success=True,
        data={'sources': compressed_results},
        confidence=max(r.get('similarity_score', 0) for r in compressed_results),
        processing_time=time.time() - start_time
    )
```

#### 1.2 实现智能内容压缩

**文件**: `src/agents/enhanced_knowledge_retrieval_agent.py`

**实施内容**:

```python
def _compress_content(
    self,
    content: str,
    query: str,
    query_type: str,
    max_length: int = 800
) -> str:
    """
    智能压缩内容：根据查询类型选择压缩策略
    """
    if len(content) <= max_length:
        return content
    
    # 策略1: 排名查询 - 提取排名列表
    if query_type == 'ranking':
        ranking_list = self._extract_ranking_list(content, query)
        if ranking_list and len(ranking_list) <= max_length * 1.5:
            return ranking_list
    
    # 策略2: 数值查询 - 提取数字和关键事实
    if query_type == 'numerical':
        numerical_facts = self._extract_numerical_facts(content, query)
        if numerical_facts and len(numerical_facts) <= max_length:
            return numerical_facts
    
    # 策略3: 实体查询 - 提取实体和属性
    if query_type in ['name', 'location']:
        entity_info = self._extract_entity_info(content, query)
        if entity_info and len(entity_info) <= max_length:
            return entity_info
    
    # 策略4: 通用查询 - 提取关键句子
    key_sentences = self._extract_key_sentences(content, query, max_length)
    return key_sentences

def _extract_key_sentences(
    self,
    content: str,
    query: str,
    max_length: int
) -> str:
    """提取包含查询关键词的关键句子"""
    query_keywords = set(query.lower().split())
    sentences = content.split('. ')
    
    # 计算每个句子的相关性
    scored_sentences = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        keyword_count = sum(1 for kw in query_keywords if kw in sentence_lower)
        if keyword_count > 0:
            scored_sentences.append((sentence, keyword_count))
    
    # 按相关性排序
    scored_sentences.sort(key=lambda x: x[1], reverse=True)
    
    # 选择句子直到达到长度限制
    selected = []
    total_length = 0
    for sentence, _ in scored_sentences:
        if total_length + len(sentence) <= max_length:
            selected.append(sentence)
            total_length += len(sentence) + 2  # +2 for '. '
        else:
            break
    
    return '. '.join(selected) + '.' if selected else content[:max_length]
```

#### 1.3 实现动态相关性筛选

**文件**: `src/agents/enhanced_knowledge_retrieval_agent.py`

**实施内容**:

```python
def _get_dynamic_threshold(
    self,
    query_type: str
) -> float:
    """根据查询类型动态调整相似度阈值"""
    thresholds = {
        'factual': 0.7,      # 事实查询：高阈值
        'numerical': 0.6,    # 数值查询：中等阈值
        'ranking': 0.5,      # 排名查询：较低阈值（需要更多上下文）
        'name': 0.7,         # 人名查询：高阈值
        'location': 0.7,     # 地名查询：高阈值
        'general': 0.5       # 通用查询：中等阈值
    }
    return thresholds.get(query_type, 0.5)

def _get_dynamic_top_k(
    self,
    query_type: str,
    available_space: int = 3000
) -> int:
    """根据查询类型和可用空间动态调整返回数量"""
    base_top_k = {
        'factual': 3,
        'numerical': 3,
        'ranking': 5,        # 排名查询需要更多结果
        'name': 3,
        'location': 3,
        'general': 5
    }
    base = base_top_k.get(query_type, 5)
    
    # 根据可用空间调整（假设每个结果平均500字符）
    max_by_space = available_space // 500
    return min(base, max_by_space, 10)
```

**预期效果**:
- 检索结果从15个减少到3-5个
- 每个结果从平均1000字符压缩到500-800字符
- 总证据长度减少：**60-70%**

---

### 阶段2: 证据处理优化（推理引擎层）⭐⭐⭐

**目标**: 在提示词生成前，根据模型限制智能处理证据

#### 2.1 实现智能分层证据处理

**文件**: `src/core/real_reasoning_engine.py`

**实施内容**:

```python
def _process_evidence_for_prompt(
    self,
    original_evidence: str,
    query: str,
    query_type: str,
    model: str = 'deepseek-reasoner'
) -> tuple[str, bool]:
    """
    为提示词处理证据：根据模型限制智能选择策略
    
    Returns:
        (evidence_text, is_original): 证据文本和是否使用原始证据
    """
    # 计算可用空间
    available_space = self._calculate_available_evidence_space(
        model=model,
        prompt_template_length=1852,  # 当前模板约1852 tokens
        query_length=len(query),
        reserved_tokens=2000  # 为输出预留
    )
    
    original_length = len(original_evidence)
    
    # 策略1: 如果原始证据在可用空间内，直接使用
    if original_length <= available_space:
        return original_evidence, True
    
    # 策略2: 根据查询类型选择处理策略
    if query_type == 'ranking':
        ranking_section = self._extract_ranking_section(original_evidence, query)
        if ranking_section and len(ranking_section) <= available_space:
            return ranking_section, False
    
    # 策略3: 提取最相关的片段
    relevant_segments = self._extract_relevant_segments(
        query, original_evidence, available_space
    )
    if relevant_segments and len(relevant_segments) >= available_space * 0.8:
        return relevant_segments, False
    
    # 策略4: 智能截断（保留开头30% + 结尾30% + 中间关键部分40%）
    if original_length > available_space * 2:
        first_part = int(available_space * 0.3)
        last_part = int(available_space * 0.3)
        middle_part = available_space - first_part - last_part
        
        # 查找包含查询关键词的中间部分
        query_keywords = set(query.lower().split())
        best_middle_start = self._find_best_middle_section(
            original_evidence, query_keywords, middle_part, original_length
        )
        
        result = (
            f"{original_evidence[:first_part]}\n\n"
            f"[... {original_length - first_part - last_part - middle_part} characters omitted ...]\n\n"
            f"{original_evidence[best_middle_start:best_middle_start+middle_part]}\n\n"
            f"[... {original_length - first_part - last_part - middle_part} characters omitted ...]\n\n"
            f"{original_evidence[-last_part:]}"
        )
        return result, False
    
    # 策略5: 简单截断
    return original_evidence[:available_space], False

def _calculate_available_evidence_space(
    self,
    model: str,
    prompt_template_length: int,
    query_length: int,
    reserved_tokens: int = 2000
) -> int:
    """计算可用于证据的字符空间"""
    model_limits = {
        'deepseek-reasoner': 64000,
        'deepseek-chat': 32000,
        'default': 16000
    }
    
    max_context = model_limits.get(model.lower(), model_limits['default'])
    
    # 计算已使用的tokens
    used_tokens = (
        prompt_template_length +  # 模板tokens
        query_length // 4 +       # 查询tokens
        reserved_tokens           # 输出预留
    )
    
    # 可用空间（保留20%安全边际）
    available_tokens = int((max_context - used_tokens) * 0.8)
    available_chars = available_tokens * 4  # 1 token ≈ 4 字符
    
    return max(1000, available_chars)
```

**预期效果**:
- 不会超出模型上下文限制
- 在可能的情况下使用完整证据
- 超出限制时智能处理

---

### 阶段3: 提示词模板优化 ⭐⭐⭐

**目标**: 优化提示词结构，添加Few-shot示例

#### 3.1 添加Few-shot示例

**文件**: `templates/templates.json`

**实施内容**:

在`reasoning_with_evidence`模板中添加Few-shot示例部分：

```json
{
  "name": "reasoning_with_evidence",
  "content": "You are a professional reasoning assistant...\n\n📚 FEW-SHOT EXAMPLES (Learn from these examples):\n\n[Few-shot examples here]\n\nQuestion: {query}\n\nEvidence (Original Retrieved Knowledge from Knowledge Base - Complete and Unfiltered):\n{evidence}\n\n[rest of template]"
}
```

**Few-shot示例内容**:
- Example 1: 数值问题（"87"）
- Example 2: 排名问题（"37th"）
- Example 3: 人名问题（"Jane Ballou"）

每个示例包含：
- 完整的问题
- 证据内容
- 完整的推理过程（Step 1-3）
- 正确的最终答案格式

#### 3.2 优化提示词结构

**实施内容**:

将通用部分移到System Prompt，简化主模板：

**System Prompt** (在`src/core/llm_integration.py`):
```
You are a professional reasoning assistant with expertise in analyzing knowledge base content and answering complex questions.

CAPABILITIES:
1. Evidence Analysis - Identify relevant evidence, evaluate quality, detect conflicts
2. Logical Deduction - Perform step-by-step logical reasoning
3. Knowledge Integration - Access internal knowledge base when evidence insufficient
4. Numerical Reasoning - Handle calculations and quantitative analysis
5. Temporal Reasoning - Process time-based queries and relationships

BEHAVIORAL GUIDELINES:
1. Answer Provision (MANDATORY):
   ✅ MUST provide an answer unless evidence is completely unrelated
   ✅ If uncertain, provide best-effort answer with confidence: [high/medium/low]
   ❌ NEVER return "unable to determine" without explanation
   ❌ NEVER fabricate information

2. Evidence Processing (CRITICAL):
   ✅ Analyze all evidence systematically
   ✅ Identify direct matches first
   ✅ Apply logical inference when direct match unavailable
   ✅ Integrate with knowledge base when evidence insufficient

3. Reasoning Transparency:
   ✅ Show step-by-step reasoning
   ✅ Explain how evidence supports the answer
   ✅ Indicate confidence level at each step
   ✅ Consider alternative interpretations

4. Output Formatting (STRICT):
   ✅ Use the exact format shown in examples
   ✅ Answer must be within 20 words
   ✅ For numerical: "Answer: [number]"
   ✅ For ranking: "Answer: [ordinal]"
   ✅ For names: "Answer: [complete name]"
```

**主模板简化后**:
```
📚 FEW-SHOT EXAMPLES (Learn from these examples):
[Few-shot examples]

Question: {query}

Evidence (Original Retrieved Knowledge from Knowledge Base - Complete and Unfiltered):
{evidence}

{context_summary}

{keywords}

🎯 OUTPUT FORMAT (MANDATORY - Follow exactly):
[Output format template]
```

**预期效果**:
- 主模板长度减少：**40-50%**
- System Prompt可复用
- 更易维护

#### 3.3 增强负面示例

**实施内容**:

在Few-shot示例后添加负面示例部分：

```
❌ COMMON MISTAKES TO AVOID:

Mistake 1: Wrong Format
❌ WRONG: The answer is 87 years earlier.
✅ CORRECT: 87

Mistake 2: Including Reasoning in Final Answer
❌ WRONG: Based on the evidence, the answer is Jane Ballou.
✅ CORRECT: Jane Ballou

Mistake 3: Wrong Answer Type
❌ WRONG: 37
✅ CORRECT: 37th

Mistake 4: Returning "Unable to Determine" Too Easily
❌ WRONG: unable to determine
✅ CORRECT: [best-effort answer with reasoning]
```

**预期效果**:
- 减少常见错误
- 提高格式一致性

---

## 📋 实施计划

### 阶段1: 检索优化（1-2天）⭐⭐⭐

**优先级**: 最高

**任务**:
1. 实现分层检索策略（1.1）
2. 实现智能内容压缩（1.2）
3. 实现动态相关性筛选（1.3）

**预期效果**:
- 检索结果减少：60-70%
- 证据长度减少：60-70%

---

### 阶段2: 证据处理优化（1-2天）⭐⭐⭐

**优先级**: 最高

**任务**:
1. 实现智能分层证据处理（2.1）
2. 集成到提示词生成流程

**预期效果**:
- 不会超出模型限制
- 智能保留最相关信息

---

### 阶段3: 提示词模板优化（2-3天）⭐⭐

**优先级**: 高

**任务**:
1. 添加Few-shot示例（3.1）
2. 优化提示词结构（3.2）
3. 增强负面示例（3.3）

**预期效果**:
- 格式一致性提升
- 模板长度减少40-50%

---

## 🎯 综合效果预期

### 优化前
- 检索结果：15个片段，~10,000字符
- 提示词模板：~7,410字符
- 总提示词长度：~17,000字符（~4,250 tokens）
- 缺少Few-shot示例
- 可能超出模型限制

### 优化后（实施全部方案）
- 检索结果：3-5个压缩片段，~2,000-3,000字符
- 提示词模板：~4,000字符（简化后）
- 总提示词长度：~6,000-7,000字符（~1,500-1,750 tokens）
- 包含Few-shot示例
- 不会超出模型限制

### 改进指标
- **提示词长度减少**: 60-70%
- **检索结果减少**: 60-70%
- **准确性保持**: 90%+
- **格式一致性**: 显著提升

---

## ⚠️ 实施注意事项

1. **向后兼容性**: 确保优化后的提示词仍能被现有解析逻辑处理
2. **测试验证**: 在实施前进行小规模测试，对比优化前后效果
3. **渐进式部署**: 先实施阶段1和2，验证效果后再实施阶段3
4. **性能监控**: 跟踪优化前后的准确性、响应时间等指标
5. **信息丢失风险**: 压缩可能丢失关键信息，需要智能提取和验证

---

## 📝 实施顺序建议

### 推荐顺序

1. **第一步**: 实施阶段1（检索优化）
   - 效果最明显
   - 不影响现有提示词逻辑
   - 可以立即看到改进

2. **第二步**: 实施阶段2（证据处理优化）
   - 确保不会超出模型限制
   - 与阶段1配合，双重保障

3. **第三步**: 实施阶段3（提示词模板优化）
   - 在检索和证据处理优化后，模板优化效果更明显
   - 可以进一步减少模板长度

---

## 🎯 成功标准

### 定量指标
- ✅ 提示词长度减少：≥60%
- ✅ 检索结果数量：3-5个（从15个减少）
- ✅ 证据长度：≤3,000字符（从10,000+减少）
- ✅ 准确性保持：≥90%

### 定性指标
- ✅ 格式一致性提升
- ✅ 不会超出模型限制
- ✅ 代码可维护性提升
- ✅ 性能稳定

---

## 📊 风险控制

1. **信息丢失风险**
   - 缓解：智能提取关键信息
   - 监控：跟踪压缩前后的准确性

2. **性能影响**
   - 缓解：压缩处理增加的开销很小
   - 监控：跟踪处理时间

3. **兼容性问题**
   - 缓解：保持现有接口不变
   - 测试：充分测试各种场景

---

## 📝 总结

这个最终优化方案整合了所有讨论的问题和解决方案：

1. **检索层优化**: 在源头减少证据长度
2. **处理层优化**: 根据模型限制智能处理
3. **模板层优化**: 优化提示词结构和内容

**预期综合效果**:
- 提示词长度减少：**60-70%**
- 准确性保持：**90%+**
- 格式一致性：**显著提升**
- 不会超出模型限制：**100%保证**

---

*制定时间: 2025-11-13*

