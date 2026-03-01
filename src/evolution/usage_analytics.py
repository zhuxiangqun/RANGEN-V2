#!/usr/bin/env python3
"""
使用数据分析与优化建议系统
收集系统使用数据，分析模式，为进化提供智能建议
"""

import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json

from ..hook.hook_types import HookEventType, HookEvent
from ..hook.transparency import HookTransparencySystem


class SuggestionType(Enum):
    """优化建议类型"""
    HAND_IMPROVEMENT = "hand_improvement"  # Hand能力改进
    HAND_CREATION = "hand_creation"  # 创建新Hand
    EVOLUTION_PRIORITY = "evolution_priority"  # 进化优先级调整
    PERFORMANCE_OPTIMIZATION = "performance_optimization"  # 性能优化
    USABILITY_IMPROVEMENT = "usability_improvement"  # 可用性改进
    INTEGRATION_ENHANCEMENT = "integration_enhancement"  # 集成增强


class SuggestionPriority(Enum):
    """建议优先级"""
    CRITICAL = "critical"  # 关键
    HIGH = "high"  # 高
    MEDIUM = "medium"  # 中
    LOW = "low"  # 低


@dataclass
class HandUsageStats:
    """Hand使用统计"""
    hand_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_execution_time: float = 0.0
    last_execution_time: Optional[datetime] = None
    avg_execution_time: float = 0.0
    success_rate: float = 0.0
    
    def update(self, success: bool, execution_time: float):
        """更新统计"""
        self.total_executions += 1
        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1
            
        self.total_execution_time += execution_time
        self.last_execution_time = datetime.now()
        
        if self.total_executions > 0:
            self.avg_execution_time = self.total_execution_time / self.total_executions
            self.success_rate = self.successful_executions / self.total_executions


@dataclass
class EvolutionUsageStats:
    """进化使用统计"""
    plan_id: str
    execution_count: int = 0
    successful_count: int = 0
    failed_count: int = 0
    avg_execution_time: float = 0.0
    performance_improvement: float = 0.0  # 性能改进百分比
    last_execution_time: Optional[datetime] = None


@dataclass
class OptimizationSuggestion:
    """优化建议"""
    suggestion_id: str
    suggestion_type: SuggestionType
    title: str
    description: str
    priority: SuggestionPriority
    target_component: str  # 目标组件（hand名称、模块等）
    data_evidence: Dict[str, Any]  # 数据证据
    estimated_impact: str  # 预计影响
    implementation_effort: int  # 实施工作量（小时）
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending, approved, rejected, implemented


class UsageAnalytics:
    """使用数据分析系统"""
    
    def __init__(self, system_name: str = "default"):
        self.system_name = system_name
        self.logger = logging.getLogger(__name__)
        
        # 初始化数据库
        self.db_path = Path(f"usage_analytics_{system_name}.db")
        self._init_database()
        
        # 内存缓存
        self.hand_stats: Dict[str, HandUsageStats] = {}
        self.evolution_stats: Dict[str, EvolutionUsageStats] = {}
        self.suggestions: Dict[str, OptimizationSuggestion] = {}
        
        # Hook系统订阅
        self.hook_system = HookTransparencySystem(system_name)
        
        self.logger.info(f"使用分析系统初始化: {system_name}")
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Hand使用统计表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hand_usage_stats (
                hand_name TEXT PRIMARY KEY,
                total_executions INTEGER DEFAULT 0,
                successful_executions INTEGER DEFAULT 0,
                failed_executions INTEGER DEFAULT 0,
                total_execution_time REAL DEFAULT 0.0,
                last_execution_time TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 进化使用统计表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evolution_usage_stats (
                plan_id TEXT PRIMARY KEY,
                execution_count INTEGER DEFAULT 0,
                successful_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                avg_execution_time REAL DEFAULT 0.0,
                performance_improvement REAL DEFAULT 0.0,
                last_execution_time TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 优化建议表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_suggestions (
                suggestion_id TEXT PRIMARY KEY,
                suggestion_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT NOT NULL,
                target_component TEXT NOT NULL,
                data_evidence TEXT NOT NULL,
                estimated_impact TEXT NOT NULL,
                implementation_effort INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 系统使用趋势表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_usage_trends (
                date TEXT PRIMARY KEY,
                total_requests INTEGER DEFAULT 0,
                successful_requests INTEGER DEFAULT 0,
                failed_requests INTEGER DEFAULT 0,
                avg_response_time REAL DEFAULT 0.0,
                unique_users INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    async def start(self):
        """启动分析系统"""
        self.logger.info("启动使用分析系统...")
        
        # 加载历史数据
        self._load_historical_data()
        
        # 订阅Hook事件
        await self._subscribe_to_hooks()
        
        # 启动定期分析
        asyncio.create_task(self._periodic_analysis())
        
        self.logger.info("使用分析系统启动完成")
    
    def _load_historical_data(self):
        """加载历史数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 加载Hand统计
        cursor.execute("SELECT * FROM hand_usage_stats")
        for row in cursor.fetchall():
            hand_name = row[0]
            stats = HandUsageStats(
                hand_name=hand_name,
                total_executions=row[1],
                successful_executions=row[2],
                failed_executions=row[3],
                total_execution_time=row[4],
                last_execution_time=datetime.fromisoformat(row[5]) if row[5] else None
            )
            if stats.total_executions > 0:
                stats.avg_execution_time = stats.total_execution_time / stats.total_executions
                stats.success_rate = stats.successful_executions / stats.total_executions
            self.hand_stats[hand_name] = stats
        
        # 加载进化统计
        cursor.execute("SELECT * FROM evolution_usage_stats")
        for row in cursor.fetchall():
            plan_id = row[0]
            stats = EvolutionUsageStats(
                plan_id=plan_id,
                execution_count=row[1],
                successful_count=row[2],
                failed_count=row[3],
                avg_execution_time=row[4],
                performance_improvement=row[5],
                last_execution_time=datetime.fromisoformat(row[6]) if row[6] else None
            )
            self.evolution_stats[plan_id] = stats
        
        # 加载建议
        cursor.execute("SELECT * FROM optimization_suggestions WHERE status = 'pending'")
        for row in cursor.fetchall():
            suggestion = OptimizationSuggestion(
                suggestion_id=row[0],
                suggestion_type=SuggestionType(row[1]),
                title=row[2],
                description=row[3],
                priority=SuggestionPriority(row[4]),
                target_component=row[5],
                data_evidence=json.loads(row[6]),
                estimated_impact=row[7],
                implementation_effort=row[8],
                status=row[9],
                created_at=datetime.fromisoformat(row[10])
            )
            self.suggestions[suggestion.suggestion_id] = suggestion
        
        conn.close()
    
    async def _subscribe_to_hooks(self):
        """订阅Hook事件"""
        # 监听Hand执行事件
        self.hook_system.recorder.subscribe(
            event_type=HookEventType.HAND_EXECUTION.value,
            callback=self._handle_hand_execution_event
        )
        
        # 监听进化计划事件
        self.hook_system.recorder.subscribe(
            event_type=HookEventType.EVOLUTION_PLAN.value,
            callback=self._handle_evolution_plan_event
        )
        
        # 监听错误事件
        self.hook_system.recorder.subscribe(
            event_type=HookEventType.ERROR_OCCURRED.value,
            callback=self._handle_error_event
        )
        
        self.logger.info("已订阅Hook事件")
    
    async def _handle_hand_execution_event(self, event: HookEvent):
        """处理Hand执行事件"""
        try:
            data = event.data
            hand_name = data.get("hand_name")
            success = data.get("success", False)
            execution_time = data.get("execution_time", 0.0)
            
            if not hand_name:
                return
            
            # 更新内存统计
            if hand_name not in self.hand_stats:
                self.hand_stats[hand_name] = HandUsageStats(hand_name=hand_name)
            
            self.hand_stats[hand_name].update(success, execution_time)
            
            # 保存到数据库
            self._save_hand_stats(hand_name)
            
            # 检查是否需要生成建议
            await self._analyze_hand_usage(hand_name)
            
        except Exception as e:
            self.logger.error(f"处理Hand执行事件失败: {e}")
    
    async def _handle_evolution_plan_event(self, event: HookEvent):
        """处理进化计划事件"""
        try:
            data = event.data
            plan_id = data.get("plan_id")
            status = data.get("status")
            execution_time = data.get("execution_time", 0.0)
            performance_impact = data.get("performance_impact", {})
            
            if not plan_id:
                return
            
            # 更新内存统计
            if plan_id not in self.evolution_stats:
                self.evolution_stats[plan_id] = EvolutionUsageStats(plan_id=plan_id)
            
            stats = self.evolution_stats[plan_id]
            stats.execution_count += 1
            
            if status == "completed":
                stats.successful_count += 1
            elif status == "failed":
                stats.failed_count += 1
            
            # 更新平均执行时间
            total_time = stats.avg_execution_time * (stats.execution_count - 1) + execution_time
            stats.avg_execution_time = total_time / stats.execution_count
            
            # 更新性能改进
            if performance_impact and "improvement_percentage" in performance_impact:
                stats.performance_improvement = performance_impact["improvement_percentage"]
            
            stats.last_execution_time = datetime.now()
            
            # 保存到数据库
            self._save_evolution_stats(plan_id)
            
            # 检查是否需要生成建议
            await self._analyze_evolution_usage(plan_id)
            
        except Exception as e:
            self.logger.error(f"处理进化计划事件失败: {e}")
    
    async def _handle_error_event(self, event: HookEvent):
        """处理错误事件"""
        try:
            data = event.data
            error_type = data.get("error_type", "")
            component = data.get("component", "")
            
            # 基于错误频率生成建议
            await self._analyze_error_patterns(error_type, component)
            
        except Exception as e:
            self.logger.error(f"处理错误事件失败: {e}")
    
    def _save_hand_stats(self, hand_name: str):
        """保存Hand统计到数据库"""
        if hand_name not in self.hand_stats:
            return
        
        stats = self.hand_stats[hand_name]
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO hand_usage_stats 
            (hand_name, total_executions, successful_executions, failed_executions, 
             total_execution_time, last_execution_time, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            hand_name,
            stats.total_executions,
            stats.successful_executions,
            stats.failed_executions,
            stats.total_execution_time,
            stats.last_execution_time.isoformat() if stats.last_execution_time else None,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def _save_evolution_stats(self, plan_id: str):
        """保存进化统计到数据库"""
        if plan_id not in self.evolution_stats:
            return
        
        stats = self.evolution_stats[plan_id]
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO evolution_usage_stats 
            (plan_id, execution_count, successful_count, failed_count,
             avg_execution_time, performance_improvement, last_execution_time, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            plan_id,
            stats.execution_count,
            stats.successful_count,
            stats.failed_count,
            stats.avg_execution_time,
            stats.performance_improvement,
            stats.last_execution_time.isoformat() if stats.last_execution_time else None,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    async def _analyze_hand_usage(self, hand_name: str):
        """分析Hand使用模式"""
        if hand_name not in self.hand_stats:
            return
        
        stats = self.hand_stats[hand_name]
        
        # 检查高频使用但成功率低的Hand
        if stats.total_executions >= 10 and stats.success_rate < 0.7:
            suggestion_id = f"hand_improve_{hand_name}_{datetime.now().timestamp()}"
            suggestion = OptimizationSuggestion(
                suggestion_id=suggestion_id,
                suggestion_type=SuggestionType.HAND_IMPROVEMENT,
                title=f"改进Hand: {hand_name}",
                description=f"Hand '{hand_name}' 使用频繁但成功率较低 ({stats.success_rate*100:.1f}%)，建议优化错误处理或功能实现",
                priority=SuggestionPriority.HIGH if stats.success_rate < 0.5 else SuggestionPriority.MEDIUM,
                target_component=hand_name,
                data_evidence={
                    "total_executions": stats.total_executions,
                    "success_rate": stats.success_rate,
                    "avg_execution_time": stats.avg_execution_time
                },
                estimated_impact="提高系统可靠性和用户体验",
                implementation_effort=4  # 小时
            )
            await self._add_suggestion(suggestion)
        
        # 检查执行时间过长的Hand
        if stats.total_executions >= 5 and stats.avg_execution_time > 5.0:
            suggestion_id = f"hand_perf_{hand_name}_{datetime.now().timestamp()}"
            suggestion = OptimizationSuggestion(
                suggestion_id=suggestion_id,
                suggestion_type=SuggestionType.PERFORMANCE_OPTIMIZATION,
                title=f"优化Hand性能: {hand_name}",
                description=f"Hand '{hand_name}' 平均执行时间较长 ({stats.avg_execution_time:.2f}秒)，建议进行性能优化",
                priority=SuggestionPriority.MEDIUM,
                target_component=hand_name,
                data_evidence={
                    "avg_execution_time": stats.avg_execution_time,
                    "total_executions": stats.total_executions
                },
                estimated_impact="减少用户等待时间，提高系统响应速度",
                implementation_effort=8  # 小时
            )
            await self._add_suggestion(suggestion)
    
    async def _analyze_evolution_usage(self, plan_id: str):
        """分析进化使用模式"""
        if plan_id not in self.evolution_stats:
            return
        
        stats = self.evolution_stats[plan_id]
        
        # 检查高成功率的进化计划
        if stats.execution_count >= 3 and stats.successful_count / stats.execution_count > 0.8:
            suggestion_id = f"evolution_priority_{plan_id}_{datetime.now().timestamp()}"
            suggestion = OptimizationSuggestion(
                suggestion_id=suggestion_id,
                suggestion_type=SuggestionType.EVOLUTION_PRIORITY,
                title=f"提高进化计划优先级: {plan_id}",
                description=f"进化计划 '{plan_id}' 成功率高 ({stats.successful_count}/{stats.execution_count})，建议更频繁执行类似计划",
                priority=SuggestionPriority.MEDIUM,
                target_component="evolution_engine",
                data_evidence={
                    "success_rate": stats.successful_count / stats.execution_count,
                    "execution_count": stats.execution_count,
                    "performance_improvement": stats.performance_improvement
                },
                estimated_impact="加速系统优化进程",
                implementation_effort=2  # 小时
            )
            await self._add_suggestion(suggestion)
    
    async def _analyze_error_patterns(self, error_type: str, component: str):
        """分析错误模式"""
        # 简化实现：基于错误类型生成建议
        if "timeout" in error_type.lower():
            suggestion_id = f"error_timeout_{datetime.now().timestamp()}"
            suggestion = OptimizationSuggestion(
                suggestion_id=suggestion_id,
                suggestion_type=SuggestionType.PERFORMANCE_OPTIMIZATION,
                title="优化超时处理",
                description=f"检测到超时错误，组件: {component}",
                priority=SuggestionPriority.MEDIUM,
                target_component=component,
                data_evidence={"error_type": error_type, "component": component},
                estimated_impact="提高系统稳定性和用户体验",
                implementation_effort=6  # 小时
            )
            await self._add_suggestion(suggestion)
    
    async def _add_suggestion(self, suggestion: OptimizationSuggestion):
        """添加优化建议"""
        self.suggestions[suggestion.suggestion_id] = suggestion
        
        # 保存到数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO optimization_suggestions 
            (suggestion_id, suggestion_type, title, description, priority, 
             target_component, data_evidence, estimated_impact, 
             implementation_effort, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            suggestion.suggestion_id,
            suggestion.suggestion_type.value,
            suggestion.title,
            suggestion.description,
            suggestion.priority.value,
            suggestion.target_component,
            json.dumps(suggestion.data_evidence),
            suggestion.estimated_impact,
            suggestion.implementation_effort,
            suggestion.status,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"生成优化建议: {suggestion.title}")
    
    async def _periodic_analysis(self):
        """定期分析"""
        while True:
            try:
                await asyncio.sleep(3600)  # 每小时分析一次
                
                # 分析整体趋势
                await self._analyze_overall_trends()
                
                # 生成综合建议
                await self._generate_comprehensive_suggestions()
                
                self.logger.info("定期分析完成")
                
            except Exception as e:
                self.logger.error(f"定期分析失败: {e}")
                await asyncio.sleep(300)  # 错误后等待5分钟
    
    async def _analyze_overall_trends(self):
        """分析整体趋势"""
        # 检查最常用的Hands
        if self.hand_stats:
            sorted_hands = sorted(
                self.hand_stats.values(),
                key=lambda x: x.total_executions,
                reverse=True
            )
            
            top_hands = sorted_hands[:3]
            if top_hands:
                suggestion_id = f"top_hands_{datetime.now().timestamp()}"
                suggestion = OptimizationSuggestion(
                    suggestion_id=suggestion_id,
                    suggestion_type=SuggestionType.HAND_IMPROVEMENT,
                    title="优化高频使用Hands",
                    description=f"最常用的Hands: {', '.join(h.hand_name for h in top_hands)}，建议优先优化这些Hands",
                    priority=SuggestionPriority.MEDIUM,
                    target_component="hands_system",
                    data_evidence={
                        "top_hands": [
                            {"hand_name": h.hand_name, "executions": h.total_executions}
                            for h in top_hands
                        ]
                    },
                    estimated_impact="提高系统核心功能的性能和可靠性",
                    implementation_effort=12  # 小时
                )
                await self._add_suggestion(suggestion)
    
    async def _generate_comprehensive_suggestions(self):
        """生成综合建议"""
        # 检查是否缺少某些类型的Hands
        # 这里可以基于使用模式推断可能需要的新Hands
        pass
    
    def get_hand_stats(self, hand_name: Optional[str] = None) -> Dict[str, Any]:
        """获取Hand统计"""
        if hand_name:
            if hand_name in self.hand_stats:
                stats = self.hand_stats[hand_name]
                return {
                    "hand_name": stats.hand_name,
                    "total_executions": stats.total_executions,
                    "successful_executions": stats.successful_executions,
                    "failed_executions": stats.failed_executions,
                    "avg_execution_time": stats.avg_execution_time,
                    "success_rate": stats.success_rate,
                    "last_execution_time": stats.last_execution_time.isoformat() if stats.last_execution_time else None
                }
            return {}
        
        return {
            hand_name: {
                "total_executions": stats.total_executions,
                "success_rate": stats.success_rate,
                "avg_execution_time": stats.avg_execution_time
            }
            for hand_name, stats in self.hand_stats.items()
        }
    
    def get_suggestions(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取优化建议"""
        suggestions = self.suggestions.values()
        
        if status:
            suggestions = [s for s in suggestions if s.status == status]
        
        return [
            {
                "suggestion_id": s.suggestion_id,
                "suggestion_type": s.suggestion_type.value,
                "title": s.title,
                "description": s.description,
                "priority": s.priority.value,
                "target_component": s.target_component,
                "data_evidence": s.data_evidence,
                "estimated_impact": s.estimated_impact,
                "implementation_effort": s.implementation_effort,
                "status": s.status,
                "created_at": s.created_at.isoformat()
            }
            for s in suggestions
        ]
    
    def approve_suggestion(self, suggestion_id: str) -> bool:
        """批准建议"""
        if suggestion_id not in self.suggestions:
            return False
        
        self.suggestions[suggestion_id].status = "approved"
        
        # 更新数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE optimization_suggestions SET status = ?, updated_at = ? WHERE suggestion_id = ?",
            ("approved", datetime.now().isoformat(), suggestion_id)
        )
        conn.commit()
        conn.close()
        
        return True
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计"""
        total_hand_executions = sum(s.total_executions for s in self.hand_stats.values())
        total_successful_hand_executions = sum(s.successful_executions for s in self.hand_stats.values())
        
        total_evolution_executions = sum(s.execution_count for s in self.evolution_stats.values())
        total_successful_evolution_executions = sum(s.successful_count for s in self.evolution_stats.values())
        
        avg_hand_success_rate = 0
        if total_hand_executions > 0:
            avg_hand_success_rate = total_successful_hand_executions / total_hand_executions
        
        avg_evolution_success_rate = 0
        if total_evolution_executions > 0:
            avg_evolution_success_rate = total_successful_evolution_executions / total_evolution_executions
        
        return {
            "total_hand_executions": total_hand_executions,
            "total_successful_hand_executions": total_successful_hand_executions,
            "avg_hand_success_rate": avg_hand_success_rate,
            "total_evolution_executions": total_evolution_executions,
            "total_successful_evolution_executions": total_successful_evolution_executions,
            "avg_evolution_success_rate": avg_evolution_success_rate,
            "unique_hands": len(self.hand_stats),
            "unique_evolution_plans": len(self.evolution_stats),
            "pending_suggestions": len([s for s in self.suggestions.values() if s.status == "pending"]),
            "total_suggestions": len(self.suggestions)
        }


# 便捷启动函数
async def start_usage_analytics(system_name: str = "default"):
    """启动使用分析系统"""
    analytics = UsageAnalytics(system_name)
    await analytics.start()
    return analytics