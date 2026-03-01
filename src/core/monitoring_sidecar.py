"""
边车监控学习系统 - 分层架构重构

实现边车模式的监控和学习系统：
1. 事件监听：监听业务工作流的事件
2. 异步处理：监控和学习异步执行，不影响业务性能
3. 数据收集：收集性能指标、执行结果、错误信息
4. 学习优化：基于收集的数据进行持续学习
5. 反馈回路：将学习结果反馈给业务系统

替代原有的紧耦合学习监控架构。
"""

import asyncio
import logging
import threading
import time
from typing import Dict, Any, List, Optional, Callable, Protocol
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from queue import Queue
import json

logger = logging.getLogger(__name__)


@dataclass
class WorkflowEvent:
    """工作流事件"""
    event_type: str  # "node_start", "node_end", "workflow_start", "workflow_end", "error"
    event_id: str
    timestamp: datetime
    workflow_id: str
    node_name: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    workflow_id: str
    total_execution_time: float
    node_execution_times: Dict[str, float]
    memory_usage: float
    cpu_usage: float
    error_count: int
    success_rate: float
    collected_at: datetime


@dataclass
class LearningData:
    """学习数据"""
    pattern_type: str
    features: Dict[str, Any]
    outcome: Dict[str, Any]
    confidence: float
    collected_at: datetime
    workflow_context: Dict[str, Any]


class MonitoringInterface(Protocol):
    """监控接口"""

    async def collect_metrics(self, event: WorkflowEvent) -> Optional[PerformanceMetrics]:
        """收集指标"""
        ...

    async def analyze_performance(self, metrics: PerformanceMetrics) -> Dict[str, Any]:
        """分析性能"""
        ...


class LearningInterface(Protocol):
    """学习接口"""

    async def process_learning_data(self, data: LearningData) -> Dict[str, Any]:
        """处理学习数据"""
        ...

    async def generate_insights(self, learning_history: List[LearningData]) -> List[Dict[str, Any]]:
        """生成洞察"""
        ...

    async def optimize_parameters(self, insights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """优化参数"""
        ...


class MonitoringSidecar:
    """边车监控学习系统

    核心特性：
    1. 事件驱动：监听业务工作流事件
    2. 异步处理：监控和学习异步执行
    3. 资源隔离：独立资源池，不影响业务性能
    4. 智能反馈：基于学习结果优化业务参数
    """

    def __init__(self, business_workflow=None):
        self.business_workflow = business_workflow

        # 事件队列
        self.event_queue: Queue = Queue(maxsize=10000)

        # 监控和学习组件
        self.monitor = PerformanceMonitor()
        self.learner = ContinuousLearner()

        # 数据存储
        self.metrics_history: List[PerformanceMetrics] = []
        self.learning_history: List[LearningData] = []
        self.insights: List[Dict[str, Any]] = []

        # 控制标志
        self.running = False
        self.monitoring_enabled = True
        self.learning_enabled = True

        # 工作线程
        self.monitor_thread: Optional[threading.Thread] = None
        self.learning_thread: Optional[threading.Thread] = None

        # 反馈机制
        self.feedback_callbacks: List[Callable] = []

        logger.info("✅ 边车监控学习系统初始化完成")

    def attach_to_workflow(self, workflow):
        """附加到业务工作流"""
        self.business_workflow = workflow
        # 这里可以添加事件钩子，具体实现取决于工作流框架
        logger.info("✅ 边车系统已附加到业务工作流")

    def start(self):
        """启动边车系统"""
        if self.running:
            return

        self.running = True

        # 启动监控线程
        if self.monitoring_enabled:
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("✅ 监控线程已启动")

        # 启动学习线程
        if self.learning_enabled:
            self.learning_thread = threading.Thread(target=self._learning_loop, daemon=True)
            self.learning_thread.start()
            logger.info("✅ 学习线程已启动")

    def stop(self):
        """停止边车系统"""
        self.running = False

        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        if self.learning_thread:
            self.learning_thread.join(timeout=5)

        logger.info("✅ 边车系统已停止")

    def publish_event(self, event: WorkflowEvent):
        """发布事件到边车系统"""
        try:
            self.event_queue.put_nowait(event)
        except:
            logger.warning("⚠️ 事件队列已满，丢弃事件")

    async def on_workflow_event_async(self, event: WorkflowEvent):
        """异步处理工作流事件"""
        # 立即处理关键事件
        if event.event_type in ["error", "workflow_end"]:
            await self._process_critical_event(event)

        # 发布到队列进行异步处理
        self.publish_event(event)

    def add_feedback_callback(self, callback: Callable):
        """添加反馈回调"""
        self.feedback_callbacks.append(callback)

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "running": self.running,
            "monitoring_enabled": self.monitoring_enabled,
            "learning_enabled": self.learning_enabled,
            "event_queue_size": self.event_queue.qsize(),
            "metrics_collected": len(self.metrics_history),
            "learning_data_points": len(self.learning_history),
            "insights_generated": len(self.insights),
            "feedback_callbacks": len(self.feedback_callbacks)
        }

    def _monitoring_loop(self):
        """监控循环"""
        while self.running:
            try:
                # 从队列获取事件
                if not self.event_queue.empty():
                    event = self.event_queue.get(timeout=1)

                    # 异步处理监控
                    asyncio.run(self._process_monitoring_event(event))

                else:
                    time.sleep(0.1)  # 避免忙等待

            except Exception as e:
                logger.error(f"❌ 监控循环错误: {e}")

    def _learning_loop(self):
        """学习循环"""
        while self.running:
            try:
                # 检查是否有足够的学习数据
                if len(self.learning_history) >= 10:  # 最小批次大小
                    # 执行学习批次
                    asyncio.run(self._execute_learning_batch())

                time.sleep(5)  # 学习间隔

            except Exception as e:
                logger.error(f"❌ 学习循环错误: {e}")

    async def _process_monitoring_event(self, event: WorkflowEvent):
        """处理监控事件"""
        try:
            # 收集指标
            metrics = await self.monitor.collect_metrics(event)
            if metrics:
                self.metrics_history.append(metrics)

                # 保留最近的指标（避免内存泄漏）
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]

            # 实时性能分析
            if metrics:
                analysis = await self.monitor.analyze_performance(metrics)

                # 如果发现性能问题，触发学习
                if analysis.get("needs_optimization", False):
                    await self._trigger_learning_event(event, analysis)

        except Exception as e:
            logger.error(f"❌ 处理监控事件失败: {e}")

    async def _execute_learning_batch(self):
        """执行学习批次"""
        try:
            # 获取最近的学习数据
            recent_data = self.learning_history[-50:]  # 最近50个数据点

            # 生成洞察
            new_insights = await self.learner.generate_insights(recent_data)
            self.insights.extend(new_insights)

            # 优化参数
            if new_insights:
                optimizations = await self.learner.optimize_parameters(new_insights)

                # 通过反馈回调应用优化
                for callback in self.feedback_callbacks:
                    try:
                        await callback(optimizations)
                    except Exception as e:
                        logger.error(f"❌ 应用反馈优化失败: {e}")

            logger.info(f"✅ 学习批次完成: 生成{len(new_insights)}个洞察")

        except Exception as e:
            logger.error(f"❌ 执行学习批次失败: {e}")

    async def _process_critical_event(self, event: WorkflowEvent):
        """处理关键事件"""
        if event.event_type == "error":
            # 错误事件：立即记录并分析
            error_data = LearningData(
                pattern_type="error_pattern",
                features={
                    "error_type": event.data.get("error_type", "unknown"),
                    "node_name": event.node_name,
                    "workflow_id": event.workflow_id
                },
                outcome={"error_occurred": True},
                confidence=1.0,
                collected_at=datetime.now(),
                workflow_context=event.metadata
            )
            self.learning_history.append(error_data)

        elif event.event_type == "workflow_end":
            # 工作流结束：收集完整指标
            await self._collect_workflow_metrics(event)

    async def _trigger_learning_event(self, event: WorkflowEvent, analysis: Dict[str, Any]):
        """触发学习事件"""
        learning_data = LearningData(
            pattern_type="performance_pattern",
            features={
                "node_name": event.node_name,
                "execution_time": event.data.get("execution_time", 0),
                "performance_issue": analysis.get("issue_type", "unknown")
            },
            outcome=analysis,
            confidence=analysis.get("confidence", 0.5),
            collected_at=datetime.now(),
            workflow_context=event.metadata
        )

        self.learning_history.append(learning_data)

    async def _collect_workflow_metrics(self, event: WorkflowEvent):
        """收集完整工作流指标"""
        # 这里可以实现更完整的指标收集逻辑
        # 目前只是占位符
        pass


class PerformanceMonitor:
    """性能监控器"""

    async def collect_metrics(self, event: WorkflowEvent) -> Optional[PerformanceMetrics]:
        """收集性能指标"""
        if event.event_type == "workflow_end":
            return PerformanceMetrics(
                workflow_id=event.workflow_id,
                total_execution_time=event.data.get("total_execution_time", 0),
                node_execution_times=event.data.get("node_execution_times", {}),
                memory_usage=event.data.get("memory_usage", 0),
                cpu_usage=event.data.get("cpu_usage", 0),
                error_count=event.data.get("error_count", 0),
                success_rate=1.0 if event.data.get("success", True) else 0.0,
                collected_at=datetime.now()
            )
        return None

    async def analyze_performance(self, metrics: PerformanceMetrics) -> Dict[str, Any]:
        """分析性能指标"""
        analysis = {
            "needs_optimization": False,
            "issue_type": None,
            "confidence": 0.0
        }

        # 检查执行时间
        if metrics.total_execution_time > 10:  # 超过10秒
            analysis["needs_optimization"] = True
            analysis["issue_type"] = "slow_execution"
            analysis["confidence"] = 0.8

        # 检查错误率
        elif metrics.error_count > 0:
            analysis["needs_optimization"] = True
            analysis["issue_type"] = "high_error_rate"
            analysis["confidence"] = 0.9

        # 检查资源使用
        elif metrics.memory_usage > 100 * 1024 * 1024:  # 超过100MB
            analysis["needs_optimization"] = True
            analysis["issue_type"] = "high_memory_usage"
            analysis["confidence"] = 0.7

        return analysis


class ContinuousLearner:
    """持续学习器"""

    async def process_learning_data(self, data: LearningData) -> Dict[str, Any]:
        """处理学习数据"""
        # 简化的学习处理逻辑
        return {
            "processed": True,
            "pattern_recognized": data.pattern_type,
            "insights_generated": 1
        }

    async def generate_insights(self, learning_history: List[LearningData]) -> List[Dict[str, Any]]:
        """生成洞察"""
        insights = []

        # 分析错误模式
        error_patterns = [d for d in learning_history if d.pattern_type == "error_pattern"]
        if error_patterns:
            error_types = {}
            for pattern in error_patterns:
                error_type = pattern.features.get("error_type", "unknown")
                error_types[error_type] = error_types.get(error_type, 0) + 1

            most_common_error = max(error_types.items(), key=lambda x: x[1])
            insights.append({
                "type": "error_pattern_insight",
                "description": f"最常见的错误类型: {most_common_error[0]} ({most_common_error[1]}次)",
                "recommendation": "增加错误处理和重试机制",
                "confidence": 0.85
            })

        # 分析性能模式
        performance_patterns = [d for d in learning_history if d.pattern_type == "performance_pattern"]
        if performance_patterns:
            slow_nodes = [p.features.get("node_name") for p in performance_patterns
                         if p.features.get("performance_issue") == "slow_execution"]

            if slow_nodes:
                node_counts = {}
                for node in slow_nodes:
                    node_counts[node] = node_counts.get(node, 0) + 1

                slowest_node = max(node_counts.items(), key=lambda x: x[1])
                insights.append({
                    "type": "performance_insight",
                    "description": f"最慢的节点: {slowest_node[0]} ({slowest_node[1]}次慢执行)",
                    "recommendation": "优化该节点的执行逻辑或增加缓存",
                    "confidence": 0.8
                })

        return insights

    async def optimize_parameters(self, insights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """基于洞察优化参数"""
        optimizations = {}

        for insight in insights:
            if insight["type"] == "error_pattern_insight":
                # 增加重试次数
                optimizations["retry_policy"] = {
                    "max_retries": 5,
                    "backoff_factor": 2.0
                }

            elif insight["type"] == "performance_insight":
                # 增加缓存
                optimizations["cache_policy"] = {
                    "enable_cache": True,
                    "cache_size": 1000,
                    "ttl_seconds": 3600
                }

                # 调整并发度
                optimizations["concurrency"] = {
                    "max_concurrent_requests": 5
                }

        return optimizations


# 全局边车实例
_sidecar_instance: Optional[MonitoringSidecar] = None


def get_monitoring_sidecar() -> MonitoringSidecar:
    """获取边车实例（单例模式）"""
    global _sidecar_instance
    if _sidecar_instance is None:
        _sidecar_instance = MonitoringSidecar()
    return _sidecar_instance
