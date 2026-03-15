"""
智能模型路由服务 - 基于性能预测的动态路由
Intelligent Model Routing Service with Performance Prediction

核心功能：
1. 性能预测 - 基于历史数据和当前状态预测模型性能
2. 智能路由 - 根据任务特征和模型状态动态选择最优模型
3. 负载均衡 - 多模型实例间的智能负载分配
4. 降级策略 - 故障时自动切换到备用模型

技术特性：
- 时间序列预测模型
- 任务特征提取
- 多臂老虎机算法
- 实时性能监控
"""

import logging
import time
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """任务类型"""
    GENERAL = "general"               # 通用任务
    REASONING = "reasoning"           # 推理任务
    CREATIVE = "creative"             # 创造性任务
    ANALYTICAL = "analytical"         # 分析任务
    CODE_GENERATION = "code_generation"  # 代码生成
    SUMMARIZATION = "summarization"   # 摘要任务
    TRANSLATION = "translation"        # 翻译任务
    EMBEDDING = "embedding"           # 向量嵌入


class ModelStatus(str, Enum):
    """模型状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OVERLOADED = "overloaded"
    UNAVAILABLE = "unavailable"


@dataclass
class ModelCapability:
    """模型能力配置"""
    model_name: str
    supported_tasks: List[TaskType]
    strengths: List[str]              # 优势领域
    weaknesses: List[str]             # 劣势领域
    avg_latency_ms: float = 0.0      # 平均延迟
    max_tokens: int = 4000            # 最大token数
    context_window: int = 128000      # 上下文窗口


@dataclass
class TaskContext:
    """任务上下文"""
    task_type: TaskType
    estimated_tokens: int
    priority: int = 5                 # 1-10, 10最高
    deadline_ms: Optional[int] = None  # 截止时间
    user_preference: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelPerformancePrediction:
    """模型性能预测"""
    model_name: str
    predicted_latency_ms: float
    confidence: float                  # 预测置信度 0-1
    availability_probability: float    # 可用性概率 0-1
    recommendation_score: float        # 推荐分数 0-1
    factors: List[str] = field(default_factory=list)


@dataclass
class RoutingDecision:
    """路由决策"""
    selected_model: str
    alternative_models: List[str]
    predicted_performance: ModelPerformancePrediction
    reasoning: List[str]
    timestamp: float = field(default_factory=time.time)


class PerformancePredictor:
    """性能预测器"""
    
    def __init__(self, history_window: int = 100):
        self.history_window = history_window
        self.performance_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.lock = threading.RLock()
    
    def record(self, model_name: str, metrics: Dict[str, Any]) -> None:
        """记录性能数据"""
        with self.lock:
            data = {
                **metrics,
                'timestamp': time.time()
            }
            self.performance_history[model_name].append(data)
            
            # 保持历史窗口大小
            if len(self.performance_history[model_name]) > self.history_window:
                self.performance_history[model_name] = \
                    self.performance_history[model_name][-self.history_window:]
    
    def predict(self, model_name: str, task_context: TaskContext) -> ModelPerformancePrediction:
        """预测模型性能"""
        with self.lock:
            history = self.performance_history.get(model_name, [])
            
            if not history:
                return ModelPerformancePrediction(
                    model_name=model_name,
                    predicted_latency_ms=1000.0,
                    confidence=0.3,
                    availability_probability=0.8,
                    recommendation_score=0.5,
                    factors=["无历史数据，使用默认值"]
                )
            
            # 1. 预测延迟
            recent_latencies = [h.get('latency_ms', 0) for h in history[-10:] if 'latency_ms' in h]
            if recent_latencies:
                avg_latency = sum(recent_latencies) / len(recent_latencies)
                
                # 考虑任务复杂度
                task_complexity = self._estimate_task_complexity(task_context)
                predicted_latency = avg_latency * task_complexity
            else:
                predicted_latency = 1000.0
            
            # 2. 计算置信度（基于数据量）
            confidence = min(0.9, len(history) / 50)
            
            # 3. 预测可用性
            recent_errors = [h.get('error', False) for h in history[-10:]]
            error_rate = sum(1 for e in recent_errors if e) / max(len(recent_errors), 1)
            availability = max(0.5, 1.0 - error_rate)
            
            # 4. 综合推荐分数
            recommendation_score = self._calculate_recommendation_score(
                predicted_latency, confidence, availability, task_context
            )
            
            # 5. 分析影响因素
            factors = self._analyze_factors(history, task_context)
            
            return ModelPerformancePrediction(
                model_name=model_name,
                predicted_latency_ms=predicted_latency,
                confidence=confidence,
                availability_probability=availability,
                recommendation_score=recommendation_score,
                factors=factors
            )
    
    def _estimate_task_complexity(self, task_context: TaskContext) -> float:
        """估计任务复杂度"""
        base = 1.0
        
        # 基于token数量
        if task_context.estimated_tokens > 4000:
            base *= 1.5
        elif task_context.estimated_tokens > 2000:
            base *= 1.2
        
        # 基于任务类型
        complexity_map = {
            TaskType.REASONING: 1.5,
            TaskType.CODE_GENERATION: 1.3,
            TaskType.ANALYTICAL: 1.2,
            TaskType.GENERAL: 1.0,
            TaskType.CREATIVE: 1.1,
            TaskType.SUMMARIZATION: 0.9,
            TaskType.TRANSLATION: 0.8,
            TaskType.EMBEDDING: 0.7
        }
        
        return base * complexity_map.get(task_context.task_type, 1.0)
    
    def _calculate_recommendation_score(
        self,
        predicted_latency: float,
        confidence: float,
        availability: float,
        task_context: TaskContext
    ) -> float:
        """计算推荐分数"""
        # 延迟得分（越低越好）
        latency_score = max(0, 1.0 - (predicted_latency / 5000))
        
        # 可用性权重
        availability_weight = 0.4
        latency_weight = 0.3
        confidence_weight = 0.3
        
        score = (
            availability * availability_weight +
            latency_score * latency_weight +
            confidence * confidence_weight
        )
        
        # 优先级加权
        priority_weight = task_context.priority / 10.0
        score = score * 0.7 + priority_weight * 0.3
        
        return min(1.0, max(0.0, score))
    
    def _analyze_factors(self, history: List[Dict], task_context: TaskContext) -> List[str]:
        """分析影响因素"""
        factors = []
        
        # 检查最近错误
        recent_errors = [h.get('error') for h in history[-5:] if 'error' in h]
        if any(recent_errors):
            factors.append("最近有错误记录")
        
        # 检查延迟趋势
        latencies = [h.get('latency_ms', 0) for h in history[-10:] if 'latency_ms' in h]
        if len(latencies) >= 5:
            if latencies[-1] > sum(latencies[:-1]) / len(latencies[:-1]):
                factors.append("延迟呈上升趋势")
        
        # 检查负载
        recent_loads = [h.get('queue_length', 0) for h in history[-5:] if 'queue_length' in h]
        if recent_loads and max(recent_loads) > 10:
            factors.append("模型负载较高")
        
        return factors if factors else ["性能稳定"]


class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self):
        self.model_loads: Dict[str, float] = defaultdict(float)  # 0-1表示负载
        self.lock = threading.RLock()
    
    def update_load(self, model_name: str, load: float) -> None:
        """更新模型负载"""
        with self.lock:
            self.model_loads[model_name] = min(1.0, max(0.0, load))
    
    def get_least_loaded(self, model_names: List[str]) -> Optional[str]:
        """获取负载最低的模型"""
        with self.lock:
            if not model_names:
                return None
            
            available = [(name, self.model_loads.get(name, 0.0)) for name in model_names]
            available.sort(key=lambda x: x[1])
            
            return available[0][0] if available else None
    
    def get_load_distribution(self, model_names: List[str]) -> Dict[str, float]:
        """获取负载分布"""
        with self.lock:
            return {name: self.model_loads.get(name, 0.0) for name in model_names}


class IntelligentModelRouter:
    """智能模型路由服务"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 性能预测器
        self.predictor = PerformancePredictor(history_window=self.config.get('history_window', 100))
        
        # 负载均衡器
        self.load_balancer = LoadBalancer()
        
        # 模型能力配置
        self.model_capabilities: Dict[str, ModelCapability] = {}
        
        # 模型状态
        self.model_status: Dict[str, ModelStatus] = {}
        
        # 路由历史
        self.routing_history: List[RoutingDecision] = []
        
        # 降级链
        self.fallback_chains: Dict[str, List[str]] = {}
        
        # 统计
        self.stats = {
            'total_routes': 0,
            'successful_routes': 0,
            'fallback_routes': 0,
            'failed_routes': 0
        }
        
        self.lock = threading.RLock()
        
        # 初始化默认模型能力
        self._init_default_capabilities()
        
        logger.info("智能模型路由服务初始化完成")
    
    def _init_default_capabilities(self) -> None:
        """初始化默认模型能力"""
        default_capabilities = {
            'deepseek': ModelCapability(
                model_name='deepseek',
                supported_tasks=[TaskType.REASONING, TaskType.ANALYTICAL, TaskType.CODE_GENERATION, TaskType.CREATIVE],
                strengths=['复杂推理', '代码生成', '深度分析', '中文优化', '性价比高'],
                weaknesses=['创意写作一般', '超长文本处理有限'],
                avg_latency_ms=1500.0,
                max_tokens=4000,
                context_window=64000
            ),
            'step-3.5-flash': ModelCapability(
                model_name='step-3.5-flash',
                supported_tasks=[TaskType.GENERAL, TaskType.SUMMARIZATION, TaskType.TRANSLATION, TaskType.REASONING],
                strengths=['速度快', '成本极低', '开源免费', '支持本地部署'],
                weaknesses=['复杂推理能力有限', '创意写作一般'],
                avg_latency_ms=800.0,
                max_tokens=4000,
                context_window=256000
            ),
            'local-llama': ModelCapability(
                model_name='local-llama',
                supported_tasks=[TaskType.GENERAL, TaskType.SUMMARIZATION, TaskType.TRANSLATION],
                strengths=['完全本地', '数据隐私', '零API成本', '可定制'],
                weaknesses=['资源要求高', '性能有限', '需要训练'],
                avg_latency_ms=2000.0,
                max_tokens=2000,
                context_window=32000
            ),
            'local-qwen': ModelCapability(
                model_name='local-qwen',
                supported_tasks=[TaskType.GENERAL, TaskType.REASONING, TaskType.CODE_GENERATION],
                strengths=['中文优化', '代码能力强', '开源免费'],
                weaknesses=['需要GPU资源', '性能优化需要配置'],
                avg_latency_ms=1800.0,
                max_tokens=3000,
                context_window=32000
            )
        }
        
        self.model_capabilities.update(default_capabilities)
    
    def register_model(self, capability: ModelCapability) -> None:
        """注册模型能力"""
        self.model_capabilities[capability.model_name] = capability
        self.model_status[capability.model_name] = ModelStatus.HEALTHY
        logger.info(f"注册模型能力: {capability.model_name}")
    
    def update_model_status(self, model_name: str, status: ModelStatus) -> None:
        """更新模型状态"""
        self.model_status[model_name] = status
        logger.info(f"模型状态更新: {model_name} -> {status.value}")
    
    def record_performance(self, model_name: str, metrics: Dict[str, Any]) -> None:
        """记录性能数据"""
        self.predictor.record(model_name, metrics)
        
        # 更新负载
        if 'queue_length' in metrics:
            load = metrics['queue_length'] / 20.0  # 假设20为满负载
            self.load_balancer.update_load(model_name, load)
        
        # 检查是否需要降级
        if metrics.get('error', False):
            self._handle_model_error(model_name)
    
    def _handle_model_error(self, model_name: str) -> None:
        """处理模型错误"""
        current_status = self.model_status.get(model_name, ModelStatus.HEALTHY)
        
        if current_status == ModelStatus.HEALTHY:
            self.update_model_status(model_name, ModelStatus.DEGRADED)
        elif current_status == ModelStatus.DEGRADED:
            self.update_model_status(model_name, ModelStatus.OVERLOADED)
    
    def set_fallback_chain(self, primary_model: str, fallback_models: List[str]) -> None:
        """设置降级链"""
        self.fallback_chains[primary_model] = fallback_models
        logger.info(f"设置降级链: {primary_model} -> {fallback_models}")
    
    async def route(self, task_context: TaskContext) -> RoutingDecision:
        """执行智能路由"""
        with self.lock:
            self.stats['total_routes'] += 1
        
        try:
            # 1. 筛选可用模型
            available_models = self._filter_available_models(task_context)
            
            if not available_models:
                return self._create_error_decision("无可用模型")
            
            # 2. 为每个模型预测性能
            predictions = []
            for model_name in available_models:
                prediction = self.predictor.predict(model_name, task_context)
                predictions.append((model_name, prediction))
            
            # 3. 考虑任务匹配度
            for model_name, prediction in predictions:
                capability = self.model_capabilities.get(model_name)
                if capability:
                    task_match = self._calculate_task_match(capability, task_context)
                    prediction.recommendation_score *= task_match
            
            # 4. 排序选择最优模型
            predictions.sort(key=lambda x: x[1].recommendation_score, reverse=True)
            
            # 5. 选择最佳模型
            selected_model, best_prediction = predictions[0]
            
            # 6. 准备备选模型
            alternatives = [m for m, _ in predictions[1:3]]
            
            # 7. 生成决策理由
            reasoning = self._generate_reasoning(task_context, selected_model, best_prediction, alternatives)
            
            # 8. 更新统计
            with self.lock:
                self.stats['successful_routes'] += 1
            
            decision = RoutingDecision(
                selected_model=selected_model,
                alternative_models=alternatives,
                predicted_performance=best_prediction,
                reasoning=reasoning
            )
            
            # 保存历史
            self.routing_history.append(decision)
            if len(self.routing_history) > 1000:
                self.routing_history = self.routing_history[-1000:]
            
            logger.info(f"路由决策: {selected_model} (置信度: {best_prediction.confidence:.2f})")
            
            return decision
            
        except Exception as e:
            logger.error(f"路由失败: {e}")
            with self.lock:
                self.stats['failed_routes'] += 1
            return self._create_error_decision(str(e))
    
    def _filter_available_models(self, task_context: TaskContext) -> List[str]:
        """筛选可用模型"""
        available = []
        
        for model_name, status in self.model_status.items():
            if status == ModelStatus.UNAVAILABLE:
                continue
            
            # 检查模型能力
            capability = self.model_capabilities.get(model_name)
            if not capability:
                continue
            
            # 检查是否支持该任务类型
            if task_context.task_type in capability.supported_tasks:
                available.append(model_name)
        
        # 如果没有精确匹配的，返回所有健康模型
        if not available:
            available = [m for m, s in self.model_status.items() 
                       if s in [ModelStatus.HEALTHY, ModelStatus.DEGRADED]]
        
        return available
    
    def _calculate_task_match(self, capability: ModelCapability, task_context: TaskContext) -> float:
        """计算任务匹配度"""
        if task_context.task_type not in capability.supported_tasks:
            return 0.0
        
        match_score = 0.8  # 基础匹配分
        
        # 根据任务类型加分
        task_type_strengths = {
            TaskType.REASONING: '复杂推理',
            TaskType.CODE_GENERATION: '代码生成',
            TaskType.ANALYTICAL: '深度分析',
            TaskType.CREATIVE: '创意写作',
            TaskType.SUMMARIZATION: '长文本处理'
        }
        
        expected_strength = task_type_strengths.get(task_context.task_type, '')
        if expected_strength in capability.strengths:
            match_score += 0.2
        
        # 检查token限制
        if task_context.estimated_tokens <= capability.max_tokens:
            match_score += 0.1
        
        return min(1.0, match_score)
    
    def _generate_reasoning(
        self,
        task_context: TaskContext,
        selected_model: str,
        prediction: ModelPerformancePrediction,
        alternatives: List[str]
    ) -> List[str]:
        """生成决策理由"""
        reasoning = []
        
        capability = self.model_capabilities.get(selected_model)
        if capability:
            reasoning.append(f"选择 {selected_model}: 支持 {task_context.task_type.value} 任务")
            if capability.strengths:
                reasoning.append(f"优势领域: {', '.join(capability.strengths[:2])}")
        
        reasoning.append(f"预测延迟: {prediction.predicted_latency_ms:.0f}ms")
        reasoning.append(f"预测置信度: {prediction.confidence:.2f}")
        reasoning.append(f"可用性: {prediction.availability_probability:.2f}")
        
        if prediction.factors:
            reasoning.append(f"分析因素: {', '.join(prediction.factors)}")
        
        if alternatives:
            reasoning.append(f"备选模型: {', '.join(alternatives)}")
        
        return reasoning
    
    def _create_error_decision(self, error_message: str) -> RoutingDecision:
        """创建错误决策"""
        return RoutingDecision(
            selected_model="",
            alternative_models=[],
            predicted_performance=ModelPerformancePrediction(
                model_name="",
                predicted_latency_ms=0.0,
                confidence=0.0,
                availability_probability=0.0,
                recommendation_score=0.0,
                factors=[f"错误: {error_message}"]
            ),
            reasoning=[error_message]
        )
    
    async def execute_with_fallback(
        self,
        task_context: TaskContext,
        execute_func: callable
    ) -> Any:
        """带降级的执行"""
        # 初始路由
        decision = await self.route(task_context)
        
        if not decision.selected_model:
            raise Exception("无法路由到任何可用模型")
        
        # 尝试执行
        models_to_try = [decision.selected_model] + decision.alternative_models
        last_error = None
        
        for model_name in models_to_try:
            try:
                result = await execute_func(model_name, task_context)
                
                # 记录成功
                self.record_performance(model_name, {
                    'success': True,
                    'latency_ms': result.get('latency_ms', 0)
                })
                
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(f"模型 {model_name} 执行失败: {e}")
                
                # 记录失败
                self.record_performance(model_name, {
                    'success': False,
                    'error': True
                })
                
                # 更新状态
                self._handle_model_error(model_name)
                
                # 更新统计
                with self.lock:
                    self.stats['fallback_routes'] += 1
                
                continue
        
        raise Exception(f"所有模型都执行失败: {last_error}")
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """获取路由统计"""
        with self.lock:
            total = self.stats['total_routes']
            return {
                **self.stats,
                'success_rate': self.stats['successful_routes'] / total if total > 0 else 0,
                'fallback_rate': self.stats['fallback_routes'] / total if total > 0 else 0,
                'failure_rate': self.stats['failed_routes'] / total if total > 0 else 0
            }
    
    def get_model_status_summary(self) -> Dict[str, Any]:
        """获取模型状态摘要"""
        return {
            'total_models': len(self.model_capabilities),
            'healthy_models': sum(1 for s in self.model_status.values() if s == ModelStatus.HEALTHY),
            'degraded_models': sum(1 for s in self.model_status.values() if s == ModelStatus.DEGRADED),
            'unavailable_models': sum(1 for s in self.model_status.values() if s == ModelStatus.UNAVAILABLE),
            'model_details': {
                name: {
                    'status': status.value,
                    'capability': {
                        'supported_tasks': [t.value for t in cap.supported_tasks],
                        'avg_latency_ms': cap.avg_latency_ms
                    }
                }
                for name, status in self.model_status.items()
                for cap in [self.model_capabilities.get(name)]
                if cap
            }
        }


# 全局实例
_intelligent_router: Optional[IntelligentModelRouter] = None


def get_intelligent_model_router(config: Optional[Dict[str, Any]] = None) -> IntelligentModelRouter:
    """获取智能模型路由服务实例"""
    global _intelligent_router
    if _intelligent_router is None:
        _intelligent_router = IntelligentModelRouter(config)
    return _intelligent_router


def create_intelligent_model_router(config: Optional[Dict[str, Any]] = None) -> IntelligentModelRouter:
    """创建智能模型路由服务实例"""
    return IntelligentModelRouter(config)
