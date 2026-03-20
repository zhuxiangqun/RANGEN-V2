#!/usr/bin/env python3
"""
基础智能体 - 提供智能体的基础功能和接口
"""
import os
import time
import logging
import threading
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
from enum import Enum

from .agent_models import (
    AgentConfig, AgentState, ProcessingResult, AgentResult, 
    AgentCapability, StrategyDecision, PerformanceMetrics, LearningResult
)
from .agent_config_manager import AgentConfigManager
from .agent_performance_tracker import AgentPerformanceTracker
from .agent_history_manager import AgentHistoryManager, HistoryType, HistoryQuery
from .self_evolving_mixin import SelfEvolvingMixin, SelfEvolvingConfig





class BaseAgent(ABC):
    """基础智能体抽象类
    
    遵循三大原则:
    1. Superpowers (方法论): TDDEnforcer, TaskPlanner, TwoStageReviewer
    2. Claude HUD (可观测性): AgentHUD 实时状态追踪
    3. Open SWE (团队协作): MiddlewareChain 统一架构
    """
    
    def __init__(self, agent_id: str, capabilities: Optional[List[str]] = None, config: Optional[AgentConfig] = None, max_history_size: int = 1000):
        """初始化基础智能体 - 重构版，使用管理器模式"""
        self.agent_id = agent_id
        self.capabilities = capabilities or []
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        self.status = "initialized"
        self.last_activity = time.time()
        
        self.config_manager = AgentConfigManager(agent_id, config)
        self.performance_tracker = AgentPerformanceTracker(agent_id)
        self.history_manager = AgentHistoryManager(agent_id, max_history_size)
        
        # === OpenClaw: Claude HUD 可观测性集成 ===
        self._init_hud()
        
        # 向后兼容：保持原有属性的访问
        self.config = self.config_manager.config
        self.max_history_size = max_history_size
        self.unified_config_center = self.config_manager.unified_config_center
        
        # 线程锁保护性能指标（向后兼容）
        self._performance_lock = threading.Lock()
        
        # AI上下文网络（简化的神经网络）
        self._ai_context_network = self._initialize_ai_network()
        
        # 增强功能组件
        self.intelligent_processor = None
        self.intelligent_generator = None
        self.llm_client = None
        
        # 智能能力配置
        self.capabilities_dict: Dict[AgentCapability, bool] = {
            AgentCapability.EXTENSIBILITY: True,
            AgentCapability.INTELLIGENCE: True,
            AgentCapability.AUTONOMOUS_DECISION: True,
            AgentCapability.DYNAMIC_STRATEGY: True,
            AgentCapability.STRATEGY_LEARNING: True,
            AgentCapability.SELF_LEARNING: True,
            AgentCapability.AUTOMATIC_REASONING: True,
            AgentCapability.DYNAMIC_CONFIDENCE: True,
            AgentCapability.LLM_DRIVEN_RECOGNITION: True,
            AgentCapability.DYNAMIC_CHAIN_OF_THOUGHT: True,
            AgentCapability.DYNAMIC_CLASSIFICATION: True
        }
        
        # 动态参数
        self.dynamic_params: Dict[str, Any] = {}
        self.adaptation_threshold = 0.05
        self.learning_rate = 0.1
        
        # 初始化智能能力
        self._init_intelligent_capabilities()
        
        self.logger.info(f"智能体 {agent_id} 初始化完成（重构版）")
        
        # 注册到心跳监控器
        try:
            from src.core.monitoring.heartbeat_monitor import get_heartbeat_monitor
            heartbeat_monitor = get_heartbeat_monitor()
            heartbeat_monitor.register_agent(self.agent_id, self)
            self.logger.debug(f"智能体 {agent_id} 已注册到心跳监控器")
        except ImportError as e:
            self.logger.warning(f"无法导入心跳监控器: {e}")
        except Exception as e:
            self.logger.error(f"注册到心跳监控器失败: {e}")
    
    def _init_hud(self):
        """初始化 AgentHUD 可观测性 (Claude HUD 原则)"""
        try:
            from src.ui.agent_hud import AgentHUD, get_hud_instance
            self.hud = get_hud_instance()
            self.logger.debug(f"AgentHUD 集成成功: {self.agent_id}")
        except ImportError as e:
            self.logger.warning(f"无法导入 AgentHUD: {e}")
            self.hud = None
        except Exception as e:
            self.logger.warning(f"AgentHUD 初始化失败: {e}")
            self.hud = None
    
    def record_start(self, action: str = "execute"):
        """记录操作开始 (Claude HUD)"""
        if self.hud:
            self.hud.record_agent_start(self.agent_id, self.__class__.__name__)
            self.hud.set_current_action(self.agent_id, action)
    
    def record_complete(self, success: bool = True, error: str = None):
        """记录操作完成 (Claude HUD)"""
        if self.hud:
            self.hud.record_agent_complete(self.agent_id, success=success)
            if error:
                self.hud.set_error(self.agent_id, error)
    
    # ==================== 自进化能力 ====================
    
    def enable_self_evolving(
        self,
        config: Optional[SelfEvolvingConfig] = None,
        llm_provider=None
    ) -> None:
        """启用自进化能力
        
        Args:
            config: 自进化配置
            llm_provider: LLM提供者
        """
        if not hasattr(self, '_self_evolving_mixin'):
            self._self_evolving_mixin = SelfEvolvingMixin()
        
        self._self_evolving_mixin.init_self_evolving(config, llm_provider)
        self.logger.info(f"{self.agent_id}: Self-evolving enabled")
    
    def disable_self_evolving(self) -> None:
        """禁用自进化能力"""
        if hasattr(self, '_self_evolving_mixin'):
            self._self_evolving_mixin.disable_self_evolving()
            self.logger.info(f"{self.agent_id}: Self-evolving disabled")
    
    def is_self_evolving_enabled(self) -> bool:
        """检查自进化是否启用"""
        return hasattr(self, '_self_evolving_mixin') and self._self_evolving_mixin.is_self_evolving_enabled()
    
    async def execute_with_self_evolving(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        execute_func: Optional[callable] = None
    ) -> Dict[str, Any]:
        """带自进化的执行(如果启用)
        
        Args:
            task: 任务描述
            context: 执行上下文
            execute_func: 实际执行函数
            
        Returns:
            执行结果 + 自进化元数据
        """
        if not self.is_self_evolving_enabled():
            # 未启用，直接执行
            if execute_func:
                return await execute_func(task, context)
            return {"success": True}
        
        return await self._self_evolving_mixin.execute_with_self_evolving(
            task, context, execute_func
        )
    
    def get_evolution_state(self) -> Optional[Any]:
        """获取进化状态"""
        if hasattr(self, '_self_evolving_mixin'):
            return self._self_evolving_mixin.get_evolution_state()
        return None
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if hasattr(self, '_self_evolving_mixin'):
            return self._self_evolving_mixin.get_success_rate()
        return 0.0
    
    def get_learned_patterns(self) -> Dict[str, Any]:
        """获取学习到的模式"""
        if hasattr(self, '_self_evolving_mixin'):
            return self._self_evolving_mixin.get_patterns()
        return {}
    
    
    def _cleanup_history(self, history_list: List[Any]) -> None:
        pass
    
    def add_performance_history(self, metrics: PerformanceMetrics) -> None:
        """添加性能历史记录并自动清理"""
        self.history_manager.add_entry(
            HistoryType.PERFORMANCE,
            asdict(metrics),
            importance=0.7
        )
    
    def add_strategy_history(self, decision: StrategyDecision) -> None:
        """添加策略历史记录并自动清理"""
        self.history_manager.add_entry(
            HistoryType.STRATEGY,
            asdict(decision),
            importance=0.8
        )
    
    def add_learning_history(self, result: LearningResult) -> None:
        """添加学习历史记录并自动清理"""
        self.history_manager.add_entry(
            HistoryType.LEARNING,
            asdict(result),
            importance=0.6
        )
    
    def _init_unified_config_center(self):
        """初始化统一配置中心"""
        try:
            from ..utils.unified_centers import UnifiedConfigCenter, SmartConfigCenter
            # 优先使用智能配置中心，回退到标准配置中心
            try:
                return SmartConfigCenter()
            except Exception:
                return UnifiedConfigCenter()
        except ImportError:
            self.logger.warning("统一配置中心不可用，使用本地配置")
            return None
    
    def get_config_value(self, key: str, default: Any = None, context: Optional[Dict[str, Any]] = None) -> Any:
        """获取配置值 - 优先使用统一配置中心"""
        return self.config_manager.get_config_value(key, default, context)
    
    def update_config(self, config_data: Dict[str, Any]) -> bool:
        """更新配置"""
        result = self.config_manager.update_config(config_data)
        if result:
            self.config = self.config_manager.config
        return result
    
    def _init_intelligent_capabilities(self):
        """初始化智能能力"""
        try:
            self._load_dynamic_config()
            self._init_strategy_learning()
            self._init_self_learning()
            self._init_dynamic_confidence()
            self.logger.info("智能能力初始化完成")
        except Exception as e:
            self.logger.error(f"智能能力初始化失败: {e}")
    
    def _load_dynamic_config(self):
        """加载动态配置"""
        try:
            from ..utils.unified_centers import get_smart_config
            # 加载基础配置
            self.dynamic_params = {
                "learning_rate": get_smart_config("learning_rate", {"default": 0.01}),
                "confidence_threshold": get_smart_config("confidence_threshold", {"default": 0.7}),
                "max_iterations": get_smart_config("max_iterations", {"default": 100}),
                "timeout": get_smart_config("timeout", {"default": 30}),
                "enable_learning": get_smart_config("enable_learning", {"default": True}),
                "enable_reflection": get_smart_config("enable_reflection", {"default": True})
            }
            self.logger.info("动态配置加载完成")
        except Exception as e:
            self.logger.error(f"动态配置加载失败: {e}")
            self.dynamic_params = {}
    
    def _init_strategy_learning(self):
        """初始化策略学习"""
        self.strategy_patterns: Dict[str, Dict[str, Any]] = {}
        self.strategy_performance: Dict[str, List[float]] = {}
        self.learning_rate = 0.1
    
    def _init_self_learning(self):
        """初始化自主学习"""
        self.self_improvement_patterns: Dict[str, Any] = {}
        self.error_patterns: Dict[str, List[str]] = {}
        self.success_patterns: Dict[str, List[str]] = {}
    
    def _init_dynamic_confidence(self):
        """初始化动态置信度"""
        self.confidence_history: List[float] = []
        self.confidence_threshold = 0.7
        self.uncertainty_threshold = 0.7
    
    def _initialize_ai_network(self) -> Dict[str, np.ndarray]:
        """初始化AI上下文网络"""
        # 简化的神经网络权重
        input_size = 10
        hidden_size = 8
        output_size = 4
        
        return {
            'W1': np.random.normal(0, 0.1, (input_size, hidden_size)),
            'b1': np.zeros(hidden_size),
            'W2': np.random.normal(0, 0.1, (hidden_size, output_size)),
            'b2': np.zeros(output_size)
        }
    
    @abstractmethod
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """处理查询 - 抽象方法"""
        try:
            # 验证输入
            if not query or not isinstance(query, str):
                return AgentResult(
                    success=False,
                    data=None,
                    confidence=0.0,
                    processing_time=0.0,
                    error="Invalid query input"
                )
            
            # 预处理查询
            processed_query = self._preprocess_query(query)
            
            # 处理上下文
            processed_context = self._process_context(context or {})
            
            # 执行查询处理
            result = self._execute_query_processing(processed_query, processed_context)
            
            # 后处理结果
            final_result = self._postprocess_result(result)
            
            # 记录处理历史
            self._record_query_processing(query, final_result)
            
            return AgentResult(
                success=True,
                data=final_result,
                confidence=self._calculate_confidence(final_result),
                processing_time=0.0,
                metadata={'query': query, 'context': processed_context}
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                data=None,
                confidence=0.0,
                processing_time=0.0,
                error=f"Query processing failed: {e}"
            )
    
    def _preprocess_query(self, query: str) -> str:
        """预处理查询"""
        # 清理查询
        cleaned_query = query.strip()
        
        
        
        return cleaned_query
    
    def _process_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理上下文"""
        processed_context = context.copy()
        
        # 清理无效数据
        processed_context = {k: v for k, v in processed_context.items() if v is not None}
        
        # 添加默认上下文
        if 'timestamp' not in processed_context:
            processed_context['timestamp'] = time.time()
        
        if 'agent_id' not in processed_context:
            processed_context['agent_id'] = getattr(self, 'agent_id', 'unknown')
        
        return processed_context
    
    def _execute_query_processing(self, query: str, context: Dict[str, Any]) -> Any:
        """执行查询处理"""
        # 根据查询类型处理
        if query.startswith('what'):
            return self._handle_what_query(query, context)
        elif query.startswith('how'):
            return self._handle_how_query(query, context)
        elif query.startswith('why'):
            return self._handle_why_query(query, context)
        elif query.startswith('when'):
            return self._handle_when_query(query, context)
        elif query.startswith('where'):
            return self._handle_where_query(query, context)
        else:
            return self._handle_general_query(query, context)
    
    def _postprocess_result(self, result: Any) -> Any:
        """后处理结果"""
        if isinstance(result, str):
            return result.strip()
        elif isinstance(result, dict):
            return {k: v for k, v in result.items() if v is not None}
        else:
            return result
    
    def _record_query_processing(self, query: str, result: Any):
        """记录查询处理"""
        self.history_manager.add_entry(
            HistoryType.QUERY,
            {
                'query': query,
                'result': result
            },
            tags=["query", "processing"]
        )
    
    def _calculate_confidence(self, result: Any) -> float:
        """计算置信度"""
        if result is None:
            return 0.0
        elif isinstance(result, str) and len(result) > 0:
            return 0.8
        elif isinstance(result, dict) and len(result) > 0:
            return 0.9
        else:
            return 0.7
    
    def _handle_what_query(self, query: str, context: Dict[str, Any]) -> str:
        """处理what查询"""
        return f"What query processed: {query}"
    
    def _handle_how_query(self, query: str, context: Dict[str, Any]) -> str:
        """处理how查询"""
        return f"How query processed: {query}"
    
    def _handle_why_query(self, query: str, context: Dict[str, Any]) -> str:
        """处理why查询"""
        return f"Why query processed: {query}"
    
    def _handle_when_query(self, query: str, context: Dict[str, Any]) -> str:
        """处理when查询"""
        return f"When query processed: {query}"
    
    def _handle_where_query(self, query: str, context: Dict[str, Any]) -> str:
        """处理where查询"""
        return f"Where query processed: {query}"
    
    def _handle_general_query(self, query: str, context: Dict[str, Any]) -> str:
        """处理一般查询"""
        return f"General query processed: {query}"
    
    def process_request(self, request_data: Dict[str, Any]) -> ProcessingResult:
        """处理请求"""
        start_time = time.time()
        
        try:
            self.status = "processing"
            self.last_activity = time.time()
            
            # 提取查询和上下文
            query = request_data.get("query", "")
            context = request_data.get("context", {})
            
            # 处理查询
            result = self.process_query(query, context)
            
            # 更新性能指标
            processing_time = time.time() - start_time
            self._update_performance_metrics(result.success, result.confidence, processing_time)
            
            self.status = "idle"
            return ProcessingResult(
                success=result.success,
                result=result.data,
                confidence=result.confidence,
                processing_time=processing_time,
                metadata=result.metadata or {}
            )
                
        except Exception as e:
            self.logger.error(f"请求处理失败: {e}")
            self.status = "error"
            return ProcessingResult(
                success=False,
                result=None,
                confidence=0.0,
                processing_time=time.time() - start_time,
                metadata={"error": str(e)}
            )
    
    def _update_performance_metrics(self, success: bool, confidence: float, processing_time: float):
        """更新性能指标"""
        self.performance_tracker.record_request(
            success=success,
            confidence=confidence,
            processing_time=processing_time
        )
        
        with self._performance_lock:
            stats = self.performance_tracker.get_performance_stats()
            self.performance_metrics = {
                "total_requests": stats.total_requests,
                "successful_requests": stats.successful_requests,
                "average_processing_time": stats.average_processing_time,
                "average_confidence": stats.average_confidence
            }
    
    def enhance_with_ai_context(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """使用AI上下文增强特征"""
        try:
            # 构建特征向量
            feature_vector = np.array([
                features.get('complexity_score', 0.5),
                features.get('urgency_level', 0.5),
                features.get('user_experience', 0.5),
                features.get('system_load', 0.5),
                features.get('resource_availability', 0.5),
                features.get('priority_level', 0.5),
                features.get('performance_factor', 0.5),
                features.get('context_relevance', 0.5),
                features.get('historical_success', 0.5),
                features.get('environmental_factor', 0.5)
            ], dtype=np.float32)
            
            # 神经网络前向传播
            hidden = np.tanh(np.dot(feature_vector, self._ai_context_network['W1']) + self._ai_context_network['b1'])
            output = np.tanh(np.dot(hidden, self._ai_context_network['W2']) + self._ai_context_network['b2'])
            
            features['ai_confidence'] = float(np.max(output))
            features['ai_context_score'] = float(np.mean(output))
            features['ai_recommendation'] = self._generate_ai_recommendation(output)
            
            return features
            
        except Exception as e:
            self.logger.error(f"AI上下文增强失败: {e}")
            features['ai_confidence'] = 0.5
            features['ai_context_score'] = 0.5
            features['ai_recommendation'] = "default"
        return features
    
    def _generate_ai_recommendation(self, output: np.ndarray) -> str:
        """生成AI推荐"""
        max_index = np.argmax(output)
        
        recommendations = [
            "optimize_performance",
            "increase_resources", 
            "adjust_strategy",
            "maintain_current"
        ]
        
        return recommendations[max_index] if max_index < len(recommendations) else "maintain_current"
    
    @property
    def performance_history(self) -> List[PerformanceMetrics]:
        query = HistoryQuery(
            entry_types=[HistoryType.PERFORMANCE],
            sort_by="timestamp",
            sort_order="desc"
        )
        entries = self.history_manager.query_history(query)
        return [
            PerformanceMetrics(
                accuracy=entry.data.get("accuracy", 0.0),
                execution_time=entry.data.get("execution_time", 0.0),
                success_rate=entry.data.get("success_rate", 0.0),
                confidence=entry.data.get("confidence", 0.0),
                quality_score=entry.data.get("quality_score", 0.0),
                timestamp=datetime.fromtimestamp(entry.timestamp)
            )
            for entry in entries
        ]
    
    @property
    def strategy_history(self) -> List[StrategyDecision]:
        query = HistoryQuery(
            entry_types=[HistoryType.STRATEGY],
            sort_by="timestamp",
            sort_order="desc"
        )
        entries = self.history_manager.query_history(query)
        return [
            StrategyDecision(
                strategy_name=entry.data.get("strategy_name", ""),
                strategy_type=entry.data.get("strategy_type", ""),
                confidence=entry.data.get("confidence", 0.0),
                reasoning=entry.data.get("reasoning", ""),
                parameters=entry.data.get("parameters", {}),
                expected_outcome=entry.data.get("expected_outcome", ""),
                fallback_strategies=entry.data.get("fallback_strategies", [])
            )
            for entry in entries
        ]
    
    @property
    def learning_history(self) -> List[LearningResult]:
        query = HistoryQuery(
            entry_types=[HistoryType.LEARNING],
            sort_by="timestamp",
            sort_order="desc"
        )
        entries = self.history_manager.query_history(query)
        return [
            LearningResult(
                learning_type=entry.data.get("learning_type", ""),
                improvement=entry.data.get("improvement", 0.0),
                confidence=entry.data.get("confidence", 0.0),
                timestamp=datetime.fromtimestamp(entry.timestamp)
            )
            for entry in entries
        ]

    def get_agent_state(self) -> AgentState:
        """获取智能体状态"""
        with self._performance_lock:
            performance_metrics_copy = self.performance_metrics.copy()
        
        return AgentState(
            agent_id=self.agent_id,
            status=self.status,
            last_activity=self.last_activity,
            performance_metrics=performance_metrics_copy,
            capabilities=self.capabilities.copy()
        )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        stats = self.performance_tracker.get_performance_stats()
        
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "total_requests": stats.total_requests,
            "success_rate": stats.success_rate,
            "average_processing_time": stats.average_processing_time,
            "average_confidence": stats.average_confidence,
            "capabilities": self.capabilities,
            "last_activity": self.last_activity
        }
    
    def add_capability(self, capability: str) -> bool:
        """添加能力"""
        try:
            if capability not in self.capabilities:
                self.capabilities.append(capability)
                self.logger.info(f"添加能力: {capability}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"添加能力失败: {e}")
            return False
    
    def remove_capability(self, capability: str) -> bool:
        """移除能力"""
        try:
            if capability in self.capabilities:
                self.capabilities.remove(capability)
                self.logger.info(f"移除能力: {capability}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"移除能力失败: {e}")
            return False
    
    def reset_performance_metrics(self) -> None:
        """重置性能指标"""
        self.performance_tracker.reset_metrics()
        with self._performance_lock:
            self.performance_metrics = {
                "total_requests": 0,
                "successful_requests": 0,
                "average_processing_time": 0.0,
                "average_confidence": 0.0
            }
        self.logger.info("性能指标已重置")
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        current_time = time.time()
        time_since_activity = current_time - self.last_activity
        
        health_status = "healthy"
        if time_since_activity > 3600:  # 1小时无活动
            health_status = "idle"
        elif self.status == "error":
            health_status = "error"
        
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "health": health_status,
            "time_since_activity": time_since_activity,
            "capabilities_count": len(self.capabilities),
            "performance_summary": self.get_performance_summary()
        }
    
    def export_configuration(self) -> Dict[str, Any]:
        """导出配置"""
        return {
            "agent_id": self.agent_id,
            "capabilities": self.capabilities,
            "config": self.config_manager.export_config(),
            "performance_data": self.performance_tracker.export_performance_data(),
            "history_stats": self.history_manager.get_history_stats().__dict__,
            "ai_network_shape": {
                "W1": self._ai_context_network['W1'].shape,
                "W2": self._ai_context_network['W2'].shape
            }
        }
    
    def import_configuration(self, config: Dict[str, Any]) -> bool:
        """导入配置"""
        try:
            if "capabilities" in config:
                self.capabilities = config["capabilities"]
            
            if "config" in config:
                self.config_manager.import_config(config["config"])
                self.config = self.config_manager.config
            
            if "performance_data" in config:
                pass
            
            if "history_stats" in config:
                pass
            
            self.logger.info("配置导入成功")
            return True
            
        except Exception as e:
            self.logger.error(f"配置导入失败: {e}")
            return False


class SimpleAgent(BaseAgent):
    """简单智能体实现"""
    
    def __init__(self, agent_id: str, capabilities: Optional[List[str]] = None):
        super().__init__(agent_id, capabilities)
        self.knowledge_base = {}
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """处理查询"""
        try:
            # 简化的查询处理
            result = f"处理查询: {query}"
            confidence = 0.8
            
            return AgentResult(
                success=True,
                data=result,
                confidence=confidence,
                processing_time=0.0,
                metadata={"query_length": len(query), "context_keys": list(context.keys()) if context else []}
            )
            
        except Exception as e:
            self.logger.error(f"查询处理失败: {e}")
            return AgentResult(
                success=False,
                data=None,
                confidence=0.0,
                processing_time=0.0,
                error=str(e)
            )


def create_agent(agent_id: str, agent_type: str = "simple", 
                capabilities: Optional[List[str]] = None) -> BaseAgent:
    """创建智能体"""
    if agent_type == "simple":
        return SimpleAgent(agent_id, capabilities)
    else:
        raise ValueError(f"未知的智能体类型: {agent_type}")


if __name__ == "__main__":
    # 测试基础智能体
    agent = SimpleAgent("test_agent", ["query_processing", "context_analysis"])
    
    # 测试请求处理
    request_data = {
        "query": "测试查询",
        "context": {"user_id": "test_user"}
    }
    
    result = agent.process_request(request_data)
    print(f"处理结果: {result}")
    
    # 获取性能摘要
    summary = agent.get_performance_summary()
    print(f"性能摘要: {summary}")
    
    # 健康检查
    health = agent.health_check()
    print(f"健康状态: {health}")