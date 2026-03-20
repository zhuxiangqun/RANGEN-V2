# 核心系统中剩余的硬编码关键词问题分析

## 问题概述
虽然我们已经将主要的分类逻辑改为智能的语义相似度方案，但核心系统中仍存在多处硬编码关键词匹配。

## 发现的问题

### 1. `src/core/frames_processor.py`

#### 1.1 时间操作符识别（第846, 939-943行）
**位置**：`_extract_temporal_constraints` 方法
**问题**：硬编码时间操作符关键词
```python
operator = "before" if any(word in pattern for word in ["before", "之前", "先于", "早于", "prior"]) else "after"
if any(word in pattern for word in ["during", "期间", "while", "当"]):
elif any(word in pattern for word in ["until", "直到"]):
elif any(word in pattern for word in ["since", "自从"]):
```
**影响**：低-中等（特定于时间约束提取，不是主要分类路径）

#### 1.2 约束类型识别（第1913-1937行）
**位置**：`_extract_constraints` 方法
**问题**：硬编码约束类型关键词
```python
if any(word in query_lower for word in ['时间', 'time', 'before', 'after', 'during']):
    # 时间约束
if any(word in query_lower for word in ['位置', 'location', 'place', 'where', '空间']):
    # 空间约束
if any(word in query_lower for word in ['数量', 'number', 'count', 'how many']):
    # 数值约束
if any(word in query_lower for word in ['逻辑', 'logic', 'if', 'then', 'and', 'or']):
    # 逻辑约束
```
**影响**：中等（影响约束提取的准确性）

### 2. `src/core/real_reasoning_engine.py`

#### 2.1 数值查询识别（第989行）
**位置**：`_derive_final_answer_with_ml` 方法
**问题**：硬编码数值关键词
```python
if any(keyword in query_lower for keyword in ['how many', 'number', 'count', 'quantity', 'times', 'years', 'people']):
```
**影响**：低（用于确定是否优先提取数值答案）

#### 2.2 数值查询识别（第1791行）
**位置**：`_extract_answer_from_evidence` 方法
**问题**：硬编码数值关键词
```python
if any(keyword in query.lower() for keyword in ['how many', 'number', 'count', 'quantity']):
```
**影响**：低（用于确定答案提取策略）

### 3. `src/utils/unified_intelligent_processor.py`

#### 3.1 概念类型分类（第1015-1043行）
**位置**：`_classify_concept_type` 函数
**问题**：硬编码概念类型关键词
```python
if any(term in concept_lower for term in ['算法', '模型', '优化', '分析', '推理', '学习', '智能', '处理', '计算', '数据']):
    return 'TECHNICAL'
if any(term in concept_lower for term in ['方法', '技术', '系统', '架构', '设计', '实现', '应用']):
    return 'METHOD'
```
**影响**：中等（影响概念分类的准确性和扩展性）

## 优化建议

### 优先级1：核心分类路径（已完成）
- ✅ `_identify_problem_type_with_rules` - 已改为使用统一分类服务
- ✅ `_analyze_query_type_with_rules` - 已改为使用统一分类服务
- ✅ `_identify_reasoning_type_with_rules` - 已改为使用统一分类服务

### 优先级2：约束提取（建议优化）
- `_extract_constraints` - 可以考虑使用LLM或语义匹配
- `_extract_temporal_constraints` - 时间操作符识别可以更智能

### 优先级3：辅助判断（可保留）
- 数值关键词判断用于答案提取策略，属于业务逻辑，可以保留
- 但可以改为使用统一分类服务的查询类型判断结果

## 总结

**主要分类逻辑**：✅ 已全部改为智能语义方案
**辅助判断逻辑**：⚠️ 仍有少量硬编码，但影响较小，可根据需要优化
**业务特定逻辑**：部分硬编码是业务逻辑的一部分，可选择性优化

