# Prompt 动态编排实施总结

## 实施目标

按照方案1实施 Prompt 动态编排功能，包括：
1. 片段库：定义可复用的提示词片段
2. 编排引擎：实现片段组合逻辑
3. 动态调整：根据上下文动态选择片段

## 实施内容

### 1. 创建 PromptOrchestrator (`src/utils/prompt_orchestrator.py`)

#### ✅ 片段库

定义了 **20+ 个可复用的提示词片段**，包括：

**基础片段**：
- `introduction` - 基础介绍
- `introduction_reasoning` - 推理专家介绍
- `introduction_analysis` - 分析专家介绍

**查询相关片段**：
- `query_section` - 查询内容
- `query_with_context` - 带上下文的查询

**证据相关片段**：
- `evidence_section` - 证据内容
- `evidence_guidance` - 证据使用指导
- `evidence_quality_note` - 证据质量说明

**上下文相关片段**：
- `context_section` - 上下文信息
- `context_confidence` - 上下文置信度

**推理相关片段**：
- `reasoning_guidance` - 推理要求
- `reasoning_steps` - 推理步骤
- `multi_step_reasoning` - 多步骤推理要求
- `multi_hop_guidance` - 多跳推理指导
- `dependency_analysis` - 依赖关系分析

**答案相关片段**：
- `answer_requirement` - 答案要求
- `answer_format` - 答案格式
- `answer_validation` - 答案验证

**输出格式片段**：
- `output_format_json` - JSON格式输出
- `output_format_text` - 文本格式输出

**特殊场景片段**：
- `entity_completion_guidance` - 实体补全指导

#### ✅ 编排策略

定义了 **6 种编排策略**：

1. **DEFAULT** - 默认策略
   - 包含：introduction, query_section, answer_requirement, output_format_text

2. **SIMPLE** - 简单策略（最少片段）
   - 包含：introduction, query_section, answer_format

3. **DETAILED** - 详细策略（最多片段）
   - 包含：所有主要片段

4. **EVIDENCE_BASED** - 基于证据的策略
   - 包含：introduction, query_section, evidence_section, evidence_guidance, evidence_quality_note, answer_requirement, output_format_text

5. **REASONING_BASED** - 基于推理的策略
   - 包含：introduction_reasoning, query_section, reasoning_guidance, reasoning_steps, multi_step_reasoning, answer_requirement, output_format_text

6. **CONTEXT_RICH** - 上下文丰富的策略
   - 包含：introduction, query_with_context, context_confidence, evidence_section, evidence_guidance, reasoning_guidance, answer_requirement, output_format_text

#### ✅ 动态调整功能

**根据上下文自动调整片段**：
- 如果有证据，自动添加证据相关片段
- 如果有上下文信息，自动添加上下文片段
- 如果是多步骤推理，自动添加多步骤指导
- 如果需要实体补全，自动添加实体补全指导
- 根据查询类型调整片段选择

#### ✅ 核心方法

1. **`orchestrate()`** - 动态编排提示词
   - 根据策略和上下文选择片段
   - 组合片段生成完整提示词

2. **`_select_fragments()`** - 选择片段
   - 根据策略获取基础片段
   - 根据上下文动态调整

3. **`_compose_fragments()`** - 组合片段
   - 格式化每个片段
   - 组合成完整提示词

4. **`add_fragment()`** - 添加自定义片段
   - 支持扩展片段库

5. **`register_strategy()`** - 注册自定义策略
   - 支持扩展编排策略

### 2. 集成到 UnifiedPromptManager

#### ✅ 集成点

**位置**: `src/utils/unified_prompt_manager.py`

**修改内容**：
1. 添加 `orchestrator` 属性
2. 在 `get_prompt()` 方法中优先使用编排器
3. 添加 `_select_orchestration_strategy()` 方法

**执行流程**：
```
get_prompt()
    ↓
1. 如果启用编排，使用 PromptOrchestrator.orchestrate()
    ↓
2. 如果编排失败，回退到 PromptEngineeringAgent
    ↓
3. 如果 Agent 失败，回退到 PromptEngine
    ↓
4. 如果都失败，使用编排器的简单策略
    ↓
5. 最终 fallback：返回简单提示词
```

## 功能特点

### 1. 多片段组合

✅ **支持将多个片段组合成一个完整的提示词**

示例：
```python
orchestrator = get_prompt_orchestrator()
prompt = await orchestrator.orchestrate(
    query="你的问题",
    context={"evidence": [...], "query_type": "multi_hop"},
    orchestration_strategy="reasoning_based"
)
# 自动组合：introduction_reasoning + query_section + reasoning_guidance + 
#          reasoning_steps + multi_step_reasoning + evidence_section + 
#          evidence_guidance + answer_requirement + output_format_text
```

### 2. 动态调整

✅ **根据上下文动态选择片段**

- 自动检测是否有证据，添加证据片段
- 自动检测是否有上下文，添加上下文片段
- 自动检测是否是多步骤推理，添加多步骤指导
- 根据查询类型调整策略

### 3. 灵活扩展

✅ **支持自定义片段和策略**

```python
# 添加自定义片段
orchestrator.add_fragment("custom_section", "自定义内容：{query}")

# 注册自定义策略
orchestrator.register_strategy("custom_strategy", [
    "introduction",
    "custom_section",
    "answer_requirement"
])
```

## 使用示例

### 示例1：基础使用

```python
from src.utils.unified_prompt_manager import get_unified_prompt_manager

manager = get_unified_prompt_manager()
prompt = await manager.get_prompt(
    prompt_type="answer_generation",
    query="你的问题",
    context={"evidence": [...]},
    use_orchestration=True  # 启用动态编排
)
```

### 示例2：直接使用编排器

```python
from src.utils.prompt_orchestrator import get_prompt_orchestrator

orchestrator = get_prompt_orchestrator()
prompt = await orchestrator.orchestrate(
    query="你的问题",
    context={
        "evidence": [...],
        "query_type": "multi_hop",
        "is_multi_step": True
    },
    orchestration_strategy="reasoning_based"
)
```

### 示例3：自定义片段和策略

```python
orchestrator = get_prompt_orchestrator()

# 添加自定义片段
orchestrator.add_fragment(
    "custom_instruction",
    "**特殊要求**：{custom_requirement}"
)

# 注册自定义策略
orchestrator.register_strategy("custom", [
    "introduction",
    "query_section",
    "custom_instruction",
    "answer_requirement"
])

# 使用自定义策略
prompt = await orchestrator.orchestrate(
    query="你的问题",
    context={"custom_requirement": "请提供详细分析"},
    orchestration_strategy="custom"
)
```

## 优势

1. **灵活性**：支持多种编排策略，可根据场景选择
2. **可扩展性**：支持自定义片段和策略
3. **智能化**：根据上下文自动调整片段选择
4. **可维护性**：片段化管理，易于维护和更新
5. **向后兼容**：集成到现有系统，不影响现有功能

## 验证

- ✅ 语法检查通过（无 linter 错误）
- ✅ 导入测试通过
- ✅ 片段库初始化成功
- ✅ 策略配置初始化成功

## 文件变更

### 新增文件
- `src/utils/prompt_orchestrator.py` - Prompt 动态编排器

### 修改文件
- `src/utils/unified_prompt_manager.py` - 集成动态编排功能

## 总结

✅ **Prompt 动态编排功能已成功实施**

- 创建了 PromptOrchestrator 类
- 定义了 20+ 个可复用片段
- 实现了 6 种编排策略
- 支持动态调整和自定义扩展
- 集成到 UnifiedPromptManager

系统现在支持 Prompt 动态编排，可以根据上下文和策略灵活组合提示词片段，生成最优的提示词。

