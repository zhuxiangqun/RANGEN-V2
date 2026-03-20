# StepGenerator 重构计划

## 🎯 当前问题分析

### 📊 规模统计
- **总行数**: 4,180+ 行
- **方法数量**: 48+ 个
- **职责范围**: 生成、验证、缓存、优化、复杂度分析、错误处理

### 🔍 核心问题

#### 1. 责任混杂 (Violation of Single Responsibility Principle)
```
当前: StepGenerator 同时处理
├── 步骤生成 (Primary)
├── 语义验证
├── 格式验证
├── 缓存管理
├── 并行检测
├── 复杂度判断
├── 依赖分析
└── 自我修正
```

#### 2. 硬编码验证逻辑 (Lack of Flexibility)
```python
# 硬编码的验证规则 - 难以维护和扩展
irrelevant_keywords = ['novel', 'book', 'movie', 'film', 'award', 'actor', 'actress', 'author', 'writer']
```

#### 3. 过度复杂的错误处理 (Complex Error Handling)
- 多层级嵌套错误处理
- 逻辑路径复杂
- 调试困难

#### 4. 缺乏清晰的模块边界 (Poor Module Boundaries)
```python
def _validate_reasoning_relevance(self, steps, query):
    # 这个方法包含了多个验证策略，应该拆分
    self._validate_semantic_relevance()
    self._validate_topic_consistency()
    self._validate_reasoning_chain_integrity()
```

## 🛠 重构方案

### 方案A：模块化重构 (推荐)

```python
# 新的架构
class StepGeneratorCoordinator:  # 原StepGenerator重命名为协调者
    def __init__(self, validators, generators, optimizers):
        self.validators = validators
        self.generators = generators
        self.optimizers = optimizers

    def generate_reasoning_steps(self, query):
        # 1. 分析查询
        analysis = self.query_analyzer.analyze(query)

        # 2. 选择生成策略
        strategy = self.strategy_selector.select(analysis)

        # 3. 生成步骤
        steps = strategy.generate_steps(query, analysis)

        # 4. 验证步骤
        validation_result = self.validator.validate(steps, query)

        # 5. 优化步骤
        optimized_steps = self.optimizer.optimize(steps, analysis)

        return optimized_steps
```

### 方案B：渐进式重构 (当前推荐)

## 📋 实施计划

### Phase 1: 紧急修复 (1-2天) ✅
**目标**: 解决最严重的问题，保证基本功能正常

#### 1.1 提取验证逻辑
```python
class StepValidator:
    def __init__(self, semantic_validator, topic_validator, chain_validator):
        self.semantic_validator = semantic_validator
        self.topic_validator = topic_validator
        self.chain_validator = chain_validator

    def validate(self, steps, query):
        results = []
        results.append(self.semantic_validator.validate(steps, query))
        results.append(self.topic_validator.validate(steps, query))
        results.append(self.chain_validator.validate(steps, query))
        return self._aggregate_results(results)

class SemanticRelevanceValidator:
    def validate(self, steps, query):
        # 语义相关性验证逻辑
        pass

class TopicConsistencyValidator:
    def validate(self, steps, query):
        # 主题一致性验证逻辑
        pass

class ReasoningChainValidator:
    def validate(self, steps, query):
        # 推理链完整性验证逻辑
        pass
```

#### 1.2 简化主流程
```python
def generate_reasoning_steps(self, query: str, context=None, max_retries=1):
    """简化的主入口"""
    try:
        # 尝试主路径
        steps = self._try_main_generation(query)
        if steps and self.validator.validate(steps, query).is_valid:
            return steps

        # 尝试fallback
        steps = self._try_fallback_generation(query)
        if steps and self.validator.validate(steps, query).is_valid:
            return steps

        # 返回最小可用步骤
        return self._generate_minimal_steps(query)

    except Exception as e:
        logger.error(f"步骤生成失败: {e}")
        return self._generate_emergency_steps(query)
```

### Phase 2: 核心抽象 (3-5天)

#### 2.1 创建LLM交互抽象
```python
class LLMInteractionManager:
    """统一的LLM调用管理器"""

    def __init__(self, primary_llm, fallback_llm=None, cache_manager=None):
        self.primary_llm = primary_llm
        self.fallback_llm = fallback_llm
        self.cache_manager = cache_manager

    def call_with_cache(self, prompt, cache_key=None):
        """带缓存的LLM调用"""
        if self.cache_manager and cache_key:
            cached = self.cache_manager.get(cache_key)
            if cached:
                return cached

        try:
            result = self._call_llm(prompt)
            if self.cache_manager and cache_key:
                self.cache_manager.set(cache_key, result)
            return result
        except Exception as e:
            if self.fallback_llm:
                return self.fallback_llm.call(prompt)
            raise

    def _call_llm(self, prompt):
        """统一的LLM调用接口"""
        # 支持多种LLM接口
        methods = ['generate', '_call_llm', 'call']
        for method in methods:
            if hasattr(self.primary_llm, method):
                func = getattr(self.primary_llm, method)
                try:
                    return func(prompt)
                except Exception:
                    continue
        raise RuntimeError("No compatible LLM method found")
```

#### 2.2 创建提示词模板管理器
```python
from jinja2 import Template

class PromptTemplateManager:
    """提示词模板管理器"""

    def __init__(self):
        self.templates = {}

    def load_template(self, name, template_str):
        """加载模板"""
        self.templates[name] = Template(template_str)

    def render(self, name, **kwargs):
        """渲染模板"""
        if name not in self.templates:
            raise ValueError(f"Template {name} not found")
        return self.templates[name].render(**kwargs)

# 使用示例
prompt_manager = PromptTemplateManager()
prompt_manager.load_template('step_generation', """
You are an expert reasoning planner...
Query: {{ query }}
Context: {{ context }}
...
""")

prompt = prompt_manager.render('step_generation', query=user_query, context=context)
```

### Phase 3: 策略模式重构 (1-2周)

#### 3.1 创建生成策略
```python
from abc import ABC, abstractmethod

class StepGenerationStrategy(ABC):
    """步骤生成策略基类"""

    @abstractmethod
    def can_handle(self, query_analysis):
        """判断是否能处理此查询"""
        pass

    @abstractmethod
    def generate_steps(self, query, analysis):
        """生成步骤"""
        pass

class SimpleQueryStrategy(StepGenerationStrategy):
    """简单查询策略"""

    def can_handle(self, analysis):
        return analysis.complexity_score <= 3.0

    def generate_steps(self, query, analysis):
        # 简单查询的生成逻辑
        return [{"type": "direct_answer", "sub_query": query}]

class ComplexQueryStrategy(StepGenerationStrategy):
    """复杂查询策略"""

    def can_handle(self, analysis):
        return analysis.complexity_score > 3.0

    def generate_steps(self, query, analysis):
        # 复杂查询的生成逻辑
        return self._generate_multi_step_reasoning(query, analysis)

class StepGenerationStrategySelector:
    """策略选择器"""

    def __init__(self, strategies):
        self.strategies = strategies

    def select(self, analysis):
        """选择合适的策略"""
        for strategy in self.strategies:
            if strategy.can_handle(analysis):
                return strategy
        return self.strategies[-1]  # 默认使用最后一个策略
```

### Phase 4: 完整模块化 (2-4周)

#### 4.1 创建独立模块
```
src/core/reasoning/
├── generators/
│   ├── __init__.py
│   ├── base_generator.py
│   ├── llm_generator.py
│   ├── rule_based_generator.py
│   └── fallback_generator.py
├── validators/
│   ├── __init__.py
│   ├── base_validator.py
│   ├── semantic_validator.py
│   ├── schema_validator.py
│   └── hallucination_detector.py
├── optimizers/
│   ├── __init__.py
│   ├── step_optimizer.py
│   └── dependency_analyzer.py
├── strategies/
│   ├── __init__.py
│   ├── generation_strategies.py
│   └── selection_strategy.py
├── managers/
│   ├── __init__.py
│   ├── llm_manager.py
│   ├── prompt_manager.py
│   └── cache_manager.py
└── coordinator.py  # 原StepGenerator
```

#### 4.2 重构后的协调器
```python
class StepGenerationCoordinator:
    """步骤生成协调器"""

    def __init__(self,
                 strategy_selector,
                 generators,
                 validators,
                 optimizers,
                 llm_manager,
                 prompt_manager):

        self.strategy_selector = strategy_selector
        self.generators = generators
        self.validators = validators
        self.optimizers = optimizers
        self.llm_manager = llm_manager
        self.prompt_manager = prompt_manager

    def generate_steps(self, query):
        """协调生成过程"""
        # 1. 分析查询
        analysis = self._analyze_query(query)

        # 2. 选择策略
        strategy = self.strategy_selector.select(analysis)

        # 3. 生成步骤
        steps = strategy.generate_steps(query, analysis)

        # 4. 验证步骤
        validation_results = []
        for validator in self.validators:
            result = validator.validate(steps, query)
            validation_results.append(result)

        # 5. 优化步骤
        if all(r.is_valid for r in validation_results):
            for optimizer in self.optimizers:
                steps = optimizer.optimize(steps, analysis)

        return steps
```

## 📅 实施时间表

### Week 1: 紧急修复
- [x] 提取验证逻辑到独立类
- [x] 简化主流程错误处理
- [ ] 添加架构警告注释
- [ ] 创建基本测试覆盖

### Week 2-3: 核心抽象
- [ ] 创建LLMInteractionManager
- [ ] 创建PromptTemplateManager
- [ ] 重构缓存逻辑
- [ ] 更新依赖注入

### Week 4-6: 策略模式
- [ ] 实现StepGenerationStrategy
- [ ] 创建StrategySelector
- [ ] 重构生成逻辑
- [ ] 添加新策略支持

### Week 7-10: 完整模块化
- [ ] 创建独立模块目录结构
- [ ] 迁移现有代码
- [ ] 更新所有引用
- [ ] 完整测试验证

## 🎯 成功标准

### 功能完整性
- [ ] 所有现有功能正常工作
- [ ] API接口保持兼容
- [ ] 错误处理完善

### 代码质量
- [ ] 每个类职责单一
- [ ] 单元测试覆盖率 > 80%
- [ ] 代码重复度 < 10%
- [ ] 圈复杂度 < 10

### 可维护性
- [ ] 新功能开发时间减少50%
- [ ] Bug修复时间减少70%
- [ ] 代码审查效率提升

## 🚨 风险控制

### 技术风险
1. **回归风险**: 建立完整的集成测试套件
2. **性能风险**: 添加性能监控和基准测试
3. **兼容性风险**: 创建API兼容层

### 组织风险
1. **学习曲线**: 分阶段实施，逐步迁移
2. **团队协调**: 建立代码审查和结对编程机制
3. **进度风险**: 设置里程碑和检查点

## 📈 预期收益

### 短期收益 (3个月内)
- 代码可读性提升60%
- 新功能开发速度提升40%
- Bug修复效率提升50%

### 长期收益 (6个月后)
- 系统稳定性显著提升
- 维护成本降低70%
- 团队开发效率提升100%
- 技术债务大幅减少

---

**结论**: 这个重构是必要的，将带来长期的代码质量和开发效率提升。虽然需要投入时间，但收益远大于成本。
