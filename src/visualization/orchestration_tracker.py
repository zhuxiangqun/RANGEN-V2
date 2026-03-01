"""
编排过程追踪器
追踪 Agent、工具、提示词工程、上下文工程的执行过程
"""
import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class OrchestrationEventType(Enum):
    """编排事件类型"""
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    AGENT_THINK = "agent_think"
    AGENT_PLAN = "agent_plan"
    AGENT_ACT = "agent_act"
    AGENT_OBSERVE = "agent_observe"
    
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    TOOL_CALL = "tool_call"
    
    PROMPT_GENERATE = "prompt_generate"
    PROMPT_OPTIMIZE = "prompt_optimize"
    PROMPT_ORCHESTRATE = "prompt_orchestrate"
    
    CONTEXT_ENHANCE = "context_enhance"
    CONTEXT_UPDATE = "context_update"
    CONTEXT_MERGE = "context_merge"


@dataclass
class OrchestrationEvent:
    """编排事件"""
    event_type: OrchestrationEventType
    component_name: str  # Agent名称、工具名称等
    component_type: str  # "agent", "tool", "prompt_engineering", "context_engineering"
    timestamp: float
    duration: Optional[float] = None
    data: Dict[str, Any] = field(default_factory=dict)
    parent_event_id: Optional[str] = None  # 父事件ID（用于建立层级关系）
    event_id: str = field(default_factory=lambda: f"event_{int(time.time() * 1000000)}")


class OrchestrationTracker:
    """编排过程追踪器"""
    
    def __init__(self):
        self.events: List[OrchestrationEvent] = []
        self.active_events: Dict[str, OrchestrationEvent] = {}  # 正在执行的事件
        self.event_callbacks: List[Callable[[OrchestrationEvent], None]] = []
        self.execution_id: Optional[str] = None
    
    def start_execution(self, execution_id: str):
        """开始追踪执行"""
        self.execution_id = execution_id
        self.events.clear()
        self.active_events.clear()
        logger.info(f"🎯 [编排追踪] 开始追踪执行: {execution_id}")
    
    def track_agent_start(self, agent_name: str, agent_type: str = "agent", context: Dict[str, Any] = None):
        """追踪 Agent 开始执行"""
        event = OrchestrationEvent(
            event_type=OrchestrationEventType.AGENT_START,
            component_name=agent_name,
            component_type=agent_type,
            timestamp=time.time(),
            data={"context": context or {}}
        )
        self._add_event(event)
        self.active_events[f"agent_{agent_name}"] = event
        return event.event_id
    
    def track_agent_end(self, agent_name: str, result: Dict[str, Any] = None, error: Optional[str] = None, parent_event_id: Optional[str] = None):
        """追踪 Agent 执行结束"""
        event_key = f"agent_{agent_name}"
        start_event = self.active_events.pop(event_key, None)
        
        duration = None
        if start_event:
            duration = time.time() - start_event.timestamp
            # 如果提供了 parent_event_id，使用它；否则使用 start_event 的 event_id
            final_parent_id = parent_event_id if parent_event_id is not None else start_event.event_id
        else:
            final_parent_id = parent_event_id
        
        event = OrchestrationEvent(
            event_type=OrchestrationEventType.AGENT_END,
            component_name=agent_name,
            component_type="agent",
            timestamp=time.time(),
            duration=duration,
            data={"result": result, "error": error},
            parent_event_id=final_parent_id
        )
        self._add_event(event)
        return event.event_id
    
    def track_agent_think(self, agent_name: str, thought: str, parent_event_id: Optional[str] = None):
        """追踪 Agent 思考"""
        event = OrchestrationEvent(
            event_type=OrchestrationEventType.AGENT_THINK,
            component_name=agent_name,
            component_type="agent",
            timestamp=time.time(),
            data={"thought": thought},
            parent_event_id=parent_event_id
        )
        self._add_event(event)
        return event.event_id
    
    def track_agent_plan(self, agent_name: str, plan: Dict[str, Any], parent_event_id: Optional[str] = None):
        """追踪 Agent 规划"""
        event = OrchestrationEvent(
            event_type=OrchestrationEventType.AGENT_PLAN,
            component_name=agent_name,
            component_type="agent",
            timestamp=time.time(),
            data={"plan": plan},
            parent_event_id=parent_event_id
        )
        self._add_event(event)
        return event.event_id
    
    def track_agent_act(self, agent_name: str, action: Dict[str, Any], parent_event_id: Optional[str] = None):
        """追踪 Agent 行动"""
        event = OrchestrationEvent(
            event_type=OrchestrationEventType.AGENT_ACT,
            component_name=agent_name,
            component_type="agent",
            timestamp=time.time(),
            data={"action": action},
            parent_event_id=parent_event_id
        )
        self._add_event(event)
        return event.event_id
    
    def track_agent_observe(self, agent_name: str, observation: Dict[str, Any], parent_event_id: Optional[str] = None):
        """追踪 Agent 观察"""
        event = OrchestrationEvent(
            event_type=OrchestrationEventType.AGENT_OBSERVE,
            component_name=agent_name,
            component_type="agent",
            timestamp=time.time(),
            data={"observation": observation},
            parent_event_id=parent_event_id
        )
        self._add_event(event)
        return event.event_id
    
    def track_tool_start(self, tool_name: str, params: Dict[str, Any] = None, parent_event_id: Optional[str] = None):
        """追踪工具开始执行"""
        event = OrchestrationEvent(
            event_type=OrchestrationEventType.TOOL_START,
            component_name=tool_name,
            component_type="tool",
            timestamp=time.time(),
            data={"params": params or {}},
            parent_event_id=parent_event_id
        )
        self._add_event(event)
        self.active_events[f"tool_{tool_name}"] = event
        return event.event_id
    
    def track_tool_end(self, tool_name: str, result: Dict[str, Any] = None, error: Optional[str] = None, parent_event_id: Optional[str] = None):
        """追踪工具执行结束"""
        event_key = f"tool_{tool_name}"
        start_event = self.active_events.pop(event_key, None)
        
        duration = None
        if start_event:
            duration = time.time() - start_event.timestamp
            # 如果提供了 parent_event_id，使用它；否则使用 start_event 的 event_id
            final_parent_id = parent_event_id if parent_event_id is not None else start_event.event_id
        else:
            final_parent_id = parent_event_id
        
        event = OrchestrationEvent(
            event_type=OrchestrationEventType.TOOL_END,
            component_name=tool_name,
            component_type="tool",
            timestamp=time.time(),
            duration=duration,
            data={"result": result, "error": error},
            parent_event_id=final_parent_id
        )
        self._add_event(event)
        return event.event_id
    
    def track_prompt_generate(self, prompt_type: str, query: str, context: Dict[str, Any] = None, parent_event_id: Optional[str] = None):
        """追踪提示词生成"""
        event = OrchestrationEvent(
            event_type=OrchestrationEventType.PROMPT_GENERATE,
            component_name=prompt_type,
            component_type="prompt_engineering",
            timestamp=time.time(),
            data={"query": query, "context": context or {}},
            parent_event_id=parent_event_id
        )
        self._add_event(event)
        return event.event_id
    
    def track_prompt_orchestrate(self, strategy: str, fragments: List[str], parent_event_id: Optional[str] = None):
        """追踪提示词编排"""
        event = OrchestrationEvent(
            event_type=OrchestrationEventType.PROMPT_ORCHESTRATE,
            component_name="orchestrator",
            component_type="prompt_engineering",
            timestamp=time.time(),
            data={"strategy": strategy, "fragments": fragments},
            parent_event_id=parent_event_id
        )
        self._add_event(event)
        return event.event_id
    
    def track_prompt_optimize(self, prompt_type: str, optimized_query: str, context: Dict[str, Any] = None, parent_event_id: Optional[str] = None):
        """追踪提示词优化"""
        event = OrchestrationEvent(
            event_type=OrchestrationEventType.PROMPT_OPTIMIZE,
            component_name=prompt_type,
            component_type="prompt_engineering",
            timestamp=time.time(),
            data={"optimized_query": optimized_query, "context": context or {}},
            parent_event_id=parent_event_id
        )
        self._add_event(event)
        return event.event_id
    
    def track_context_enhance(self, enhancement_type: str, context: Dict[str, Any] = None, parent_event_id: Optional[str] = None):
        """追踪上下文增强"""
        event = OrchestrationEvent(
            event_type=OrchestrationEventType.CONTEXT_ENHANCE,
            component_name=enhancement_type,
            component_type="context_engineering",
            timestamp=time.time(),
            data={"context": context or {}},
            parent_event_id=parent_event_id
        )
        self._add_event(event)
        return event.event_id
    
    def track_context_update(self, update_type: str, updates: Dict[str, Any] = None, parent_event_id: Optional[str] = None):
        """追踪上下文更新"""
        event = OrchestrationEvent(
            event_type=OrchestrationEventType.CONTEXT_UPDATE,
            component_name=update_type,
            component_type="context_engineering",
            timestamp=time.time(),
            data={"updates": updates or {}},
            parent_event_id=parent_event_id
        )
        self._add_event(event)
        return event.event_id
    
    def track_context_merge(self, merge_type: str, merge_data: Dict[str, Any] = None, parent_event_id: Optional[str] = None):
        """追踪上下文合并"""
        event = OrchestrationEvent(
            event_type=OrchestrationEventType.CONTEXT_MERGE,
            component_name=merge_type,
            component_type="context_engineering",
            timestamp=time.time(),
            data={"merge_data": merge_data or {}},
            parent_event_id=parent_event_id
        )
        self._add_event(event)
        return event.event_id
    
    def _add_event(self, event: OrchestrationEvent):
        """添加事件"""
        self.events.append(event)
        
        # 触发回调
        for callback in self.event_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.warning(f"编排事件回调失败: {e}")
    
    def add_callback(self, callback: Callable[[OrchestrationEvent], None]):
        """添加事件回调"""
        self.event_callbacks.append(callback)
    
    def get_events_by_type(self, event_type: OrchestrationEventType) -> List[OrchestrationEvent]:
        """根据类型获取事件"""
        return [e for e in self.events if e.event_type == event_type]
    
    def get_events_by_component(self, component_name: str) -> List[OrchestrationEvent]:
        """根据组件名称获取事件"""
        return [e for e in self.events if e.component_name == component_name]
    
    def get_event_tree(self, root_event_id: Optional[str] = None) -> Dict[str, Any]:
        """获取事件树（层级结构）"""
        if root_event_id:
            root_events = [e for e in self.events if e.event_id == root_event_id]
        else:
            # 找到所有没有父事件的事件作为根
            root_events = [e for e in self.events if e.parent_event_id is None]
        
        def build_tree(event: OrchestrationEvent) -> Dict[str, Any]:
            children = [e for e in self.events if e.parent_event_id == event.event_id]
            return {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "component_name": event.component_name,
                "component_type": event.component_type,
                "timestamp": event.timestamp,
                "duration": event.duration,
                "data": event.data,
                "children": [build_tree(child) for child in children]
            }
        
        return [build_tree(e) for e in root_events]
    
    def get_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        agent_events = [e for e in self.events if e.component_type == "agent"]
        tool_events = [e for e in self.events if e.component_type == "tool"]
        prompt_events = [e for e in self.events if e.component_type == "prompt_engineering"]
        context_events = [e for e in self.events if e.component_type == "context_engineering"]
        
        return {
            "execution_id": self.execution_id,
            "total_events": len(self.events),
            "agents": {
                "count": len(set(e.component_name for e in agent_events)),
                "events": len(agent_events),
                "names": list(set(e.component_name for e in agent_events))
            },
            "tools": {
                "count": len(set(e.component_name for e in tool_events)),
                "events": len(tool_events),
                "names": list(set(e.component_name for e in tool_events))
            },
            "prompt_engineering": {
                "count": len(prompt_events),
                "types": list(set(e.component_name for e in prompt_events))
            },
            "context_engineering": {
                "count": len(context_events),
                "types": list(set(e.component_name for e in context_events))
            },
            "duration": self.events[-1].timestamp - self.events[0].timestamp if self.events else 0
        }


# 全局追踪器实例
_global_tracker: Optional[OrchestrationTracker] = None


def get_orchestration_tracker() -> OrchestrationTracker:
    """获取全局编排追踪器"""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = OrchestrationTracker()
    return _global_tracker


def reset_orchestration_tracker():
    """重置全局追踪器"""
    global _global_tracker
    _global_tracker = None

