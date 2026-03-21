#!/usr/bin/env python3
"""
自进化引擎
Self-Evolution Engine

V3核心理念：基于反思和改进循环的自进化能力。
实现性能反思和分析、配置自适应调整、能力动态扩展、经验学习和优化、架构自我调整。
"""
import asyncio
import logging
import time
import json
import pickle
from typing import Dict, List, Any, Optional, Callable, Tuple
from enum import Enum
from datetime import datetime, timedelta
import hashlib
import statistics

logger = logging.getLogger(__name__)


class EvolutionPhase(Enum):
    """进化阶段"""
    MONITORING = "monitoring"      # 监控阶段
    ANALYSIS = "analysis"          # 分析阶段
    REFLECTION = "reflection"      # 反思阶段
    ADAPTATION = "adaptation"      # 适应阶段
    DEPLOYMENT = "deployment"      # 部署阶段


class PerformanceMetric(Enum):
    """性能指标"""
    RESPONSE_TIME = "response_time"
    SUCCESS_RATE = "success_rate"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    RESOURCE_USAGE = "resource_usage"
    USER_SATISFACTION = "user_satisfaction"


class ImprovementSuggestion:
    """改进建议"""
    
    def __init__(
        self,
        suggestion_id: str,
        description: str,
        area: str,
        priority: int,
        expected_impact: float,
        implementation_cost: int,
        rationale: str,
        suggested_changes: Dict[str, Any]
    ):
        self.suggestion_id = suggestion_id
        self.description = description
        self.area = area  # performance, configuration, capability, architecture
        self.priority = priority  # 1-5, 5为最高
        self.expected_impact = expected_impact  # 0-1, 预期改进程度
        self.implementation_cost = implementation_cost  # 1-5, 实施成本
        self.rationale = rationale
        self.suggested_changes = suggested_changes
        self.created_at = time.time()
        self.status = "pending"  # pending, approved, implemented, rejected
        self.implemented_at: Optional[float] = None
        self.actual_impact: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "suggestion_id": self.suggestion_id,
            "description": self.description,
            "area": self.area,
            "priority": self.priority,
            "expected_impact": self.expected_impact,
            "implementation_cost": self.implementation_cost,
            "rationale": self.rationale,
            "suggested_changes": self.suggested_changes,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "status": self.status,
            "implemented_at": datetime.fromtimestamp(self.implemented_at).isoformat() if self.implemented_at else None,
            "actual_impact": self.actual_impact
        }
    
    def calculate_roi(self) -> float:
        """计算投资回报率（ROI）"""
        if self.implementation_cost == 0:
            return float('inf')
        return self.expected_impact / self.implementation_cost


class PerformanceSnapshot:
    """性能快照"""
    
    def __init__(self, snapshot_id: str):
        self.snapshot_id = snapshot_id
        self.timestamp = time.time()
        self.metrics: Dict[str, float] = {}
        self.context: Dict[str, Any] = {}
        self.annotations: List[str] = []
    
    def add_metric(self, metric_name: str, value: float):
        """添加指标"""
        self.metrics[metric_name] = value
    
    def add_context(self, key: str, value: Any):
        """添加上下文信息"""
        self.context[key] = value
    
    def add_annotation(self, annotation: str):
        """添加注释"""
        self.annotations.append(annotation)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": datetime.fromtimestamp(self.timestamp).isoformat(),
            "metrics": self.metrics,
            "context": self.context,
            "annotations": self.annotations
        }


class ExperienceMemory:
    """经验记忆"""
    
    def __init__(self, memory_id: str):
        self.memory_id = memory_id
        self.created_at = time.time()
        self.experience_type: str = ""
        self.description: str = ""
        self.key_insights: List[str] = []
        self.success_patterns: List[Dict[str, Any]] = []
        self.failure_patterns: List[Dict[str, Any]] = []
        self.learned_lessons: List[str] = []
        self.applicable_contexts: List[Dict[str, Any]] = []
        self.usage_count: int = 0
        self.last_used: Optional[float] = None
        self.effectiveness_score: float = 0.0
    
    def record_success(self, pattern: Dict[str, Any], context: Dict[str, Any]):
        """记录成功模式"""
        self.success_patterns.append({
            "pattern": pattern,
            "context": context,
            "recorded_at": time.time()
        })
    
    def record_failure(self, pattern: Dict[str, Any], context: Dict[str, Any], analysis: str):
        """记录失败模式"""
        self.failure_patterns.append({
            "pattern": pattern,
            "context": context,
            "analysis": analysis,
            "recorded_at": time.time()
        })
    
    def add_insight(self, insight: str):
        """添加关键洞察"""
        self.key_insights.append(insight)
    
    def add_lesson(self, lesson: str):
        """添加学习教训"""
        self.learned_lessons.append(lesson)
    
    def mark_used(self, effectiveness: float = 1.0):
        """标记使用"""
        self.usage_count += 1
        self.last_used = time.time()
        self.effectiveness_score = (self.effectiveness_score * (self.usage_count - 1) + effectiveness) / self.usage_count
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "experience_type": self.experience_type,
            "description": self.description,
            "key_insights": self.key_insights,
            "success_patterns_count": len(self.success_patterns),
            "failure_patterns_count": len(self.failure_patterns),
            "learned_lessons": self.learned_lessons,
            "usage_count": self.usage_count,
            "last_used": datetime.fromtimestamp(self.last_used).isoformat() if self.last_used else None,
            "effectiveness_score": self.effectiveness_score
        }


class SelfEvolutionEngine:
    """自进化引擎"""
    
    def __init__(self, engine_id: str = "evolution_engine_001"):
        self.engine_id = engine_id
        self.current_phase = EvolutionPhase.MONITORING
        self.performance_snapshots: List[PerformanceSnapshot] = []
        self.improvement_suggestions: List[ImprovementSuggestion] = []
        self.experience_memories: List[ExperienceMemory] = []
        self.config_history: List[Dict[str, Any]] = []
        self.evolution_cycles: int = 0
        self.last_evolution_time: float = 0.0
        
        # 进化配置
        self.evolution_config = {
            "monitoring_interval_seconds": 300,  # 5分钟
            "analysis_depth": "medium",  # low, medium, high
            "adaptation_aggressiveness": 0.3,  # 0-1, 适应激进程度
            "max_suggestions_per_cycle": 10,
            "auto_implement_low_cost": True,  # 自动实施低成本改进
            "learning_enabled": True
        }
        
        logger.info(f"自进化引擎初始化完成: {engine_id}")
    
    async def start_monitoring(self):
        """开始监控阶段"""
        self.current_phase = EvolutionPhase.MONITORING
        logger.info(f"进化引擎进入监控阶段 (周期: {self.evolution_cycles + 1})")
        
        # 收集性能数据
        snapshot = await self.collect_performance_snapshot()
        self.performance_snapshots.append(snapshot)
        
        # 限制快照数量
        max_snapshots = 100
        if len(self.performance_snapshots) > max_snapshots:
            self.performance_snapshots = self.performance_snapshots[-max_snapshots:]
        
        logger.info(f"收集性能快照: {snapshot.snapshot_id}, 指标数: {len(snapshot.metrics)}")
    
    async def collect_performance_snapshot(self) -> PerformanceSnapshot:
        """收集性能快照"""
        snapshot_id = f"snapshot_{int(time.time())}_{len(self.performance_snapshots)}"
        snapshot = PerformanceSnapshot(snapshot_id)
        
        # 收集系统指标（这里需要集成现有的指标收集系统）
        try:
            # 模拟收集一些指标
            snapshot.add_metric("response_time_ms", 150.5)
            snapshot.add_metric("success_rate", 0.95)
            snapshot.add_metric("error_rate", 0.05)
            snapshot.add_metric("throughput_rps", 10.2)
            snapshot.add_metric("cpu_usage_percent", 25.0)
            snapshot.add_metric("memory_usage_percent", 40.0)
            
            # 添加上下文
            snapshot.add_context("system_load", "medium")
            snapshot.add_context("active_users", 5)
            snapshot.add_context("time_of_day", datetime.now().hour)
            
            # 添加注释
            snapshot.add_annotation("常规性能监控")
            
        except Exception as e:
            logger.error(f"收集性能指标失败: {e}")
            snapshot.add_annotation(f"指标收集错误: {e}")
        
        return snapshot
    
    async def analyze_performance(self):
        """分析性能阶段"""
        self.current_phase = EvolutionPhase.ANALYSIS
        logger.info("进化引擎进入分析阶段")
        
        if len(self.performance_snapshots) < 2:
            logger.warning("性能快照不足，跳过分析阶段")
            return
        
        # 分析性能趋势
        latest_snapshot = self.performance_snapshots[-1]
        previous_snapshot = self.performance_snapshots[-2] if len(self.performance_snapshots) >= 2 else None
        
        analysis_results = await self._analyze_performance_trends(latest_snapshot, previous_snapshot)
        
        # 生成改进建议
        suggestions = await self._generate_improvement_suggestions(analysis_results)
        
        # 添加建议到列表
        for suggestion in suggestions:
            self.improvement_suggestions.append(suggestion)
            logger.info(f"生成改进建议: {suggestion.description} (优先级: {suggestion.priority})")
        
        # 限制建议数量
        max_suggestions = self.evolution_config["max_suggestions_per_cycle"]
        if len(self.improvement_suggestions) > max_suggestions:
            self.improvement_suggestions = self.improvement_suggestions[-max_suggestions:]
    
    async def _analyze_performance_trends(
        self, 
        latest: PerformanceSnapshot, 
        previous: Optional[PerformanceSnapshot]
    ) -> Dict[str, Any]:
        """分析性能趋势"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "performance_changes": {},
            "issues_detected": [],
            "opportunities": []
        }
        
        if previous is None:
            analysis["issues_detected"].append("缺乏历史数据进行比较分析")
            return analysis
        
        # 分析关键指标变化
        key_metrics = ["response_time_ms", "success_rate", "error_rate", "throughput_rps"]
        
        for metric in key_metrics:
            if metric in latest.metrics and metric in previous.metrics:
                latest_value = latest.metrics[metric]
                previous_value = previous.metrics[metric]
                
                if previous_value != 0:
                    change_percent = ((latest_value - previous_value) / abs(previous_value)) * 100
                    analysis["performance_changes"][metric] = {
                        "latest": latest_value,
                        "previous": previous_value,
                        "change_percent": change_percent,
                        "trend": "improving" if (metric in ["success_rate", "throughput_rps"] and change_percent > 0) or 
                                           (metric in ["response_time_ms", "error_rate"] and change_percent < 0) 
                                   else "degrading" if change_percent != 0 else "stable"
                    }
                    
                    # 检测问题
                    if metric == "response_time_ms" and latest_value > 500:
                        analysis["issues_detected"].append(f"响应时间过高: {latest_value}ms")
                    elif metric == "error_rate" and latest_value > 0.1:
                        analysis["issues_detected"].append(f"错误率过高: {latest_value*100:.1f}%")
                    elif metric == "success_rate" and latest_value < 0.9:
                        analysis["issues_detected"].append(f"成功率过低: {latest_value*100:.1f}%")
        
        # 检测机会
        if "cpu_usage_percent" in latest.metrics and latest.metrics["cpu_usage_percent"] < 20:
            analysis["opportunities"].append("CPU使用率低，可增加处理能力")
        
        if "memory_usage_percent" in latest.metrics and latest.metrics["memory_usage_percent"] < 30:
            analysis["opportunities"].append("内存使用率低，可优化缓存策略")
        
        return analysis
    
    async def _generate_improvement_suggestions(self, analysis: Dict[str, Any]) -> List[ImprovementSuggestion]:
        """生成改进建议"""
        suggestions = []
        
        # 基于检测到的问题生成建议
        for issue in analysis.get("issues_detected", []):
            suggestion_id = f"suggestion_{int(time.time())}_{len(suggestions)}"
            
            if "响应时间过高" in issue:
                suggestion = ImprovementSuggestion(
                    suggestion_id=suggestion_id,
                    description="优化系统响应时间",
                    area="performance",
                    priority=4,
                    expected_impact=0.7,
                    implementation_cost=3,
                    rationale=f"检测到响应时间问题: {issue}",
                    suggested_changes={
                        "action": "优化数据库查询",
                        "config_changes": {"database_pool_size": "increase"},
                        "monitoring_focus": ["response_time_ms", "query_duration"]
                    }
                )
                suggestions.append(suggestion)
            
            elif "错误率过高" in issue:
                suggestion = ImprovementSuggestion(
                    suggestion_id=suggestion_id,
                    description="降低系统错误率",
                    area="performance",
                    priority=5,
                    expected_impact=0.8,
                    implementation_cost=2,
                    rationale=f"检测到错误率问题: {issue}",
                    suggested_changes={
                        "action": "增强错误处理和重试机制",
                        "config_changes": {"max_retries": 3, "retry_delay_ms": 1000},
                        "monitoring_focus": ["error_rate", "exception_types"]
                    }
                )
                suggestions.append(suggestion)
        
        # 基于机会生成建议
        for opportunity in analysis.get("opportunities", []):
            suggestion_id = f"suggestion_{int(time.time())}_{len(suggestions)}"
            
            if "CPU使用率低" in opportunity:
                suggestion = ImprovementSuggestion(
                    suggestion_id=suggestion_id,
                    description="利用空闲CPU资源",
                    area="configuration",
                    priority=2,
                    expected_impact=0.3,
                    implementation_cost=1,
                    rationale=opportunity,
                    suggested_changes={
                        "action": "增加并发处理线程",
                        "config_changes": {"worker_threads": "increase_by_50%"},
                        "monitoring_focus": ["cpu_usage_percent", "throughput_rps"]
                    }
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    async def reflect_and_learn(self):
        """反思和学习阶段"""
        self.current_phase = EvolutionPhase.REFLECTION
        logger.info("进化引擎进入反思阶段")
        
        # 从最近的改进中学习
        recent_suggestions = [s for s in self.improvement_suggestions 
                             if s.status == "implemented" and 
                             s.implemented_at and 
                             (time.time() - s.implemented_at) < 86400]  # 24小时内
        
        for suggestion in recent_suggestions:
            await self._learn_from_improvement(suggestion)
        
        # 从经验记忆中学习
        await self._apply_experience_learning()
    
    async def _learn_from_improvement(self, suggestion: ImprovementSuggestion):
        """从改进中学习"""
        memory_id = f"memory_{int(time.time())}_{len(self.experience_memories)}"
        memory = ExperienceMemory(memory_id)
        memory.experience_type = "improvement_implementation"
        memory.description = f"实施改进: {suggestion.description}"
        
        # 记录成功或失败
        if suggestion.actual_impact is not None:
            if suggestion.actual_impact >= suggestion.expected_impact * 0.8:
                # 成功
                memory.record_success(
                    pattern={"improvement_type": suggestion.area, "implementation": suggestion.suggested_changes},
                    context={"expected_impact": suggestion.expected_impact, "actual_impact": suggestion.actual_impact}
                )
                memory.add_insight(f"{suggestion.area}类型的改进在类似上下文中有效")
            else:
                # 失败或效果不佳
                memory.record_failure(
                    pattern={"improvement_type": suggestion.area, "implementation": suggestion.suggested_changes},
                    context={"expected_impact": suggestion.expected_impact, "actual_impact": suggestion.actual_impact},
                    analysis=f"实际效果({suggestion.actual_impact:.2f})低于预期({suggestion.expected_impact:.2f})"
                )
                memory.add_lesson(f"{suggestion.area}类型的改进在此上下文中效果不佳")
        
        memory.add_lesson(f"实施{suggestion.area}改进的成本为{suggestion.implementation_cost}")
        
        self.experience_memories.append(memory)
        logger.info(f"创建经验记忆: {memory_id}")
    
    async def _apply_experience_learning(self):
        """应用经验学习"""
        # 查找相关经验记忆
        relevant_memories = []
        for memory in self.experience_memories:
            if memory.usage_count < 5 and memory.effectiveness_score > 0.7:
                relevant_memories.append(memory)
        
        # 应用学习到的经验
        for memory in relevant_memories[-5:]:  # 最近5个相关记忆
            logger.info(f"应用经验记忆: {memory.memory_id}, 洞察: {memory.key_insights[:1]}")
            memory.mark_used()
    
    async def adapt_configuration(self):
        """适应配置阶段"""
        self.current_phase = EvolutionPhase.ADAPTATION
        logger.info("进化引擎进入适应阶段")
        
        # 评估并实施高优先级、低成本的改进
        pending_suggestions = [s for s in self.improvement_suggestions if s.status == "pending"]
        
        for suggestion in pending_suggestions:
            # 计算ROI
            roi = suggestion.calculate_roi()
            
            # 自动实施低成本高ROI的改进
            if (suggestion.implementation_cost <= 2 and roi > 0.5 and 
                self.evolution_config["auto_implement_low_cost"]):
                
                logger.info(f"自动实施改进: {suggestion.description} (成本: {suggestion.implementation_cost}, ROI: {roi:.2f})")
                await self._implement_suggestion(suggestion)
    
    async def _implement_suggestion(self, suggestion: ImprovementSuggestion):
        """实施改进建议"""
        try:
            # 记录当前配置
            current_config = await self._capture_current_config()
            self.config_history.append({
                "timestamp": time.time(),
                "config": current_config,
                "change_reason": f"实施改进: {suggestion.description}"
            })
            
            # 实施建议的更改
            # 这里需要根据suggested_changes实际修改系统配置
            # 当前为模拟实现
            logger.info(f"实施配置更改: {suggestion.suggested_changes}")
            
            # 标记为已实施
            suggestion.status = "implemented"
            suggestion.implemented_at = time.time()
            # 模拟实际效果（在真实系统中需要后续测量）
            suggestion.actual_impact = suggestion.expected_impact * 0.8  # 假设达到80%预期效果
            
            logger.info(f"改进实施完成: {suggestion.description}")
            
        except Exception as e:
            logger.error(f"实施改进失败 {suggestion.suggestion_id}: {e}")
            suggestion.status = "failed"
    
    async def _capture_current_config(self) -> Dict[str, Any]:
        """捕获当前配置"""
        # 这里需要集成实际的配置收集
        return {
            "timestamp": time.time(),
            "system_config": {
                "evolution_config": self.evolution_config,
                "engine_id": self.engine_id
            }
        }
    
    async def deploy_changes(self):
        """部署更改阶段"""
        self.current_phase = EvolutionPhase.DEPLOYMENT
        logger.info("进化引擎进入部署阶段")
        
        # 记录进化周期完成
        self.evolution_cycles += 1
        self.last_evolution_time = time.time()
        
        # 生成进化报告
        report = await self.generate_evolution_report()
        
        logger.info(f"进化周期 {self.evolution_cycles} 完成: {report['summary']}")
        
        # 重置阶段
        self.current_phase = EvolutionPhase.MONITORING
    
    async def run_evolution_cycle(self):
        """运行完整的进化周期"""
        logger.info(f"开始进化周期 {self.evolution_cycles + 1}")
        
        try:
            await self.start_monitoring()
            await asyncio.sleep(1)  # 模拟监控间隔
            
            await self.analyze_performance()
            await self.reflect_and_learn()
            await self.adapt_configuration()
            await self.deploy_changes()
            
            logger.info(f"进化周期 {self.evolution_cycles} 完成")
            
        except Exception as e:
            logger.error(f"进化周期执行失败: {e}")
            self.current_phase = EvolutionPhase.MONITORING
    
    async def generate_evolution_report(self) -> Dict[str, Any]:
        """生成进化报告"""
        return {
            "timestamp": datetime.now().isoformat(),
            "engine_id": self.engine_id,
            "evolution_cycle": self.evolution_cycles,
            "current_phase": self.current_phase.value,
            "performance_snapshots_count": len(self.performance_snapshots),
            "improvement_suggestions_count": len(self.improvement_suggestions),
            "implemented_suggestions_count": len([s for s in self.improvement_suggestions if s.status == "implemented"]),
            "experience_memories_count": len(self.experience_memories),
            "config_history_count": len(self.config_history),
            "summary": f"完成 {self.evolution_cycles} 个进化周期，生成 {len(self.improvement_suggestions)} 个改进建议",
            "recent_suggestions": [s.to_dict() for s in self.improvement_suggestions[-3:]] if self.improvement_suggestions else [],
            "top_insights": [m.key_insights[0] for m in self.experience_memories[-3:] if m.key_insights] if self.experience_memories else []
        }
    
    async def get_engine_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            "engine_id": self.engine_id,
            "current_phase": self.current_phase.value,
            "evolution_cycles": self.evolution_cycles,
            "last_evolution_time": datetime.fromtimestamp(self.last_evolution_time).isoformat() if self.last_evolution_time else None,
            "uptime_hours": (time.time() - self.last_evolution_time) / 3600 if self.last_evolution_time else 0,
            "config": self.evolution_config,
            "metrics": {
                "performance_snapshots": len(self.performance_snapshots),
                "improvement_suggestions": len(self.improvement_suggestions),
                "experience_memories": len(self.experience_memories),
                "config_changes": len(self.config_history)
            }
        }


# 全局实例和便捷函数
_evolution_engine: Optional[SelfEvolutionEngine] = None

def get_self_evolution_engine() -> SelfEvolutionEngine:
    """获取自进化引擎实例"""
    global _evolution_engine
    if _evolution_engine is None:
        _evolution_engine = SelfEvolutionEngine()
    return _evolution_engine

async def start_evolution_engine():
    """启动自进化引擎（便捷函数）"""
    engine = get_self_evolution_engine()
    # 这里可以启动定期进化周期
    logger.info("自进化引擎已就绪")

async def run_evolution_cycle():
    """运行进化周期（便捷函数）"""
    engine = get_self_evolution_engine()
    await engine.run_evolution_cycle()


if __name__ == "__main__":
    # 测试代码
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    async def test_evolution_engine():
        print("=" * 60)
        print("测试自进化引擎")
        print("=" * 60)
        
        engine = SelfEvolutionEngine("test_engine")
        
        # 运行一个完整的进化周期
        await engine.run_evolution_cycle()
        
        # 获取状态
        status = await engine.get_engine_status()
        print(f"引擎状态:")
        print(f"  引擎ID: {status['engine_id']}")
        print(f"  当前阶段: {status['current_phase']}")
        print(f"  进化周期: {status['evolution_cycles']}")
        print(f"  性能快照: {status['metrics']['performance_snapshots']}")
        print(f"  改进建议: {status['metrics']['improvement_suggestions']}")
        
        # 生成报告
        report = await engine.generate_evolution_report()
        print(f"\n进化报告:")
        print(f"  总结: {report['summary']}")
        
        print("=" * 60)
        print("✅ 自进化引擎测试完成")
        print("=" * 60)
    
    asyncio.run(test_evolution_engine())