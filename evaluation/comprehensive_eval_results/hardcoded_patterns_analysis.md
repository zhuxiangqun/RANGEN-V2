# 核心系统硬编码模式分析

## 📋 问题概述

经过分析，核心系统中还存在多处硬编码模式匹配的问题，与 `_extract_from_reasoning_process` 类似，缺乏智能性和扩展性。

## 🔍 发现的硬编码问题

### 1. `src/core/llm_integration.py`

#### 1.1 推理链模式匹配（第468-477行）
```python
chain_patterns = [
    r'→\s*[^=→]+=\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',  # "→ mother = Arabella Mason"
    r'→\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',  # "→ Arabella Mason"
]
```
**问题**：
- 硬编码正则表达式模式
- 只能匹配特定格式的推理链
- 无法处理新的推理链格式

#### 1.2 Step模式匹配（第777-789行）
```python
step_patterns = [
    r'Step\s+\d+[:\-]\s*(.+?)(?=Step\s+\d+|Conclusion|Final|$)',
    r'步骤\s*\d+[:\-]\s*(.+?)(?=步骤\s*\d+|结论|最终|$)',
]
```
**问题**：
- 硬编码Step格式
- 无法处理其他语言的Step格式
- 无法处理变体格式（如"Step 1."、"Step 1-"等）

#### 1.3 结论模式匹配（第792-804行）
```python
conclusion_patterns = [
    r'(?:Conclusion|Final Answer|Final Conclusion|结论|最终答案)[:：]\s*(.+?)(?=\n\n|\n[A-Z]|$)',
    r'(?:Therefore|So|Thus|因此|所以)[,，]?\s+(.+?)(?=\n\n|\n[A-Z]|$)',
]
```
**问题**：
- 硬编码结论标记
- 无法处理其他语言的结论标记
- 无法处理语义相似但表达不同的结论

#### 1.4 前缀列表（第752-761行）
```python
prefixes_to_remove = [
    "the answer is:", "answer is:", "answer:", "答案是：", "答案是", "答案：",
    "final answer is:", "final answer:", "最终答案是：", "最终答案："
]
```
**问题**：
- 硬编码前缀列表
- 无法处理新的前缀格式
- 无法处理语义相似但表达不同的前缀

### 2. `src/core/frames_processor.py`

#### 2.1 条件约束模式匹配（第1027-1053行）
```python
conditional_patterns = [
    r'if\s+(\w+)\s+then\s+(\w+)',
    r'如果\s+(\w+)\s+那么\s+(\w+)',
    r'(\w+)\s+implies\s+(\w+)',
    r'(\w+)\s+意味着\s+(\w+)',
    # ... 更多硬编码模式
]
```
**问题**：
- 硬编码条件约束模式
- 只能匹配特定格式的条件表达
- 无法处理语义相似但表达不同的条件

#### 2.2 否定约束模式匹配（第1056-1079行）
```python
negation_patterns = [
    r'not\s+(\w+)',
    r'不是\s+(\w+)',
    r'不\s+(\w+)',
    # ... 更多硬编码模式
]
```
**问题**：
- 硬编码否定约束模式
- 只能匹配特定格式的否定表达
- 无法处理语义相似但表达不同的否定

#### 2.3 合取约束模式匹配（第1082-1109行）
```python
conjunction_patterns = [
    r'(\w+)\s+and\s+(\w+)',
    r'(\w+)\s+和\s+(\w+)',
    # ... 更多硬编码模式
]
```
**问题**：
- 硬编码合取约束模式
- 只能匹配特定格式的合取表达
- 无法处理语义相似但表达不同的合取

## 🎯 改进方案

### 方案1：使用LLM进行智能提取（推荐）

#### 1.1 `llm_integration.py` 改进
- **`_extract_answer_from_reasoning`**: 优先使用LLM提取，模式匹配作为fallback
- **`_extract_answer_from_step`**: 使用LLM提取Step中的答案
- **`_clean_answer_prefix`**: 使用LLM识别和移除前缀

#### 1.2 `frames_processor.py` 改进
- **`_extract_logical_constraints`**: 使用LLM提取逻辑约束，模式匹配作为fallback
- **`_extract_temporal_constraints`**: 使用LLM提取时间约束

### 方案2：使用统一中心系统

#### 2.1 配置中心
- 将模式列表移到配置中心
- 支持动态添加新模式
- 支持多语言模式

#### 2.2 提示词工程
- 使用提示词工程生成提取提示词
- 根据查询类型和语言生成针对性提示词

## 📊 优先级

### P0（高优先级）
1. **`llm_integration.py` 中的推理链和Step提取** - 直接影响答案提取质量
2. **`llm_integration.py` 中的结论提取** - 影响答案提取准确性

### P1（中优先级）
3. **`frames_processor.py` 中的约束提取** - 影响FRAMES问题处理
4. **`llm_integration.py` 中的前缀清理** - 影响答案格式

## 🔧 实施步骤

1. **重构 `_extract_answer_from_reasoning`**
   - 优先使用LLM提取
   - 模式匹配作为fallback
   - 使用统一中心系统

2. **重构 `_extract_logical_constraints`**
   - 使用LLM提取约束
   - 模式匹配作为fallback
   - 支持多语言和语义理解

3. **重构前缀清理逻辑**
   - 使用LLM识别前缀
   - 配置中心存储常见前缀
   - 支持动态扩展

## ✅ 预期效果

1. **更智能**：LLM能理解复杂的推理格式和语义
2. **更可扩展**：不需要硬编码新格式，LLM能适应新格式
3. **更准确**：LLM能理解上下文和语义关系
4. **向后兼容**：保留模式匹配作为fallback

