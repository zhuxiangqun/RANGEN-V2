# 样本知识检索和提示词组织流程分析

**分析时间**: 2025-11-08

---

## 📊 完整流程概览

```
用户查询 (Query)
    ↓
[1] 查询类型分析 (query_type)
    ↓
[2] 知识检索 (Knowledge Retrieval)
    ↓
[3] 证据收集和处理 (Evidence Processing)
    ↓
[4] 提示词生成 (Prompt Generation)
    ↓
[5] LLM推理 (LLM Reasoning)
    ↓
[6] 答案提取和验证 (Answer Extraction & Validation)
```

---

## 🔍 详细流程分析

### 步骤1: 查询类型分析

**代码位置**: `src/core/real_reasoning_engine.py` Line 896

**流程**:
```python
query_type = self._analyze_query_type_with_ml(query)
# 返回: "factual", "numerical", "temporal", "location", "country", "general" 等
```

**作用**: 
- 确定查询类型，用于后续的知识检索阈值调整和提示词生成

---

### 步骤2: 知识检索

**代码位置**: `src/core/real_reasoning_engine.py` Line 850-950 (调用 `_gather_evidence`)

**详细流程**:

#### 2.1 调用知识检索智能体
```python
# Line 850-870
knowledge_agent = EnhancedKnowledgeRetrievalAgent()
knowledge_result = await knowledge_agent.execute({
    "query": query,
    "query_type": query_type  # 用于动态阈值调整
})
```

#### 2.2 知识检索智能体内部流程
**代码位置**: `src/agents/enhanced_knowledge_retrieval_agent.py` Line 927-1067

```python
# 1. 确定检索参数
enhanced_top_k = max(top_k * 3, 15)  # 至少检索15条
optimized_threshold = self._get_dynamic_similarity_threshold(query_type, query)
# - name/location/person/country: 0.55
# - numerical/ranking/mathematical: 0.35
# - general: 0.45

# 2. 调用知识库管理系统
results = self.kms_service.query_knowledge(
    query=query,  # 原始查询，直接使用
    modality="text",
    top_k=enhanced_top_k,
    similarity_threshold=optimized_threshold,
    use_rerank=True,  # 使用Jina Rerank二次排序
    use_graph=True    # 启用知识图谱
)

# 3. 多维度验证
for result in results:
    if self._validate_result_multi_dimension(result, query, query_type):
        validated_results.append(result)
    # 验证包括：
    # - 相似度验证（动态阈值）
    # - 实体匹配验证（至少20%实体匹配）
    # - 关键词匹配验证（至少15%关键词匹配）

# 4. 如果所有结果都被过滤，使用宽松模式
if not validated_results:
    # 降低阈值重试
    relaxed_threshold = max(0.25, optimized_threshold - 0.1)
    # 只检查相似度和基本内容
```

**关键点**:
- **查询直接使用**: 查询文本直接传递给知识库，没有查询扩展
- **动态阈值**: 根据查询类型调整相似度阈值
- **多维度验证**: 相似度 + 实体匹配 + 关键词匹配
- **宽松模式**: 如果严格验证失败，使用更宽松的阈值

---

### 步骤3: 证据收集和处理

**代码位置**: `src/core/real_reasoning_engine.py` Line 2325-2408

#### 3.1 证据收集 (`_gather_evidence`)
```python
# 从knowledge_result中提取证据
evidence = []
for source in knowledge_result.data.get('sources', []):
    evidence.append(Evidence(
        content=source.get('content', ''),
        source=source.get('source', 'unknown'),
        confidence=source.get('similarity', 0.0)
    ))
```

#### 3.2 证据过滤
```python
# 过滤无效证据（如问题、错误消息等）
filtered_evidence = []
for ev in evidence:
    if self._is_valid_evidence(ev, query):
        filtered_evidence.append(ev)
```

#### 3.3 证据文本提取
```python
evidence_text_filtered = "\n".join([
    ev.content for ev in filtered_evidence
])
```

#### 3.4 智能证据处理 (`_process_evidence_intelligently`)
**代码位置**: `src/core/real_reasoning_engine.py` Line 319-373

```python
enhanced_evidence_text = self._process_evidence_intelligently(
    query, evidence_text_filtered, filtered_evidence
)

# 处理逻辑：
# 1. 根据查询复杂度确定目标长度
#    - 简单查询: 1200字符
#    - 中等查询: 1500字符
#    - 复杂查询: 2000字符
# 2. 如果证据超过目标长度，智能压缩：
#    - 优先保留包含查询关键词的片段
#    - 提取第一句话（通常是摘要）
#    - 如果仍超长，使用智能截断（保留开头和结尾）
```

---

### 步骤4: 提示词生成

**代码位置**: `src/core/real_reasoning_engine.py` Line 375-500

#### 4.1 选择模板
```python
if has_valid_evidence:
    template_name = "reasoning_with_evidence"
else:
    template_name = "reasoning_without_evidence"
```

#### 4.2 提取上下文信息
```python
# 从enhanced_context中提取
context_summary = enhanced_context.get('context_summary', '')
keywords = enhanced_context.get('keywords', [])
query_type = query_type  # 已分析的查询类型
```

#### 4.3 构建提示词参数
```python
prompt_kwargs = {
    'query': query,
    'query_type': query_type,
    'evidence': enhanced_evidence_text,  # 处理后的证据
    'context_summary': context_summary,
    'keywords': ', '.join(keywords[:5])
}
```

#### 4.4 生成提示词
```python
# 使用提示词工程模块
prompt = self.prompt_engineering.generate_prompt(
    template_name,
    **prompt_kwargs
)

# 在提示词开头添加答案格式要求
format_instruction = self._get_answer_format_instruction(query_type, query)
if format_instruction:
    prompt = format_instruction + "\n\n" + prompt
```

#### 4.5 提示词模板内容
**模板位置**: `templates/templates.json`

**reasoning_with_evidence模板结构**:
```
🎯 KNOWLEDGE AND ANSWER FORMAT REQUIREMENTS (READ FIRST)
1. KNOWLEDGE CONTENT USAGE (CRITICAL)
2. ANSWER FORMAT (MANDATORY)

Question: {query}

Evidence (Retrieved Knowledge):
{evidence}

{context_summary}
{keywords}

AVAILABLE REASONING CAPABILITIES:
...

BEHAVIORAL GUIDELINES:
1. Answer Provision (MANDATORY)
2. Evidence Processing (CRITICAL - SMART USAGE)
   - STEP 1: KNOWLEDGE CONTENT ANALYSIS
   - STEP 2: INTELLIGENT KNOWLEDGE USAGE
   - STEP 3: SYSTEMATIC KNOWLEDGE EXTRACTION
3. Reasoning Transparency
4. Output Formatting (STRICT)

OUTPUT TEMPLATE (MANDATORY):
Reasoning Process:
Step 1: Evidence Quality Assessment and Review
Step 2: Logical Inference
Step 3: Answer Synthesis
Final Answer: [answer]
```

---

### 步骤5: LLM推理

**代码位置**: `src/core/real_reasoning_engine.py` Line 2431-2495

```python
# 1. 选择LLM模型
llm_to_use = self._select_llm_for_task(query, filtered_evidence, query_type)
# - 复杂推理任务: 使用推理模型 (deepseek-reasoner)
# - 简单任务: 使用快速模型 (deepseek-chat)

# 2. 调用LLM
response = llm_to_use._call_llm(prompt)

# 3. 处理响应
# - 提取"Reasoning Process:"格式的答案
# - 验证答案有效性
# - 清理答案
```

---

### 步骤6: 答案提取和验证

**代码位置**: `src/core/real_reasoning_engine.py` Line 2500-2950

```python
# 1. 提取答案
cleaned_response = self._extract_answer_from_reasoning_process(response)

# 2. 验证答案
reasonableness_result = self._validate_answer_reasonableness(
    cleaned_response, query_type, query, evidence
)

# 3. 如果验证失败，进入fallback
if not reasonableness_result['is_valid']:
    # 从证据中提取答案
    # 对提取的答案也进行验证
```

---

## 📝 关键发现

### 1. 查询直接使用，没有扩展
- **问题**: 查询文本直接传递给知识库，没有查询扩展
- **影响**: 如果查询用词与知识库不一致，可能检索不到相关知识
- **示例**: "FIFA World Cup holder" 可能检索不到，但 "World Cup winner" 可以

### 2. 证据处理可能丢失关键信息
- **问题**: 证据压缩可能截断关键信息
- **影响**: 即使检索到相关信息，也可能被截断
- **示例**: 排名列表可能被截断，丢失具体排名信息

### 3. 提示词要求LLM使用证据，但不强制
- **问题**: 提示词要求"基于证据回答"，但如果证据不相关，LLM仍可能使用自身知识
- **影响**: LLM可能生成不在证据中的答案
- **示例**: 证据中没有"France"，但LLM仍可能回答"France"

### 4. 验证逻辑在答案生成后
- **问题**: 答案验证在LLM生成答案后进行
- **影响**: 如果LLM生成错误答案，验证只能拒绝，不能预防
- **改进**: 应该在调用LLM前检查证据是否包含答案所需信息

---

## 🔧 改进建议

### 1. 查询扩展（P0）
- 添加查询扩展逻辑，生成多个查询变体
- 使用同义词和关联词扩展查询

### 2. 证据质量检查（P0）
- 在调用LLM前检查证据是否包含答案所需信息
- 如果证据不相关，直接返回"unable to determine"

### 3. 提示词增强（P1）
- 明确要求：如果证据不包含答案，必须返回"unable to determine"
- 禁止LLM在证据不相关时使用自身知识

### 4. 证据处理改进（P2）
- 改进证据压缩逻辑，保留关键实体和信息
- 使用智能摘要而非简单截断

