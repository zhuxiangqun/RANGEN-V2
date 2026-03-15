# 统一证据处理框架使用指南

## 概述

`UnifiedEvidenceFramework` 整合了所有证据相关的处理功能，遵循统一中心系统原则，提供一站式证据处理服务。

## 架构设计

### 整合的模块

1. **证据检索** (`EvidenceProcessor`)
2. **证据预处理** (`EvidencePreprocessor`)
3. **证据验证** (`EvidenceValidator`)
4. **质量评估** (`EvidenceQualityAssessor`)
5. **格式化** (`format_for_prompt`)

### 处理流程

```
检索 → 预处理 → 验证 → 质量评估 → 格式化 → 完成
```

## 使用方式

### 1. 完整流程（推荐用于新代码）

```python
from src.core.reasoning.unified_evidence_framework import UnifiedEvidenceFramework

# 初始化框架
framework = UnifiedEvidenceFramework(
    knowledge_retrieval_agent=knowledge_retrieval_agent,
    config_center=config_center,
    learning_manager=learning_manager,
    llm_integration=llm_integration
)

# 完整处理流程
result = await framework.process_evidence_complete(
    query="Who was the 15th first lady?",
    context=context,
    query_analysis=query_analysis,
    format_type="structured"
)

# 使用结果
evidence = result.evidence
validation_result = result.validation_result
quality_assessment = result.quality_assessment
formatted_text = result.formatted_text
```

### 2. 分阶段处理（灵活使用）

```python
# 仅检索
raw_evidence = await framework.retrieve_only(query, context, query_analysis)

# 仅预处理
processed = framework.preprocess_only(raw_evidence)

# 仅验证
validation = framework.validate_only(processed, query)

# 仅质量评估
quality = framework.assess_quality_only(processed, query)

# 仅格式化
formatted = framework.format_only(processed, query, format_type="structured")
```

### 3. 步骤级别处理

```python
# 为推理步骤处理证据
result = await framework.process_evidence_for_step(
    sub_query="Who was the mother of Sarah Polk?",
    step=step_dict,
    context=context,
    query_analysis=query_analysis,
    previous_evidence=previous_evidence,  # 可选，用于复用
    format_type="structured"
)
```

## 实现状态

### ✅ 已实现

1. **统一框架类** (`UnifiedEvidenceFramework`)
   - ✅ 完整流程方法 `process_evidence_complete`
   - ✅ 分阶段方法（`retrieve_only`, `preprocess_only`, `validate_only`, `assess_quality_only`, `format_only`）
   - ✅ 步骤级别方法 `process_evidence_for_step`
   - ✅ 列表格式化方法 `format_list_evidence`

2. **引擎集成** (`engine.py`)
   - ✅ 使用统一框架初始化证据预处理器
   - ✅ 通过统一框架访问证据检索处理器（向后兼容）
   - ✅ 保持向后兼容性（fallback机制）

3. **验证和标记**
   - ✅ 证据验证器 (`EvidenceValidator`)
   - ✅ 智能标记系统
   - ✅ 不确定性量化
   - ✅ 矛盾检测

4. **提示词增强**
   - ✅ 检测验证信息
   - ✅ 处理矛盾指导
   - ✅ 统计标准说明

### 📝 使用建议

#### 新代码
- ✅ **直接使用** `UnifiedEvidenceFramework` 的完整流程
- ✅ 使用 `process_evidence_complete` 方法

#### 现有代码
- ✅ **逐步迁移**到统一框架
- ✅ `engine.py` 已更新为通过统一框架访问（向后兼容）
- ✅ 其他模块可以保持现状，逐步迁移

#### 特殊需求
- ✅ **可以使用**分阶段方法
- ✅ 所有分阶段方法已实现

## 向后兼容性

### 兼容策略

1. **统一框架优先**：如果统一框架初始化成功，使用框架内的模块
2. **Fallback机制**：如果统一框架不可用，fallback到单独的模块
3. **接口兼容**：统一框架暴露底层模块的接口，保持API兼容

### 示例

```python
# engine.py 中的实现
if isinstance(self.evidence_preprocessor, UnifiedEvidenceFramework):
    # 使用统一框架内的检索处理器
    self.evidence_processor = self.evidence_preprocessor.retrieval_processor
else:
    # Fallback: 使用单独的EvidenceProcessor
    self.evidence_processor = EvidenceProcessor(...)
```

## 优势

1. **统一管理**：所有证据处理集中在一个框架中
2. **模块化**：各模块可独立使用，也可组合使用
3. **向后兼容**：支持单独使用各个模块
4. **可扩展**：易于添加新的处理阶段
5. **符合原则**：遵循统一中心系统原则

## 迁移路径

### 阶段1：新代码使用统一框架 ✅
- 已完成：新代码可以直接使用 `UnifiedEvidenceFramework`

### 阶段2：核心模块迁移 ✅
- 已完成：`engine.py` 已迁移到统一框架

### 阶段3：其他模块迁移（可选）
- `prompt_generator.py`：可以保持现状（仅使用质量评估器）
- 其他模块：根据需要逐步迁移

## 总结

✅ **所有使用建议的内容都已实现**：

1. ✅ 新代码可以直接使用统一框架的完整流程
2. ✅ 现有代码已逐步迁移（`engine.py` 已完成）
3. ✅ 特殊需求可以使用分阶段方法
4. ✅ 保持向后兼容性
5. ✅ 提供完整的文档和示例

