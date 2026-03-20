# 准确率和置信度计算机制详细分析（2025-11-23）

## 📋 概览

本文档详细分析核心系统中**准确率**和**答案置信度**的计算机制。

---

## 1. 准确率计算机制

### 1.1 计算位置

**代码位置**: `evaluation_system/analyzers/frames_analyzer.py`

**主要方法**: `_calculate_real_accuracy()`

### 1.2 计算流程

```python
def _calculate_real_accuracy(expected_answers: List[str], actual_answers: List[str]) -> Dict[str, Any]:
    """计算真正的准确率 - 增强版，支持智能匹配和动态阈值调整"""
    
    # 1. 获取相似度阈值（动态调整）
    similarity_threshold = threshold_manager.get_dynamic_threshold(
        'similarity',
        context=context,
        default_value=0.3  # 默认值0.3
    )
    
    # 2. 比较每个答案
    for i in range(total_comparisons):
        expected = expected_answers[i].lower().strip()
        actual = actual_answers[i].lower().strip()
        
        # 3. 智能匹配检查
        match_result = self._intelligent_match(expected, actual)
        
        if match_result["exact_match"]:
            exact_matches += 1
        elif match_result["similarity"] > similarity_threshold:
            similarity_matches += 1
    
    # 4. 计算准确率
    correct_count = exact_matches + similarity_matches
    accuracy = correct_count / total_comparisons if total_comparisons > 0 else 0.0
```

### 1.3 计算公式

```
准确率 = (精确匹配数 + 相似度匹配数) / 总比较数

其中：
- 精确匹配数：完全匹配的答案数量
- 相似度匹配数：相似度超过阈值的答案数量
- 总比较数：min(len(expected_answers), len(actual_answers))
```

### 1.4 智能匹配算法 (`_intelligent_match`)

**匹配策略**（按优先级顺序）：

#### 1. 完全相等匹配
```python
expected_normalized = self._normalize_answer(expected)
actual_normalized = self._normalize_answer(actual)
if expected_normalized == actual_normalized:
    return {"exact_match": True, "similarity": 1.0, "method": "exact_equal"}
```

**规范化处理**:
- 转换为小写
- 去除多余空格
- 去除标点符号（部分）

#### 2. 数字精确匹配
```python
# 如果期望答案是数字，优先进行数字匹配
if expected_is_digit:
    actual_numbers = re.findall(r'\d+', actual_normalized)
    if expected_number in actual_numbers:
        return {"exact_match": True, "similarity": 1.0, "method": "number_exact_match"}
```

**特点**:
- 数字必须完全匹配，不允许部分匹配
- 避免"2" in "12 people"的误判

#### 3. 直接包含匹配
```python
if expected_normalized in actual_normalized:
    return {"exact_match": True, "similarity": 1.0, "method": "direct_contain"}
```

**示例**:
- 期望: "Paris"
- 实际: "The answer is Paris"
- 结果: ✅ 匹配

#### 4. 反向包含匹配
```python
if actual_normalized in expected_normalized:
    return {"exact_match": True, "similarity": 1.0, "method": "reverse_contain"}
```

**示例**:
- 期望: "The answer is Paris"
- 实际: "Paris"
- 结果: ✅ 匹配

#### 5. 核心答案提取匹配
```python
core_actual = self._extract_core_answer(actual)
if core_actual and expected in core_actual:
    return {"exact_match": True, "similarity": 1.0, "method": "core_answer_match"}
```

**特点**:
- 提取答案的核心部分（去除前缀、后缀等）
- 例如: "答案是：Paris" → "Paris"

#### 6. 句子匹配
```python
sentence_match = self._check_sentence_match(expected, actual)
if sentence_match["found"]:
    return {"exact_match": True, "similarity": sentence_match["score"], "method": "sentence_match"}
```

**特点**:
- 检查期望答案是否在句子的某个位置
- 考虑句子结构

#### 7. 关键词匹配
```python
keyword_match_score = self._calculate_keyword_similarity(expected_keywords, actual_keywords)
if keyword_match_score > 0.6:
    return {"exact_match": True, "similarity": keyword_match_score, "method": "keyword_match"}
```

**特点**:
- 提取关键词并计算相似度
- 阈值: 0.6

#### 8. 同义词匹配
```python
synonym_score = self._calculate_synonym_similarity(expected, actual)
if synonym_score > 0.7:
    return {"exact_match": True, "similarity": synonym_score, "method": "synonym_match"}
```

**特点**:
- 使用同义词库进行匹配
- 阈值: 0.7

#### 9. 部分匹配
```python
partial_score = self._calculate_partial_match(expected, actual)
if partial_score > 0.5:
    return {"exact_match": True, "similarity": partial_score, "method": "partial_match"}
```

**特点**:
- 计算部分匹配分数
- 阈值: 0.5

#### 10. 数字匹配
```python
number_score = self._calculate_number_match(expected, actual)
if number_score > 0.7:
    return {"exact_match": True, "similarity": number_score, "method": "number_match"}
```

**特点**:
- 专门处理数字匹配
- 阈值: 0.7

#### 11. 缩写匹配
```python
abbreviation_score = self._calculate_abbreviation_match(expected, actual)
if abbreviation_score > 0.8:
    return {"exact_match": True, "similarity": abbreviation_score, "method": "abbreviation_match"}
```

**特点**:
- 处理缩写形式
- 阈值: 0.8

#### 12. 数字提取匹配
```python
number_match = self._calculate_number_extraction_match(expected, actual)
if number_match > 0.7:
    return {"exact_match": True, "similarity": number_match, "method": "number_extraction_match"}
```

**特点**:
- 从文本中提取数字并匹配
- 阈值: 0.7

#### 13. 部分词匹配
```python
partial_word_match = self._calculate_partial_word_match(expected, actual)
if partial_word_match > 0.6:
    return {"exact_match": True, "similarity": partial_word_match, "method": "partial_word_match"}
```

**特点**:
- 部分词匹配
- 阈值: 0.6

#### 14. 语义相似度匹配
```python
semantic_match = self._calculate_semantic_similarity(expected, actual)
if semantic_match > 0.35:  # 从0.4降低到0.35
    return {"exact_match": True, "similarity": semantic_match, "method": "semantic_match"}
```

**特点**:
- 使用embedding向量计算语义相似度
- 阈值: 0.35（已优化，从0.4降低）

#### 15. 一般相似度（fallback）
```python
general_similarity = self._calculate_similarity(expected, actual)
return {
    "exact_match": False, 
    "similarity": general_similarity, 
    "method": "general_similarity"
}
```

**特点**:
- 使用Jaccard相似度或其他通用相似度算法
- 作为最后的fallback

### 1.5 动态阈值调整

**阈值管理器**: `UnifiedThresholdManager`

**调整因素**:
1. **Embedding模型类型**:
   - 本地模型: 默认阈值 0.25
   - Jina API: 默认阈值 0.3

2. **查询类型**:
   - 数值查询: 可能使用更严格的阈值
   - 事实查询: 可能使用更宽松的阈值

3. **历史表现**:
   - 根据历史准确率调整阈值

### 1.6 准确率计算示例

**示例1**: 完全匹配
- 期望: "Paris"
- 实际: "Paris"
- 匹配方法: `exact_equal`
- 结果: ✅ 精确匹配

**示例2**: 包含匹配
- 期望: "Paris"
- 实际: "The answer is Paris"
- 匹配方法: `direct_contain`
- 结果: ✅ 精确匹配

**示例3**: 数字匹配
- 期望: "87"
- 实际: "100"
- 匹配方法: `number_exact_match`
- 结果: ❌ 不匹配（数字不同）

**示例4**: 语义相似
- 期望: "The capital of France"
- 实际: "Paris"
- 匹配方法: `semantic_match`
- 相似度: 0.85
- 结果: ✅ 相似度匹配（如果阈值 < 0.85）

---

## 2. 答案置信度计算机制

### 2.1 计算位置

**代码位置**: `src/core/real_reasoning_engine.py`

**主要方法**: `_calculate_confidence_intelligently()`

### 2.2 计算流程

```python
def _calculate_confidence_intelligently(
    answer: str, 
    query: str, 
    evidence: List[Dict[str, Any]], 
    query_type: str
) -> Dict[str, Any]:
    """多维度智能置信度计算"""
    
    # 1. 综合LLM评估（合并两个评估为一个调用）
    comprehensive_result = self._calculate_confidence_comprehensively_with_llm(
        answer, query, evidence
    )
    semantic_correctness = comprehensive_result.get('semantic_correctness', 0.5)
    evidence_support = comprehensive_result.get('evidence_support', 0.0)
    
    # 2. 计算各维度分数
    confidence = 0.0
    confidence += semantic_correctness * 0.4      # 语义正确性（40%）
    confidence += evidence_support * 0.3          # 证据支持度（30%）
    confidence += completeness * 0.2              # 答案完整性（20%）
    confidence += type_match * 0.1                # 答案类型匹配（10%）
    
    # 3. 确保置信度在0-1范围内
    confidence = max(0.0, min(1.0, confidence))
```

### 2.3 计算公式

```
总置信度 = 语义正确性 × 40% + 证据支持度 × 30% + 答案完整性 × 20% + 答案类型匹配 × 10%

其中：
- 语义正确性: 0.0-1.0（使用LLM评估）
- 证据支持度: 0.0-1.0（使用LLM评估）
- 答案完整性: 0.0-1.0（基于长度、格式等）
- 答案类型匹配: 0.0-1.0（基于查询类型）
```

### 2.4 各维度详细说明

#### 维度1: 语义正确性（40%权重）

**计算方法**: `_calculate_confidence_comprehensively_with_llm()`

**评估内容**:
1. **语义上是否合理**: 答案本身是否有意义
2. **是否符合查询要求**: 答案是否回答了查询
3. **格式是否正确**: 答案格式是否合理

**LLM提示词**:
```
判断以下答案是否语义正确（不依赖证据，只判断答案本身是否合理）：

查询：{query}
答案：{answer}

请评估答案是否：
1. 语义上合理（答案本身是否有意义）
2. 符合查询要求（答案是否回答了查询）
3. 格式正确（答案格式是否合理）

返回JSON格式：
{
    "is_semantically_correct": true/false,
    "confidence": 0.0-1.0,
    "reason": "判断理由"
}
```

**特点**:
- ✅ 不依赖证据匹配
- ✅ 只判断答案本身是否合理
- ✅ 使用LLM进行智能评估

#### 维度2: 证据支持度（30%权重）

**计算方法**: `_calculate_confidence_comprehensively_with_llm()`

**评估内容**:
1. **答案是否可以从证据中推理得出**: 即使不在证据中，也可以推理
2. **答案是否与证据语义相关**: 使用语义相似度
3. **证据是否支持答案**: 证据是否支持答案的正确性

**LLM提示词**:
```
判断以下答案是否可以从证据中推理得出（不要求直接匹配，允许推理）：

查询：{query}
答案：{answer}
证据：{evidence_text}

请评估：
1. 答案是否可以从证据中推理得出（即使不在证据中）
2. 答案是否与证据语义相关
3. 证据是否支持答案

返回JSON格式：
{
    "can_infer": true/false,
    "semantic_relevance": 0.0-1.0,
    "evidence_support": 0.0-1.0,
    "reason": "判断理由"
}
```

**Fallback方法**（如果LLM不可用）:
```python
# 1. 检查直接匹配
if answer_lower in evidence_text_lower:
    return 0.9

# 2. 检查部分匹配
answer_words = set(answer_lower.split())
evidence_words = set(evidence_text_lower.split())
match_ratio = len(answer_words & evidence_words) / len(answer_words)
if match_ratio >= 0.5:
    return 0.7
elif match_ratio >= 0.3:
    return 0.5
else:
    return 0.3
```

**特点**:
- ✅ 支持推理匹配（不要求直接匹配）
- ✅ 支持语义匹配
- ✅ 使用LLM进行智能评估

#### 维度3: 答案完整性（20%权重）

**计算方法**: `_calculate_completeness()`

**评估内容**:
1. **答案长度**: 是否过短或过长
2. **答案格式**: 格式是否合理
3. **答案结构**: 结构是否完整

**评估逻辑**:
```python
def _calculate_completeness(answer: str, query_type: str) -> float:
    """计算答案完整性"""
    # 1. 长度检查
    if len(answer) < 1:
        return 0.0
    if len(answer) > 1000:  # 过长
        return 0.5
    
    # 2. 格式检查
    # 检查是否包含明显的格式错误
    # ...
    
    # 3. 结构检查
    # 检查答案结构是否完整
    # ...
    
    return completeness_score  # 0.0-1.0
```

**特点**:
- ✅ 基于规则评估
- ✅ 考虑查询类型
- ✅ 快速计算

#### 维度4: 答案类型匹配（10%权重）

**计算方法**: `_calculate_type_match()`

**评估内容**:
1. **答案类型是否与查询类型匹配**: 
   - 数值查询 → 数值答案
   - 事实查询 → 事实答案
   - 时间查询 → 时间答案

**评估逻辑**:
```python
def _calculate_type_match(answer: str, query_type: str) -> float:
    """计算答案类型匹配度"""
    # 1. 判断答案类型
    answer_type = self._infer_answer_type(answer)
    
    # 2. 检查是否匹配查询类型
    if answer_type == query_type:
        return 1.0
    elif self._are_types_compatible(answer_type, query_type):
        return 0.7
    else:
        return 0.3
```

**特点**:
- ✅ 基于规则评估
- ✅ 考虑类型兼容性
- ✅ 快速计算

### 2.5 优化：合并LLM调用

**优化前**:
- `_judge_semantic_correctness_with_llm()`: 1次LLM调用
- `_calculate_evidence_support()`: 1次LLM调用
- **总计**: 2次LLM调用

**优化后**:
- `_calculate_confidence_comprehensively_with_llm()`: 1次LLM调用
- **总计**: 1次LLM调用

**节省时间**: 20-40秒（每次推理）

### 2.6 置信度计算示例

**示例1**: 高置信度答案
- 语义正确性: 0.9
- 证据支持度: 0.8
- 答案完整性: 0.9
- 答案类型匹配: 1.0

**计算**:
```
置信度 = 0.9 × 0.4 + 0.8 × 0.3 + 0.9 × 0.2 + 1.0 × 0.1
      = 0.36 + 0.24 + 0.18 + 0.10
      = 0.88
```

**示例2**: 中等置信度答案
- 语义正确性: 0.6
- 证据支持度: 0.5
- 答案完整性: 0.7
- 答案类型匹配: 0.8

**计算**:
```
置信度 = 0.6 × 0.4 + 0.5 × 0.3 + 0.7 × 0.2 + 0.8 × 0.1
      = 0.24 + 0.15 + 0.14 + 0.08
      = 0.61
```

**示例3**: 低置信度答案
- 语义正确性: 0.4
- 证据支持度: 0.3
- 答案完整性: 0.5
- 答案类型匹配: 0.6

**计算**:
```
置信度 = 0.4 × 0.4 + 0.3 × 0.3 + 0.5 × 0.2 + 0.6 × 0.1
      = 0.16 + 0.09 + 0.10 + 0.06
      = 0.41
```

---

## 3. 关键区别

### 3.1 准确率 vs 置信度

| 特性 | 准确率 | 置信度 |
|-----|--------|--------|
| **计算时机** | 评测时（有期望答案） | 推理时（无期望答案） |
| **计算方式** | 比较期望答案和实际答案 | 多维度评估答案质量 |
| **依赖** | 需要期望答案 | 不需要期望答案 |
| **用途** | 评估系统性能 | 评估答案可靠性 |
| **范围** | 0.0-1.0 | 0.0-1.0 |

### 3.2 匹配策略

**准确率匹配**:
- ✅ 支持多种匹配策略（13种）
- ✅ 支持语义相似度匹配
- ✅ 动态阈值调整

**置信度评估**:
- ✅ 多维度评估（4个维度）
- ✅ 使用LLM进行智能评估
- ✅ 支持推理匹配

---

## 4. 优化建议

### 4.1 准确率优化

1. **调整相似度阈值**:
   - 当前阈值: 0.35（语义相似度）
   - 建议: 根据实际效果调整

2. **优化匹配策略**:
   - 当前: 13种匹配策略
   - 建议: 根据匹配效果优化策略顺序

3. **改进语义相似度计算**:
   - 当前: 使用embedding向量
   - 建议: 优化embedding模型或使用更好的相似度算法

### 4.2 置信度优化

1. **调整权重**:
   - 当前: 语义正确性40%, 证据支持度30%, 完整性20%, 类型匹配10%
   - 建议: 根据实际效果调整权重

2. **优化LLM评估**:
   - 当前: 合并为1次LLM调用
   - 建议: 优化提示词，提高评估准确性

3. **改进完整性评估**:
   - 当前: 基于规则
   - 建议: 使用更智能的完整性评估方法

---

## 5. 总结

### 5.1 准确率计算

- **方法**: 智能匹配算法（13种策略）
- **阈值**: 动态调整（默认0.3）
- **特点**: 支持精确匹配和相似度匹配

### 5.2 置信度计算

- **方法**: 多维度评估（4个维度）
- **权重**: 语义正确性40%, 证据支持度30%, 完整性20%, 类型匹配10%
- **特点**: 使用LLM进行智能评估，支持推理匹配

### 5.3 关键优化

- ✅ 准确率: 降低语义相似度阈值（0.4 → 0.35）
- ✅ 置信度: 合并LLM调用（2次 → 1次，节省20-40秒）
- ✅ 动态阈值: 根据embedding模型类型调整阈值

---

**分析完成时间**: 2025-11-23  
**状态**: ✅ 完成  
**代码位置**: 
- 准确率: `evaluation_system/analyzers/frames_analyzer.py`
- 置信度: `src/core/real_reasoning_engine.py`

