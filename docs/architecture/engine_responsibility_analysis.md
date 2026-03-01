# `engine.py` 职责划分分析

## 问题描述

`src/core/reasoning/engine.py` 的职责应该是**协调各个子模块**，但目前包含大量**具体处理逻辑**，违反了单一职责原则。

## 当前问题

### 1. 文件注释与实际不符
```python
"""
推理引擎主模块 - 协调各个子模块
"""
```
但实际包含大量具体处理逻辑。

### 2. 方法分类分析

#### ✅ **应该保留在 `engine.py`（协调逻辑）**

| 方法 | 行号 | 职责 | 说明 |
|------|------|------|------|
| `__init__` | 36 | 初始化各个子模块 | ✅ 协调职责 |
| `reason` | 426 | 主入口，协调整个推理流程 | ✅ 协调职责 |
| `_initialize_*` | 258-401 | 初始化各个子模块 | ✅ 协调职责 |
| `_execute_reasoning_steps` | ~800-1000 | 执行推理步骤，协调各个子模块 | ✅ 协调职责 |
| `_initialize_reasoning_context` | 2001 | 初始化推理上下文 | ✅ 协调职责 |
| `_analyze_query_type` | 2043 | 分析查询类型（可能应该移到子模块） | ⚠️ 边界情况 |
| `_generate_reasoning_steps` | 2080 | 生成推理步骤（调用step_generator） | ✅ 协调职责 |
| `_validate_and_decompose_steps` | 2132 | 验证和分解步骤（调用step_generator） | ✅ 协调职责 |
| `learn_from_result` | 4002 | 学习管理（调用learning_manager） | ✅ 协调职责 |
| `get_learning_insights` | 4006 | 获取学习洞察（调用learning_manager） | ✅ 协调职责 |
| `apply_learned_insights` | 4010 | 应用学习洞察（调用learning_manager） | ✅ 协调职责 |
| `_trigger_online_learning` | 4014 | 触发在线学习（调用learning_manager） | ✅ 协调职责 |
| `_auto_register_ml_components` | 4037 | 自动注册ML组件（协调职责） | ✅ 协调职责 |

#### ❌ **应该移到子模块（具体处理逻辑）**

| 方法 | 行号 | 当前职责 | 应该移到 | 原因 |
|------|------|----------|----------|------|
| `_extract_answer_direct` | 2160-2519 | 直接使用LLM从证据中提取答案 | `AnswerExtractor` 或 `UnifiedEvidenceFramework` | 这是答案提取的具体实现，不是协调逻辑 |
| `_verify_and_correct_answer` | 2521-2587 | 验证和修正答案 | `FactVerificationService` | 已经使用了 `FactVerificationService`，但方法本身应该在验证服务中 |
| `_validate_step_answer_reasonableness` | 2589-2863 | 验证步骤答案的合理性 | `AnswerValidator` | 这是答案验证的具体实现，应该放在验证器中 |
| `_analyze_step_dependencies` | 2865-3066 | 分析步骤依赖关系 | `StepGenerator` | 这是步骤生成的具体逻辑，应该放在步骤生成器中 |
| `_attempt_step_answer_recovery` | 3068-3168 | 尝试恢复步骤答案 | `AnswerExtractor` | 这是答案提取的恢复策略，应该放在答案提取器中 |
| `_validate_replacement_context_match` | 3170-3284 | 验证替换值上下文匹配 | `SubQueryProcessor` | 这是子查询处理的具体逻辑，应该放在子查询处理器中 |
| `_analyze_placeholder_context` | 3286-3336 | 分析占位符上下文 | `SubQueryProcessor` | 这是子查询处理的具体逻辑 |
| `_analyze_context_mismatch` | 3338-3391 | 分析上下文不匹配 | `SubQueryProcessor` | 这是子查询处理的具体逻辑 |
| `_validate_reasoning_chain_consistency` | 3393-3466 | 验证推理链一致性 | `StepGenerator` | 这是步骤生成的具体逻辑 |
| `_attempt_reasoning_chain_correction` | 3468-3623 | 尝试推理链修正 | `StepGenerator` | 这是步骤生成的具体逻辑 |
| `_attempt_robust_evidence_retrieval` | 3625-3739 | 尝试多种检索策略 | `EvidenceProcessor` | 这是证据检索的具体逻辑 |
| `_generate_query_variants` | 3741-3770 | 生成查询变体 | `EvidenceProcessor` | 这是证据检索的具体逻辑 |
| `_attempt_commonsense_reasoning` | 3772-3838 | 尝试常识推理 | `AnswerExtractor` | 这是答案提取的备选策略 |
| `_is_complex_step` | 3840-3921 | 判断步骤复杂度 | `StepGenerator` | 这是步骤生成的具体逻辑 |
| `_decompose_complex_step` | 3923-4000 | 分解复杂步骤 | `StepGenerator` | 这是步骤生成的具体逻辑 |
| `_extract_answer_generic` | 4127-4144 | 通用答案提取（代理方法） | `AnswerExtractor` | 这是答案提取的具体逻辑 |

## 重构建议

### 阶段1：高优先级（核心功能）

1. **答案提取相关** → `AnswerExtractor`
   - `_extract_answer_direct` → `AnswerExtractor.extract_answer_direct`
   - `_attempt_step_answer_recovery` → `AnswerExtractor.attempt_recovery`
   - `_attempt_commonsense_reasoning` → `AnswerExtractor.attempt_commonsense_reasoning`
   - `_extract_answer_generic` → `AnswerExtractor.extract_answer_generic`（已经是代理方法，可以直接删除）

2. **答案验证相关** → `AnswerValidator`
   - `_validate_step_answer_reasonableness` → `AnswerValidator.validate_step_answer_reasonableness`
   - `_verify_and_correct_answer` → `FactVerificationService.verify_and_correct`（已经使用，可以删除包装方法）

### 阶段2：中优先级（步骤生成）

3. **步骤生成相关** → `StepGenerator`
   - `_analyze_step_dependencies` → `StepGenerator.analyze_dependencies`
   - `_validate_reasoning_chain_consistency` → `StepGenerator.validate_chain_consistency`
   - `_attempt_reasoning_chain_correction` → `StepGenerator.attempt_correction`
   - `_is_complex_step` → `StepGenerator.is_complex_step`
   - `_decompose_complex_step` → `StepGenerator.decompose_complex_step`

### 阶段3：低优先级（子查询和证据）

4. **子查询处理相关** → `SubQueryProcessor`
   - `_validate_replacement_context_match` → `SubQueryProcessor.validate_replacement_context`
   - `_analyze_placeholder_context` → `SubQueryProcessor.analyze_placeholder_context`
   - `_analyze_context_mismatch` → `SubQueryProcessor.analyze_context_mismatch`

5. **证据检索相关** → `EvidenceProcessor`
   - `_attempt_robust_evidence_retrieval` → `EvidenceProcessor.attempt_robust_retrieval`
   - `_generate_query_variants` → `EvidenceProcessor.generate_query_variants`

## 重构后的架构

### `engine.py` 的职责（协调层）

```python
class RealReasoningEngine:
    """推理引擎 - 协调各个子模块"""
    
    async def reason(self, query: str, ...):
        """主入口：协调整个推理流程"""
        # 1. 初始化上下文
        context = await self._initialize_reasoning_context(...)
        
        # 2. 生成推理步骤（委托给StepGenerator）
        steps = await self.step_generator.generate_steps(...)
        
        # 3. 执行推理步骤（协调各个子模块）
        for step in steps:
            # 3.1 检索证据（委托给EvidenceProcessor）
            evidence = await self.evidence_processor.gather_evidence(...)
            
            # 3.2 提取答案（委托给AnswerExtractor）
            answer = await self.answer_extractor.extract_answer(...)
            
            # 3.3 验证答案（委托给AnswerValidator）
            is_valid = self.answer_validator.validate(...)
        
        # 4. 生成最终答案
        final_answer = self._derive_final_answer(...)
        
        return ReasoningResult(...)
```

### 子模块的职责（处理层）

- **`StepGenerator`**: 步骤生成、依赖分析、复杂度判断、步骤分解
- **`EvidenceProcessor`**: 证据检索、查询变体生成、多种检索策略
- **`AnswerExtractor`**: 答案提取、答案恢复、常识推理
- **`AnswerValidator`**: 答案验证、合理性检查
- **`SubQueryProcessor`**: 子查询处理、占位符替换、上下文验证
- **`FactVerificationService`**: 事实验证和修正

## 重构收益

1. **单一职责原则**: 每个模块只负责自己的职责
2. **可维护性**: 修改某个功能时，只需要修改对应的子模块
3. **可测试性**: 每个子模块可以独立测试
4. **可扩展性**: 添加新功能时，只需要扩展对应的子模块
5. **代码复用**: 子模块的方法可以被其他模块复用

## 实施步骤

1. **创建TODO列表**: 列出所有需要重构的方法
2. **逐个迁移**: 按照优先级逐个迁移方法
3. **更新调用**: 更新 `engine.py` 中的调用
4. **测试验证**: 确保重构后功能正常
5. **清理代码**: 删除 `engine.py` 中的旧方法

## 注意事项

1. **向后兼容**: 确保重构后不影响现有功能
2. **依赖关系**: 注意子模块之间的依赖关系
3. **测试覆盖**: 确保每个迁移的方法都有测试覆盖
4. **文档更新**: 更新相关文档和注释

