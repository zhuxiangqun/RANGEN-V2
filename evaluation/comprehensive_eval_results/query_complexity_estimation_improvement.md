# 查询复杂度估算改进方案

**分析时间**: 2025-11-09  
**问题**: 硬编码关键词列表判断查询复杂度，扩展性差

---

## 🔍 当前实现的问题

### 问题1：硬编码关键词列表

**位置**: `src/core/llm_integration.py` 第240-252行

**当前实现**:
```python
complexity_keywords = [
    "compare", "analyze", "explain", "why", "how", "relationship",
    "multiple", "several", "various", "different", "calculate",
    "step", "process", "method", "approach", "strategy"
]
has_complexity_keywords = any(keyword in prompt.lower() for keyword in complexity_keywords)

has_multi_step = any(indicator in prompt.lower() for indicator in [
    "step 1", "step 2", "first", "then", "next", "finally",
    "reasoning process", "logical deduction", "inference"
])
```

**问题**:
1. **扩展性差**：需要手动维护关键词列表，无法适应新的查询类型
2. **准确性低**：简单的字符串匹配可能误判（例如，"how" 可能出现在简单问题中）
3. **无法理解语义**：只能做简单的字符串匹配，无法理解查询的真实复杂度
4. **维护成本高**：每次需要添加新的复杂度特征，都要修改代码

---

## 🚀 改进方案

### 方案1：使用LLM判断查询复杂度（推荐，P0）

**原理**:
- 使用LLM分析查询的语义复杂度
- LLM可以理解查询的真实意图和复杂度
- 不需要维护关键词列表

**实现**:
```python
def _estimate_query_complexity(self, prompt: str) -> str:
    """使用LLM估算查询复杂度"""
    try:
        # 提取查询部分（去除提示词模板内容）
        query = self._extract_query_from_prompt(prompt)
        
        # 使用LLM判断复杂度
        if self.fast_llm_integration:  # 使用快速模型
            complexity_prompt = f"""Analyze the complexity of the following query and return ONLY one word: "simple", "medium", or "complex".

Complexity criteria:
- simple: Short, single-fact questions (e.g., "What is the capital of France?")
- medium: Questions requiring some reasoning or multiple facts (e.g., "How many people live in Tokyo?")
- complex: Long queries, multi-step reasoning, complex logic (e.g., "Compare the economic policies of USA and China and explain their impact")

Query: {query}

Complexity:"""
            
            response = self.fast_llm_integration._call_llm(complexity_prompt)
            complexity = response.strip().lower()
            
            if complexity in ["simple", "medium", "complex"]:
                return complexity
            else:
                # 如果LLM返回了其他内容，尝试提取
                if "simple" in complexity:
                    return "simple"
                elif "complex" in complexity:
                    return "complex"
                else:
                    return "medium"
        else:
            # Fallback: 使用简单启发式
            return self._estimate_query_complexity_fallback(prompt)
    except Exception as e:
        self.logger.debug(f"LLM估算查询复杂度失败: {e}，使用fallback")
        return self._estimate_query_complexity_fallback(prompt)
```

**优点**:
- ✅ 智能：LLM可以理解语义，准确判断复杂度
- ✅ 可扩展：不需要维护关键词列表
- ✅ 准确：基于语义理解，而非简单字符串匹配

**缺点**:
- ⚠️ 需要额外的LLM调用（但可以使用快速模型，成本低）
- ⚠️ 如果LLM不可用，需要fallback

---

### 方案2：特征提取 + 机器学习（可选，P1）

**原理**:
- 提取查询的特征（长度、词数、句数、实体数等）
- 使用简单的规则或机器学习模型判断复杂度

**实现**:
```python
def _estimate_query_complexity(self, prompt: str) -> str:
    """使用特征提取估算查询复杂度"""
    try:
        query = self._extract_query_from_prompt(prompt)
        
        # 提取特征
        features = {
            'length': len(query),
            'word_count': len(query.split()),
            'sentence_count': len([s for s in query.split('.') if s.strip()]),
            'question_words': sum(1 for w in ['what', 'who', 'where', 'when', 'why', 'how'] if w in query.lower()),
            'complex_indicators': sum(1 for w in ['compare', 'analyze', 'explain', 'relationship'] if w in query.lower())
        }
        
        # 简单规则判断
        if features['length'] < 50 and features['word_count'] < 10 and features['question_words'] <= 1:
            return "simple"
        elif features['length'] > 200 or features['word_count'] > 30 or features['complex_indicators'] >= 2:
            return "complex"
        else:
            return "medium"
    except Exception as e:
        self.logger.debug(f"特征提取估算查询复杂度失败: {e}")
        return "medium"
```

**优点**:
- ✅ 不需要LLM调用
- ✅ 比硬编码关键词更灵活

**缺点**:
- ⚠️ 仍然需要维护特征提取规则
- ⚠️ 准确性不如LLM

---

### 方案3：混合方案（推荐，P0）

**原理**:
- 优先使用LLM判断（智能、准确）
- 如果LLM不可用或失败，使用改进的特征提取方法（fallback）

**实现**:
```python
def _estimate_query_complexity(self, prompt: str) -> str:
    """估算查询复杂度（混合方案：LLM优先，特征提取fallback）"""
    try:
        query = self._extract_query_from_prompt(prompt)
        
        # 🚀 策略1: 使用LLM判断（优先，智能且可扩展）
        if self.fast_llm_integration:
            try:
                complexity = self._estimate_query_complexity_with_llm(query)
                if complexity:
                    return complexity
            except Exception as e:
                self.logger.debug(f"LLM估算查询复杂度失败: {e}，使用fallback")
        
        # 🚀 策略2: 使用改进的特征提取方法（fallback）
        return self._estimate_query_complexity_with_features(query)
        
    except Exception as e:
        self.logger.debug(f"估算查询复杂度失败: {e}，使用默认值（medium）")
        return "medium"
    
def _estimate_query_complexity_with_llm(self, query: str) -> Optional[str]:
    """使用LLM判断查询复杂度"""
    try:
        complexity_prompt = f"""Analyze the complexity of the following query and return ONLY one word: "simple", "medium", or "complex".

Complexity criteria:
- simple: Short, single-fact questions
- medium: Questions requiring some reasoning
- complex: Long queries, multi-step reasoning, complex logic

Query: {query}

Complexity:"""
        
        response = self.fast_llm_integration._call_llm(complexity_prompt)
        complexity = response.strip().lower()
        
        if complexity in ["simple", "medium", "complex"]:
            return complexity
        else:
            # 尝试提取
            if "simple" in complexity:
                return "simple"
            elif "complex" in complexity:
                return "complex"
            else:
                return "medium"
    except Exception as e:
        self.logger.debug(f"LLM判断查询复杂度失败: {e}")
        return None
    
def _estimate_query_complexity_with_features(self, query: str) -> str:
    """使用特征提取判断查询复杂度（fallback）"""
    try:
        features = {
            'length': len(query),
            'word_count': len(query.split()),
            'sentence_count': len([s for s in query.split('.') if s.strip()]),
            'question_words': sum(1 for w in ['what', 'who', 'where', 'when', 'why', 'how'] if w in query.lower()),
        }
        
        # 改进的规则判断（不使用硬编码关键词列表）
        if features['length'] < 50 and features['word_count'] < 10 and features['question_words'] <= 1:
            return "simple"
        elif features['length'] > 200 or features['word_count'] > 30:
            return "complex"
        else:
            return "medium"
    except Exception as e:
        self.logger.debug(f"特征提取判断查询复杂度失败: {e}")
        return "medium"
```

**优点**:
- ✅ 智能：优先使用LLM，准确且可扩展
- ✅ 可靠：有fallback机制，即使LLM失败也能工作
- ✅ 可扩展：不需要维护关键词列表

---

## 📊 改进效果预估

### 改进前

**问题**:
- 硬编码关键词列表，扩展性差
- 简单字符串匹配，准确性低
- 需要手动维护关键词列表

**示例**:
```python
# 可能误判的情况
"how are you?"  # 简单问题，但包含"how"，可能被误判为复杂
"what is the relationship between A and B?"  # 复杂问题，但如果没有关键词，可能被误判为简单
```

---

### 改进后（预期）

**优势**:
- LLM可以理解语义，准确判断复杂度
- 不需要维护关键词列表
- 可以适应新的查询类型

**示例**:
```python
# LLM可以正确判断
"how are you?"  # LLM判断为simple（理解这是问候语）
"what is the relationship between A and B?"  # LLM判断为complex（理解需要分析关系）
```

---

## ✅ 推荐实施方案

### P0（立即实施）：混合方案

1. **优先使用LLM判断**（智能、准确、可扩展）
2. **Fallback使用改进的特征提取**（不使用硬编码关键词列表）

**实施步骤**:
1. 实现 `_estimate_query_complexity_with_llm` 方法
2. 实现 `_estimate_query_complexity_with_features` 方法（改进版，不使用硬编码关键词）
3. 修改 `_estimate_query_complexity` 方法，使用混合方案
4. 添加 `_extract_query_from_prompt` 辅助方法

---

## 📝 设计理念

### 核心原则

1. **智能优先**：使用LLM理解语义，而非简单字符串匹配
2. **可扩展性**：不需要维护硬编码列表
3. **可靠性**：有fallback机制，即使LLM失败也能工作

### 与系统设计理念一致

- ✅ 完全依赖LLM进行智能处理
- ✅ 不使用硬编码规则
- ✅ 保持系统的智能性和扩展性

---

*本分析基于2025-11-09的代码审查和用户反馈生成*

