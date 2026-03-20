# 核心系统LLM使用情况分析

## 总结

**核心系统全部使用DeepSeek**，但根据任务复杂度使用了**两个不同的DeepSeek模型**：
- `deepseek-reasoner` - 用于复杂推理任务（响应时间：100-180秒）
- `deepseek-chat` - 用于简单快速任务（响应时间：3-10秒）

## LLM调用位置详细清单

### 1. **`src/core/real_reasoning_engine.py`**

#### 1.1 核心推理LLM调用
**位置**: `_derive_final_answer_with_ml()` (Line 1640-1756)
- **模型**: 根据任务复杂度智能选择
  - 简单任务 → `deepseek-chat` (通过 `fast_llm_integration`)
  - 复杂任务 → `deepseek-reasoner` (通过 `llm_integration`)
- **选择策略**: `_select_llm_for_task()` 方法
- **调用方式**: `llm_to_use._call_llm(prompt)`
- **用途**: 推导最终答案（有证据/无证据两种情况）

#### 1.2 证据生成LLM调用
**位置**: `_get_builtin_evidence()` (Line 1328-1385)
- **模型**: `deepseek-chat` (通过 `fast_llm_integration`)
- **调用方式**: `llm_to_use._call_llm(prompt)`
- **用途**: 生成内置证据（使用 `evidence_generation` 模板）

#### 1.3 推理步骤生成LLM调用
**位置**: `_execute_reasoning_steps_with_prompts()` (Line 1589)
- **模型**: `deepseek-chat` (通过 `fast_llm_integration` 或 `llm_integration`)
- **调用方式**: `llm_to_use._call_llm(prompt)`
- **用途**: 生成多个推理步骤（使用 `reasoning_steps_generation` 模板）

#### 1.4 答案提取LLM调用
**位置**: `_extract_answer_with_llm()` (Line 1187)
- **模型**: `deepseek-reasoner` (通过 `llm_integration`)
- **调用方式**: `self.llm_integration._call_llm(prompt)`
- **用途**: 从内容中提取答案

#### 1.5 查询类型分类LLM调用
**位置**: `_analyze_query_type_with_ml()` (通过 `UnifiedClassificationService`)
- **模型**: `deepseek-chat` (通过 `fast_llm_integration`)
- **调用方式**: 通过 `UnifiedClassificationService.classify()`
- **用途**: 分类查询类型（factual, numerical, temporal等）

#### 1.6 推理步骤类型分类LLM调用
**位置**: `ReasoningStepType.generate_step_type()` (通过 `UnifiedClassificationService`)
- **模型**: `deepseek-chat` (通过 `fast_llm_integration`)
- **调用方式**: 通过 `UnifiedClassificationService.classify()`
- **用途**: 分类推理步骤类型

**LLM集成初始化** (Line 250-285):
- `self.llm_integration`: `deepseek-reasoner`
- `self.fast_llm_integration`: `deepseek-chat`

### 2. **`src/core/frames_processor.py`**

#### 2.1 问题类型分类LLM调用
**位置**: `_identify_problem_type()` (通过 `UnifiedClassificationService`)
- **模型**: `deepseek-chat` (通过 `fast_llm_integration`)
- **调用方式**: 通过 `UnifiedClassificationService.classify()`
- **用途**: 分类FRAMES问题类型

#### 2.2 默认推理LLM调用
**位置**: `_execute_default_reasoning()` (Line 1778)
- **模型**: `deepseek-reasoner`
- **调用方式**: `llm_integration._call_llm(prompt)`
- **用途**: 执行FRAMES问题的默认推理

**LLM集成初始化** (Line 136-164):
- `self.llm_integration`: `deepseek-reasoner`
- `self.fast_llm_integration`: `deepseek-chat`

### 3. **`src/core/multi_hop_reasoning.py`**

#### 3.1 推理类型分类LLM调用
**位置**: `_identify_reasoning_type()` (通过 `UnifiedClassificationService`)
- **模型**: `deepseek-chat` (通过 `fast_llm_integration`)
- **调用方式**: 通过 `UnifiedClassificationService.classify()`
- **用途**: 分类多跳推理类型

**LLM集成初始化** (Line 80-106):
- `self.fast_llm_integration`: `deepseek-chat`

### 4. **`src/core/llm_integration.py`**

#### 4.1 核心LLM调用接口
**位置**: `_call_llm()` (Line 249-255)
- **实现**: 强制使用DeepSeek（无论配置如何）
- **方法**: `_call_deepseek()`

#### 4.2 具体LLM方法调用
所有通过 `LLMIntegration` 实例的方法都最终调用 `_call_deepseek()`:
- `detect_person_content()` → `_call_llm()` → `_call_deepseek()`
- `detect_location_content()` → `_call_llm()` → `_call_deepseek()`
- `extract_answer()` → `_call_llm()` → `_call_deepseek()`
- `classify_query()` → `_call_llm()` → `_call_deepseek()`
- `calculate_relevance()` → `_call_llm()` → `_call_deepseek()`
- `validate_answer()` → `_call_llm()` → `_call_deepseek()`
- `generate_reasoning()` → `_call_llm()` → `_call_deepseek()`

## 模型选择策略

### 策略实现位置
**文件**: `src/core/real_reasoning_engine.py`
**方法**: `_select_llm_for_task()` (Line 2091-2135)

### 选择规则

```python
简单任务 → deepseek-chat (fast_llm_integration)
  ├─ 查询类型: factual, numerical (简单数值查询)
  ├─ 查询长度 < 50字符
  ├─ 证据数量 <= 1
  └─ 响应时间: 3-10秒

复杂任务 → deepseek-reasoner (llm_integration)
  ├─ 查询类型: temporal, causal, comparative, general
  ├─ 查询长度 >= 50字符
  ├─ 证据数量 > 1
  ├─ 需要多步推理
  └─ 响应时间: 100-180秒
```

### 具体逻辑

```python
def _select_llm_for_task(self, query: str, evidence: List[Evidence], query_type: str):
    fast_llm = getattr(self, 'fast_llm_integration', None)
    
    # 简单任务使用快速模型
    if query_type in ['factual', 'numerical']:
        if len(query) < 50 and len(evidence) <= 1:
            return fast_llm or self.llm_integration
    
    # 复杂任务使用推理模型
    return self.llm_integration
```

## LLM使用统计

### 按模块分类

| 模块 | LLM调用次数 | 主要用途 | 使用的模型 |
|------|------------|---------|-----------|
| `real_reasoning_engine.py` | 6+ | 推理、证据生成、分类、答案提取 | `deepseek-chat` + `deepseek-reasoner` |
| `frames_processor.py` | 2 | 问题分类、推理 | `deepseek-chat` + `deepseek-reasoner` |
| `multi_hop_reasoning.py` | 1 | 推理类型分类 | `deepseek-chat` |
| `llm_integration.py` | 7+ | 检测、提取、分类、验证、生成 | 根据实例配置（通常是`deepseek-reasoner`或`deepseek-chat`） |

### 按用途分类

| 用途 | 使用位置 | 模型 | 响应时间 |
|------|---------|------|----------|
| **核心推理** | `_derive_final_answer_with_ml()` | 智能选择 | 3-10秒 或 100-180秒 |
| **证据生成** | `_get_builtin_evidence()` | `deepseek-chat` | 3-10秒 |
| **推理步骤生成** | `_execute_reasoning_steps_with_prompts()` | `deepseek-chat` | 3-10秒 |
| **类型分类** | `UnifiedClassificationService` | `deepseek-chat` | 3-10秒 |
| **答案提取** | `_extract_answer_with_llm()` | `deepseek-reasoner` | 100-180秒 |
| **FRAMES推理** | `_execute_default_reasoning()` | `deepseek-reasoner` | 100-180秒 |
| **内容检测** | `detect_person_content()`, `detect_location_content()` | 根据实例配置 | 3-10秒 |
| **相关性计算** | `calculate_relevance()` | 根据实例配置 | 3-10秒 |
| **答案验证** | `validate_answer()` | 根据实例配置 | 100-180秒 |

## 模型配置

### 所有模块都使用DeepSeek

1. **提供商**: `'deepseek'` (硬编码，不可更改)
2. **API端点**: `https://api.deepseek.com/v1` (默认)
3. **环境变量**:
   - `DEEPSEEK_API_KEY`: API密钥
   - `DEEPSEEK_MODEL`: 推理模型（默认: `deepseek-reasoner`）
   - `DEEPSEEK_FAST_MODEL`: 快速模型（默认: `deepseek-chat`）
   - `DEEPSEEK_BASE_URL`: API基础URL（默认: `https://api.deepseek.com/v1`）

### 模型选择逻辑

```python
# 在 _call_llm() 中强制使用DeepSeek
def _call_llm(self, prompt: str) -> str:
    if self.llm_provider == 'deepseek':
        return self._call_deepseek(prompt)
    else:
        # 即使配置了其他提供商，也强制使用DeepSeek
        self.logger.warning(f"Non-DeepSeek provider detected: {self.llm_provider}, forcing DeepSeek")
        return self._call_deepseek(prompt)
```

## 关键发现

### ✅ 所有LLM调用都是DeepSeek
- 没有使用其他提供商（OpenAI、Claude等，虽然有代码但未使用）
- `_call_llm()` 方法强制使用 `_call_deepseek()`

### ✅ 智能模型选择
- 简单任务使用 `deepseek-chat`（快速）
- 复杂任务使用 `deepseek-reasoner`（推理能力强）

### ✅ 双模型策略
每个模块通常初始化两个LLM集成实例：
- `llm_integration`: 推理模型
- `fast_llm_integration`: 快速模型

### ⚠️ 注意
- 虽然代码中保留了 `_call_openai()` 和 `_call_claude()` 方法，但它们从未被调用
- 系统完全依赖DeepSeek API

## LLM调用流程图

```
用户查询
    ↓
RealReasoningEngine.reason()
    ├─> 查询类型分类 (fast_llm: deepseek-chat)
    ├─> 证据生成 (fast_llm: deepseek-chat)
    ├─> 推理步骤生成 (fast_llm: deepseek-chat)
    └─> 最终答案推导 (智能选择: deepseek-chat 或 deepseek-reasoner)
        └─> _select_llm_for_task()
            ├─> 简单任务 → fast_llm (deepseek-chat)
            └─> 复杂任务 → llm_integration (deepseek-reasoner)
```

## 结论

**核心系统完全使用DeepSeek**，通过智能模型选择策略，根据任务复杂度选择：
- **快速模型** (`deepseek-chat`): 用于分类、简单推理、证据生成等快速任务
- **推理模型** (`deepseek-reasoner`): 用于复杂推理、多步推理等需要强推理能力的任务

这种设计在保证性能的同时，充分利用了不同模型的优势。

