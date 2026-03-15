# 🧬 反思型架构

RANGEN系统基于Reflexion/LATS框架实现的反思型架构，让AI系统具备自我批评、持续改进和零微调学习能力。

## 🎯 概述

反思型架构是RANGEN系统的核心创新之一，借鉴了最新的AI研究（Reflexion/LATS论文），使系统能够：
1. **自我诊断**：分析执行过程中的问题和不足
2. **自我改进**：生成改进建议并优化后续执行
3. **零微调学习**：无需重新训练模型即可提升性能
4. **跨试验记忆**：记住历史经验和最佳实践

### 设计理念

- **人类式反思**：模拟人类"事后反思"的学习过程
- **渐进式优化**：通过多次迭代逐步改进决策质量
- **上下文感知**：根据具体任务和场景调整反思策略
- **资源高效**：反思过程不阻塞主请求，异步执行

## 📚 理论基础

### Reflexion框架

Reflexion（Reflection + Action）框架让语言模型通过自我反思来改进决策：

```
初始执行 → 反思分析 → 改进建议 → 重新执行
```

**核心组件**：
1. **执行器**：执行具体任务
2. **反思器**：分析执行结果，找出问题
3. **记忆存储**：保存反思经验和改进策略
4. **决策优化器**：基于反思结果优化后续决策

### LATS（Language Agent Tree Search）

LATS扩展了Reflexion框架，引入树搜索机制：
- **广度优先搜索**：探索多种可能的反思路径
- **回溯机制**：当当前路径不理想时回退到之前节点
- **剪枝优化**：避免无效的反思分支，提高效率

## 🏗️ 系统架构

### 核心组件

```
┌─────────────────────────────────────────────────────────┐
│                   反思型架构系统                          │
├─────────────────────────────────────────────────────────┤
│ 1. ReflectionAgent (基础反思器)                          │
│ 2. ReflexionAgent (增强反思器)                          │
│ 3. ModelRoutingReflectionAgent (模型路由反思器)          │
│ 4. ReflectionMemory (反思记忆存储)                       │
│ 5. LearningOrchestrator (学习协调器)                     │
└─────────────────────────────────────────────────────────┘
```

### 组件详解

#### 1. ReflectionAgent (基础反思器)

位于`src/core/reflection.py`，提供基础反思能力：

```python
class ReflectionAgent:
    """反思型Agent
    让AI能够:
    1. 分析自己输出的问题
    2. 提出改进建议
    3. 生成改进后的版本
    """
    
    def reflect(self, task: str, output: Any, context: Dict) -> ReflectionResult:
        """执行反思分析"""
        # 1. 生成反思提示
        prompt = self._generate_reflection_prompt(task, output, context)
        
        # 2. 调用LLM进行分析
        analysis = self.llm_provider.generate(prompt)
        
        # 3. 解析反思结果
        result = self._parse_reflection_result(analysis)
        
        return result
```

**反思类型**：
- `SUCCESS`：成功反思，总结经验
- `FAILURE`：失败反思，分析原因
- `PARTIAL`：部分成功，找出不足
- `IMPROVEMENT`：改进建议，优化方案

#### 2. ModelRoutingReflectionAgent (模型路由反思器)

位于`src/services/model_routing_reflection.py`，专门优化模型路由决策：

```python
class ModelRoutingReflectionAgent(ReflexionAgent):
    """模型路由反思Agent
    
    专门分析路由决策质量，优化模型选择策略。
    支持三种反思类型：
    1. 初始决策反思 - 分析初始选择是否合理
    2. 失败分析反思 - 分析失败原因和备选方案
    3. 备用模型选择反思 - 分析备用模型选择策略
    """
```

**路由决策类型**：
- `INITIAL`：初始选择
- `FALLBACK`：回退选择  
- `RETRY`：重试选择
- `LEARNED`：基于学习的选择

**路由质量评估**：
- `EXCELLENT`：快速成功，高质量
- `GOOD`：成功但可能有小问题
- `ACCEPTABLE`：可接受但有问题
- `POOR`：成功但质量低
- `FAILED`：模型调用失败

#### 3. ReflectionMemory (反思记忆存储)

存储历史反思经验和优化策略：

```python
class ReflectionMemory:
    """反思记忆存储
    
    存储历史反思结果，支持：
    1. 相似场景检索 - 找到相关的历史反思
    2. 模式识别 - 识别常见问题和解决方案
    3. 策略优化 - 基于历史数据优化决策策略
    """
    
    def store_reflection(self, reflection: ReflectionResult):
        """存储反思结果"""
        
    def find_similar_reflections(self, task: str, context: Dict) -> List[ReflectionResult]:
        """查找相似反思"""
```

## 🔄 工作流程

### 标准反思流程

```
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  任务    │───▶│  初始执行  │───▶│  反思分析  │───▶│ 改进执行  │
│  输入    │    │          │    │          │    │          │
└─────────┘    └──────────┘    └──────────┘    └──────────┘
                     │                │                │
                     ▼                ▼                ▼
               ┌──────────┐    ┌──────────┐    ┌──────────┐
               │  执行结果  │    │反思结果与│    │  改进后   │
               │          │    │ 改进建议  │    │  的结果   │
               └──────────┘    └──────────┘    └──────────┘
```

### 模型路由反思流程

对于模型路由场景，反思流程更加精细化：

```
┌─────────────────────────────────────────────────────────┐
│                     路由决策执行                         │
├─────────────────────────────────────────────────────────┤
│ 1. 接收请求，分析复杂度                                  │
│ 2. 选择初始模型（基于规则/历史/预测）                    │
│ 3. 执行模型调用                                          │
│ 4. 评估结果质量                                          │
└─────────────────────────────────────────────────────────┘
                            │
                    ┌───────▼───────┐
                    │   质量评估     │
                    │               │
                    └───────┬───────┘
                            │
           ┌────────────────┼────────────────┐
           │                │                │
    ┌──────▼─────┐   ┌─────▼──────┐   ┌─────▼──────┐
    │  质量优秀   │   │  质量一般   │   │  质量差/失败 │
    │  记录经验   │   │  触发反思   │   │  深度反思   │
    └────────────┘   └────────────┘   └────────────┘
                            │                │
                    ┌───────▼───────┐ ┌──────▼───────┐
                    │  轻度反思      │ │  重度反思     │
                    │ 分析小问题     │ │ 分析根本原因  │
                    └───────┬───────┘ └──────┬───────┘
                            │                │
                    ┌───────▼────────────────▼───────┐
                    │        生成改进建议             │
                    │  - 模型选择策略优化            │
                    │  - 参数调整建议               │
                    │  - 备选方案推荐               │
                    └────────────────────────────────┘
```

## ⚙️ 配置和使用

### 基础配置

```yaml
# config/environments/reflection.yaml
reflection:
  enabled: true
  mode: "async"  # sync, async, hybrid
  
  # 反思触发条件
  triggers:
    on_failure: true
    on_partial_success: true
    on_success: false  # 成功后不反思，减少开销
    quality_threshold: 0.7  # 质量低于此阈值触发反思
    
  # 反思深度控制
  depth:
    max_iterations: 3
    timeout_seconds: 30
    early_stopping: true
    
  # 记忆存储配置
  memory:
    enabled: true
    max_entries: 1000
    similarity_threshold: 0.8
    cleanup_interval_hours: 24
```

### 模型路由反思配置

```yaml
# config/models/routing_reflection.yaml
model_routing_reflection:
  enabled: true
  
  # 反思类型配置
  reflection_types:
    initial_decision:
      enabled: true
      sample_rate: 0.1  # 10%的初始决策进行反思
      
    failure_analysis:
      enabled: true
      required: true  # 所有失败都必须分析
      
    alternative_selection:
      enabled: true
      threshold: 2  # 超过2次回退触发反思
  
  # 质量评估指标
  quality_metrics:
    response_time_weight: 0.3
    success_rate_weight: 0.4
    user_feedback_weight: 0.3
    content_quality_metrics: ["coherence", "relevance", "accuracy"]
  
  # 学习模式配置
  learning:
    mode: "adaptive"  # adaptive, aggressive, conservative
    update_interval_hours: 1
    min_samples_for_update: 10
```

### API使用示例

```python
from src.services.model_routing_reflection import ModelRoutingReflectionAgent
from src.core.reflection import ReflectionAgent

# 1. 基础反思使用
reflection_agent = ReflectionAgent(llm_provider=llm_client)

result = agent.execute_task(task_description)
reflection = reflection_agent.reflect(
    task=task_description,
    output=result,
    context={"user_id": "user123", "session_id": "session456"}
)

if reflection.reflection_type == "failure":
    improved_result = reflection_agent.improve(
        task=task_description,
        output=result,
        issues=reflection.issues
    )

# 2. 模型路由反思使用
routing_reflection_agent = ModelRoutingReflectionAgent()

# 记录路由决策
decision = RoutingDecision(
    timestamp=time.time(),
    request_id="req_123",
    selected_model="deepseek-chat",
    available_models=["deepseek-chat", "step-3.5-flash", "local-llama"],
    routing_strategy="complexity_based"
)

# 记录结果
outcome = RoutingOutcome(
    decision=decision,
    response=llm_response,
    latency_ms=1500,
    success=True,
    user_feedback=0.85
)

# 触发反思（如果需要）
if outcome.quality in [RoutingQuality.POOR, RoutingQuality.FAILED]:
    reflection_result = routing_reflection_agent.analyze_routing_failure(
        decision=decision,
        outcome=outcome,
        available_models=available_models
    )
    
    # 应用改进建议
    improved_routing = routing_reflection_agent.apply_improvements(
        reflection_result,
        current_routing_strategy
    )
```

## 📊 性能优化

### 反思开销控制

反思过程会增加系统开销，需要进行精细控制：

```python
class ReflectionOptimizer:
    """反思优化器 - 控制反思开销"""
    
    def should_reflect(self, context: Dict) -> bool:
        """判断是否应该进行反思"""
        factors = {
            "execution_time": context.get("execution_time", 0),
            "resource_usage": context.get("resource_usage", 0),
            "time_of_day": context.get("time_of_day", "normal"),
            "system_load": context.get("system_load", 0.5),
            "importance": context.get("importance", "normal")
        }
        
        # 计算反思得分
        score = self._calculate_reflection_score(factors)
        
        # 根据系统负载动态调整阈值
        dynamic_threshold = self._get_dynamic_threshold(factors["system_load"])
        
        return score > dynamic_threshold
```

### 异步反思机制

为了避免阻塞主请求，采用异步反思机制：

```python
async def process_request_with_async_reflection(request):
    """异步反思处理流程"""
    
    # 1. 同步执行主请求
    result = await execute_main_request(request)
    
    # 2. 异步触发反思（不阻塞）
    if should_trigger_reflection(result):
        asyncio.create_task(
            trigger_async_reflection(request, result)
        )
    
    # 3. 立即返回结果
    return result


async def trigger_async_reflection(request, result):
    """异步触发反思"""
    try:
        reflection_result = await reflection_agent.reflect_async(
            task=request.task,
            output=result,
            context=request.context
        )
        
        # 存储反思结果供后续使用
        await reflection_memory.store_async(reflection_result)
        
        # 触发学习更新（如果需要）
        if reflection_result.has_significant_improvements:
            await learning_orchestrator.update_from_reflection(reflection_result)
            
    except Exception as e:
        logger.error(f"异步反思失败: {e}")
        # 失败不影响主流程
```

## 🧠 学习机制

### 零微调学习 (Zero-shot Learning from Reflection)

系统通过反思实现零微调学习：

1. **模式识别**：从多次反思中识别常见问题模式
2. **策略归纳**：归纳出通用的改进策略
3. **规则生成**：生成新的决策规则
4. **参数优化**：优化算法参数

```python
class ZeroShotLearner:
    """零微调学习器"""
    
    def learn_from_reflections(self, reflections: List[ReflectionResult]):
        """从反思中学习"""
        
        # 1. 聚类分析：找出常见问题类型
        clusters = self._cluster_reflections(reflections)
        
        # 2. 模式提取：从每个聚类提取通用模式
        patterns = self._extract_patterns(clusters)
        
        # 3. 规则生成：基于模式生成决策规则
        rules = self._generate_rules(patterns)
        
        # 4. 策略更新：更新系统策略
        self._update_strategies(rules)
        
        return rules
```

### 跨试验记忆 (Cross-Trial Memory)

系统记住历史试验的经验教训：

```python
class CrossTrialMemory:
    """跨试验记忆"""
    
    def __init__(self):
        self.success_patterns = []  # 成功模式
        self.failure_patterns = []  # 失败模式
        self.optimization_strategies = []  # 优化策略
    
    def remember_trial(self, trial_result: TrialResult):
        """记住一次试验结果"""
        if trial_result.success:
            self._extract_success_pattern(trial_result)
        else:
            self._extract_failure_pattern(trial_result)
    
    def get_relevant_memories(self, current_task: str) -> List[MemoryEntry]:
        """获取相关记忆"""
        return self._find_similar_memories(current_task)
```

## 📈 效果评估

### 性能指标

| 指标 | 描述 | 目标值 |
|------|------|--------|
| 反思触发率 | 需要反思的请求比例 | < 20% |
| 反思成功率 | 反思后改进成功的比例 | > 70% |
| 反思延迟 | 反思过程增加的平均延迟 | < 100ms |
| 质量提升率 | 反思后质量提升的比例 | > 30% |
| 学习收敛速度 | 系统学习到稳定策略所需请求数 | < 1000 |

### A/B测试框架

```python
class ReflectionABTest:
    """反思A/B测试框架"""
    
    def run_experiment(self, control_group, treatment_group):
        """运行A/B测试"""
        
        results = {
            "control": self._evaluate_group(control_group),
            "treatment": self._evaluate_group(treatment_group)
        }
        
        # 统计显著性检验
        significance = self._calculate_significance(
            results["control"],
            results["treatment"]
        )
        
        return {
            "results": results,
            "significance": significance,
            "recommendation": self._make_recommendation(results, significance)
        }
```

## 🚀 最佳实践

### 反思策略选择

1. **轻量级反思**（适合简单任务）
   - 单次反思迭代
   - 有限的问题分析
   - 快速改进建议

2. **标准反思**（适合中等复杂度任务）
   - 2-3次反思迭代
   - 全面问题分析
   - 详细改进方案

3. **深度反思**（适合复杂任务）
   - 多次迭代直到收敛
   - 根本原因分析
   - 长期策略优化

### 资源管理建议

1. **时间资源**：
   - 设置反思超时时间
   - 限制最大迭代次数
   - 优先级队列管理

2. **计算资源**：
   - 控制并发反思数量
   - 优化提示词减少token消耗
   - 缓存常见反思结果

3. **存储资源**：
   - 定期清理旧反思记录
   - 压缩存储反思数据
   - 分层存储（热/温/冷数据）

### 监控和告警

```yaml
monitoring:
  reflection:
    metrics:
      - reflection_rate
      - reflection_success_rate
      - reflection_latency_p95
      - quality_improvement_rate
      
    alerts:
      - name: high_reflection_rate
        condition: reflection_rate > 0.3
        severity: warning
        
      - name: low_success_rate
        condition: reflection_success_rate < 0.5
        severity: critical
        
      - name: high_latency
        condition: reflection_latency_p95 > 500
        severity: warning
```

## 🔮 未来发展方向

### 短期优化（V3.1）

1. **反思算法优化**
   - 更智能的反思触发机制
   - 多维度反思质量评估
   - 自适应反思深度控制

2. **学习效率提升**
   - 强化学习与反思结合
   - 迁移学习应用
   - 元学习能力增强

### 中期规划（V3.2）

1. **多模态反思**
   - 文本、代码、图像多模态反思
   - 跨模态问题检测
   - 统一改进策略

2. **分布式反思**
   - 跨节点反思协作
   - 联邦学习式反思
   - 去中心化反思记忆

### 长期愿景（V4.0）

1. **自主反思进化**
   - 反思策略自我优化
   - 反思过程自我改进
   - 完全自主的学习循环

2. **通用反思框架**
   - 可应用于任意AI系统
   - 标准化反思接口
   - 开源反思组件库

## 🔗 相关资源

- [Reflection源代码](../../src/core/reflection.py)
- [ModelRoutingReflection源代码](../../src/services/model_routing_reflection.py)
- [Reflexion论文](https://arxiv.org/abs/2303.11366)
- [LATS论文](https://arxiv.org/abs/2310.04406)
- [学习协调器](../../src/core/learning_orchestrator.py)

## 📝 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2026-03-07 | 初始版本，完整反思型架构文档 |
| 1.0.1 | 2026-03-07 | 添加配置示例和最佳实践 |
| 1.0.2 | 2026-03-07 | 完善性能评估和未来规划 |

---

*最后更新：2026-03-07*  
*文档版本：1.0.2*  
*维护团队：RANGEN反思架构研究组*
