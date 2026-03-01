#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一智能体生命周期管理器
提供智能体的注册、启动、停止等生命周期管理功能
"""

import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class AgentStatus(Enum):
    """智能体状态"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"

@dataclass
class AgentInfo:
    """智能体信息"""
    agent_id: str
    name: str
    status: AgentStatus
    created_at: datetime
    last_updated: datetime
    metadata: Dict[str, Any]

class UnifiedAgentLifecycleManager:
    """统一智能体生命周期管理器"""
    
    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}
        self.lock = threading.Lock()
    
    def register_agent(self, agent_id: str, agent_name: str, agent_type: str) -> bool:
        """注册智能体"""
        try:
            # 验证输入
            if not self._validate_agent_input(agent_id, agent_name, agent_type):
                return False
            
            with self.lock:
                if agent_id in self.agents:
                    return False
                
                agent_info = AgentInfo(
                    agent_id=agent_id,
                    name=agent_name,
                    status=AgentStatus.STOPPED,
                    created_at=datetime.now(),
                    last_updated=datetime.now(),
                    metadata={"agent_type": agent_type}
                )
                self.agents[agent_id] = agent_info
                
                # 记录注册事件
                self._record_agent_event(agent_id, "registered", {"agent_type": agent_type})
                
                return True
        except Exception as e:
            print(f"Error registering agent: {e}")
            return False
    
    def _validate_agent_input(self, agent_id: str, agent_name: str, agent_type: str) -> bool:
        """验证智能体输入"""
        if not agent_id or not agent_id.strip():
            return False
        
        if not agent_name or not agent_name.strip():
            return False
        
        if not agent_type or not agent_type.strip():
            return False
        
        # 检查ID格式
        if len(agent_id) < 3 or len(agent_id) > 50:
            return False
        
        return True
    
    def _record_agent_event(self, agent_id: str, event_type: str, metadata: Dict[str, Any]):
        """记录智能体事件"""
        try:
            event = {
                'timestamp': datetime.now(),
                'agent_id': agent_id,
                'event_type': event_type,
                'metadata': metadata
            }
            # 这里可以添加事件记录逻辑
            print(f"Agent event: {event}")
        except Exception as e:
            print(f"Error recording agent event: {e}")
    
    def start_agent(self, agent_id: str) -> bool:
        """启动智能体"""
        try:
            with self.lock:
                if agent_id not in self.agents:
                    return False
                
                self.agents[agent_id].status = AgentStatus.RUNNING
                self.agents[agent_id].last_updated = datetime.now()
                return True
        except Exception as e:
            print(f"Error starting agent: {e}")
            return False
    
    def stop_agent(self, agent_id: str) -> bool:
        """停止智能体"""
        try:
            with self.lock:
                if agent_id not in self.agents:
                    return False
                
                self.agents[agent_id].status = AgentStatus.STOPPED
                self.agents[agent_id].last_updated = datetime.now()
                return True
        except Exception as e:
            print(f"Error stopping agent: {e}")
            return False
    
    def get_agent_status(self, agent_id: str) -> Optional[AgentStatus]:
        """获取智能体状态"""
        with self.lock:
            agent = self.agents.get(agent_id)
            return agent.status if agent else None
    
    def list_agents(self) -> List[AgentInfo]:
        """列出所有智能体"""
        with self.lock:
            return list(self.agents.values())

# 全局实例
_manager_instance = None

def get_unified_agent_lifecycle_manager() -> UnifiedAgentLifecycleManager:
    """获取统一智能体生命周期管理器实例"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = UnifiedAgentLifecycleManager()
    return _manager_instance

# 版本信息
__version__ = "1.0"
__author__ = "RANGEN Team"
