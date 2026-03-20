# 缓存内容详细分析（2025-11-23）

## 📋 缓存系统概览

系统中有**多种类型的缓存**，分别存储不同类型的内容。缓存的主要目的是**避免重复计算和API调用**，提高系统性能和降低成本。

---

## 🗂️ 缓存类型和内容

### 1. LLM调用结果缓存 (`_llm_cache`)

**存储位置**:
- 内存: `RealReasoningEngine._llm_cache`
- 持久化文件: `data/learning/llm_cache.json`

**缓存内容**:
```json
{
  "c523413e9c3122350fc4053d3e53cd0c": {
    "result": "LLM API的完整响应内容（字符串）",
    "timestamp": 1763571294.669891
  }
}
```

**缓存键生成**:
- 基于 `func_name` + `prompt` 内容的MD5哈希
- 例如: `_get_cache_key("query_analysis", prompt)`

**存储的数据**:
- `result`: LLM API返回的完整响应文本
- `timestamp`: 缓存创建时间戳

**缓存TTL**: 24小时（86400秒）

**使用场景**:
- 缓存LLM API调用结果（如查询分析、推理步骤生成、答案提取等）
- 避免重复调用相同的prompt
- 节省API调用成本和响应时间

**代码位置**: `src/core/real_reasoning_engine.py`

---

### 2. 查询结果缓存 (`query_cache`)

**存储位置**:
- 内存: `UnifiedResearchSystem._cache_system['query_cache']`
- 不持久化（仅在内存中）

**缓存内容**:
```json
{
  "query_hash_md5": {
    "result": {
      "query": "查询内容",
      "success": true,
      "answer": "答案",
      "knowledge": [...],
      "reasoning": "...",
      "citations": [...],
      "confidence": 0.85,
      "metadata": {...}
    },
    "timestamp": 1234567890.123
  }
}
```

**缓存键生成**:
- 基于查询内容的MD5哈希: `hashlib.md5(request.query.encode()).hexdigest()`

**存储的数据**:
- `result`: 完整的 `ResearchResult` 对象（包含答案、知识、推理、引用等）
- `timestamp`: 缓存创建时间戳

**缓存TTL**: 5分钟（300秒）

**使用场景**:
- 缓存完整的查询处理结果
- 当相同的查询再次出现时，直接返回缓存结果
- 避免重复执行整个研究流程

**代码位置**: `src/unified_research_system.py`

---

### 3. 知识检索缓存 (`knowledge_cache`)

**存储位置**:
- 内存: `UnifiedResearchSystem._cache_system['knowledge_cache']`
- 不持久化（仅在内存中）

**缓存内容**:
```json
{
  "knowledge_key_hash": {
    "data": {
      "knowledge_items": [...],
      "retrieval_metadata": {...}
    },
    "timestamp": 1234567890.123
  }
}
```

**存储的数据**:
- `data`: 知识检索结果（知识条目列表、检索元数据等）
- `timestamp`: 缓存创建时间戳

**缓存TTL**: 5分钟（300秒）

**使用场景**:
- 缓存知识库检索结果
- 避免重复检索相同的知识内容
- 提高知识检索速度

**代码位置**: `src/unified_research_system.py`

---

### 4. 推理结果缓存 (`reasoning_cache`)

**存储位置**:
- 内存: `UnifiedResearchSystem._cache_system['reasoning_cache']`
- 不持久化（仅在内存中）

**缓存内容**:
```json
{
  "reasoning_key_hash": {
    "data": {
      "reasoning_steps": [...],
      "reasoning_result": {...}
    },
    "timestamp": 1234567890.123
  }
}
```

**存储的数据**:
- `data`: 推理过程和结果（推理步骤、推理结果等）
- `timestamp`: 缓存创建时间戳

**缓存TTL**: 5分钟（300秒）

**使用场景**:
- 缓存推理过程和结果
- 避免重复执行相同的推理任务
- 提高推理效率

**代码位置**: `src/unified_research_system.py`

---

### 5. NLP处理结果缓存 (`_nlp_cache`)

**存储位置**:
- 内存: `RealReasoningEngine._nlp_cache`
- 不持久化（仅在内存中）

**缓存内容**:
```json
{
  "nlp_key_hash": {
    "data": {
      "summary": "摘要内容",
      "keywords": ["关键词1", "关键词2"],
      "entities": [...],
      ...
    },
    "timestamp": 1234567890.123
  }
}
```

**存储的数据**:
- `data`: NLP处理结果（摘要、关键词、实体等）
- `timestamp`: 缓存创建时间戳

**缓存TTL**: 30分钟（1800秒）

**使用场景**:
- 缓存NLP处理结果（摘要生成、关键词提取等）
- 避免重复处理相同的文本
- 提高NLP处理速度

**代码位置**: `src/core/real_reasoning_engine.py`

---

### 6. 语义相似度缓存 (`_semantic_similarity_cache`)

**存储位置**:
- 内存: `RealReasoningEngine._semantic_similarity_cache`
- 不持久化（仅在内存中）

**缓存内容**:
```json
{
  "similarity_key_hash": {
    "data": 0.85,  // 相似度分数（0-1之间）
    "timestamp": 1234567890.123
  }
}
```

**存储的数据**:
- `data`: 语义相似度分数（浮点数，0-1之间）
- `timestamp`: 缓存创建时间戳

**缓存TTL**: 1小时（3600秒）

**使用场景**:
- 缓存文本之间的语义相似度计算结果
- 避免重复计算相同的文本对相似度
- 提高相似度计算速度

**代码位置**: `src/core/real_reasoning_engine.py`

---

### 7. 知识检索结果缓存 (`_knowledge_retrieval_cache`)

**存储位置**:
- 内存: `RealReasoningEngine._knowledge_retrieval_cache`
- 不持久化（仅在内存中）

**缓存内容**:
```json
{
  "retrieval_key_hash": {
    "data": {
      "knowledge_items": [...],
      "retrieval_metadata": {...}
    },
    "timestamp": 1234567890.123
  }
}
```

**存储的数据**:
- `data`: 知识检索结果（知识条目列表、检索元数据等）
- `timestamp`: 缓存创建时间戳

**缓存TTL**: 30分钟（1800秒）

**使用场景**:
- 缓存知识检索结果
- 避免重复检索相同的知识内容
- 提高知识检索速度

**代码位置**: `src/core/real_reasoning_engine.py`

---

### 8. 验证结果缓存 (`_validation_cache`)

**存储位置**:
- 内存: `RealReasoningEngine._validation_cache`
- 不持久化（仅在内存中）

**缓存内容**:
```json
{
  "validation_key": {
    "data": {
      "is_valid": true,
      "confidence": 0.85,
      "reasons": [...],
      "verification_result": {...}
    },
    "timestamp": 1234567890.123
  }
}
```

**缓存键生成**:
- 基于答案、查询类型、查询内容: `f"{answer}_{query_type}_{query[:50]}"`

**存储的数据**:
- `data`: 答案验证结果（是否有效、置信度、原因等）
- `timestamp`: 缓存创建时间戳

**缓存TTL**: 30分钟（1800秒）

**使用场景**:
- 缓存答案验证结果
- 避免重复验证相同的答案
- 提高验证速度

**代码位置**: `src/core/real_reasoning_engine.py`

---

### 9. Embedding向量缓存 (`_embedding_cache`)

**存储位置**:
- 内存: `VectorKnowledgeBase._embedding_cache`
- 持久化文件: `data/learning/embedding_cache.json` 或 `data/learning/kms_embedding_cache.json`

**缓存内容**:
```json
{
  "2d032b4479925b496535faf69fc43b6c": {
    "embedding": [0.123, 0.456, ...],  // 768维向量
    "timestamp": 1763598210.1307058,
    "text_preview": "文本预览（用于调试）",
    "model": "jina-embeddings-v2-base-en"  // 或 "all-mpnet-base-v2"
  }
}
```

**缓存键生成**:
- 基于文本内容的MD5哈希: `hashlib.md5(text.encode('utf-8')).hexdigest()`

**存储的数据**:
- `embedding`: 文本的embedding向量（768维浮点数数组）
- `timestamp`: 缓存创建时间戳
- `text_preview`: 文本预览（用于调试）
- `model`: 使用的embedding模型名称

**缓存TTL**: 24小时（86400秒）

**使用场景**:
- 缓存文本的embedding向量
- 避免重复调用Jina API或本地模型生成embedding
- 特别适用于知识检索中的向量相似度计算
- 节省API调用成本和计算时间

**代码位置**: `src/knowledge/vector_database.py`

---

### 10. 智能过滤中心相似度缓存 (`_similarity_cache`)

**存储位置**:
- 内存: `IntelligentFilterCenter._similarity_cache`
- 不持久化（仅在内存中）

**缓存内容**:
```json
{
  "text_rule_name": 0.85  // 相似度分数（0-1之间）
}
```

**存储的数据**:
- 键: `f"{text}_{rule.name}"`
- 值: 语义相似度分数（浮点数，0-1之间）

**缓存TTL**: 无（仅在内存中，程序退出后清除）

**使用场景**:
- 缓存文本与过滤规则的语义相似度计算结果
- 避免重复计算相同的文本-规则对相似度
- 提高过滤速度

**代码位置**: `src/core/intelligent_filter_center.py`

---

### 11. 知识检索Agent查询缓存 (`query_cache`)

**存储位置**:
- 内存: `EnhancedKnowledgeRetrievalAgent.query_cache`
- 不持久化（仅在内存中）

**缓存内容**:
```json
{
  "normalized_query": {
    "knowledge_items": [...],
    "timestamp": 1234567890.123,
    ...
  }
}
```

**存储的数据**:
- 键: 规范化后的查询字符串
- 值: 知识检索结果（知识条目列表、时间戳等）

**缓存TTL**: 无固定TTL（使用LRU策略，缓存满时删除最旧条目）

**使用场景**:
- 缓存知识检索Agent的查询结果
- 避免重复检索相同的查询
- 提高知识检索速度

**代码位置**: `src/agents/enhanced_knowledge_retrieval_agent.py`

---

## 📊 缓存统计信息

### 缓存大小限制

| 缓存类型 | 最大条目数 | 当前状态 |
|---------|-----------|---------|
| LLM缓存 | 100 | 可配置 |
| 查询缓存 | 1000 | 可配置 |
| 知识缓存 | 1000 | 可配置 |
| 推理缓存 | 1000 | 可配置 |
| NLP缓存 | 无限制 | LRU策略 |
| 语义相似度缓存 | 无限制 | LRU策略 |
| 知识检索缓存 | 无限制 | LRU策略 |
| 验证缓存 | 无限制 | LRU策略 |
| Embedding缓存 | 无限制 | 持久化到文件 |

### 缓存命中率统计

**当前状态**（来自评测报告）:
- 缓存命中率: **0.0%** ⚠️
- 缓存命中次数: 0
- 缓存未命中次数: 未知

**可能原因**:
1. 查询内容差异大，没有重复查询
2. 缓存TTL过短（5分钟），缓存已过期
3. 缓存机制未正常工作
4. 缓存键生成方式导致无法命中

---

## 🔍 缓存键生成方式总结

### 1. LLM缓存键
```python
# 基于 func_name + prompt 的MD5哈希
cache_key = hashlib.md5(f"{func_name}_{prompt}".encode()).hexdigest()
```

### 2. 查询缓存键
```python
# 基于查询内容的MD5哈希
cache_key = hashlib.md5(query.encode()).hexdigest()
```

### 3. Embedding缓存键
```python
# 基于文本内容的MD5哈希
cache_key = hashlib.md5(text.encode('utf-8')).hexdigest()
```

### 4. 验证缓存键
```python
# 基于答案、查询类型、查询内容
cache_key = f"{answer}_{query_type}_{query[:50]}"
```

### 5. 知识检索缓存键
```python
# 基于规范化后的查询字符串
cache_key = normalized_query
```

---

## 💡 缓存使用建议

### 1. 提高缓存命中率

**问题**: 当前缓存命中率为0%

**建议**:
1. **检查缓存配置**: 确认缓存TTL和大小限制是否合理
2. **优化缓存键生成**: 确保相同内容的查询生成相同的缓存键
3. **延长缓存TTL**: 对于不经常变化的内容，可以延长TTL
4. **增加缓存大小**: 如果内存允许，可以增加缓存大小限制

### 2. 缓存清理策略

**当前策略**:
- 基于TTL自动清理过期缓存
- 基于LRU策略清理最旧条目（当缓存满时）
- 批次结束时清理缓存（`_cleanup_caches`）

**建议**:
- 定期清理过期缓存（每N个样本）
- 监控缓存使用情况，避免内存泄漏
- 在系统关闭时保存持久化缓存

### 3. 缓存持久化

**当前状态**:
- ✅ LLM缓存: 持久化到 `data/learning/llm_cache.json`
- ✅ Embedding缓存: 持久化到 `data/learning/embedding_cache.json` 或 `data/learning/kms_embedding_cache.json`
- ❌ 其他缓存: 仅在内存中，不持久化

**建议**:
- 考虑持久化查询缓存（如果查询会重复）
- 考虑持久化知识检索缓存（如果知识库不经常变化）
- 定期备份持久化缓存文件

---

## 🎯 总结

### 缓存存储的主要内容

1. **LLM API调用结果** - 避免重复调用API
2. **查询处理结果** - 避免重复处理相同查询
3. **知识检索结果** - 避免重复检索知识
4. **推理过程和结果** - 避免重复推理
5. **NLP处理结果** - 避免重复处理文本
6. **语义相似度计算结果** - 避免重复计算相似度
7. **答案验证结果** - 避免重复验证答案
8. **Embedding向量** - 避免重复生成向量

### 缓存的作用

1. **提高性能**: 避免重复计算和API调用
2. **降低成本**: 减少API调用次数
3. **提高响应速度**: 直接从缓存获取结果
4. **减少资源消耗**: 减少CPU、内存、网络使用

### 当前问题

1. **缓存命中率为0%** - 需要检查缓存机制
2. **部分缓存不持久化** - 重启后丢失
3. **缓存TTL可能过短** - 导致缓存过早过期

---

**分析完成时间**: 2025-11-23  
**数据来源**: 代码分析和评测报告  
**状态**: ✅ 完成

