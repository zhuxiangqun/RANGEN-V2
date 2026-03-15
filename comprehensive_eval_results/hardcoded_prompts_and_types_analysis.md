# 核心系统硬编码提示词和类型判断问题分析

**生成时间**: 2025-11-01
**目的**: 全面分析核心系统中存在的硬编码提示词和硬编码类型判断问题

---

## 📋 概述

经过全面搜索，发现核心系统中存在以下两类问题：

1. **硬编码提示词构建**：没有使用 `PromptEngine` 系统，而是直接构建提示词字符串
2. **硬编码类型判断**：使用关键词匹配而非LLM智能分类

---

## 🔍 问题1：硬编码提示词构建

### 1.1 `src/core/llm_integration.py`

**问题位置**: 多个 `_build_*_prompt` 方法

**涉及的方法**:
- `_build_person_detection_prompt` (第200-211行)
- `_build_location_detection_prompt` (第213-224行)
- `_build_answer_extraction_prompt` (第715-728行)
- `_build_query_classification_prompt` (第730-742行)
- `_build_relevance_calculation_prompt` (第744-759行)
- `_build_answer_validation_prompt` (第761-777行)
- `_build_reasoning_generation_prompt` (第779行及之后)

**示例代码**:
```python
def _build_answer_extraction_prompt(self, query: str, content: str) -> str:
    """Build answer extraction prompt (English only)"""
    return f"""Extract the most accurate answer from the text based on the following query.

Query: {query}
Text: {content}
...
"""
```

**问题**: 
- 硬编码提示词，无法通过配置系统统一管理
- 无法利用 `PromptEngine` 的性能跟踪和优化功能
- 难以扩展和维护

**影响**: ⚠️ **中等** - 这些是底层LLM集成方法，可能被多个模块使用

---

### 1.2 `src/core/frames_processor.py`

**问题位置**: `_execute_default_reasoning` 方法 (第1666-1679行)

**示例代码**:
```python
# 构建推理提示词
prompt = f"""
请分析以下FRAMES问题并提供推理过程和答案：

问题: {problem.query}
问题类型: {analysis.get('problem_type', 'unknown')}
复杂度: {analysis.get('complexity', 1)}

请提供：
1. 推理过程
2. 最终答案
3. 置信度评估

请确保答案简洁明了。
"""
```

**问题**:
- 硬编码中文提示词（违反核心系统英文化原则）
- 没有使用 `PromptEngine` 系统
- 无法统一管理和优化

**影响**: ⚠️ **高** - 这是核心FRAMES处理逻辑的一部分

---

### 1.3 `src/core/real_reasoning_engine.py`

**问题位置**: `ReasoningStepType.generate_step_type` 方法 (第31行)

**示例代码**:
```python
prompt = f"Query: {query[:100]}\nReturn only the type name: evidence_gathering,query_analysis,logical_deduction,pattern_recognition,causal_reasoning,analogical_reasoning,mathematical_reasoning,answer_synthesis"
```

**问题**:
- 硬编码提示词字符串，过于简单
- 没有使用 `PromptEngine` 系统
- 提示词质量低，可能影响分类准确性

**影响**: ⚠️ **高** - 影响推理步骤类型生成的准确性

---

## 🔍 问题2：硬编码类型判断

### 2.1 `src/core/frames_processor.py`

**问题位置**: `_identify_problem_type` 方法 (第287-386行)

**问题描述**: 
- 使用硬编码关键词匹配判断FRAMES问题类型
- 包含大量中文关键词（违反核心系统英文化原则）
- 无法理解语义，只能匹配关键词

**示例代码**:
```python
# 数值推理关键词
numerical_keywords = [
    "number", "count", "how many", "多少", "数量", "total", "sum",
    ...
]
type_scores[FramesProblemType.NUMERICAL_REASONING] = sum(1 for kw in numerical_keywords if kw in query_lower)
```

**影响**: ⚠️ **高** - 这是FRAMES问题处理的核心逻辑，直接影响问题分类准确性

---

### 2.2 `src/core/multi_hop_reasoning.py`

**问题位置**: `_identify_reasoning_type` 方法 (第344-360行)

**问题描述**:
- 使用硬编码关键词匹配判断推理类型
- 支持中英文关键词，但方法简单
- 无法理解复杂的推理语义

**示例代码**:
```python
if any(word in question_lower for word in ["如果", "假设", "那么", "if", "then"]):
    return "deductive"
elif any(word in question_lower for word in ["通常", "一般", "总是", "usually", "generally", "always"]):
    return "inductive"
```

**影响**: ⚠️ **中等** - 用于多跳推理的类型识别

---

## 📊 问题总结表

| 文件 | 问题类型 | 位置 | 严重程度 | 影响范围 |
|------|---------|------|---------|---------|
| `src/core/llm_integration.py` | 硬编码提示词 | 多个 `_build_*_prompt` 方法 | ⚠️ 中等 | 底层LLM集成 |
| `src/core/frames_processor.py` | 硬编码提示词 | `_execute_default_reasoning` (第1666行) | ⚠️ 高 | FRAMES处理 |
| `src/core/real_reasoning_engine.py` | 硬编码提示词 | `ReasoningStepType.generate_step_type` (第31行) | ⚠️ 高 | 推理步骤类型 |
| `src/core/frames_processor.py` | 硬编码类型判断 | `_identify_problem_type` (第287行) | ⚠️ 高 | FRAMES问题分类 |
| `src/core/multi_hop_reasoning.py` | 硬编码类型判断 | `_identify_reasoning_type` (第344行) | ⚠️ 中等 | 推理类型识别 |

---

## 💡 改进建议

### 建议1：统一使用 PromptEngine

**优先级**: 🔴 **高**

**实施步骤**:
1. 将所有硬编码提示词注册到 `PromptEngine`
2. 修改相关方法使用 `PromptEngine.generate_prompt()`
3. 移除硬编码提示词字符串

**受益**:
- 统一管理所有提示词
- 性能跟踪和优化
- 易于扩展和维护

---

### 建议2：使用LLM进行智能类型判断

**优先级**: 🔴 **高**

**实施步骤**:
1. 为每种类型判断创建LLM分类提示词模板
2. 使用快速LLM模型进行分类（3-5秒）
3. 保留规则匹配作为fallback

**受益**:
- 真正的语义理解
- 更高的分类准确度
- 更好的可扩展性

---

### 建议3：移除中文硬编码

**优先级**: 🟡 **中**

**实施步骤**:
1. 将所有中文提示词改为英文
2. 移除中文关键词匹配
3. 统一使用英文提示词

**受益**:
- 符合核心系统英文化原则
- 更好的国际化支持

---

## 🎯 下一步行动

1. ✅ 已完成：`src/core/real_reasoning_engine.py` 的查询类型分类已改为使用LLM和PromptEngine
2. 🔄 待改进：
   - `src/core/frames_processor.py` 的问题类型识别和提示词构建
   - `src/core/multi_hop_reasoning.py` 的推理类型识别
   - `src/core/real_reasoning_engine.py` 的推理步骤类型生成
   - `src/core/llm_integration.py` 的提示词构建方法（可选，因为它们是底层方法）

---

**结论**: 核心系统中确实存在多处硬编码提示词和类型判断问题，需要系统性地改进，统一使用 `PromptEngine` 和LLM智能分类。

