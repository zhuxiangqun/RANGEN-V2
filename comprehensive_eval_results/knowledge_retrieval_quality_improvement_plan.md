# 知识检索质量改进计划

**制定时间**: 2025-11-09  
**优先级**: P0（最高优先级）  
**核心目标**: 改进知识检索质量，避免进入fallback

---

## 🎯 核心问题

### 问题表现
从日志分析：
- **答案与证据匹配度为0.00** → 说明检索到的证据完全不相关
- **所有结果都被过滤** → 说明检索到的结果质量差
- **进入fallback** → 说明核心功能失败

### 根本原因
1. **检索到的证据不相关** → LLM无法从证据中得出正确答案
2. **检索数量不足** → 可能遗漏了相关证据
3. **查询理解不准确** → 检索查询可能没有准确表达用户意图

---

## 🚀 改进方案

### 改进1：增强查询理解（P0）

**问题**：
- 用户查询可能包含隐含信息
- 直接使用原始查询检索可能不够准确

**解决方案**：
```python
def _enhance_query_for_retrieval(self, query: str) -> str:
    """增强查询以提高检索准确性"""
    # 1. 使用LLM扩展查询（添加同义词、相关概念）
    # 2. 提取关键实体和关系
    # 3. 生成多个检索查询变体
    # 4. 合并检索结果
```

**实现步骤**：
1. 使用LLM分析查询，提取关键信息
2. 生成查询扩展（同义词、相关概念）
3. 使用多个查询变体检索
4. 合并和去重结果

---

### 改进2：改进检索策略（P0）

**问题**：
- 当前只使用单一检索方法
- 可能遗漏相关证据

**解决方案**：
```python
async def _multi_strategy_retrieval(self, query: str) -> List[Dict]:
    """多策略检索"""
    results = []
    
    # 策略1: 向量检索（语义相似度）
    vector_results = await self._vector_retrieval(query)
    results.extend(vector_results)
    
    # 策略2: 关键词检索（精确匹配）
    keyword_results = await self._keyword_retrieval(query)
    results.extend(keyword_results)
    
    # 策略3: 实体检索（基于实体匹配）
    entity_results = await self._entity_retrieval(query)
    results.extend(entity_results)
    
    # 策略4: 知识图谱检索（基于关系）
    graph_results = await self._graph_retrieval(query)
    results.extend(graph_results)
    
    # 合并、去重、排序
    return self._merge_and_rank_results(results, query)
```

---

### 改进3：改进LLM相关性判断（P0）

**问题**：
- 当前LLM相关性判断可能不够准确
- 可能误判相关结果为不相关

**解决方案**：
```python
def _validate_result_with_llm_enhanced(self, result: Dict, query: str) -> Optional[bool]:
    """增强的LLM相关性判断"""
    # 1. 使用更详细的提示词
    # 2. 要求LLM提供置信度分数
    # 3. 对于边界情况，使用多个LLM判断并投票
    # 4. 记录判断原因，便于调试
```

**改进点**：
1. 更详细的提示词，包含查询上下文
2. 要求LLM提供置信度分数（0.0-1.0）
3. 对于低置信度结果，使用多个LLM判断
4. 记录判断原因，便于分析和改进

---

### 改进4：如果检索结果不相关，重新检索（P0）

**问题**：
- 当前如果检索结果不相关，直接进入fallback
- 应该尝试重新检索，而不是进入fallback

**解决方案**：
```python
async def _retrieve_with_retry(self, query: str, max_retries: int = 2) -> List[Dict]:
    """带重试的检索"""
    for attempt in range(max_retries):
        results = await self._perform_retrieval(query)
        
        # 检查结果相关性
        relevant_count = sum(1 for r in results if self._is_relevant(r, query))
        
        if relevant_count >= 3:  # 至少3个相关结果
            return results
        
        # 如果结果不相关，尝试改进查询
        if attempt < max_retries - 1:
            query = await self._improve_query(query, results)
            logger.info(f"检索结果不相关，改进查询后重试: {query[:100]}")
    
    # 如果重试后仍然不相关，返回结果（让LLM判断）
    return results
```

---

### 改进5：增加检索数量（P1）

**问题**：
- 当前top_k可能太小，遗漏相关证据

**解决方案**：
```python
# 当前：enhanced_top_k = max(top_k_for_search * 3, 15)
# 改进：根据查询复杂度动态调整
def _get_dynamic_top_k(self, query: str, query_type: str) -> int:
    """动态确定top_k"""
    base_top_k = 15
    
    # 复杂查询需要更多结果
    if query_type in ['complex', 'multi_hop', 'reasoning']:
        return base_top_k * 2  # 30
    
    # 简单查询可以减少结果
    if query_type in ['factual', 'definition']:
        return base_top_k  # 15
    
    return base_top_k * 1.5  # 22-23
```

---

## 📋 实施优先级

### P0（立即实施）

1. **改进LLM相关性判断**
   - 使用更详细的提示词
   - 要求LLM提供置信度分数
   - 记录判断原因

2. **如果检索结果不相关，重新检索**
   - 检查结果相关性
   - 如果相关性低，改进查询后重试
   - 避免直接进入fallback

3. **增强查询理解**
   - 使用LLM扩展查询
   - 生成多个查询变体
   - 合并检索结果

### P1（短期实施）

1. **多策略检索**
   - 向量检索 + 关键词检索 + 实体检索 + 知识图谱检索
   - 合并和排序结果

2. **动态调整top_k**
   - 根据查询复杂度调整
   - 根据查询类型调整

### P2（长期优化）

1. **检索结果缓存**
   - 缓存常见查询的检索结果
   - 减少重复检索

2. **检索质量监控**
   - 记录检索质量指标
   - 分析检索失败原因
   - 持续改进检索策略

---

## 🎯 预期效果

### 改进前
- 检索结果相关性：30-40%
- Fallback触发率：50%
- 答案准确性：20-30%

### 改进后（预期）
- 检索结果相关性：70-80%
- Fallback触发率：<10%
- 答案准确性：60-70%

---

## 📝 下一步行动

1. **立即实施（P0）**：
   - 改进LLM相关性判断
   - 实现检索重试机制
   - 增强查询理解

2. **短期实施（P1）**：
   - 实现多策略检索
   - 动态调整top_k

3. **长期优化（P2）**：
   - 检索结果缓存
   - 检索质量监控

---

*本计划基于2025-11-09的fallback根本原因分析制定*

