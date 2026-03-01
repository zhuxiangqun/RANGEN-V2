"""
Multi-Agent Collaboration Enhancement

Enhanced features for multi-agent collaboration:
- Event-driven notifications for agent activities
- Structured handoff protocols between agents
- Shared state billboard for agent communication
- Agent lifecycle management
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)


class AgentEventType(Enum):
    """Agent event types"""
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    TASK_HANDOVER = "task_handover"
    AGENT_REGISTERED = "agent_registered"
    AGENT_UNREGISTERED = "agent_unregistered"
    AGENT_BUSY = "agent_busy"
    AGENT_AVAILABLE = "agent_available"
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    STATE_UPDATED = "state_updated"


class HandoffStatus(Enum):
    """Handoff status"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"


@dataclass
class AgentEvent:
    """Agent event"""
    event_id: str
    event_type: AgentEventType
    agent_id: str
    task_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HandoffRequest:
    """Task handoff request"""
    request_id: str
    from_agent: str
    to_agent: str
    task_id: str
    task_description: str
    task_data: Dict[str, Any]
    priority: int = 5  # 1-10
    status: HandoffStatus = HandoffStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    response_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SharedState:
    """Shared state entry"""
    key: str
    value: Any
    owner_agent: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    ttl: Optional[int] = None  # Time to live in seconds
    tags: Set[str] = field(default_factory=set)


class AgentEventBus:
    """
    Event bus for agent activities
    Provides pub/sub messaging for agent events
    """
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._subscribers: Dict[AgentEventType, List[Callable]] = defaultdict(list)
        self._all_subscribers: List[Callable] = []
        self._event_history: List[AgentEvent] = []
        self._lock = asyncio.Lock()
    
    def subscribe(
        self, 
        event_type: AgentEventType, 
        callback: Callable[[AgentEvent], None]
    ):
        """Subscribe to specific event type"""
        self._subscribers[event_type].append(callback)
        logger.info(f"Subscribed to {event_type.value}")
    
    def subscribe_all(self, callback: Callable[[AgentEvent], None]):
        """Subscribe to all events"""
        self._all_subscribers.append(callback)
        logger.info("Subscribed to all agent events")
    
    def unsubscribe(
        self, 
        event_type: AgentEventType, 
        callback: Callable[[AgentEvent], None]
    ):
        """Unsubscribe from event type"""
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)
    
    async def publish(self, event: AgentEvent):
        """Publish an event"""
        async with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self.max_history:
                self._event_history = self._event_history[-self.max_history:]
        
        # Notify subscribers
        callbacks = self._subscribers.get(event.event_type, [])
        callbacks.extend(self._all_subscribers)
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Event callback error: {e}")
    
    def get_history(
        self, 
        event_type: Optional[AgentEventType] = None,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AgentEvent]:
        """Get event history"""
        events = self._event_history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if agent_id:
            events = [e for e in events if e.agent_id == agent_id]
        
        return events[-limit:]


class HandoffProtocol:
    """
    Structured handoff protocol between agents
    Ensures clean task transfer with context preservation
    """
    
    def __init__(self, event_bus: AgentEventBus):
        self.event_bus = event_bus
        self._pending_requests: Dict[str, HandoffRequest] = {}
        self._active_handovers: Dict[str, HandoffRequest] = {}
        self._lock = asyncio.Lock()
    
    async def request_handoff(
        self,
        from_agent: str,
        to_agent: str,
        task_id: str,
        task_description: str,
        task_data: Dict[str, Any],
        priority: int = 5
    ) -> str:
        """Request a task handoff"""
        request_id = str(uuid.uuid4())
        
        request = HandoffRequest(
            request_id=request_id,
            from_agent=from_agent,
            to_agent=to_agent,
            task_id=task_id,
            task_description=task_description,
            task_data=task_data,
            priority=priority
        )
        
        async with self._lock:
            self._pending_requests[request_id] = request
        
        # Publish event
        await self.event_bus.publish(AgentEvent(
            event_id=str(uuid.uuid4()),
            event_type=AgentEventType.TASK_HANDOVER,
            agent_id=from_agent,
            task_id=task_id,
            data={
                "request_id": request_id,
                "to_agent": to_agent,
                "priority": priority
            }
        ))
        
        logger.info(f"Handoff requested: {from_agent} -> {to_agent} for task {task_id}")
        return request_id
    
    async def accept_handoff(
        self, 
        request_id: str, 
        response_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Accept a handoff request"""
        async with self._lock:
            if request_id not in self._pending_requests:
                return False
            
            request = self._pending_requests.pop(request_id)
            request.status = HandoffStatus.ACCEPTED
            request.response_data = response_data or {}
            self._active_handovers[request_id] = request
        
        logger.info(f"Handoff accepted: {request_id}")
        return True
    
    async def reject_handoff(
        self, 
        request_id: str, 
        reason: str
    ) -> bool:
        """Reject a handoff request"""
        async with self._lock:
            if request_id not in self._pending_requests:
                return False
            
            request = self._pending_requests.pop(request_id)
            request.status = HandoffStatus.REJECTED
            request.response_data = {"reason": reason}
        
        logger.info(f"Handoff rejected: {request_id}, reason: {reason}")
        return True
    
    async def complete_handoff(
        self, 
        request_id: str,
        result_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Complete a handoff"""
        async with self._lock:
            if request_id not in self._active_handovers:
                return False
            
            request = self._active_handovers.pop(request_id)
            request.status = HandoffStatus.COMPLETED
            request.completed_at = datetime.now()
            request.response_data = result_data or {}
        
        logger.info(f"Handoff completed: {request_id}")
        return True
    
    def get_pending_requests(
        self, 
        agent_id: Optional[str] = None
    ) -> List[HandoffRequest]:
        """Get pending handoff requests"""
        requests = list(self._pending_requests.values())
        
        if agent_id:
            requests = [r for r in requests if r.to_agent == agent_id]
        
        return sorted(requests, key=lambda r: r.priority, reverse=True)


class SharedStateBillboard:
    """
    Shared state billboard for agent communication
    Provides a shared key-value store with versioning and TTL
    """
    
    def __init__(self, event_bus: AgentEventBus):
        self.event_bus = event_bus
        self._states: Dict[str, SharedState] = {}
        self._lock = asyncio.Lock()
    
    async def set(
        self,
        key: str,
        value: Any,
        owner_agent: str,
        ttl: Optional[int] = None,
        tags: Optional[Set[str]] = None
    ) -> bool:
        """Set a shared state"""
        async with self._lock:
            old_state = self._states.get(key)
            
            state = SharedState(
                key=key,
                value=value,
                owner_agent=owner_agent,
                ttl=ttl,
                tags=tags or set()
            )
            
            if old_state:
                state.version = old_state.version + 1
            
            self._states[key] = state
        
        # Publish event
        await self.event_bus.publish(AgentEvent(
            event_id=str(uuid.uuid4()),
            event_type=AgentEventType.STATE_UPDATED,
            agent_id=owner_agent,
            data={"key": key, "version": state.version}
        ))
        
        return True
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a shared state value"""
        async with self._lock:
            state = self._states.get(key)
            return state.value if state else None
    
    async def get_with_metadata(self, key: str) -> Optional[SharedState]:
        """Get a shared state with metadata"""
        async with self._lock:
            return self._states.get(key)
    
    async def delete(self, key: str, agent_id: str) -> bool:
        """Delete a shared state"""
        async with self._lock:
            if key in self._states:
                state = self._states[key]
                if state.owner_agent != agent_id:
                    logger.warning(f"Agent {agent_id} tried to delete {key} owned by {state.owner_agent}")
                    return False
                
                del self._states[key]
                return True
            return False
    
    async def query(
        self,
        tags: Optional[Set[str]] = None,
        owner_agent: Optional[str] = None,
        prefix: Optional[str] = None
    ) -> List[SharedState]:
        """Query shared states"""
        async with self._lock:
            states = list(self._states.values())
        
        if tags:
            states = [s for s in states if tags.intersection(s.tags)]
        
        if owner_agent:
            states = [s for s in states if s.owner_agent == owner_agent]
        
        if prefix:
            states = [s for s in states if s.key.startswith(prefix)]
        
        return states
    
    async def subscribe_changes(
        self, 
        key: str, 
        callback: Callable[[SharedState], None]
    ):
        """Subscribe to state changes for a key"""
        async def wrapper(event: AgentEvent):
            if event.data.get("key") == key:
                state = await self.get_with_metadata(key)
                if state:
                    callback(state)
        
        self.event_bus.subscribe(AgentEventType.STATE_UPDATED, wrapper)


class CollaborationEnhancement:
    """
    Main class for multi-agent collaboration enhancement
    Combines event bus, handoff protocol, and shared state
    """
    
    def __init__(self):
        self.event_bus = AgentEventBus()
        self.handoff_protocol = HandoffProtocol(self.event_bus)
        self.billboard = SharedStateBillboard(self.event_bus)
        
        # Agent registry with status
        self._agent_status: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        
        logger.info("CollaborationEnhancement initialized")
    
    async def register_agent(
        self, 
        agent_id: str, 
        capabilities: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Register an agent"""
        async with self._lock:
            self._agent_status[agent_id] = {
                "status": "available",
                "capabilities": capabilities,
                "metadata": metadata or {},
                "registered_at": datetime.now(),
                "current_task": None
            }
        
        await self.event_bus.publish(AgentEvent(
            event_id=str(uuid.uuid4()),
            event_type=AgentEventType.AGENT_REGISTERED,
            agent_id=agent_id,
            data={"capabilities": capabilities}
        ))
        
        logger.info(f"Agent registered: {agent_id}")
    
    async def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        async with self._lock:
            if agent_id in self._agent_status:
                del self._agent_status[agent_id]
        
        await self.event_bus.publish(AgentEvent(
            event_id=str(uuid.uuid4()),
            event_type=AgentEventType.AGENT_UNREGISTERED,
            agent_id=agent_id,
            data={}
        ))
        
        logger.info(f"Agent unregistered: {agent_id}")
    
    async def set_agent_busy(self, agent_id: str, task_id: str):
        """Mark agent as busy"""
        async with self._lock:
            if agent_id in self._agent_status:
                self._agent_status[agent_id]["status"] = "busy"
                self._agent_status[agent_id]["current_task"] = task_id
        
        await self.event_bus.publish(AgentEvent(
            event_id=str(uuid.uuid4()),
            event_type=AgentEventType.AGENT_BUSY,
            agent_id=agent_id,
            task_id=task_id,
            data={}
        ))
    
    async def set_agent_available(self, agent_id: str):
        """Mark agent as available"""
        async with self._lock:
            if agent_id in self._agent_status:
                self._agent_status[agent_id]["status"] = "available"
                self._agent_status[agent_id]["current_task"] = None
        
        await self.event_bus.publish(AgentEvent(
            event_id=str(uuid.uuid4()),
            event_type=AgentEventType.AGENT_AVAILABLE,
            agent_id=agent_id,
            data={}
        ))
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent status"""
        return self._agent_status.get(agent_id)
    
    def get_available_agents(self, capability: Optional[str] = None) -> List[str]:
        """Get list of available agents"""
        agents = []
        for agent_id, status in self._agent_status.items():
            if status["status"] == "available":
                if capability is None or capability in status["capabilities"]:
                    agents.append(agent_id)
        return agents
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collaboration statistics"""
        return {
            "total_agents": len(self._agent_status),
            "available_agents": len(self.get_available_agents()),
            "pending_handovers": len(self.handoff_protocol._pending_requests),
            "active_handovers": len(self.handoff_protocol._active_handovers),
            "shared_states": len(self.billboard._states),
            "events_in_history": len(self.event_bus._event_history)
        }


# ==================== Global Instance ====================

_collaboration: Optional[CollaborationEnhancement] = None


def get_collaboration_enhancement() -> CollaborationEnhancement:
    """Get global collaboration enhancement instance"""
    global _collaboration
    if _collaboration is None:
        _collaboration = CollaborationEnhancement()
    return _collaboration
