"""
统一模型路由服务模块

合并以下服务:
- IntelligentModelRouter (intelligent_model_router.py)
- EnhancedIntelligentRouter (enhanced_intelligent_router.py)
- ABTestingRouter (ab_testing_router.py)
- MultiModelConfigService (multi_model_config_service.py)

使用示例:
```python
from src.services.routing import ModelRouter

router = ModelRouter()
model = router.select_model("complex reasoning task")
```
"""

import time
import random
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field


# ============== Enums ==============

class TaskType(str, Enum):
    """任务类型"""
    SIMPLE = "simple"              # 简单任务
    COMPLEX = "complex"            # 复杂任务
    REASONING = "reasoning"        # 推理任务
    CREATIVE = "creative"          # 创意任务
    CODE = "code"                  # 代码任务
    FAST = "fast"                  # 快速响应


class ModelProvider(str, Enum):
    """模型提供商"""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class RoutingStrategy(str, Enum):
    """路由策略"""
    COST_FIRST = "cost_first"      # 成本优先
    PERFORMANCE_FIRST = "performance_first"  # 性能优先
    BALANCED = "balanced"          # 平衡
    ADAPTIVE = "adaptive"          # 自适应
    AB_TESTING = "ab_testing"      # A/B测试


class ModelStatus(str, Enum):
    """模型状态"""
    AVAILABLE = "available"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


# ============== Data Classes ==============

@dataclass
class ModelConfig:
    """模型配置"""
    provider: ModelProvider
    model_name: str
    max_tokens: int
    temperature: float
    cost_per_1k_input: float
    cost_per_1k_output: float
    capabilities: List[str]
    avg_latency: float  # seconds


@dataclass
class TaskContext:
    """任务上下文"""
    task_type: TaskType
    complexity: float  # 0-1
    priority: str
    user_preference: Optional[str] = None
    budget_limit: Optional[float] = None


@dataclass
class RoutingDecision:
    """路由决策"""
    model: ModelConfig
    strategy: RoutingStrategy
    reason: str
    confidence: float
    alternatives: List[ModelConfig] = field(default_factory=list)


@dataclass
class RoutingMetrics:
    """路由指标"""
    total_requests: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_latency: float = 0.0
    total_cost: float = 0.0
    model_usage: Dict[str, int] = field(default_factory=dict)


# ============== Main Class ==============

class ModelRouter:
    """
    统一模型路由服务
    
    支持:
    - 智能模型选择
    - 成本优化
    - 性能优化
    - A/B测试
    - 自适应路由
    - 负载均衡
    """
    
    def __init__(self):
        self._models: Dict[str, ModelConfig] = {}
        self._metrics = RoutingMetrics()
        self._strategy = RoutingStrategy.BALANCED
        self._load_balancer_weights: Dict[str, float] = {}
        self._ab_tests: Dict[str, Dict[str, int]] = {}
        
        # Default models
        self._init_default_models()
    
    def _init_default_models(self) -> None:
        """初始化默认模型"""
        self.add_model(
            "deepseek-chat",
            ModelConfig(
                provider=ModelProvider.DEEPSEEK,
                model_name="deepseek-chat",
                max_tokens=4096,
                temperature=0.7,
                cost_per_1k_input=0.14,
                cost_per_1k_output=0.28,
                capabilities=["reasoning", "chat", "general"],
                avg_latency=2.0
            )
        )
        
        self.add_model(
            "deepseek-coder",
            ModelConfig(
                provider=ModelProvider.DEEPSEEK,
                model_name="deepseek-coder",
                max_tokens=4096,
                temperature=0.7,
                cost_per_1k_input=0.14,
                cost_per_1k_output=0.28,
                capabilities=["code", "reasoning"],
                avg_latency=2.0
            )
        )
        
        self.add_model(
            "gpt-4",
            ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4",
                max_tokens=8192,
                temperature=0.7,
                cost_per_1k_input=30.0,
                cost_per_1k_output=60.0,
                capabilities=["reasoning", "chat", "general", "code"],
                avg_latency=5.0
            )
        )
        
        self.add_model(
            "gpt-3.5-turbo",
            ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-3.5-turbo",
                max_tokens=4096,
                temperature=0.7,
                cost_per_1k_input=0.5,
                cost_per_1k_output=1.5,
                capabilities=["chat", "fast"],
                avg_latency=1.0
            )
        )
    
    # ============== Model Management ==============
    
    def add_model(self, model_id: str, config: ModelConfig) -> None:
        """添加模型"""
        self._models[model_id] = config
        self._load_balancer_weights[model_id] = 1.0
    
    def remove_model(self, model_id: str) -> None:
        """移除模型"""
        if model_id in self._models:
            del self._models[model_id]
        if model_id in self._load_balancer_weights:
            del self._load_balancer_weights[model_id]
    
    def set_strategy(self, strategy: RoutingStrategy) -> None:
        """设置路由策略"""
        self._strategy = strategy
    
    def set_ab_test(
        self,
        test_name: str,
        variants: Dict[str, float]
    ) -> None:
        """设置A/B测试"""
        self._ab_tests[test_name] = {
            model_id: 0 for model_id in variants.keys()
        }
        self._ab_tests[test_name + "_weights"] = variants
    
    # ============== Routing ==============
    
    def select_model(
        self,
        query: str,
        context: Optional[TaskContext] = None
    ) -> RoutingDecision:
        """选择模型"""
        # Determine task type
        task_type = self._classify_task(query)
        
        if context is None:
            context = TaskContext(
                task_type=task_type,
                complexity=self._estimate_complexity(query),
                priority="normal"
            )
        
        # Apply strategy
        if self._strategy == RoutingStrategy.COST_FIRST:
            return self._select_cost_first(context)
        elif self._strategy == RoutingStrategy.PERFORMANCE_FIRST:
            return self._select_performance_first(context)
        elif self._strategy == RoutingStrategy.AB_TESTING:
            return self._select_ab_test(context)
        elif self._strategy == RoutingStrategy.ADAPTIVE:
            return self._select_adaptive(context)
        else:  # BALANCED
            return self._select_balanced(context)
    
    def _classify_task(self, query: str) -> TaskType:
        """分类任务类型"""
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ["代码", "code", "function", "def "]):
            return TaskType.CODE
        elif any(kw in query_lower for kw in ["为什么", "why", "原因", "分析"]):
            return TaskType.REASONING
        elif any(kw in query_lower for kw in ["创意", "creative", "写诗", "故事"]):
            return TaskType.CREATIVE
        elif any(kw in query_lower for kw in ["快速", "fast", "简单", "what is"]):
            return TaskType.FAST
        elif len(query) > 200:
            return TaskType.COMPLEX
        else:
            return TaskType.SIMPLE
    
    def _estimate_complexity(self, query: str) -> float:
        """估计复杂度"""
        complexity = 0.0
        
        # Length
        if len(query) > 500:
            complexity += 0.3
        elif len(query) > 200:
            complexity += 0.2
        elif len(query) > 100:
            complexity += 0.1
        
        # Keywords
        if any(kw in query.lower() for kw in ["分析", "compare", "详细", "explain"]):
            complexity += 0.3
        
        # Multiple questions
        complexity += min(0.3, query.count("?") * 0.1)
        
        return min(1.0, complexity)
    
    def _select_cost_first(self, context: TaskContext) -> RoutingDecision:
        """成本优先选择"""
        # Filter by capability
        candidates = [
            m for m in self._models.values()
            if self._matches_capability(m, context.task_type)
        ]
        
        if not candidates:
            return self._fallback_decision(context)
        
        # Sort by cost
        candidates.sort(key=lambda m: m.cost_per_1k_input)
        
        return RoutingDecision(
            model=candidates[0],
            strategy=RoutingStrategy.COST_FIRST,
            reason=f"Lowest cost for {context.task_type}",
            confidence=0.8,
            alternatives=candidates[1:3]
        )
    
    def _select_performance_first(self, context: TaskContext) -> RoutingDecision:
        """性能优先选择"""
        candidates = [
            m for m in self._models.values()
            if self._matches_capability(m, context.task_type)
        ]
        
        if not candidates:
            return self._fallback_decision(context)
        
        # Sort by latency
        candidates.sort(key=lambda m: m.avg_latency)
        
        return RoutingDecision(
            model=candidates[0],
            strategy=RoutingStrategy.PERFORMANCE_FIRST,
            reason=f"Fastest for {context.task_type}",
            confidence=0.8,
            alternatives=candidates[1:3]
        )
    
    def _select_balanced(self, context: TaskContext) -> RoutingDecision:
        """平衡选择"""
        candidates = [
            m for m in self._models.values()
            if self._matches_capability(m, context.task_type)
        ]
        
        if not candidates:
            return self._fallback_decision(context)
        
        # Score each model
        scored = []
        for m in candidates:
            # Cost score (lower is better)
            cost_score = 1.0 - (m.cost_per_1k_input / 100)
            
            # Capability match (higher is better)
            cap_score = 1.0 if self._matches_capability(m, context.task_type) else 0.5
            
            # Latency score (lower is better)
            latency_score = 1.0 - (m.avg_latency / 10)
            
            # Combined
            score = (cost_score * 0.3 + cap_score * 0.3 + latency_score * 0.4)
            scored.append((m, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return RoutingDecision(
            model=scored[0][0],
            strategy=RoutingStrategy.BALANCED,
            reason=f"Best balance for {context.task_type}",
            confidence=0.7,
            alternatives=[m for m, _ in scored[1:3]]
        )
    
    def _select_ab_test(self, context: TaskContext) -> RoutingDecision:
        """A/B测试选择"""
        if not self._ab_tests:
            return self._select_balanced(context)
        
        test_name = "default"
        weights = self._ab_tests.get(test_name + "_weights", {})
        
        if not weights:
            return self._select_balanced(context)
        
        # Select based on weights
        model_id = random.choices(
            list(weights.keys()),
            weights=list(weights.values())
        )[0]
        
        model = self._models.get(model_id, list(self._models.values())[0])
        
        return RoutingDecision(
            model=model,
            strategy=RoutingStrategy.AB_TESTING,
            reason="A/B test variant",
            confidence=0.6,
            alternatives=list(self._models.values())[:2]
        )
    
    def _select_adaptive(self, context: TaskContext) -> RoutingDecision:
        """自适应选择"""
        # Use metrics to decide
        if self._metrics.total_requests > 0:
            success_rate = self._metrics.success_count / self._metrics.total_requests
            
            # If recent failures, avoid that model
            if success_rate < 0.8:
                return self._select_cost_first(context)
        
        return self._select_balanced(context)
    
    def _matches_capability(self, model: ModelConfig, task_type: TaskType) -> bool:
        """检查模型是否匹配任务类型"""
        capability_map = {
            TaskType.CODE: ["code"],
            TaskType.REASONING: ["reasoning"],
            TaskType.CREATIVE: ["creative"],
            TaskType.FAST: ["fast"],
            TaskType.SIMPLE: ["general", "chat"],
            TaskType.COMPLEX: ["reasoning", "general"],
        }
        
        required = capability_map.get(task_type, ["general"])
        return any(cap in model.capabilities for cap in required)
    
    def _fallback_decision(self, context: TaskContext) -> RoutingDecision:
        """备用决策"""
        default_model = list(self._models.values())[0] if self._models else None
        
        if default_model:
            return RoutingDecision(
                model=default_model,
                strategy=self._strategy,
                reason="Fallback to default",
                confidence=0.5,
                alternatives=[]
            )
        
        raise ValueError("No models available")
    
    # ============== Metrics ==============
    
    def record_result(
        self,
        model_id: str,
        success: bool,
        latency: float,
        cost: float
    ) -> None:
        """记录结果"""
        self._metrics.total_requests += 1
        
        if success:
            self._metrics.success_count += 1
        else:
            self._metrics.failure_count += 1
        
        self._metrics.total_cost += cost
        self._metrics.avg_latency = (
            (self._metrics.avg_latency * (self._metrics.total_requests - 1) + latency)
            / self._metrics.total_requests
        )
        
        # Model usage
        if model_id not in self._metrics.model_usage:
            self._metrics.model_usage[model_id] = 0
        self._metrics.model_usage[model_id] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        return {
            "total_requests": self._metrics.total_requests,
            "success_rate": (
                self._metrics.success_count / self._metrics.total_requests
                if self._metrics.total_requests > 0 else 0
            ),
            "avg_latency": self._metrics.avg_latency,
            "total_cost": self._metrics.total_cost,
            "model_usage": self._metrics.model_usage,
            "current_strategy": self._strategy.value,
        }
    
    def get_available_models(self) -> List[ModelConfig]:
        """获取可用模型"""
        return list(self._models.values())


# ============== Factory ==============

def get_model_router() -> ModelRouter:
    """获取模型路由器"""
    return ModelRouter()
