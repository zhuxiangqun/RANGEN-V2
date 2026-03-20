# 硬编码模式匹配移除重构报告（2025-11-28）

**重构时间**: 2025-11-28  
**问题**: 之前的优化使用了大量硬编码和模式匹配，违反了项目的核心原则  
**解决方案**: 重构为LLM驱动的智能方法，使用统一配置中心

---

## 🔍 问题分析

### 之前的实现问题

1. **硬编码的模式匹配**:
   - 使用正则表达式匹配序数词、人名、数字等
   - 硬编码的格式转换规则（如"37" -> "37th"）
   - 无法适应新的格式变化

2. **违反项目原则**:
   - ❌ 违反了DRY原则（重复的硬编码规则）
   - ❌ 违反了智能化可扩展性规范
   - ❌ 违反了避免硬编码的原则

3. **可扩展性差**:
   - 添加新的格式要求需要修改代码
   - 无法动态配置格式规则
   - 无法适应不同语言的格式要求

---

## ✅ 重构方案

### 核心思想

**从硬编码模式匹配 → LLM驱动的智能方法**

1. **优先使用LLM**: 让LLM理解语义，智能提取和规范化答案
2. **使用统一配置中心**: 格式要求存储在配置中心，可动态配置
3. **提示词工程**: 使用提示词工程生成格式要求，而非硬编码
4. **模式匹配仅作为fallback**: 只在LLM不可用时使用

---

## 🔧 重构内容

### 1. 答案格式规范化重构

**之前**:
```python
def _normalize_answer_format(self, answer: str, query: str, query_type: str) -> str:
    # 硬编码的正则表达式匹配
    if query_type == 'ranking':
        ordinal_match = re.search(r'\b(\d+(?:st|nd|rd|th))\b', answer, re.IGNORECASE)
        # 硬编码的格式转换
        if answer.strip().isdigit():
            num = int(answer.strip())
            suffix = self._get_ordinal_suffix(num)
            return f"{num}{suffix}"
    # ... 更多硬编码规则
```

**重构后**:
```python
def _normalize_answer_format_with_llm(self, answer: str, query: str, query_type: str) -> str:
    """使用LLM智能规范化答案格式（而非硬编码规则）"""
    # 1. 从配置中心获取格式要求（可扩展）
    format_instruction = self.config_center.get_config_value(
        'answer_format', f'{query_type}_format_requirement', None
    )
    
    # 2. 如果没有配置，使用提示词工程生成格式要求
    if not format_instruction:
        format_instruction = self.prompt_engineering.generate_answer_format_instruction(
            query=query, query_type=query_type, config_center=self.config_center
        )
    
    # 3. 使用LLM智能规范化格式
    normalize_prompt = f"""Normalize the following answer to match the expected format...
    {format_instruction}
    ...
    """
    normalized = self.fast_llm_integration._call_llm(normalize_prompt, ...)
    return normalized
```

**优势**:
- ✅ 使用LLM理解语义，不依赖固定格式
- ✅ 格式要求存储在配置中心，可动态配置
- ✅ 可扩展：添加新格式要求只需更新配置
- ✅ 适应性强：可以处理各种格式变化

---

### 2. 答案提取增强

**之前**:
```python
# 硬编码的模式匹配
ordinal_patterns = [
    r'\b(\d+)(?:st|nd|rd|th)\b',
    r'\b(\d+)(?:th)\b',
]
for pattern in ordinal_patterns:
    matches = re.findall(pattern, content, re.IGNORECASE)
    # 硬编码的格式处理
```

**重构后**:
```python
# 1. 优先使用LLM提取（理解语义）
llm_extracted = self._extract_with_llm(response, query, query_type)
if llm_extracted:
    return llm_extracted

# 2. 模式匹配仅作为最后的fallback
# 🚀 注意：这应该尽可能少用，优先依赖LLM
pattern_extracted = self._extract_with_patterns(...)  # 仅作为fallback
```

**优势**:
- ✅ 优先使用LLM智能提取
- ✅ 模式匹配仅作为fallback
- ✅ 在LLM提取时通过提示词确保格式正确

---

### 3. 人名提取重构

**之前**:
```python
# 硬编码的人名模式匹配
person_patterns = [
    r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b',
    r'答案[是：]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
    # ... 更多硬编码模式
]
```

**重构后**:
```python
# 1. 优先使用LLM智能提取人名
if self.fast_llm_integration:
    llm_prompt = f"""Extract the person name from the following content...
    """
    llm_extracted = self.fast_llm_integration._call_llm(llm_prompt, ...)
    if llm_extracted:
        return llm_extracted

# 2. Fallback: 使用简单的模式匹配（仅作为最后的fallback）
# 🚀 注意：这应该尽可能少用，优先依赖LLM
```

**优势**:
- ✅ 使用LLM理解语义，提取完整人名
- ✅ 不依赖固定的格式模式
- ✅ 可以处理各种人名格式（包括缩写、中间名等）

---

### 4. 格式要求集成到提示词

**之前**:
- 格式要求硬编码在代码中
- 无法动态配置

**重构后**:
```python
# 从配置中心或提示词工程获取格式要求
format_instruction = self.config_center.get_config_value(
    'answer_format', f'{query_type}_format_requirement', None
)

# 如果没有配置，使用提示词工程生成
if not format_instruction:
    format_instruction = self.prompt_engineering.generate_answer_format_instruction(
        query=query, query_type=query_type, config_center=self.config_center
    )

# 在提取提示词中包含格式要求
prompt_template = f"""Extract the answer...
{format_instruction}
...
"""
```

**优势**:
- ✅ 格式要求存储在配置中心，可动态配置
- ✅ 使用提示词工程生成格式要求
- ✅ LLM在生成时就按照正确格式生成，减少后处理

---

## 📊 重构效果

### 智能化提升
- ✅ 使用LLM理解语义，不依赖固定格式
- ✅ 可以适应各种格式变化
- ✅ 可以处理多语言格式要求

### 可扩展性提升
- ✅ 格式要求存储在配置中心，可动态配置
- ✅ 添加新格式要求只需更新配置，无需修改代码
- ✅ 使用提示词工程生成格式要求，支持动态扩展

### 代码质量提升
- ✅ 移除硬编码规则，符合项目原则
- ✅ 减少代码重复，符合DRY原则
- ✅ 提高代码可维护性

---

## 🎯 下一步优化

1. **配置中心完善**: 在配置中心添加更多格式要求模板
2. **提示词优化**: 优化格式规范化的提示词，提高准确性
3. **性能优化**: 考虑缓存格式规范化结果，减少LLM调用

---

**状态**: ✅ 重构完成 - 移除硬编码，使用LLM驱动的智能方法  
**原则**: 符合项目的核心原则（DRY、智能化可扩展性、避免硬编码）

