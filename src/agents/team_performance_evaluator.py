#!/usr/bin/env python3
"""
团队绩效评估器 - 负责评估和优化多Agent团队的协作性能

功能：
1. 团队绩效指标收集和计算
2. 团队健康评分和状态评估
3. 协作瓶颈分析和识别
4. 优化建议生成和优先级排序
5. 历史趋势分析和预测
6. 与Agent性能跟踪器和协作协调器集成
"""

import time
import logging
import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
import json

# 导入现有的性能跟踪器和协调器
from src.agents.agent_performance_tracker import AgentPerformanceTracker, PerformanceStats
from src.agents.multi_agent_coordinator import MultiAgentCoordinator
from src.core.enhanced_collaboration_coordinator import EnhancedCollaborationCoordinator, CollaborationPerformanceMetrics

logger = logging.getLogger(__name__)


@dataclass
class TeamPerformanceMetrics:
    """团队绩效指标"""
    team_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 基础指标
    total_agents: int = 0
    active_agents: int = 0
    total_collaborations: int = 0
    successful_collaborations: int = 0
    collaboration_success_rate: float = 0.0
    avg_collaboration_time: float = 0.0
    avg_task_completion_rate: float = 0.0
    
    # 效率指标
    communication_efficiency: float = 0.0  # 通信效率 (0-1)
    coordination_efficiency: float = 0.0  # 协调效率 (0-1)
    resource_utilization: float = 0.0  # 资源利用率 (0-1)
    load_balance_score: float = 0.0  # 负载均衡分数 (0-1)
    
    # 质量指标
    result_quality: float = 0.0  # 结果质量 (0-1)
    conflict_resolution_rate: float = 0.0  # 冲突解决率 (0-1)
    consensus_achievement_rate: float = 0.0  # 共识达成率 (0-1)
    
    # Agent个体指标
    agent_health_scores: Dict[str, float] = field(default_factory=dict)  # Agent健康评分
    agent_performance_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # Agent性能统计
    
    # 瓶颈指标
    identified_bottlenecks: List[Dict[str, Any]] = field(default_factory=list)  # 识别到的瓶颈
    bottleneck_severity: float = 0.0  # 瓶颈严重程度 (0-1)
    
    # 趋势指标
    performance_trend: str = "stable"  # improving, stable, declining
    trend_magnitude: float = 0.0  # 趋势幅度 (-1 to 1)
    
    # 综合评分
    overall_score: float = 0.0  # 综合团队评分 (0-100)
    health_status: str = "unknown"  # excellent, good, fair, poor, critical


@dataclass
class PerformanceBottleneck:
    """性能瓶颈"""
    bottleneck_id: str
    bottleneck_type: str  # agent, coordination, communication, resource, dependency
    severity: str  # critical, high, medium, low
    description: str
    affected_agents: List[str]
    metrics_impacted: List[str]
    root_cause: str
    estimated_impact: float  # 0-1 影响程度
    recommendations: List[str]
    severity_score: float = 0.0  # 严重程度评分 (0-1)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class OptimizationRecommendation:
    """优化建议"""
    recommendation_id: str
    priority: str  # critical, high, medium, low
    category: str  # agent_optimization, coordination, communication, resource_allocation
    description: str
    expected_benefit: float  # 0-1 预期收益
    implementation_cost: float  # 0-1 实施成本
    roi_score: float  # 投资回报率评分
    implementation_steps: List[str]
    prerequisites: List[str]
    validation_metrics: List[str]
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TeamPerformanceHistory:
    """团队绩效历史记录"""
    timestamp: datetime
    metrics: TeamPerformanceMetrics
    bottlenecks: List[PerformanceBottleneck]
    recommendations: List[OptimizationRecommendation]
    optimization_applied: List[str]  # 已应用的优化ID


class TeamPerformanceEvaluator:
    """团队绩效评估器"""
    
    def __init__(self, team_id: str, max_history: int = 1000):
        """
        初始化团队绩效评估器
        
        Args:
            team_id: 团队ID
            max_history: 最大历史记录数
        """
        self.team_id = team_id
        self.logger = logging.getLogger(f"{__name__}.{team_id}")
        
        # 数据存储
        self.agent_trackers: Dict[str, AgentPerformanceTracker] = {}
        self.coordinator: Optional[MultiAgentCoordinator] = None
        self.enhanced_coordinator: Optional[EnhancedCollaborationCoordinator] = None
        
        # 绩效历史
        self.performance_history: deque = deque(maxlen=max_history)
        self.bottleneck_history: deque = deque(maxlen=500)
        self.recommendation_history: deque = deque(maxlen=500)
        
        # 配置
        self.evaluation_interval = 300  # 评估间隔（秒）
        self._last_evaluation = 0
        self._running = False
        self._evaluation_task = None
        
        # 阈值配置
        self.thresholds = {
            "critical_health_score": 40.0,
            "poor_health_score": 60.0,
            "fair_health_score": 75.0,
            "good_health_score": 85.0,
            
            "bottleneck_critical": 0.8,  # 瓶颈严重程度阈值
            "bottleneck_high": 0.6,
            "bottleneck_medium": 0.4,
            
            "recommendation_critical_roi": 2.0,  # ROI阈值
            "recommendation_high_roi": 1.5,
            "recommendation_medium_roi": 1.0,
        }
        
        self.logger.info(f"团队绩效评估器初始化完成: {team_id}")
    
    def register_agent_tracker(self, agent_id: str, tracker: AgentPerformanceTracker) -> bool:
        """
        注册Agent性能跟踪器
        
        Args:
            agent_id: Agent ID
            tracker: 性能跟踪器实例
            
        Returns:
            是否注册成功
        """
        if agent_id in self.agent_trackers:
            self.logger.warning(f"Agent性能跟踪器已存在: {agent_id}")
            return False
        
        self.agent_trackers[agent_id] = tracker
        self.logger.info(f"注册Agent性能跟踪器: {agent_id}")
        return True
    
    def set_coordinator(self, coordinator: MultiAgentCoordinator) -> None:
        """设置多Agent协调器"""
        self.coordinator = coordinator
        self.logger.info("设置多Agent协调器")
    
    def set_enhanced_coordinator(self, coordinator: EnhancedCollaborationCoordinator) -> None:
        """设置增强协作协调器"""
        self.enhanced_coordinator = coordinator
        self.logger.info("设置增强协作协调器")
    
    async def start_periodic_evaluation(self) -> None:
        """启动定期评估"""
        if self._running:
            self.logger.warning("定期评估已在运行中")
            return
        
        self._running = True
        self._evaluation_task = asyncio.create_task(self._evaluation_loop())
        self.logger.info("启动定期团队绩效评估")
    
    async def stop_periodic_evaluation(self) -> None:
        """停止定期评估"""
        if not self._running:
            return
        
        self._running = False
        if self._evaluation_task:
            self._evaluation_task.cancel()
            try:
                await self._evaluation_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("停止定期团队绩效评估")
    
    async def _evaluation_loop(self) -> None:
        """评估循环"""
        while self._running:
            try:
                await self.evaluate_team_performance()
                await asyncio.sleep(self.evaluation_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"团队绩效评估失败: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟
    
    async def evaluate_team_performance(self) -> TeamPerformanceMetrics:
        """
        评估团队绩效
        
        Returns:
            团队绩效指标
        """
        self.logger.info(f"开始评估团队绩效: {self.team_id}")
        
        # 收集基础数据
        metrics = TeamPerformanceMetrics(team_id=self.team_id)
        
        # 收集Agent性能数据
        agent_metrics = await self._collect_agent_metrics()
        metrics.total_agents = len(self.agent_trackers)
        metrics.active_agents = len([aid for aid, stats in agent_metrics.items() if stats.get("is_active", False)])
        metrics.agent_health_scores = {aid: stats.get("health_score", 0) for aid, stats in agent_metrics.items()}
        metrics.agent_performance_stats = agent_metrics
        
        # 收集协作数据
        collaboration_metrics = await self._collect_collaboration_metrics()
        metrics.total_collaborations = collaboration_metrics.get("total_collaborations", 0)
        metrics.successful_collaborations = collaboration_metrics.get("successful_collaborations", 0)
        metrics.collaboration_success_rate = collaboration_metrics.get("success_rate", 0.0)
        metrics.avg_collaboration_time = collaboration_metrics.get("avg_collaboration_time", 0.0)
        metrics.avg_task_completion_rate = collaboration_metrics.get("avg_task_completion_rate", 0.0)
        
        # 计算效率指标
        efficiency_metrics = self._calculate_efficiency_metrics(agent_metrics, collaboration_metrics)
        metrics.communication_efficiency = efficiency_metrics.get("communication_efficiency", 0.0)
        metrics.coordination_efficiency = efficiency_metrics.get("coordination_efficiency", 0.0)
        metrics.resource_utilization = efficiency_metrics.get("resource_utilization", 0.0)
        metrics.load_balance_score = efficiency_metrics.get("load_balance_score", 0.0)
        
        # 计算质量指标
        quality_metrics = self._calculate_quality_metrics(agent_metrics, collaboration_metrics)
        metrics.result_quality = quality_metrics.get("result_quality", 0.0)
        metrics.conflict_resolution_rate = quality_metrics.get("conflict_resolution_rate", 0.0)
        metrics.consensus_achievement_rate = quality_metrics.get("consensus_achievement_rate", 0.0)
        
        # 识别瓶颈
        bottlenecks = await self._identify_bottlenecks(agent_metrics, collaboration_metrics, efficiency_metrics)
        metrics.identified_bottlenecks = bottlenecks
        if bottlenecks:
            metrics.bottleneck_severity = max(b.get("severity_score", 0) for b in bottlenecks)
        else:
            metrics.bottleneck_severity = 0.0
        
        # 计算综合评分
        overall_score, health_status = self._calculate_overall_score(metrics)
        metrics.overall_score = overall_score
        metrics.health_status = health_status
        
        # 分析趋势
        trend_analysis = self._analyze_performance_trend(metrics)
        metrics.performance_trend = trend_analysis.get("trend", "stable")
        metrics.trend_magnitude = trend_analysis.get("magnitude", 0.0)
        
        # 生成优化建议
        recommendations = await self._generate_optimization_recommendations(metrics, bottlenecks)
        
        # 保存历史记录
        history_entry = TeamPerformanceHistory(
            timestamp=datetime.now(),
            metrics=metrics,
            bottlenecks=[PerformanceBottleneck(**b) for b in bottlenecks],
            recommendations=[OptimizationRecommendation(**r) for r in recommendations],
            optimization_applied=[]
        )
        
        self.performance_history.append(history_entry)
        
        # 更新最后评估时间
        self._last_evaluation = time.time()
        
        self.logger.info(f"团队绩效评估完成: {self.team_id}, 综合评分: {overall_score:.2f}, 健康状态: {health_status}")
        
        return metrics
    
    async def _collect_agent_metrics(self) -> Dict[str, Dict[str, Any]]:
        """收集Agent性能指标"""
        agent_metrics = {}
        
        for agent_id, tracker in self.agent_trackers.items():
            try:
                # 获取性能统计
                stats = tracker.get_performance_stats()
                stats_dict = stats.__dict__ if hasattr(stats, '__dict__') else stats
                
                # 获取健康指标
                health = tracker.get_health_indicators()
                
                # 判断是否活跃
                is_active = (time.time() - tracker._last_activity) < 300 if hasattr(tracker, '_last_activity') else True
                
                agent_metrics[agent_id] = {
                    "performance_stats": stats_dict,
                    "health_score": health.get("health_score", 0),
                    "health_status": health.get("health_status", "unknown"),
                    "is_active": is_active,
                    "last_activity": tracker._last_activity if hasattr(tracker, '_last_activity') else 0,
                    "snapshot_count": len(tracker._snapshots) if hasattr(tracker, '_snapshots') else 0
                }
            except Exception as e:
                self.logger.error(f"收集Agent指标失败 {agent_id}: {e}")
                agent_metrics[agent_id] = {
                    "error": str(e),
                    "health_score": 0,
                    "health_status": "error",
                    "is_active": False
                }
        
        return agent_metrics
    
    async def _collect_collaboration_metrics(self) -> Dict[str, Any]:
        """收集协作指标"""
        collaboration_metrics = {
            "total_collaborations": 0,
            "successful_collaborations": 0,
            "success_rate": 0.0,
            "avg_collaboration_time": 0.0,
            "avg_task_completion_rate": 0.0,
            "conflict_count": 0,
            "conflicts_resolved": 0,
            "consensus_attempts": 0,
            "consensus_achieved": 0
        }
        
        try:
            # 从协调器获取协作统计
            if self.coordinator:
                stats = self.coordinator.get_collaboration_stats()
                collaboration_metrics.update({
                    "total_collaborations": stats.get("total_tasks_processed", 0),
                    "successful_collaborations": stats.get("successful_collaborations", 0),
                    "success_rate": stats.get("success_rate", 0.0),
                    "avg_collaboration_time": stats.get("average_task_duration", 0.0),
                    "active_tasks": stats.get("active_tasks", 0),
                    "conflicts_resolved": stats.get("collaboration_conflicts_resolved", 0)
                })
            
            # 从增强协作协调器获取更多指标
            if self.enhanced_coordinator:
                perf_report = self.enhanced_coordinator.get_performance_report()
                collaboration_metrics.update({
                    "total_collaborations_enhanced": perf_report.get("total_collaborations", 0),
                    "avg_efficiency": perf_report.get("average_efficiency", 0.0),
                    "recent_efficiency_history": perf_report.get("recent_efficiency_history", []),
                    "active_consensus_rounds": perf_report.get("active_consensus_rounds", 0)
                })
                
                # 如果有具体协作ID，获取更多细节
                if perf_report.get("total_collaborations", 0) > 0:
                    # 这里可以添加更多细节收集逻辑
                    pass
        except Exception as e:
            self.logger.error(f"收集协作指标失败: {e}")
        
        return collaboration_metrics
    
    def _calculate_efficiency_metrics(self, agent_metrics: Dict[str, Dict[str, Any]], 
                                     collaboration_metrics: Dict[str, Any]) -> Dict[str, float]:
        """计算效率指标"""
        efficiency = {
            "communication_efficiency": 0.0,
            "coordination_efficiency": 0.0,
            "resource_utilization": 0.0,
            "load_balance_score": 0.0
        }
        
        try:
            # 通信效率：基于Agent成功率和处理时间
            if agent_metrics:
                success_rates = [metrics.get("performance_stats", {}).get("success_rate", 0) 
                               for metrics in agent_metrics.values()]
                avg_success_rate = statistics.mean(success_rates) if success_rates else 0.0
                
                processing_times = [metrics.get("performance_stats", {}).get("average_processing_time", 0)
                                  for metrics in agent_metrics.values()]
                avg_processing_time = statistics.mean(processing_times) if processing_times else 0.0
                
                # 标准化处理时间（假设10秒为上限）
                normalized_time = 1.0 - min(avg_processing_time / 10.0, 1.0)
                
                efficiency["communication_efficiency"] = (avg_success_rate * 0.7 + normalized_time * 0.3)
            
            # 协调效率：基于协作成功率和时间
            if collaboration_metrics.get("total_collaborations", 0) > 0:
                success_rate = collaboration_metrics.get("success_rate", 0.0)
                avg_time = collaboration_metrics.get("avg_collaboration_time", 0.0)
                normalized_collab_time = 1.0 - min(avg_time / 60.0, 1.0)  # 假设60秒为上限
                
                efficiency["coordination_efficiency"] = (success_rate * 0.6 + normalized_collab_time * 0.4)
            
            # 资源利用率：基于活跃Agent比例和负载
            total_agents = len(agent_metrics)
            active_agents = sum(1 for metrics in agent_metrics.values() if metrics.get("is_active", False))
            
            if total_agents > 0:
                activity_ratio = active_agents / total_agents
                
                # 负载分析
                if self.coordinator and hasattr(self.coordinator, 'agent_capabilities'):
                    loads = [cap.current_load for cap in self.coordinator.agent_capabilities.values() 
                           if hasattr(cap, 'current_load')]
                    max_loads = [cap.max_concurrent_tasks for cap in self.coordinator.agent_capabilities.values()
                               if hasattr(cap, 'max_concurrent_tasks')]
                    
                    if loads and max_loads:
                        avg_utilization = sum(load / max_load for load, max_load in zip(loads, max_loads) if max_load > 0) / len(loads)
                        efficiency["resource_utilization"] = (activity_ratio * 0.4 + avg_utilization * 0.6)
                    else:
                        efficiency["resource_utilization"] = activity_ratio
                else:
                    efficiency["resource_utilization"] = activity_ratio
            
            # 负载均衡分数：基于Agent负载的标准差
            if self.coordinator and hasattr(self.coordinator, 'agent_capabilities'):
                loads = [cap.current_load for cap in self.coordinator.agent_capabilities.values() 
                       if hasattr(cap, 'current_load')]
                
                if loads:
                    if len(loads) > 1 and max(loads) > 0:
                        load_std = statistics.stdev(loads)
                        load_mean = statistics.mean(loads)
                        cv = load_std / load_mean if load_mean > 0 else 0
                        efficiency["load_balance_score"] = 1.0 - min(cv, 1.0)
                    else:
                        efficiency["load_balance_score"] = 1.0 if loads else 0.0
        
        except Exception as e:
            self.logger.error(f"计算效率指标失败: {e}")
        
        return efficiency
    
    def _calculate_quality_metrics(self, agent_metrics: Dict[str, Dict[str, Any]], 
                                  collaboration_metrics: Dict[str, Any]) -> Dict[str, float]:
        """计算质量指标"""
        quality = {
            "result_quality": 0.0,
            "conflict_resolution_rate": 0.0,
            "consensus_achievement_rate": 0.0
        }
        
        try:
            # 结果质量：基于Agent置信度和成功率
            if agent_metrics:
                confidences = [metrics.get("performance_stats", {}).get("average_confidence", 0)
                             for metrics in agent_metrics.values()]
                avg_confidence = statistics.mean(confidences) if confidences else 0.0
                
                success_rates = [metrics.get("performance_stats", {}).get("success_rate", 0)
                               for metrics in agent_metrics.values()]
                avg_success_rate = statistics.mean(success_rates) if success_rates else 0.0
                
                quality["result_quality"] = (avg_confidence * 0.6 + avg_success_rate * 0.4)
            
            # 冲突解决率
            conflict_count = collaboration_metrics.get("conflict_count", 0)
            conflicts_resolved = collaboration_metrics.get("conflicts_resolved", 0)
            
            if conflict_count > 0:
                quality["conflict_resolution_rate"] = conflicts_resolved / conflict_count
            else:
                quality["conflict_resolution_rate"] = 1.0  # 无冲突
            
            # 共识达成率
            consensus_attempts = collaboration_metrics.get("consensus_attempts", 0)
            consensus_achieved = collaboration_metrics.get("consensus_achieved", 0)
            
            if consensus_attempts > 0:
                quality["consensus_achievement_rate"] = consensus_achieved / consensus_attempts
            else:
                quality["consensus_achievement_rate"] = 1.0  # 无共识尝试
        
        except Exception as e:
            self.logger.error(f"计算质量指标失败: {e}")
        
        return quality
    
    async def _identify_bottlenecks(self, agent_metrics: Dict[str, Dict[str, Any]],
                                   collaboration_metrics: Dict[str, Any],
                                   efficiency_metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """识别性能瓶颈"""
        bottlenecks = []
        
        try:
            # 1. Agent性能瓶颈
            for agent_id, metrics in agent_metrics.items():
                health_score = metrics.get("health_score", 0)
                health_status = metrics.get("health_status", "unknown")
                
                if health_score < self.thresholds["critical_health_score"]:
                    bottlenecks.append({
                        "bottleneck_id": f"agent_critical_{agent_id}",
                        "bottleneck_type": "agent",
                        "severity": "critical",
                        "severity_score": 0.9,
                        "description": f"Agent {agent_id} 健康状态极差 ({health_score:.2f})",
                        "affected_agents": [agent_id],
                        "metrics_impacted": ["health_score", "success_rate", "processing_time"],
                        "root_cause": "Agent性能严重下降，可能需要重启或优化",
                        "estimated_impact": 0.8,
                        "recommendations": [
                            f"检查Agent {agent_id}的配置和资源",
                            f"分析Agent {agent_id}的近期错误日志",
                            f"考虑重启或替换Agent {agent_id}"
                        ]
                    })
                elif health_score < self.thresholds["poor_health_score"]:
                    bottlenecks.append({
                        "bottleneck_id": f"agent_poor_{agent_id}",
                        "bottleneck_type": "agent",
                        "severity": "high",
                        "severity_score": 0.7,
                        "description": f"Agent {agent_id} 健康状态不佳 ({health_score:.2f})",
                        "affected_agents": [agent_id],
                        "metrics_impacted": ["health_score", "success_rate"],
                        "root_cause": "Agent性能下降，影响整体团队表现",
                        "estimated_impact": 0.5,
                        "recommendations": [
                            f"监控Agent {agent_id}的性能趋势",
                            f"优化Agent {agent_id}的任务分配",
                            f"检查Agent {agent_id}的依赖资源"
                        ]
                    })
            
            # 2. 协调效率瓶颈
            coordination_efficiency = efficiency_metrics.get("coordination_efficiency", 0.0)
            if coordination_efficiency < 0.5:
                bottlenecks.append({
                    "bottleneck_id": "coordination_low_efficiency",
                    "bottleneck_type": "coordination",
                    "severity": "high",
                    "severity_score": 0.75,
                    "description": f"协调效率低下 ({coordination_efficiency:.2%})",
                    "affected_agents": list(agent_metrics.keys()),
                    "metrics_impacted": ["coordination_efficiency", "collaboration_success_rate", "avg_collaboration_time"],
                    "root_cause": "协作协调机制效率低，导致任务执行延迟和失败",
                    "estimated_impact": 0.6,
                    "recommendations": [
                        "优化协作协调算法",
                        "减少不必要的协调步骤",
                        "实现更智能的任务分配策略"
                    ]
                })
            
            # 3. 通信效率瓶颈
            communication_efficiency = efficiency_metrics.get("communication_efficiency", 0.0)
            if communication_efficiency < 0.6:
                bottlenecks.append({
                    "bottleneck_id": "communication_low_efficiency",
                    "bottleneck_type": "communication",
                    "severity": "medium",
                    "severity_score": 0.6,
                    "description": f"通信效率低下 ({communication_efficiency:.2%})",
                    "affected_agents": list(agent_metrics.keys()),
                    "metrics_impacted": ["communication_efficiency", "result_quality", "processing_time"],
                    "root_cause": "Agent间通信效率低，影响信息传递和协作",
                    "estimated_impact": 0.4,
                    "recommendations": [
                        "优化Agent间通信协议",
                        "减少通信开销",
                        "实现消息压缩和批处理"
                    ]
                })
            
            # 4. 负载不均衡瓶颈
            load_balance_score = efficiency_metrics.get("load_balance_score", 1.0)
            if load_balance_score < 0.7:
                bottlenecks.append({
                    "bottleneck_id": "load_imbalance",
                    "bottleneck_type": "resource",
                    "severity": "medium",
                    "severity_score": 0.5,
                    "description": f"负载不均衡 (均衡分数: {load_balance_score:.2f})",
                    "affected_agents": list(agent_metrics.keys()),
                    "metrics_impacted": ["load_balance_score", "resource_utilization", "avg_processing_time"],
                    "root_cause": "任务分配不均，部分Agent过载，部分闲置",
                    "estimated_impact": 0.3,
                    "recommendations": [
                        "改进负载均衡算法",
                        "实现动态任务重分配",
                        "监控并调整Agent容量"
                    ]
                })
            
            # 5. 资源利用率瓶颈
            resource_utilization = efficiency_metrics.get("resource_utilization", 0.0)
            if resource_utilization < 0.3:
                bottlenecks.append({
                    "bottleneck_id": "low_resource_utilization",
                    "bottleneck_type": "resource",
                    "severity": "low",
                    "severity_score": 0.4,
                    "description": f"资源利用率低 ({resource_utilization:.2%})",
                    "affected_agents": list(agent_metrics.keys()),
                    "metrics_impacted": ["resource_utilization", "active_agents_ratio"],
                    "root_cause": "Agent资源未充分利用，存在资源浪费",
                    "estimated_impact": 0.2,
                    "recommendations": [
                        "增加任务并发度",
                        "优化任务调度策略",
                        "合并或减少闲置Agent"
                    ]
                })
        
        except Exception as e:
            self.logger.error(f"识别瓶颈失败: {e}")
        
        # 按严重程度排序
        bottlenecks.sort(key=lambda x: x.get("severity_score", 0), reverse=True)
        
        return bottlenecks
    
    def _calculate_overall_score(self, metrics: TeamPerformanceMetrics) -> Tuple[float, str]:
        """计算综合评分"""
        overall_score = 0.0
        max_score = 100.0
        
        try:
            # 1. 基础性能权重 (30%)
            base_performance = 0.0
            
            # 协作成功率 (15%)
            collaboration_success = metrics.collaboration_success_rate * 15
            base_performance += collaboration_success
            
            # Agent健康度 (10%)
            if metrics.agent_health_scores:
                avg_agent_health = sum(metrics.agent_health_scores.values()) / len(metrics.agent_health_scores)
                agent_health_score = avg_agent_health * 10 / 100  # 转换为0-10分
                base_performance += agent_health_score
            
            # 任务完成率 (5%)
            task_completion = metrics.avg_task_completion_rate * 5
            base_performance += task_completion
            
            overall_score += base_performance
            
            # 2. 效率权重 (40%)
            efficiency_score = 0.0
            
            # 通信效率 (10%)
            communication_efficiency = metrics.communication_efficiency * 10
            efficiency_score += communication_efficiency
            
            # 协调效率 (15%)
            coordination_efficiency = metrics.coordination_efficiency * 15
            efficiency_score += coordination_efficiency
            
            # 资源利用率 (10%)
            resource_utilization = metrics.resource_utilization * 10
            efficiency_score += resource_utilization
            
            # 负载均衡 (5%)
            load_balance = metrics.load_balance_score * 5
            efficiency_score += load_balance
            
            overall_score += efficiency_score
            
            # 3. 质量权重 (20%)
            quality_score = 0.0
            
            # 结果质量 (10%)
            result_quality = metrics.result_quality * 10
            quality_score += result_quality
            
            # 冲突解决率 (5%)
            conflict_resolution = metrics.conflict_resolution_rate * 5
            quality_score += conflict_resolution
            
            # 共识达成率 (5%)
            consensus_achievement = metrics.consensus_achievement_rate * 5
            quality_score += consensus_achievement
            
            overall_score += quality_score
            
            # 4. 瓶颈惩罚 (10%)
            bottleneck_penalty = metrics.bottleneck_severity * 10
            overall_score = max(0, overall_score - bottleneck_penalty)
            
            # 确保不超过最大值
            overall_score = min(overall_score, max_score)
            
            # 确定健康状态
            if overall_score >= self.thresholds["good_health_score"]:
                health_status = "excellent" if overall_score >= 90 else "good"
            elif overall_score >= self.thresholds["fair_health_score"]:
                health_status = "fair"
            elif overall_score >= self.thresholds["poor_health_score"]:
                health_status = "poor"
            else:
                health_status = "critical"
        
        except Exception as e:
            self.logger.error(f"计算综合评分失败: {e}")
            overall_score = 0.0
            health_status = "error"
        
        return overall_score, health_status
    
    def _analyze_performance_trend(self, current_metrics: TeamPerformanceMetrics) -> Dict[str, Any]:
        """分析性能趋势"""
        trend_analysis = {
            "trend": "stable",
            "magnitude": 0.0,
            "confidence": 0.0,
            "key_indicators": []
        }
        
        try:
            if len(self.performance_history) < 3:
                return trend_analysis
            
            # 获取最近的历史记录
            recent_history = list(self.performance_history)[-5:]  # 最近5次评估
            if len(recent_history) < 3:
                return trend_analysis
            
            # 提取历史评分
            historical_scores = [entry.metrics.overall_score for entry in recent_history]
            historical_scores.append(current_metrics.overall_score)
            
            # 计算趋势
            if len(historical_scores) >= 3:
                recent_avg = statistics.mean(historical_scores[-2:])  # 最近两次
                older_avg = statistics.mean(historical_scores[:-2])  # 较早的
                
                if recent_avg > older_avg * 1.05:  # 提高5%以上
                    trend_analysis["trend"] = "improving"
                    trend_analysis["magnitude"] = (recent_avg - older_avg) / older_avg
                elif recent_avg < older_avg * 0.95:  # 降低5%以上
                    trend_analysis["trend"] = "declining"
                    trend_analysis["magnitude"] = (older_avg - recent_avg) / older_avg
                else:
                    trend_analysis["trend"] = "stable"
                    trend_analysis["magnitude"] = 0.0
                
                # 计算趋势置信度
                if len(historical_scores) >= 5:
                    # 使用线性回归或简单标准差
                    trend_analysis["confidence"] = 0.8  # 简化的置信度
        
        except Exception as e:
            self.logger.error(f"分析性能趋势失败: {e}")
        
        return trend_analysis
    
    async def _generate_optimization_recommendations(self, metrics: TeamPerformanceMetrics,
                                                    bottlenecks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成优化建议"""
        recommendations = []
        
        try:
            # 基于瓶颈生成建议
            for bottleneck in bottlenecks:
                bottleneck_id = bottleneck.get("bottleneck_id", "")
                severity = bottleneck.get("severity", "medium")
                severity_score = bottleneck.get("severity_score", 0.5)
                bottleneck_recommendations = bottleneck.get("recommendations", [])
                estimated_impact = bottleneck.get("estimated_impact", 0.3)
                
                if bottleneck_recommendations:
                    # 根据严重程度确定优先级
                    if severity_score >= 0.8:
                        priority = "critical"
                        roi_score = 2.5  # 高投资回报率
                    elif severity_score >= 0.6:
                        priority = "high"
                        roi_score = 2.0
                    elif severity_score >= 0.4:
                        priority = "medium"
                        roi_score = 1.5
                    else:
                        priority = "low"
                        roi_score = 1.0
                    
                    # 计算实施成本（基于瓶颈类型）
                    bottleneck_type = bottleneck.get("bottleneck_type", "unknown")
                    if bottleneck_type == "agent":
                        implementation_cost = 0.7  # Agent优化成本较高
                    elif bottleneck_type == "coordination":
                        implementation_cost = 0.5
                    elif bottleneck_type == "communication":
                        implementation_cost = 0.4
                    else:
                        implementation_cost = 0.3
                    
                    # 创建优化建议
                    recommendation = {
                        "recommendation_id": f"opt_{bottleneck_id}",
                        "priority": priority,
                        "category": f"{bottleneck_type}_optimization",
                        "description": f"解决瓶颈: {bottleneck.get('description', '')}",
                        "expected_benefit": estimated_impact,
                        "implementation_cost": implementation_cost,
                        "roi_score": roi_score,
                        "implementation_steps": bottleneck_recommendations,
                        "prerequisites": ["性能数据收集", "瓶颈验证"],
                        "validation_metrics": bottleneck.get("metrics_impacted", [])
                    }
                    
                    recommendations.append(recommendation)
            
            # 基于整体性能生成通用建议
            if metrics.overall_score < self.thresholds["good_health_score"]:
                if metrics.collaboration_success_rate < 0.8:
                    recommendations.append({
                        "recommendation_id": "opt_improve_collaboration_success",
                        "priority": "high" if metrics.collaboration_success_rate < 0.6 else "medium",
                        "category": "coordination_optimization",
                        "description": f"提高协作成功率 (当前: {metrics.collaboration_success_rate:.2%})",
                        "expected_benefit": 0.3,
                        "implementation_cost": 0.4,
                        "roi_score": 1.8,
                        "implementation_steps": [
                            "分析失败协作案例",
                            "优化任务分解策略",
                            "改进错误处理和重试机制"
                        ],
                        "prerequisites": ["失败案例数据"],
                        "validation_metrics": ["collaboration_success_rate", "successful_collaborations"]
                    })
                
                if metrics.communication_efficiency < 0.7:
                    recommendations.append({
                        "recommendation_id": "opt_improve_communication_efficiency",
                        "priority": "medium",
                        "category": "communication_optimization",
                        "description": f"提高通信效率 (当前: {metrics.communication_efficiency:.2%})",
                        "expected_benefit": 0.25,
                        "implementation_cost": 0.3,
                        "roi_score": 1.6,
                        "implementation_steps": [
                            "优化消息传递协议",
                            "减少通信延迟",
                            "实现通信压缩"
                        ],
                        "prerequisites": ["通信性能数据"],
                        "validation_metrics": ["communication_efficiency", "avg_processing_time"]
                    })
            
            # 按ROI评分排序
            recommendations.sort(key=lambda x: x.get("roi_score", 0), reverse=True)
        
        except Exception as e:
            self.logger.error(f"生成优化建议失败: {e}")
        
        return recommendations
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.performance_history:
            return {"error": "无性能历史数据"}
        
        latest_entry = self.performance_history[-1]
        metrics = latest_entry.metrics
        
        return {
            "team_id": self.team_id,
            "timestamp": latest_entry.timestamp.isoformat(),
            "overall_score": metrics.overall_score,
            "health_status": metrics.health_status,
            "performance_trend": metrics.performance_trend,
            "trend_magnitude": metrics.trend_magnitude,
            "key_metrics": {
                "collaboration_success_rate": metrics.collaboration_success_rate,
                "communication_efficiency": metrics.communication_efficiency,
                "coordination_efficiency": metrics.coordination_efficiency,
                "resource_utilization": metrics.resource_utilization,
                "result_quality": metrics.result_quality
            },
            "bottleneck_count": len(metrics.identified_bottlenecks),
            "critical_bottlenecks": len([b for b in metrics.identified_bottlenecks 
                                        if b.get("severity") in ["critical", "high"]]),
            "recommendation_count": len(latest_entry.recommendations),
            "top_recommendations": [r.__dict__ for r in latest_entry.recommendations[:3]] if hasattr(latest_entry.recommendations[0], '__dict__') 
                                 else latest_entry.recommendations[:3]
        }
    
    def export_performance_report(self, format: str = "json") -> str:
        """导出性能报告"""
        if not self.performance_history:
            return json.dumps({"error": "无性能历史数据"})
        
        latest_entry = self.performance_history[-1]
        
        report = {
            "team_id": self.team_id,
            "report_timestamp": datetime.now().isoformat(),
            "evaluation_period": {
                "start": self.performance_history[0].timestamp.isoformat() if self.performance_history else None,
                "end": latest_entry.timestamp.isoformat()
            },
            "current_performance": latest_entry.metrics.__dict__,
            "historical_summary": {
                "total_evaluations": len(self.performance_history),
                "average_score": statistics.mean([entry.metrics.overall_score for entry in self.performance_history]) 
                               if self.performance_history else 0.0,
                "score_trend": [entry.metrics.overall_score for entry in self.performance_history],
                "health_history": [entry.metrics.health_status for entry in self.performance_history]
            },
            "active_bottlenecks": [b.__dict__ for b in latest_entry.bottlenecks] if hasattr(latest_entry.bottlenecks[0], '__dict__')
                               else latest_entry.bottlenecks,
            "optimization_recommendations": [r.__dict__ for r in latest_entry.recommendations] if hasattr(latest_entry.recommendations[0], '__dict__')
                                          else latest_entry.recommendations,
            "applied_optimizations": latest_entry.optimization_applied,
            "analysis_insights": self._generate_analysis_insights()
        }
        
        if format == "json":
            return json.dumps(report, indent=2, ensure_ascii=False)
        else:
            # 可以添加其他格式支持
            return json.dumps(report, indent=2, ensure_ascii=False)
    
    def _generate_analysis_insights(self) -> List[str]:
        """生成分析洞察"""
        insights = []
        
        if not self.performance_history:
            return insights
        
        latest_entry = self.performance_history[-1]
        metrics = latest_entry.metrics
        
        # 基于评分的洞察
        if metrics.overall_score >= 85:
            insights.append("团队表现优秀，继续保持当前优化策略")
        elif metrics.overall_score >= 70:
            insights.append("团队表现良好，有进一步优化空间")
        elif metrics.overall_score >= 50:
            insights.append("团队表现一般，建议关注主要瓶颈")
        else:
            insights.append("团队表现不佳，需要立即采取优化措施")
        
        # 基于趋势的洞察
        if metrics.performance_trend == "improving":
            insights.append(f"团队表现正在改善，改善幅度: {metrics.trend_magnitude:.1%}")
        elif metrics.performance_trend == "declining":
            insights.append(f"团队表现正在下降，下降幅度: {metrics.trend_magnitude:.1%}")
        
        # 基于瓶颈的洞察
        if metrics.identified_bottlenecks:
            critical_bottlenecks = [b for b in metrics.identified_bottlenecks 
                                  if b.get("severity") in ["critical", "high"]]
            
            if critical_bottlenecks:
                bottleneck_types = set(b.get("bottleneck_type", "unknown") for b in critical_bottlenecks)
                insights.append(f"发现{len(critical_bottlenecks)}个关键瓶颈，主要类型: {', '.join(bottleneck_types)}")
            else:
                insights.append("当前瓶颈均为中低风险，可按计划优化")
        
        # 基于效率指标的洞察
        if metrics.communication_efficiency < 0.7:
            insights.append("通信效率有待提高，建议优化Agent间通信机制")
        
        if metrics.coordination_efficiency < 0.7:
            insights.append("协调效率有待提高，建议优化任务分配和调度策略")
        
        if metrics.resource_utilization < 0.5:
            insights.append("资源利用率较低，建议调整Agent配置和任务分配")
        
        return insights
    
    async def apply_optimization(self, recommendation_id: str) -> Dict[str, Any]:
        """
        应用优化建议
        
        Args:
            recommendation_id: 建议ID
            
        Returns:
            应用结果
        """
        # 这里应该实现具体的优化应用逻辑
        # 当前为占位实现
        
        result = {
            "recommendation_id": recommendation_id,
            "applied": False,
            "timestamp": datetime.now().isoformat(),
            "message": "优化应用功能待实现"
        }
        
        return result


# 全局团队绩效评估器实例
_team_performance_evaluator_instances = {}


def get_team_performance_evaluator(team_id: str = "default_team", 
                                   max_history: int = 1000) -> TeamPerformanceEvaluator:
    """获取团队绩效评估器实例"""
    global _team_performance_evaluator_instances
    
    if team_id not in _team_performance_evaluator_instances:
        _team_performance_evaluator_instances[team_id] = TeamPerformanceEvaluator(
            team_id=team_id, max_history=max_history
        )
    
    return _team_performance_evaluator_instances[team_id]