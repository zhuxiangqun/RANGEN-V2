#!/usr/bin/env python3
"""
Hook透明化系统主模块
整合记录、解释和监控功能，提供全面的系统可见性
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json

from .recorder import HookRecorder
from .explainer import HookExplainer
from .monitor import HookMonitor
from .hook_types import HookEventType, HookVisibilityLevel, HookEvent






class HookTransparencySystem:
    """Hook透明化系统"""
    
    def __init__(self, system_name: str = "rangen_system"):
        self.logger = logging.getLogger(__name__)
        self.system_name = system_name
        
        # 初始化组件
        self.recorder = HookRecorder(system_name)
        self.explainer = HookExplainer(system_name)
        self.monitor = HookMonitor(system_name)
        
        # 事件订阅者
        self.subscribers: List[Callable[[HookEvent], None]] = []
        
        # 配置
        self.enable_auto_explanation = True
        self.enable_real_time_monitoring = True
        self.default_visibility = HookVisibilityLevel.DEVELOPER
        
        self.logger.info(f"Hook透明化系统初始化: {system_name}")
    
    async def record_event(self, event_type: HookEventType, source: str, 
                          data: Dict[str, Any], 
                          visibility: Optional[HookVisibilityLevel] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """记录事件"""
        try:
            # 创建事件
            event_id = f"hook_{event_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            timestamp = datetime.now().isoformat()
            
            event = HookEvent(
                event_id=event_id,
                event_type=event_type,
                timestamp=timestamp,
                source=source,
                data=data,
                visibility=visibility or self.default_visibility,
                metadata=metadata or {}
            )
            
            # 记录事件
            await self.recorder.record_event(event)
            
            # 实时监控
            if self.enable_real_time_monitoring:
                await self.monitor.process_event(event)
            
            # 自动解释（如果启用）
            if self.enable_auto_explanation and self._needs_explanation(event_type):
                explanation = await self.explainer.explain_event(event)
                if explanation:
                    event.metadata["explanation"] = explanation
            
            # 通知订阅者
            await self._notify_subscribers(event)
            
            self.logger.info(f"记录Hook事件: {event_id} ({event_type.value})")
            return event_id
            
        except Exception as e:
            self.logger.error(f"记录Hook事件失败: {e}")
            return ""
    
    def _needs_explanation(self, event_type: HookEventType) -> bool:
        """判断事件是否需要解释"""
        explanation_required = [
            HookEventType.AGENT_DECISION,
            HookEventType.EVOLUTION_PLAN,
            HookEventType.CONSTITUTION_CHECK,
            HookEventType.MODEL_REVIEW,
            HookEventType.ERROR_OCCURRED
        ]
        return event_type in explanation_required
    
    async def _notify_subscribers(self, event: HookEvent):
        """通知事件订阅者"""
        if not self.subscribers:
            return
        
        for subscriber in self.subscribers:
            try:
                # 异步通知
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(event)
                else:
                    subscriber(event)
            except Exception as e:
                self.logger.error(f"通知订阅者失败: {e}")
    
    def subscribe(self, callback: Callable[[HookEvent], None]):
        """订阅事件"""
        self.subscribers.append(callback)
        self.logger.info(f"添加事件订阅者: {callback.__name__ if hasattr(callback, '__name__') else 'anonymous'}")
    
    async def record_agent_decision(self, agent_name: str, decision: Dict[str, Any], 
                                   context: Optional[Dict[str, Any]] = None) -> str:
        """记录智能体决策"""
        data = {
            "agent": agent_name,
            "decision": decision,
            "context": context or {}
        }
        
        return await self.record_event(
            event_type=HookEventType.AGENT_DECISION,
            source=f"agent:{agent_name}",
            data=data,
            visibility=HookVisibilityLevel.ENTREPRENEUR
        )
    
    async def record_evolution_plan(self, plan: Dict[str, Any], 
                                   status: str = "proposed") -> str:
        """记录进化计划"""
        data = {
            "plan": plan,
            "status": status,
            "recorded_at": datetime.now().isoformat()
        }
        
        return await self.record_event(
            event_type=HookEventType.EVOLUTION_PLAN,
            source="evolution_engine",
            data=data,
            visibility=HookVisibilityLevel.DEVELOPER
        )
    
    async def record_hand_execution(self, hand_name: str, result: Dict[str, Any], 
                                   parameters: Optional[Dict[str, Any]] = None) -> str:
        """记录Hand执行"""
        data = {
            "hand": hand_name,
            "result": result,
            "parameters": parameters or {},
            "executed_at": datetime.now().isoformat()
        }
        
        return await self.record_event(
            event_type=HookEventType.HAND_EXECUTION,
            source=f"hand:{hand_name}",
            data=data,
            visibility=HookVisibilityLevel.DEVELOPER
        )
    
    async def record_constitution_check(self, plan_id: str, result: Dict[str, Any]) -> str:
        """记录宪法检查"""
        data = {
            "plan_id": plan_id,
            "check_result": result,
            "checked_at": datetime.now().isoformat()
        }
        
        return await self.record_event(
            event_type=HookEventType.CONSTITUTION_CHECK,
            source="constitution_checker",
            data=data,
            visibility=HookVisibilityLevel.DEVELOPER
        )
    
    async def record_error(self, error_type: str, error_message: str, 
                          context: Optional[Dict[str, Any]] = None) -> str:
        """记录错误"""
        data = {
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {},
            "occurred_at": datetime.now().isoformat()
        }
        
        return await self.record_event(
            event_type=HookEventType.ERROR_OCCURRED,
            source="error_handler",
            data=data,
            visibility=HookVisibilityLevel.DEVELOPER,
            metadata={"priority": "high"}
        )
    
    async def get_event_explanation(self, event_id: str) -> Optional[Dict[str, Any]]:
        """获取事件解释"""
        try:
            event = await self.recorder.get_event(event_id)
            if not event:
                return None
            
            explanation = await self.explainer.explain_event(event)
            return explanation
            
        except Exception as e:
            self.logger.error(f"获取事件解释失败: {e}")
            return None
    
    async def get_system_summary(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """获取系统摘要"""
        try:
            events = await self.recorder.get_events_by_time_range(time_range_hours)
            
            summary = {
                "time_range_hours": time_range_hours,
                "total_events": len(events),
                "by_event_type": {},
                "by_source": {},
                "recent_events": [],
                "system_health": await self.monitor.get_system_health(),
                "key_decisions": []
            }
            
            # 统计事件类型
            for event in events:
                event_type = event.event_type.value
                if event_type not in summary["by_event_type"]:
                    summary["by_event_type"][event_type] = 0
                summary["by_event_type"][event_type] += 1
                
                # 统计来源
                source = event.source
                if source not in summary["by_source"]:
                    summary["by_source"][source] = 0
                summary["by_source"][source] += 1
            
            # 最近事件
            recent_events = events[-10:] if events else []
            summary["recent_events"] = [
                {
                    "event_id": e.event_id,
                    "type": e.event_type.value,
                    "source": e.source,
                    "timestamp": e.timestamp
                }
                for e in recent_events
            ]
            
            # 关键决策
            key_decisions = [e for e in events if e.event_type == HookEventType.AGENT_DECISION]
            summary["key_decisions"] = [
                {
                    "event_id": e.event_id,
                    "agent": e.data.get("agent", "unknown"),
                    "timestamp": e.timestamp
                }
                for e in key_decisions[-5:]
            ]
            
            return summary
            
        except Exception as e:
            self.logger.error(f"获取系统摘要失败: {e}")
            return {}
    
    async def export_transparency_report(self, format: str = "json") -> Optional[str]:
        """导出透明化报告"""
        try:
            # 获取系统摘要
            summary = await self.get_system_summary()
            
            # 获取事件数据
            events = await self.recorder.get_events_by_time_range(24)
            
            # 构建报告
            report = {
                "system": self.system_name,
                "generated_at": datetime.now().isoformat(),
                "summary": summary,
                "recent_events_detailed": [
                    {
                        "event_id": e.event_id,
                        "type": e.event_type.value,
                        "source": e.source,
                        "timestamp": e.timestamp,
                        "visibility": e.visibility.value,
                        "data_summary": self._summarize_event_data(e.data)
                    }
                    for e in events[-20:]
                ],
                "transparency_metrics": {
                    "events_recorded": len(events),
                    "explanations_generated": len([e for e in events if "explanation" in e.metadata]),
                    "monitoring_alerts": await self.monitor.get_alert_count(),
                    "data_quality": "good" if len(events) > 0 else "unknown"
                }
            }
            
            if format == "json":
                return json.dumps(report, indent=2, ensure_ascii=False)
            else:
                self.logger.warning(f"不支持的导出格式: {format}")
                return None
                
        except Exception as e:
            self.logger.error(f"导出透明化报告失败: {e}")
            return None
    
    def _summarize_event_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """摘要事件数据"""
        summary = {}
        
        for key, value in data.items():
            if isinstance(value, dict):
                summary[key] = {"type": "dict", "keys": list(value.keys())}
            elif isinstance(value, list):
                summary[key] = {"type": "list", "count": len(value)}
            elif isinstance(value, str) and len(value) > 100:
                summary[key] = {"type": "str", "length": len(value), "preview": value[:100] + "..."}
            else:
                summary[key] = {"type": type(value).__name__, "value": str(value)[:50]}
        
        return summary
    
    async def clear_old_events(self, days_old: int = 30):
        """清理旧事件"""
        try:
            count = await self.recorder.clear_old_events(days_old)
            self.logger.info(f"清理了 {count} 个超过 {days_old} 天的事件")
            return count
        except Exception as e:
            self.logger.error(f"清理旧事件失败: {e}")
            return 0
    
    def set_visibility_level(self, level: HookVisibilityLevel):
        """设置默认可见性级别"""
        self.default_visibility = level
        self.logger.info(f"设置默认可见性级别: {level.value}")
    
    def __str__(self):
        return f"HookTransparencySystem({self.system_name})"