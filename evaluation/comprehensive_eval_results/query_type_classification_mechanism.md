# 查询类型判定机制说明

**生成时间**: 2025-11-08  
**目的**: 详细说明查询类型是如何判定的

---

## 📊 判定策略概览

查询类型判定采用**多层策略**，优先级从高到低：

1. **LLM智能分类**（主要方法）✅
2. **语义相似度匹配**（Fallback 1）✅
3. **规则匹配**（Fallback 2）✅

---

## 🔍 详细实现流程

### 1. 主要方法：LLM智能分类

**文件**: `src/core/real_reasoning_engine.py`  
**方法**: `_analyze_query_type_with_ml(query)`

**实现流程**:
```python
def _analyze_query_type_with_ml(self, query: str) -> str:
    # 1. 使用统一分类服务
    classification_service = get_unified_classification_service(...)
    
    # 2. 调用LLM进行分类
    return classification_service.classify(
        query=query,
        classification_type="query_type",
        valid_types=['factual', 'numerical', 'temporal', 'causal', ...],
        template_name="query_type_classification",  # 使用LLM提示词模板
        default_type='general',
        rules_fallback=self._analyze_query_type_with_rules
    )
```

**LLM提示词模板**: `templates/templates.json` → `query_type_classification`

**提示词内容**:
- 提供9种查询类型的定义和示例
- 要求LLM分析查询的语义含义和复杂度
- 返回类型名称（一个词）

**示例**:
```
Query: "What is the capital of France?"
Reasoning: Asking for a specific fact (capital city)
Type: factual

Query: "How many people live in Tokyo?"
Reasoning: Asking for a numerical value (population count)
Type: numerical
```

**优势**:
- ✅ 理解语义，不依赖关键词
- ✅ 能处理复杂查询
- ✅ 可扩展（通过提示词模板）

---

### 2. Fallback 1：语义相似度匹配

**文件**: `src/utils/unified_classification_service.py`  
**方法**: `_try_semantic_based_fallback()`

**实现流程**:
- 如果LLM分类失败，使用语义相似度匹配
- 将查询与历史成功分类的示例进行相似度比较
- 选择最相似的示例的类型

**优势**:
- ✅ 智能（基于语义，不是关键词）
- ✅ 可学习（从历史成功案例学习）
- ✅ 可扩展（自动积累示例）

---

### 3. Fallback 2：规则匹配

**文件**: `src/core/real_reasoning_engine.py`  
**方法**: `_analyze_query_type_with_rules(query)`

**实现流程**:
- 这是最后的fallback方法
- 目前只返回默认值 `'general'`
- 实际的智能fallback由统一分类服务通过语义相似度完成

**注意**: 这个方法现在只作为最后的fallback，实际的智能分类由统一分类服务完成。

---

## 📈 判定流程图示

```
查询输入
    ↓
┌─────────────────────────────────┐
│ 1. LLM智能分类（主要方法）      │
│    - 使用提示词模板              │
│    - 分析语义含义                │
│    - 返回类型名称                │
└─────────────────────────────────┘
    ↓ (如果失败)
┌─────────────────────────────────┐
│ 2. 语义相似度匹配（Fallback 1） │
│    - 与历史成功案例比较          │
│    - 选择最相似的类型            │
└─────────────────────────────────┘
    ↓ (如果失败)
┌─────────────────────────────────┐
│ 3. 规则匹配（Fallback 2）       │
│    - 返回默认类型 'general'     │
└─────────────────────────────────┘
    ↓
返回查询类型
```

---

## 🎯 支持的查询类型

系统支持以下9种查询类型：

1. **factual** - 事实查询（who, what, where, name等）
2. **numerical** - 数值查询（how many, number, count等）
3. **temporal** - 时间查询（when, date, duration等）
4. **causal** - 因果查询（why, cause-effect等）
5. **procedural** - 过程查询（how to do等）
6. **mathematical** - 数学查询（calculate, compute等）
7. **comparative** - 比较查询（compare等）
8. **definition** - 定义查询（what is等）
9. **general** - 通用查询（复杂查询或多步骤推理）

---

## ✅ 总结

### 判定方式

**主要方法**: **LLM判断** ✅
- 使用LLM分析查询的语义含义
- 通过提示词模板指导LLM分类
- 理解查询意图，不依赖关键词

**Fallback方法**: 
- 语义相似度匹配（智能、可学习）
- 规则匹配（最后的安全网）

### 优势

1. **智能性** ✅
   - LLM理解语义，不依赖关键词匹配
   - 能处理复杂和模糊的查询

2. **可扩展性** ✅
   - 通过提示词模板扩展类型定义
   - 语义相似度自动学习新示例

3. **可靠性** ✅
   - 多层fallback机制
   - 即使LLM失败也有备用方案

---

*本报告基于2025-11-08的代码分析生成*

