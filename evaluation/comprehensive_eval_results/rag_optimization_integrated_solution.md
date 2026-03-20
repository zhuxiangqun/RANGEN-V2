# RAG架构优化提示词长度 - 综合解决方案

**分析时间**: 2025-11-13  
**基于**: 用户提供的RAG优化方案 + 当前系统分析

---

## 📊 当前系统现状分析

### ✅ 已实现的功能

1. **向量检索** ✅
   - 使用FAISS进行向量相似度搜索
   - 支持`top_k`参数（当前默认15）
   - 支持`similarity_threshold`过滤（当前默认0.35）

2. **Rerank功能** ✅
   - 使用Jina Rerank进行二次排序
   - 在知识库管理系统中实现
   - 默认启用（`use_rerank=True`）

3. **相关性过滤** ✅
   - 基于相似度阈值过滤
   - 按相似度排序返回结果

4. **混合检索** ✅（部分）
   - 向量知识库（主要）
   - 知识图谱（可选，特定场景）

### ❌ 缺失的功能

1. **分层检索策略** ❌
   - 没有多阶段检索
   - 没有基于相关性分数的二次筛选

2. **智能内容压缩** ❌
   - 没有提取关键事实
   - 没有结构化提取
   - 没有摘要生成

3. **动态上下文管理** ❌
   - 没有根据模型限制动态调整
   - 没有增量检索

4. **递归检索** ❌
   - 没有基于LLM生成关键词的二次检索

5. **缓存机制** ❌
   - 没有查询结果缓存

---

## 🎯 综合优化方案

### 方案1: 分层检索策略 ⭐⭐⭐ (高优先级)

**目标**: 实现多阶段检索，逐步缩小范围

#### 1.1 第一层：快速向量检索

**当前状态**: ✅ 已实现

**优化建议**:
- 保持当前实现
- 第一层检索返回更多候选（如`top_k=20-30`）

#### 1.2 第二层：相关性筛选

**当前状态**: ⚠️ 部分实现（有相似度阈值，但不够智能）

**需要实现**:
```python
def _second_stage_filtering(
    self,
    candidates: List[Dict],
    query: str,
    query_type: str,
    max_results: int = 5
) -> List[Dict]:
    """
    第二层：基于相关性分数和查询类型筛选
    
    策略：
    - 事实查询 → 只返回高相关性（>0.7）的结果
    - 分析查询 → 返回中等相关性（>0.5）的结果
    - 排名查询 → 优先返回包含排名列表的结果
    """
    # 根据查询类型调整阈值
    threshold_map = {
        'factual': 0.7,      # 事实查询：高阈值
        'numerical': 0.6,    # 数值查询：中等阈值
        'ranking': 0.5,      # 排名查询：较低阈值（需要更多上下文）
        'name': 0.7,         # 人名查询：高阈值
        'location': 0.7,     # 地名查询：高阈值
        'general': 0.5       # 通用查询：中等阈值
    }
    
    threshold = threshold_map.get(query_type, 0.5)
    
    # 过滤和排序
    filtered = [
        r for r in candidates 
        if r.get('similarity_score', 0) >= threshold
    ]
    
    # 按相关性排序
    filtered.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
    
    # 返回前N个
    return filtered[:max_results]
```

#### 1.3 第三层：智能压缩和摘要

**当前状态**: ❌ 未实现

**需要实现**:
```python
def _third_stage_compression(
    self,
    results: List[Dict],
    query: str,
    query_type: str,
    max_total_length: int = 3000
) -> List[Dict]:
    """
    第三层：智能压缩和摘要
    
    压缩策略：
    1. 提取关键事实（实体、数字、关系）
    2. 移除冗余信息
    3. 结构化提取（转为键值对）
    4. 摘要生成（长段落压缩为1-2句）
    """
    compressed_results = []
    total_length = 0
    
    for result in results:
        content = result.get('content', '')
        if not content:
            continue
        
        # 根据查询类型选择压缩策略
        if query_type == 'ranking':
            # 排名查询：提取排名列表
            compressed = self._extract_ranking_list(content, query)
        elif query_type == 'numerical':
            # 数值查询：提取数字和关键事实
            compressed = self._extract_numerical_facts(content, query)
        elif query_type in ['name', 'location']:
            # 实体查询：提取实体和属性
            compressed = self._extract_entity_info(content, query)
        else:
            # 通用查询：提取关键句子
            compressed = self._extract_key_sentences(content, query, max_length=500)
        
        # 检查总长度
        if total_length + len(compressed) > max_total_length:
            # 如果超出限制，截断当前结果
            remaining = max_total_length - total_length
            if remaining > 200:  # 至少保留200字符
                compressed = compressed[:remaining]
                compressed_results.append({
                    **result,
                    'content': compressed,
                    'compressed': True
                })
            break
        
        compressed_results.append({
            **result,
            'content': compressed,
            'compressed': len(compressed) < len(content)
        })
        total_length += len(compressed)
    
    return compressed_results
```

**实施位置**: `src/agents/enhanced_knowledge_retrieval_agent.py`

---

### 方案2: 智能内容压缩技术 ⭐⭐⭐ (高优先级)

**目标**: 在保留关键信息的前提下，大幅减少内容长度

#### 2.1 提取关键事实

```python
def _extract_key_facts(
    self,
    content: str,
    query: str
) -> str:
    """
    提取关键事实：只保留直接相关的实体、数字、关系
    """
    # 提取查询关键词
    query_keywords = set(query.lower().split())
    
    # 按句子分割
    sentences = content.split('. ')
    
    # 筛选包含关键词的句子
    relevant_sentences = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        # 计算相关性分数
        keyword_count = sum(1 for kw in query_keywords if kw in sentence_lower)
        if keyword_count > 0:
            relevant_sentences.append((sentence, keyword_count))
    
    # 按相关性排序，取前N个
    relevant_sentences.sort(key=lambda x: x[1], reverse=True)
    key_sentences = [s[0] for s in relevant_sentences[:5]]
    
    return '. '.join(key_sentences) + '.'
```

#### 2.2 结构化提取

```python
def _extract_structured_info(
    self,
    content: str,
    query_type: str
) -> str:
    """
    结构化提取：转为键值对格式
    """
    if query_type == 'ranking':
        # 提取排名列表
        # 格式：{排名: 名称, 属性}
        pattern = r'(\d+)(?:st|nd|rd|th|\.)\s+([^,\n]+)'
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            structured = '\n'.join([f"{rank}{'th' if rank.endswith(('1', '2', '3')) else 'th'}: {name}" 
                                   for rank, name in matches[:20]])
            return structured
    
    elif query_type == 'numerical':
        # 提取数字和关键事实
        # 格式：{实体: 数值}
        numbers = re.findall(r'(\d+(?:,\d+)*(?:\.\d+)?)', content)
        # 提取包含数字的句子
        sentences_with_numbers = [
            s for s in content.split('. ')
            if re.search(r'\d+', s)
        ]
        return '. '.join(sentences_with_numbers[:3])
    
    elif query_type in ['name', 'location']:
        # 提取实体和属性
        # 格式：{实体: {属性: 值}}
        # 简化实现：提取包含实体名称的句子
        return content  # 暂时返回原内容，后续可以增强
    
    return content
```

#### 2.3 摘要生成

```python
def _generate_summary(
    self,
    content: str,
    max_length: int = 200
) -> str:
    """
    摘要生成：将长段落压缩为1-2句核心信息
    """
    if len(content) <= max_length:
        return content
    
    # 提取第一句（通常是摘要）
    first_sentence = content.split('. ')[0] + '.'
    
    # 如果第一句太短，添加第二句
    if len(first_sentence) < max_length * 0.5:
        sentences = content.split('. ')
        if len(sentences) > 1:
            summary = '. '.join(sentences[:2]) + '.'
            if len(summary) <= max_length:
                return summary
    
    # 如果还是太长，截断
    return first_sentence[:max_length] + '...'
```

**实施位置**: `src/core/real_reasoning_engine.py` - 新增方法

---

### 方案3: 智能相关性筛选 ⭐⭐ (中优先级)

**目标**: 根据查询类型动态调整返回内容量

#### 3.1 动态阈值调整

**当前状态**: ⚠️ 有固定阈值（0.35），但没有根据查询类型调整

**需要实现**:
```python
def _get_dynamic_threshold(
    self,
    query_type: str,
    query_complexity: str = 'medium'
) -> float:
    """
    根据查询类型和复杂度动态调整相似度阈值
    """
    base_thresholds = {
        'factual': 0.7,      # 事实查询：高阈值，只要最相关的
        'numerical': 0.6,    # 数值查询：中等阈值
        'ranking': 0.5,      # 排名查询：较低阈值（需要更多上下文）
        'name': 0.7,         # 人名查询：高阈值
        'location': 0.7,     # 地名查询：高阈值
        'temporal': 0.6,     # 时间查询：中等阈值
        'causal': 0.5,       # 因果查询：较低阈值（需要更多上下文）
        'general': 0.5       # 通用查询：中等阈值
    }
    
    base = base_thresholds.get(query_type, 0.5)
    
    # 根据复杂度调整
    complexity_adjustments = {
        'simple': 0.1,   # 简单查询：提高阈值
        'medium': 0.0,   # 中等查询：保持
        'complex': -0.1  # 复杂查询：降低阈值（需要更多结果）
    }
    
    adjustment = complexity_adjustments.get(query_complexity, 0.0)
    return max(0.3, min(0.9, base + adjustment))
```

#### 3.2 动态返回数量

```python
def _get_dynamic_top_k(
    self,
    query_type: str,
    available_space: int
) -> int:
    """
    根据查询类型和可用空间动态调整返回数量
    """
    # 基础返回数量
    base_top_k = {
        'factual': 3,        # 事实查询：少量精确结果
        'numerical': 3,      # 数值查询：少量精确结果
        'ranking': 5,        # 排名查询：需要更多结果（可能包含完整列表）
        'name': 3,           # 人名查询：少量精确结果
        'location': 3,       # 地名查询：少量精确结果
        'temporal': 4,       # 时间查询：中等数量
        'causal': 5,         # 因果查询：需要更多上下文
        'general': 5         # 通用查询：中等数量
    }
    
    base = base_top_k.get(query_type, 5)
    
    # 根据可用空间调整
    # 假设每个结果平均500字符
    estimated_chars_per_result = 500
    max_results_by_space = available_space // estimated_chars_per_result
    
    return min(base, max_results_by_space, 10)  # 最多10个
```

**实施位置**: `src/agents/enhanced_knowledge_retrieval_agent.py`

---

### 方案4: 上下文窗口优化 ⭐⭐⭐ (高优先级)

**目标**: 结合模型限制和可用空间，智能管理上下文

#### 4.1 关键信息优先

```python
def _prioritize_evidence(
    self,
    evidence_list: List[Dict],
    query: str
) -> List[Dict]:
    """
    关键信息优先：把最相关的证据放在前面
    """
    # 计算每个证据的相关性分数
    for evidence in evidence_list:
        content = evidence.get('content', '')
        similarity = evidence.get('similarity_score', 0.5)
        
        # 计算关键词匹配度
        query_keywords = set(query.lower().split())
        content_lower = content.lower()
        keyword_matches = sum(1 for kw in query_keywords if kw in content_lower)
        keyword_score = keyword_matches / len(query_keywords) if query_keywords else 0
        
        # 综合分数：相似度 + 关键词匹配
        evidence['priority_score'] = similarity * 0.7 + keyword_score * 0.3
    
    # 按优先级排序
    evidence_list.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
    
    return evidence_list
```

#### 4.2 分块处理

```python
def _chunk_complex_query(
    self,
    query: str
) -> List[str]:
    """
    复杂问题分解为多个子查询
    """
    # 检测是否是多部分问题
    if ' and ' in query.lower() or ' then ' in query.lower():
        # 简单分割（可以后续增强为LLM分割）
        parts = re.split(r'\s+(?:and|then)\s+', query, flags=re.IGNORECASE)
        return [p.strip() for p in parts if p.strip()]
    
    return [query]
```

#### 4.3 增量检索

```python
async def _incremental_retrieval(
    self,
    query: str,
    initial_results: List[Dict],
    llm_intermediate_result: Optional[str] = None
) -> List[Dict]:
    """
    增量检索：根据LLM的中间结果进行第二轮检索
    """
    if not llm_intermediate_result:
        return initial_results
    
    # 从中间结果中提取新的搜索关键词
    # 例如：如果LLM说"需要查找X的信息"，则搜索X
    new_keywords = self._extract_search_keywords(llm_intermediate_result)
    
    if new_keywords:
        # 进行第二轮检索
        additional_query = ' '.join(new_keywords)
        additional_results = await self._perform_knowledge_retrieval(additional_query)
        
        # 合并结果（去重）
        combined = initial_results + additional_results
        # 去重（基于content hash）
        seen = set()
        unique_results = []
        for r in combined:
            content_hash = hash(r.get('content', ''))
            if content_hash not in seen:
                seen.add(content_hash)
                unique_results.append(r)
        
        return unique_results
    
    return initial_results
```

**实施位置**: `src/core/real_reasoning_engine.py`

---

### 方案5: 递归检索 ⭐ (低优先级，可选)

**目标**: LLM先生成搜索关键词，再进行精准检索

```python
async def _recursive_retrieval(
    self,
    query: str,
    max_iterations: int = 2
) -> List[Dict]:
    """
    递归检索：LLM生成搜索关键词，再进行检索
    """
    current_query = query
    all_results = []
    
    for iteration in range(max_iterations):
        # 第一轮：使用原始查询
        if iteration == 0:
            results = await self._perform_knowledge_retrieval(current_query)
        else:
            # 后续轮次：使用LLM生成的关键词
            keywords = await self._generate_search_keywords(current_query, all_results)
            if not keywords:
                break
            current_query = ' '.join(keywords)
            results = await self._perform_knowledge_retrieval(current_query)
        
        all_results.extend(results)
        
        # 如果结果足够，提前结束
        if len(all_results) >= 10:
            break
    
    # 去重和排序
    return self._deduplicate_and_sort(all_results)
```

**实施位置**: `src/agents/enhanced_knowledge_retrieval_agent.py`

---

### 方案6: 缓存机制 ⭐⭐ (中优先级)

**目标**: 对常见查询结果进行缓存

```python
class RetrievalCache:
    """检索结果缓存"""
    
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        self.cache: Dict[str, Tuple[List[Dict], float]] = {}
        self.max_size = max_size
        self.ttl = ttl  # 缓存有效期（秒）
    
    def get(self, query: str) -> Optional[List[Dict]]:
        """获取缓存结果"""
        cache_key = self._generate_key(query)
        if cache_key in self.cache:
            results, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.ttl:
                return results
            else:
                # 过期，删除
                del self.cache[cache_key]
        return None
    
    def set(self, query: str, results: List[Dict]):
        """设置缓存"""
        cache_key = self._generate_key(query)
        
        # 如果缓存已满，删除最旧的
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        self.cache[cache_key] = (results, time.time())
    
    def _generate_key(self, query: str) -> str:
        """生成缓存键（归一化查询）"""
        # 归一化：小写、去除多余空格
        normalized = ' '.join(query.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()
```

**实施位置**: `src/agents/enhanced_knowledge_retrieval_agent.py`

---

## 📋 综合实施策略

### 阶段1: 立即实施（1-2天）⭐⭐⭐

1. **方案1.2 + 方案1.3**: 第二层相关性筛选 + 第三层智能压缩
   - 优先级：最高
   - 预期效果：减少40-60%的证据长度
   - 工作量：中等

2. **方案4.1**: 关键信息优先
   - 优先级：高
   - 预期效果：提高关键信息可见性
   - 工作量：小

### 阶段2: 短期实施（1周内）⭐⭐

3. **方案2**: 智能内容压缩技术
   - 优先级：中
   - 预期效果：进一步减少20-30%长度
   - 工作量：中等

4. **方案3**: 智能相关性筛选
   - 优先级：中
   - 预期效果：提高检索精度
   - 工作量：小

5. **方案6**: 缓存机制
   - 优先级：中
   - 预期效果：提高性能
   - 工作量：小

### 阶段3: 长期优化（可选）⭐

6. **方案4.2 + 4.3**: 分块处理 + 增量检索
   - 优先级：低
   - 预期效果：处理复杂查询
   - 工作量：大

7. **方案5**: 递归检索
   - 优先级：低
   - 预期效果：提高检索精度
   - 工作量：大

---

## 🎯 预期效果

### 优化前
- 检索结果：15个片段，~10,000字符
- 提示词总长度：~17,000字符（~4,250 tokens）

### 优化后（实施阶段1+2）
- 检索结果：3-5个关键片段，~2,000-3,000字符
- 提示词总长度：~10,000字符（~2,500 tokens）
- **减少：40-60%**

### 优化后（实施全部方案）
- 检索结果：3-5个压缩片段，~1,500-2,000字符
- 提示词总长度：~9,000字符（~2,250 tokens）
- **减少：50-70%**

---

## 📝 实施建议

### 建议1: 优先实施方案1.2 + 1.3 + 4.1

**理由**:
- 效果最明显（减少40-60%）
- 实施相对简单
- 不影响现有功能

### 建议2: 结合之前的智能分层证据处理

**整合方案**:
1. **检索阶段**: 使用分层检索 + 智能压缩（方案1+2）
2. **提示词阶段**: 使用智能分层证据处理（之前方案）
3. **双重保障**: 即使检索阶段压缩不够，提示词阶段还会再次处理

### 建议3: 添加配置选项

```python
RAG_OPTIMIZATION_LEVEL = os.getenv('RAG_OPTIMIZATION_LEVEL', 'balanced')
# 'minimal': 最小压缩（保留更多信息）
# 'balanced': 平衡压缩（推荐）
# 'aggressive': 激进压缩（最大化减少长度）
```

---

## ⚠️ 注意事项

1. **信息丢失风险**: 压缩可能丢失关键信息，需要智能提取
2. **准确性平衡**: 在减少长度和保持准确性之间找到平衡
3. **查询类型适配**: 不同查询类型需要不同的压缩策略
4. **性能影响**: 压缩处理会增加少量计算开销

---

## 📊 对比分析

| 方案 | 当前状态 | 实施难度 | 预期效果 | 优先级 |
|------|---------|---------|---------|--------|
| 分层检索 | ⚠️ 部分 | 中 | 高 | ⭐⭐⭐ |
| 智能压缩 | ❌ 无 | 中 | 高 | ⭐⭐⭐ |
| 相关性筛选 | ⚠️ 基础 | 低 | 中 | ⭐⭐ |
| 上下文优化 | ⚠️ 基础 | 中 | 高 | ⭐⭐⭐ |
| 递归检索 | ❌ 无 | 高 | 中 | ⭐ |
| 缓存机制 | ❌ 无 | 低 | 中 | ⭐⭐ |

---

## 🎯 总结

用户提供的RAG优化方案**非常有价值**，与当前系统高度契合：

1. **分层检索策略** → 可以显著减少检索结果数量
2. **智能内容压缩** → 可以大幅减少证据长度
3. **相关性筛选** → 可以提高检索精度
4. **上下文优化** → 可以更好地利用模型限制

**推荐实施顺序**:
1. 立即实施：分层检索 + 智能压缩 + 关键信息优先
2. 短期实施：相关性筛选 + 缓存机制
3. 长期优化：递归检索 + 增量检索

**预期综合效果**:
- 提示词长度减少：**50-70%**
- 准确性保持：**90%+**
- 性能提升：**显著**

---

*分析时间: 2025-11-13*

