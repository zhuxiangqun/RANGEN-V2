# 多模型架构服务接口文档

## 概述

本文档记录了RANGEN多模型架构中各个服务的公共接口和方法。这些服务共同构成了系统的多模型管理能力。

## 服务列表

### 1. LLM适配器框架

**文件**: `src/adapters/llm_adapter_base.py`, `src/adapters/llm_adapter_factory.py`

#### 主要类和枚举

```python
# 提供商枚举
class LLMProvider(str, Enum):
    DEEPSEEK = "deepseek"
    STEPFLASH = "stepflash"
    LOCAL_LLAMA = "local_llama"
    LOCAL_QWEN = "local_qwen"
    LOCAL_PHI3 = "local_phi3"
    OPENAI = "openai"
    CLAUDE = "claude"
    MOCK = "mock"

# 适配器能力枚举
class AdapterCapability(str, Enum):
    CHAT_COMPLETION = "chat_completion"
    EMBEDDING = "embedding"
    FUNCTION_CALLING = "function_calling"
    REASONING = "reasoning"
```

#### 适配器工厂 (LLMAdapterFactory)

**主要方法**:
- `register_adapter(provider, adapter_class)`: 注册适配器类
- `create_adapter(config)`: 创建适配器实例
- `create_adapter_simple(provider, model_name, api_key, base_url, **kwargs)`: 简化版创建

**使用示例**:
```python
from src.adapters.llm_adapter_factory import LLMAdapterFactory

# 创建适配器
adapter = LLMAdapterFactory.create_adapter_simple(
    provider="deepseek",
    model_name="deepseek-chat",
    api_key="your-api-key"
)
```

### 2. 故障容忍服务 (FaultToleranceService)

**文件**: `src/services/fault_tolerance_service.py`

#### 主要类和枚举

```python
# 模型优先级枚举
class ModelPriority(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    FALLBACK = "fallback"
    EMERGENCY = "emergency"

# 故障类型枚举
class FailureType(str, Enum):
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    AUTH_ERROR = "auth_error"
    NETWORK_ERROR = "network_error"
    SERVICE_ERROR = "service_error"
    UNKNOWN_ERROR = "unknown_error"

# 降级链配置
class FallbackChainConfig:
    model_id: str
    priority: ModelPriority
    cost_per_token: float
    max_concurrent_requests: int
```

#### 主要公共方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `get_model_health(model_id)` | `model_id: str` | `Optional[ModelHealth]` | 获取模型健康状态 |
| `get_all_health_status()` | 无 | `Dict[str, ModelHealth]` | 获取所有模型健康状态 |
| `get_stats()` | 无 | `FaultToleranceStats` | 获取服务统计信息 |
| `reset_stats()` | 无 | `None` | 重置统计信息 |
| `start_health_check(interval=300)` | `interval: int` | `None` | 启动健康检查 |
| `stop_health_check()` | 无 | `None` | 停止健康检查 |
| `force_model_healthy(model_id, healthy)` | `model_id: str`, `healthy: bool` | `None` | 强制设置模型健康状态 |
| `reset_circuit_breaker(model_id)` | `model_id: str` | `None` | 重置断路器 |
| `export_config(file_path)` | `file_path: str` | `None` | 导出配置到文件 |

**使用示例**:
```python
from src.services.fault_tolerance_service import FaultToleranceService

service = FaultToleranceService()
health = service.get_model_health("deepseek-model")
stats = service.get_stats()
```

### 3. 多模型配置服务 (MultiModelConfigService)

**文件**: `src/services/multi_model_config_service.py`

#### 主要类和枚举

```python
# 模型提供商枚举
class ModelProvider(str, Enum):
    DEEPSEEK = "deepseek"
    STEPFLASH = "stepflash"
    LOCAL_LLAMA = "local_llama"
    LOCAL_QWEN = "local_qwen"
    LOCAL_PHI3 = "local_phi3"
    OPENAI = "openai"
    CLAUDE = "claude"
    MOCK = "mock"

# 路由策略枚举
class RoutingStrategy(str, Enum):
    COST_FIRST = "cost_first"
    PERFORMANCE_FIRST = "performance_first"
    QUALITY_FIRST = "quality_first"
    HYBRID = "hybrid"
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
```

#### 主要公共方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `get_model_config(model_id)` | `model_id: str` | `Optional[ModelConfig]` | 获取单个模型配置 |
| `get_all_model_configs()` | 无 | `Dict[str, ModelConfig]` | 获取所有模型配置 |
| `get_enabled_model_configs()` | 无 | `Dict[str, ModelConfig]` | 获取启用的模型配置 |
| `get_routing_config()` | 无 | `RoutingConfig` | 获取路由配置 |
| `get_cost_optimization_config()` | 无 | `CostOptimizationConfig` | 获取成本优化配置 |
| `get_performance_benchmark_config()` | 无 | `PerformanceBenchmarkConfig` | 获取性能基准配置 |
| `save_model_config(model_config)` | `model_config: ModelConfig` | `bool` | 保存模型配置 |
| `update_routing_config(updates)` | `updates: Dict[str, Any]` | `bool` | 更新路由配置 |
| `validate_config(config_type, config_data)` | `config_type: str`, `config_data: Dict[str, Any]` | `List[str]` | 验证配置 |
| `export_config(file_path)` | `file_path: str` | `bool` | 导出配置到文件 |
| `register_config_listener(listener)` | `listener: callable` | `None` | 注册配置变更监听器 |
| `unregister_config_listener(listener)` | `listener: callable` | `None` | 取消注册监听器 |
| `clear_cache()` | 无 | `None` | 清除配置缓存 |

**使用示例**:
```python
from src.services.multi_model_config_service import MultiModelConfigService

service = MultiModelConfigService()
configs = service.get_all_model_configs()
routing_config = service.get_routing_config()
```

### 4. 上下文优化服务 (ContextOptimizationService)

**文件**: `src/services/context_optimization_service.py`

#### 主要类和枚举

```python
# 优化策略枚举
class OptimizationStrategy(str, Enum):
    TOKEN_REDUCTION = "token_reduction"
    CONTEXT_COMPRESSION = "context_compression"
    SUMMARIZATION = "summarization"
    TRUNCATION = "truncation"
    DEDUPLICATION = "deduplication"
    PROMPT_OPTIMIZATION = "prompt_optimization"

# 压缩方法枚举
class CompressionMethod(str, Enum):
    EXTRACTIVE = "extractive"
    ABSTRACTIVE = "abstractive"
    HYBRID = "hybrid"
    SEMANTIC = "semantic"
```

#### 主要公共方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `optimize_context(content, context_type, strategies, max_tokens)` | `content: str`, `context_type: str = "general"`, `strategies: Optional[List[OptimizationStrategy]] = None`, `max_tokens: Optional[int] = None` | `OptimizationResult` | 优化上下文内容 |
| `analyze_token_usage(content)` | `content: str` | `TokenAnalysisResult` | 分析token使用情况 |
| `get_stats()` | 无 | `Dict[str, Any]` | 获取服务统计信息 |
| `clear_cache()` | 无 | `None` | 清除语义缓存 |

**使用示例**:
```python
from src.services.context_optimization_service import ContextOptimizationService

service = ContextOptimizationService()
result = service.optimize_context(
    content="这是一段很长的文本内容...",
    context_type="document",
    max_tokens=4000
)
analysis = service.analyze_token_usage("需要分析的文本")
```

### 5. 监控仪表板服务 (MonitoringDashboardService)

**文件**: `src/services/monitoring_dashboard_service.py`

#### 主要数据类

```python
@dataclass
class MetricData:
    metric_name: str
    value: float
    model_id: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Alert:
    alert_id: str
    alert_type: str
    severity: str
    message: str
    metric_data: MetricData
    created_at: datetime
    acknowledged: bool = False
    resolved: bool = False
```

#### 主要公共方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `start()` | 无 | `None` | 启动监控服务 |
| `stop()` | 无 | `None` | 停止监控服务 |
| `record_metric(metric_data)` | `metric_data: MetricData` | `None` | 记录指标数据 |
| `get_current_metrics(filter_model)` | `filter_model: Optional[str] = None` | `List[MetricData]` | 获取当前指标 |
| `get_active_alerts()` | 无 | `List[Alert]` | 获取活动告警 |
| `acknowledge_alert(alert_id)` | `alert_id: str` | `bool` | 确认告警 |
| `resolve_alert(alert_id)` | `alert_id: str` | `bool` | 解决告警 |
| `add_alert_config(config)` | `config: AlertConfig` | `str` | 添加告警配置 |
| `get_dashboard_summary()` | 无 | `Dict[str, Any]` | 获取仪表板摘要 |

**使用示例**:
```python
from src.services.monitoring_dashboard_service import MonitoringDashboardService, MetricData
from datetime import datetime

service = MonitoringDashboardService()
service.start()

# 记录指标
metric = MetricData(
    metric_name="response_time_ms",
    value=150.5,
    model_id="deepseek-model",
    timestamp=datetime.now()
)
service.record_metric(metric)

# 获取当前指标
metrics = service.get_current_metrics()
alerts = service.get_active_alerts()
```

### 6. A/B测试服务 (ABTestingService)

**文件**: `src/services/ab_testing_service.py`

#### 主要类和枚举

```python
# 实验状态枚举
class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"

# 变体类型枚举
class VariantType(str, Enum):
    ROUTING_STRATEGY = "routing_strategy"
    MODEL_SELECTION = "model_selection"
    PARAMETER_TUNING = "parameter_tuning"
    COST_OPTIMIZATION = "cost_optimization"
```

#### 主要公共方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `create_experiment(config)` | `config: ExperimentConfig` | `str` | 创建实验 |
| `start_experiment(experiment_id)` | `experiment_id: str` | `bool` | 启动实验 |
| `stop_experiment(experiment_id)` | `experiment_id: str` | `bool` | 停止实验 |
| `get_experiment_status(experiment_id)` | `experiment_id: str` | `Optional[Dict[str, Any]]` | 获取实验状态 |
| `assign_variant(experiment_id, user_id)` | `experiment_id: str`, `user_id: str` | `Optional[Dict[str, Any]]` | 为用户分配变体 |
| `record_result(experiment_id, variant_id, metrics)` | `experiment_id: str`, `variant_id: str`, `metrics: Dict[str, float]` | `bool` | 记录实验结果 |
| `get_experiment_result(experiment_id)` | `experiment_id: str` | `Optional[ExperimentResult]` | 获取实验结果 |
| `get_all_experiments()` | 无 | `List[Dict[str, Any]]` | 获取所有实验信息 |

#### 单例获取函数

```python
def get_ab_testing_service(storage_path: Optional[str] = None) -> ABTestingService:
    """获取A/B测试服务实例（单例模式）"""
```

**使用示例**:
```python
from src.services.ab_testing_service import get_ab_testing_service, ExperimentConfig, VariantType

service = get_ab_testing_service()

# 创建实验配置
config = ExperimentConfig(
    experiment_id="routing_test_001",
    name="路由策略测试",
    description="测试不同路由策略的性能",
    variant_type=VariantType.ROUTING_STRATEGY,
    variants=[
        {"strategy": "cost_first", "models": ["deepseek", "stepflash"]},
        {"strategy": "performance_first", "models": ["deepseek"]},
        {"strategy": "hybrid", "models": ["stepflash", "local_llama"]}
    ]
)

# 创建并启动实验
exp_id = service.create_experiment(config)
service.start_experiment(exp_id)
```

### 7. 模型基准测试服务 (ModelBenchmarkService)

**文件**: `src/services/model_benchmark_service.py`

#### 主要公共方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `run_benchmark(model_ids, test_config)` | `model_ids: List[str]`, `test_config: Dict[str, Any]` | `Dict[str, Any]` | 运行基准测试 |
| `get_benchmark_results(benchmark_id)` | `benchmark_id: str` | `Optional[Dict[str, Any]]` | 获取基准测试结果 |
| `compare_models(model_ids, test_config)` | `model_ids: List[str]`, `test_config: Dict[str, Any]` | `Dict[str, Any]` | 比较多个模型 |
| `get_all_benchmarks()` | 无 | `List[Dict[str, Any]]` | 获取所有基准测试 |

**使用示例**:
```python
from src.services.model_benchmark_service import ModelBenchmarkService

service = ModelBenchmarkService()
results = service.run_benchmark(
    model_ids=["deepseek-model", "stepflash-model"],
    test_config={
        "test_cases": 10,
        "prompt_types": ["creative_writing", "fact_retrieval"],
        "max_tokens": 1000
    }
)
```

## 服务集成模式

### 1. 服务初始化顺序

```python
# 推荐的服务初始化顺序
1. ConfigService (基础配置)
2. MultiModelConfigService (多模型配置)
3. FaultToleranceService (故障容忍)
4. ContextOptimizationService (上下文优化)
5. MonitoringDashboardService (监控仪表板)
6. ABTestingService (A/B测试)
7. ModelBenchmarkService (模型基准测试)
```

### 2. 服务依赖关系

- **MultiModelConfigService** 依赖 **ConfigService**
- **FaultToleranceService** 依赖 **MultiModelConfigService**
- **ContextOptimizationService** 可独立运行
- **MonitoringDashboardService** 可独立运行，但通常与其他服务集成
- **ABTestingService** 可独立运行，用于路由策略测试
- **ModelBenchmarkService** 可独立运行，用于模型性能评估

### 3. 错误处理模式

所有服务都应遵循统一的错误处理模式：

```python
try:
    result = service.some_method(params)
    if result:
        # 处理成功结果
        pass
    else:
        # 处理失败情况
        logger.warning("方法执行返回空结果")
except ValueError as e:
    # 参数验证错误
    logger.error(f"参数错误: {e}")
    raise
except Exception as e:
    # 其他错误
    logger.error(f"服务方法执行失败: {e}", exc_info=True)
    raise
```

## 版本兼容性

### 当前版本
- **接口版本**: v1.0.0
- **最后更新**: 2026-03-09
- **兼容性**: 向后兼容现有测试

### 变更记录

| 日期 | 版本 | 变更说明 |
|------|------|----------|
| 2026-03-09 | v1.0.0 | 初始版本，基于实际代码分析 |
| 2026-03-09 | v1.0.1 | 修复A/B测试服务语法错误 |
| 2026-03-09 | v1.0.2 | 更新测试以匹配实际接口 |

## 测试指南

### 单元测试
每个服务都应包含对应的单元测试文件：
- `tests/test_fault_tolerance_service.py`
- `tests/test_multi_model_config_service.py`
- `tests/test_context_optimization_service.py`
- `tests/test_monitoring_dashboard_service.py`
- `tests/test_ab_testing_service.py`
- `tests/test_model_benchmark_service.py`

### 集成测试
使用 `tests/test_multi_model_integration_fixed_v2.py` 进行服务间集成测试。

### 测试命令
```bash
# 运行所有集成测试
python -m pytest tests/test_multi_model_integration_fixed_v2.py -v

# 运行特定服务测试
python -m pytest tests/test_ab_testing_service.py -v

# 生成测试报告
python -m pytest tests/ --cov=src --cov-report=html
```

## 贡献指南

### 添加新服务
1. 在 `src/services/` 目录下创建新服务文件
2. 遵循现有的接口设计模式
3. 添加完整的类型提示和文档字符串
4. 创建对应的单元测试文件
5. 更新本接口文档
6. 添加集成测试用例

### 修改现有接口
1. 保持向后兼容性
2. 更新对应的测试文件
3. 更新本接口文档
4. 运行所有相关测试确保兼容性

### 接口设计原则
1. **单一职责**: 每个方法只做一件事
2. **明确输入输出**: 使用类型提示明确参数和返回值
3. **错误处理**: 提供明确的错误信息和异常类型
4. **文档完整**: 每个公共方法都有完整的文档字符串
5. **测试覆盖**: 确保所有公共方法都有对应的测试

## 常见问题

### Q1: 服务初始化失败怎么办？
检查依赖服务和配置是否正确加载。查看日志文件获取详细错误信息。

### Q2: 如何添加新的模型提供商？
1. 在 `LLMProvider` 枚举中添加新提供商
2. 创建对应的适配器类（继承 `BaseLLMAdapter`）
3. 在适配器工厂中注册新适配器
4. 更新配置服务以支持新提供商

### Q3: 服务间如何通信？
服务间通过方法调用直接通信，避免循环依赖。使用事件监听器模式处理配置变更等异步事件。

### Q4: 如何扩展服务功能？
通过添加新方法扩展功能，保持现有接口不变。如果需要重大变更，考虑创建新的服务版本。

## 联系和支持

- **文档维护**: 开发团队
- **问题反馈**: 通过GitHub Issues报告
- **更新频率**: 每月审查和更新一次

---

*本文档最后更新于: 2026-03-09*