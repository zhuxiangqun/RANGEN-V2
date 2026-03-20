# RealReasoningEngine 重构方案

## 当前问题
- 文件过大：17019行，189个方法
- 职责过多：包含推理、证据处理、子查询、上下文、提示词、答案提取、学习机制等多个职责
- 难以维护：代码耦合度高，修改影响面大
- 违反单一职责原则

## 重构目标
1. 将大文件拆分成多个职责单一的模块
2. 保持向后兼容性
3. 遵循DRY原则，避免代码重复
4. 提高代码可维护性和可测试性

## 模块拆分方案

### 1. 核心模块结构

```
src/core/reasoning/
├── __init__.py
├── engine.py                    # RealReasoningEngine (主入口，协调各模块)
├── step_generator.py            # 推理步骤生成 (31个方法)
├── evidence_processor.py        # 证据处理 (19个方法)
├── subquery_processor.py        # 子查询处理 (36个方法)
├── context_manager.py           # 上下文工程 (5个方法)
├── prompt_generator.py          # 提示词生成 (12个方法)
├── answer_extractor.py          # 答案提取 (18个方法)
├── learning_manager.py          # 学习机制 (17个方法)
├── cache_manager.py             # 缓存管理 (3个方法)
└── utils.py                     # 工具函数 (36个其他方法)
```

### 2. 模块职责划分

#### 2.1 `engine.py` - 主引擎（协调器）
**职责**：
- 初始化各个子模块
- 协调各模块之间的交互
- 提供主要的 `reason()` 方法
- 管理推理流程

**方法**：
- `__init__()` - 初始化所有子模块
- `reason()` - 主推理方法（协调各模块）
- `learn_from_result()` - 委托给 learning_manager
- `get_learning_insights()` - 委托给 learning_manager

#### 2.2 `step_generator.py` - 推理步骤生成器
**职责**：
- 生成推理步骤
- 验证和优化推理步骤
- 管理推理步骤模板

**方法**：
- `generate_reasoning_steps()`
- `_execute_reasoning_steps_with_prompts()`
- `_validate_reasoning_steps()`
- `_optimize_reasoning_chain()`
- `_register_reasoning_templates()`
- 其他31个相关方法

#### 2.3 `evidence_processor.py` - 证据处理器
**职责**：
- 收集证据
- 处理证据（过滤、排序、分配）
- 评估证据质量

**方法**：
- `gather_evidence()`
- `_gather_evidence_for_step()`
- `_process_evidence_intelligently()`
- `_process_evidence_for_prompt()`
- `_allocate_evidence_for_step()`
- `_filter_relevant_previous_evidence()`
- `_can_reuse_previous_evidence()`
- 其他19个相关方法

#### 2.4 `subquery_processor.py` - 子查询处理器
**职责**：
- 提取子查询
- 简化复杂子查询
- 增强子查询（使用上下文）

**方法**：
- `extract_sub_query()`
- `_simplify_complex_sub_query()`
- `_extract_retrievable_sub_query_from_original_query()`
- `_enhance_sub_query_with_context_engineering()`
- `_enhance_sub_query_with_previous_results()`
- `_extract_executable_sub_query()`
- 其他36个相关方法

#### 2.5 `context_manager.py` - 上下文管理器
**职责**：
- 管理推理链上下文
- 生成上下文摘要
- 提取上下文关键词

**方法**：
- `get_enhanced_context()`
- `add_context_fragment()`
- `_generate_context_summary_with_nlp()`
- `_generate_simple_context_summary()`
- `_extract_context_keywords_with_nlp()`
- 其他5个相关方法

#### 2.6 `prompt_generator.py` - 提示词生成器
**职责**：
- 生成优化提示词
- 管理提示词模板
- 根据查询类型选择模板

**方法**：
- `generate_prompt()`
- `_generate_optimized_prompt()`
- `_get_answer_format_instruction()`
- `_get_fallback_prompt()`
- `_select_optimal_template()`
- `_analyze_template_performance()`
- 其他12个相关方法

#### 2.7 `answer_extractor.py` - 答案提取器
**职责**：
- 从推理结果中提取答案
- 验证答案正确性
- 清理和格式化答案

**方法**：
- `extract_answer()`
- `_derive_final_answer_with_ml()`
- `_extract_step_result_with_context_engineering()`
- `_extract_step_result_with_context()`
- `_validate_answer_comprehensively_with_llm()`
- `_clean_answer_text()`
- 其他18个相关方法

#### 2.8 `learning_manager.py` - 学习管理器
**职责**：
- 管理学习数据
- 应用学习到的优化策略
- 与自适应优化器、贝叶斯优化器、RL优化器交互

**方法**：
- `learn_from_result()`
- `get_learning_insights()`
- `apply_learned_insights()`
- `_update_adaptive_weights()`
- `_get_learned_model_selection()`
- `_check_and_run_bayesian_optimization()`
- 其他17个相关方法

#### 2.9 `cache_manager.py` - 缓存管理器
**职责**：
- 管理LLM调用缓存
- 缓存键生成
- 缓存清理

**方法**：
- `get_cache_key()`
- `call_llm_with_cache()`
- `_cleanup_expired_cache()`

#### 2.10 `utils.py` - 工具函数
**职责**：
- 提供通用工具函数
- 查询特征提取
- 置信度计算
- 其他辅助功能

**方法**：
- `_extract_query_features()`
- `_calculate_confidence_intelligently()`
- `_detect_answer_type()`
- 其他36个工具方法

### 3. 数据类定义

将数据类移到独立文件：
```
src/core/reasoning/
└── models.py                    # 数据类定义
    - ReasoningStepType
    - Evidence
    - ReasoningStep
    - ReasoningResult
```

### 4. 重构步骤

#### 阶段1：创建模块结构（不破坏现有功能）
1. 创建 `src/core/reasoning/` 目录
2. 创建各个模块文件（空实现或最小实现）
3. 将数据类移到 `models.py`

#### 阶段2：逐步迁移功能
1. 先迁移独立的工具函数（utils.py）
2. 迁移缓存管理（cache_manager.py）
3. 迁移上下文管理（context_manager.py）
4. 迁移子查询处理（subquery_processor.py）
5. 迁移证据处理（evidence_processor.py）
6. 迁移提示词生成（prompt_generator.py）
7. 迁移答案提取（answer_extractor.py）
8. 迁移学习机制（learning_manager.py）
9. 迁移推理步骤生成（step_generator.py）
10. 最后重构主引擎（engine.py）

#### 阶段3：测试和优化
1. 确保所有功能正常工作
2. 优化模块间的接口
3. 添加单元测试
4. 性能测试

### 5. 接口设计原则

1. **依赖注入**：各模块通过构造函数接收依赖
2. **接口隔离**：每个模块只暴露必要的公共方法
3. **单一职责**：每个模块只负责一个明确的功能领域
4. **向后兼容**：保持 `RealReasoningEngine` 的公共接口不变

### 6. 示例代码结构

```python
# src/core/reasoning/engine.py
class RealReasoningEngine:
    def __init__(self):
        self.step_generator = StepGenerator(...)
        self.evidence_processor = EvidenceProcessor(...)
        self.subquery_processor = SubQueryProcessor(...)
        self.context_manager = ContextManager(...)
        self.prompt_generator = PromptGenerator(...)
        self.answer_extractor = AnswerExtractor(...)
        self.learning_manager = LearningManager(...)
        self.cache_manager = CacheManager(...)
    
    async def reason(self, query: str, context: Dict, session_id: Optional[str] = None):
        # 协调各模块完成推理
        steps = await self.step_generator.generate(query, context)
        evidence = await self.evidence_processor.gather(query, steps)
        answer = await self.answer_extractor.extract(steps, evidence)
        return ReasoningResult(...)
```

### 7. 注意事项

1. **保持向后兼容**：现有的 `RealReasoningEngine` 接口保持不变
2. **避免循环依赖**：模块之间通过接口交互，避免直接依赖
3. **统一配置**：使用统一配置中心管理配置
4. **日志统一**：使用统一的日志系统
5. **错误处理**：统一的错误处理机制

### 8. 预期收益

1. **可维护性提升**：每个模块职责单一，易于理解和修改
2. **可测试性提升**：可以独立测试每个模块
3. **可扩展性提升**：新功能可以作为新模块添加
4. **代码复用**：模块可以在其他地方复用
5. **团队协作**：不同开发者可以并行开发不同模块

