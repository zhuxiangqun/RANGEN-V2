# 核心系统提示词使用方式分析

## 问题概述
核心系统中不同模块使用提示词的方式**不统一**，存在多种处理模式。

## 当前使用情况

### 1. ✅ **已使用统一提示词工程模块（但仍有问题）**

#### `src/core/real_reasoning_engine.py`
- ✅ **主要流程**：使用 `prompt_engineering.generate_prompt()` 生成提示词
- ❌ **问题**：
  - `_get_fallback_prompt()` 方法中有**硬编码的fallback提示词**（60多行）
  - 虽然使用了统一模块，但fallback仍然是硬编码的

#### `src/core/frames_processor.py`
- ✅ **主要流程**：使用 `prompt_engineering.generate_prompt()` 生成提示词
- ❌ **问题**：
  - `_register_frames_templates()` 方法中**直接在代码中调用 `prompt_engine.add_template()`** 添加硬编码模板（50多行）
  - `_get_fallback_frames_reasoning_prompt()` 方法中有**硬编码的fallback提示词**（15行）

#### `src/core/multi_hop_reasoning.py`
- ✅ **主要流程**：使用 `prompt_engineering.generate_prompt()` 生成提示词
- ❌ **问题**：
  - `_register_reasoning_type_templates()` 方法中**直接在代码中调用 `prompt_engine.add_template()`** 添加硬编码模板（25行）

### 2. ❌ **完全硬编码提示词**

#### `src/core/llm_integration.py`
- ❌ **完全硬编码**：有多个 `_build_*_prompt()` 方法，都是硬编码的提示词：
  - `_build_answer_extraction_prompt()` (15行)
  - `_build_query_classification_prompt()` (13行)
  - `_build_relevance_calculation_prompt()` (15行)
  - `_build_answer_validation_prompt()` (16行)
  - `_build_reasoning_generation_prompt()` (25行)
  - `_build_person_detection_prompt()` (未显示但存在)
  - `_build_location_detection_prompt()` (未显示但存在)
- ❌ **未使用提示词工程模块**：完全没有集成 `PromptEngine`

## 问题总结

### 主要问题
1. **不统一的处理方式**：
   - 部分模块使用统一提示词工程模块
   - 部分模块直接在代码中注册模板
   - 部分模块完全硬编码

2. **硬编码模板注册**：
   - `frames_processor.py` 的 `_register_frames_templates()` 中硬编码注册
   - `multi_hop_reasoning.py` 的 `_register_reasoning_type_templates()` 中硬编码注册
   - 这些应该改为从配置文件加载

3. **硬编码fallback提示词**：
   - `real_reasoning_engine.py` 的 `_get_fallback_prompt()`
   - `frames_processor.py` 的 `_get_fallback_frames_reasoning_prompt()`
   - 这些应该也使用配置文件或至少更简洁的fallback

4. **完全未集成的模块**：
   - `llm_integration.py` 完全未使用提示词工程模块
   - 所有提示词都是硬编码的

## 建议的统一方案

### 原则
1. **所有提示词模板从配置文件加载** (`templates/templates.json`)
2. **所有模块统一使用 `PromptEngine`**
3. **Fallback机制简洁，避免大量硬编码**

### 具体改进建议

#### 1. `src/core/llm_integration.py`
- **优先级：高**
- 将所有的 `_build_*_prompt()` 方法改为使用 `PromptEngine`
- 在 `templates/templates.json` 中添加相应的模板：
  - `answer_extraction_llm`
  - `query_classification_llm`
  - `relevance_calculation_llm`
  - `answer_validation_llm`
  - `reasoning_generation_llm`
  - `person_detection_llm`
  - `location_detection_llm`

#### 2. `src/core/frames_processor.py`
- **优先级：中**
- `_register_frames_templates()` 改为只检查模板是否存在，不硬编码注册
- 将模板内容移到 `templates/templates.json`
- `_get_fallback_frames_reasoning_prompt()` 改为从配置加载或使用更简洁的fallback

#### 3. `src/core/multi_hop_reasoning.py`
- **优先级：中**
- `_register_reasoning_type_templates()` 改为只检查模板是否存在，不硬编码注册
- 将模板内容移到 `templates/templates.json`

#### 4. `src/core/real_reasoning_engine.py`
- **优先级：低**
- `_get_fallback_prompt()` 可以保留，但应该更简洁（只做最基本的fallback）

## 结论

**核心系统中的提示词处理方式不统一**，需要：
1. 统一所有模块使用 `PromptEngine`
2. 将所有模板内容移到配置文件
3. 移除代码中的硬编码模板注册
4. 简化或移除硬编码的fallback提示词

