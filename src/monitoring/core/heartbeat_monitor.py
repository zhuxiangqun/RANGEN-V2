#!/usr/bin/env python3
"""
心跳监控服务 - 监控Agent健康状态和系统心跳

实现基于唐朝三省六部制架构的心跳监控机制，提供Agent健康状态检测、
心跳数据收集和告警功能。
"""

import asyncio
import time
import threading
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

from src.services.logging_service import get_logger
from src.services.performance_monitor import get_performance_monitor

logger = get_logger("heartbeat_monitor")


class HeartbeatStatus(Enum):
    """心跳状态"""
    ACTIVE = "active"      # 活跃状态
    IDLE = "idle"         # 空闲状态（长时间无活动）
    WARNING = "warning"   # 警告状态
    ERROR = "error"       # 错误状态
    STALLED = "stalled"   # 停滞状态（心跳停止）


@dataclass
class AgentHeartbeat:
    """Agent心跳数据"""
    agent_id: str
    agent_type: str
    status: HeartbeatStatus
    last_activity: float  # 最后活动时间戳
    heartbeat_timestamp: float  # 心跳时间戳
    metrics: Dict[str, Any] = field(default_factory=dict)
    health_score: float = 1.0  # 健康分数 0.0-1.0
    capabilities: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class HeartbeatAlert:
    """心跳告警"""
    alert_id: str
    agent_id: str
    alert_type: str  # "heartbeat_missing", "status_error", "performance_degraded"
    message: str
    severity: str  # "info", "warning", "critical"
    timestamp: float
    resolved: bool = False
    data: Dict[str, Any] = field(default_factory=dict)


class HeartbeatMonitor:
    """
    心跳监控服务
    
    监控系统中所有Agent的健康状态，定期收集心跳数据，
    检测异常状态并生成告警。
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HeartbeatMonitor, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # 配置参数
        self.heartbeat_interval = 30  # 心跳收集间隔（秒）
        self.stalled_threshold = 300  # 停滞阈值（秒）
        self.idle_threshold = 3600    # 空闲阈值（秒）
        self.warning_threshold = 180  # 警告阈值（秒）
        
        # 数据存储
        self.agent_heartbeats: Dict[str, AgentHeartbeat] = {}
        self.active_alerts: Dict[str, HeartbeatAlert] = {}
        self.heartbeat_history: Dict[str, List[AgentHeartbeat]] = {}
        
        # 监控的Agent列表
        self.monitored_agents: Dict[str, Any] = {}  # agent_id -> agent_instance
        
        # 性能监控集成
        self.performance_monitor = get_performance_monitor()
        
        # 任务控制
        self._running = False
        self._monitor_task = None
        self._lock = threading.Lock()
        
        self._initialized = True
        logger.info("心跳监控服务初始化完成")
    
    def register_agent(self, agent_id: str, agent_instance: Any):
        """注册Agent到监控服务"""
        with self._lock:
            self.monitored_agents[agent_id] = agent_instance
            logger.info(f"Agent {agent_id} 已注册到心跳监控")
    
    def unregister_agent(self, agent_id: str):
        """从监控服务中移除Agent"""
        with self._lock:
            if agent_id in self.monitored_agents:
                del self.monitored_agents[agent_id]
                logger.info(f"Agent {agent_id} 已从心跳监控中移除")
    
    async def start_monitoring(self):
        """开始心跳监控"""
        if self._running:
            logger.warning("心跳监控已启动")
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("心跳监控已启动")
    
    async def stop_monitoring(self):
        """停止心跳监控"""
        if not self._running:
            return
        
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("心跳监控已停止")
    
    async def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                await self._collect_heartbeats()
                await self._analyze_heartbeats()
                await self._generate_alerts()
                await self._record_metrics()
                
            except Exception as e:
                logger.error(f"心跳监控循环出错: {e}")
            
            await asyncio.sleep(self.heartbeat_interval)
    
    async def _collect_heartbeats(self):
        """收集所有注册Agent的心跳数据"""
        current_time = time.time()
        
        with self._lock:
            for agent_id, agent_instance in self.monitored_agents.items():
                try:
                    # 获取Agent健康状态
                    health_data = getattr(agent_instance, 'health_check', lambda: {})()
                    
                    # 提取关键信息
                    agent_status = health_data.get('status', 'unknown')
                    last_activity = health_data.get('time_since_activity', current_time)
                    
                    # 计算心跳状态
                    heartbeat_status = self._calculate_heartbeat_status(
                        agent_status, last_activity, current_time
                    )
                    
                    # 计算健康分数
                    health_score = self._calculate_health_score(
                        agent_status, last_activity, current_time
                    )
                    
                    # 创建心跳记录
                    heartbeat = AgentHeartbeat(
                        agent_id=agent_id,
                        agent_type=type(agent_instance).__name__,
                        status=heartbeat_status,
                        last_activity=last_activity,
                        heartbeat_timestamp=current_time,
                        metrics=health_data,
                        health_score=health_score,
                        capabilities=getattr(agent_instance, 'capabilities', []),
                        tags={
                            'agent_type': type(agent_instance).__name__,
                            'status': agent_status
                        }
                    )
                    
                    # 存储心跳数据
                    self.agent_heartbeats[agent_id] = heartbeat
                    
                    # 添加到历史记录
                    if agent_id not in self.heartbeat_history:
                        self.heartbeat_history[agent_id] = []
                    self.heartbeat_history[agent_id].append(heartbeat)
                    
                    # 保持历史记录长度
                    if len(self.heartbeat_history[agent_id]) > 100:
                        self.heartbeat_history[agent_id] = self.heartbeat_history[agent_id][-100:]
                    
                except Exception as e:
                    logger.error(f"收集Agent {agent_id} 心跳数据失败: {e}")
    
    def _calculate_heartbeat_status(self, agent_status: str, last_activity: float, current_time: float) -> HeartbeatStatus:
        """计算心跳状态"""
        time_since_activity = current_time - last_activity
        
        if agent_status == "error":
            return HeartbeatStatus.ERROR
        elif time_since_activity > self.stalled_threshold:
            return HeartbeatStatus.STALLED
        elif time_since_activity > self.warning_threshold:
            return HeartbeatStatus.WARNING
        elif time_since_activity > self.idle_threshold:
            return HeartbeatStatus.IDLE
        else:
            return HeartbeatStatus.ACTIVE
    
    def _calculate_health_score(self, agent_status: str, last_activity: float, current_time: float) -> float:
        """计算健康分数"""
        time_since_activity = current_time - last_activity
        
        if agent_status == "error":
            return 0.0
        elif time_since_activity > self.stalled_threshold:
            return 0.2
        elif time_since_activity > self.warning_threshold:
            return 0.5
        elif time_since_activity > self.idle_threshold:
            return 0.8
        else:
            return 1.0
    
    async def _analyze_heartbeats(self):
        """分析心跳数据，检测异常模式"""
        current_time = time.time()
        
        for agent_id, heartbeat in self.agent_heartbeats.items():
            try:
                # 检查心跳是否缺失
                time_since_heartbeat = current_time - heartbeat.heartbeat_timestamp
                if time_since_heartbeat > self.heartbeat_interval * 3:
                    self._create_alert(
                        agent_id=agent_id,
                        alert_type="heartbeat_missing",
                        message=f"Agent {agent_id} 心跳缺失超过 {time_since_heartbeat:.0f} 秒",
                        severity="critical" if time_since_heartbeat > self.stalled_threshold else "warning"
                    )
                
                # 检查状态异常
                if heartbeat.status == HeartbeatStatus.ERROR:
                    self._create_alert(
                        agent_id=agent_id,
                        alert_type="status_error",
                        message=f"Agent {agent_id} 处于错误状态",
                        severity="critical"
                    )
                elif heartbeat.status == HeartbeatStatus.STALLED:
                    self._create_alert(
                        agent_id=agent_id,
                        alert_type="heartbeat_stalled",
                        message=f"Agent {agent_id} 心跳停滞",
                        severity="critical"
                    )
                elif heartbeat.status == HeartbeatStatus.WARNING:
                    self._create_alert(
                        agent_id=agent_id,
                        alert_type="performance_warning",
                        message=f"Agent {agent_id} 响应延迟",
                        severity="warning"
                    )
                
                # 检查健康分数过低
                if heartbeat.health_score < 0.3:
                    self._create_alert(
                        agent_id=agent_id,
                        alert_type="health_degraded",
                        message=f"Agent {agent_id} 健康分数过低: {heartbeat.health_score:.2f}",
                        severity="critical"
                    )
                elif heartbeat.health_score < 0.6:
                    self._create_alert(
                        agent_id=agent_id,
                        alert_type="health_warning",
                        message=f"Agent {agent_id} 健康分数较低: {heartbeat.health_score:.2f}",
                        severity="warning"
                    )
                    
            except Exception as e:
                logger.error(f"分析Agent {agent_id} 心跳数据失败: {e}")
    
    def _create_alert(self, agent_id: str, alert_type: str, message: str, severity: str):
        """创建告警"""
        alert_id = f"{agent_id}_{alert_type}_{int(time.time())}"
        
        alert = HeartbeatAlert(
            alert_id=alert_id,
            agent_id=agent_id,
            alert_type=alert_type,
            message=message,
            severity=severity,
            timestamp=time.time(),
            resolved=False,
            data={
                'agent_id': agent_id,
                'alert_type': alert_type,
                'severity': severity
            }
        )
        
        # 检查是否已有相同告警
        existing_key = f"{agent_id}_{alert_type}"
        if existing_key in self.active_alerts:
            # 更新现有告警时间戳
            existing_alert = self.active_alerts[existing_key]
            existing_alert.timestamp = time.time()
            logger.debug(f"更新告警: {message}")
        else:
            # 添加新告警
            self.active_alerts[existing_key] = alert
            logger.warning(f"新告警: {message}")
    
    async def _generate_alerts(self):
        """生成告警并发送到相应通道"""
        # 这里可以集成到现有的告警系统
        # 暂时只记录日志
        pass
    
    async def _record_metrics(self):
        """记录心跳指标到性能监控系统"""
        try:
            active_count = sum(1 for hb in self.agent_heartbeats.values() 
                             if hb.status == HeartbeatStatus.ACTIVE)
            warning_count = sum(1 for hb in self.agent_heartbeats.values() 
                              if hb.status == HeartbeatStatus.WARNING)
            error_count = sum(1 for hb in self.agent_heartbeats.values() 
                            if hb.status == HeartbeatStatus.ERROR)
            
            # 记录Agent健康指标
            self.performance_monitor.record_metric(
                name="heartbeat.agents.active",
                value=active_count,
                tags={"metric_type": "count"}
            )
            
            self.performance_monitor.record_metric(
                name="heartbeat.agents.warning",
                value=warning_count,
                tags={"metric_type": "count"}
            )
            
            self.performance_monitor.record_metric(
                name="heartbeat.agents.error",
                value=error_count,
                tags={"metric_type": "count"}
            )
            
            # 记录整体健康分数
            if self.agent_heartbeats:
                avg_health_score = sum(hb.health_score for hb in self.agent_heartbeats.values()) / len(self.agent_heartbeats)
                self.performance_monitor.record_metric(
                    name="heartbeat.health_score.avg",
                    value=avg_health_score,
                    tags={"metric_type": "gauge"}
                )
                
        except Exception as e:
            logger.error(f"记录心跳指标失败: {e}")
    
    def get_agent_status(self, agent_id: str) -> Optional[AgentHeartbeat]:
        """获取指定Agent的心跳状态"""
        return self.agent_heartbeats.get(agent_id)
    
    def get_all_heartbeats(self) -> Dict[str, AgentHeartbeat]:
        """获取所有Agent的心跳数据"""
        return self.agent_heartbeats.copy()
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """获取系统健康摘要"""
        if not self.agent_heartbeats:
            return {
                "total_agents": 0,
                "active_agents": 0,
                "warning_agents": 0,
                "error_agents": 0,
                "avg_health_score": 0.0,
                "system_status": "unknown"
            }
        
        active_count = sum(1 for hb in self.agent_heartbeats.values() 
                         if hb.status == HeartbeatStatus.ACTIVE)
        warning_count = sum(1 for hb in self.agent_heartbeats.values() 
                          if hb.status == HeartbeatStatus.WARNING or hb.status == HeartbeatStatus.IDLE)
        error_count = sum(1 for hb in self.agent_heartbeats.values() 
                        if hb.status == HeartbeatStatus.ERROR or hb.status == HeartbeatStatus.STALLED)
        
        avg_health_score = sum(hb.health_score for hb in self.agent_heartbeats.values()) / len(self.agent_heartbeats)
        
        # 计算系统状态
        if error_count > 0:
            system_status = "error"
        elif warning_count > len(self.agent_heartbeats) * 0.3:  # 30%以上警告
            system_status = "warning"
        elif active_count < len(self.agent_heartbeats) * 0.7:  # 少于70%活跃
            system_status = "degraded"
        else:
            system_status = "healthy"
        
        return {
            "total_agents": len(self.agent_heartbeats),
            "active_agents": active_count,
            "idle_agents": sum(1 for hb in self.agent_heartbeats.values() 
                             if hb.status == HeartbeatStatus.IDLE),
            "warning_agents": sum(1 for hb in self.agent_heartbeats.values() 
                                if hb.status == HeartbeatStatus.WARNING),
            "error_agents": error_count,
            "stalled_agents": sum(1 for hb in self.agent_heartbeats.values() 
                                if hb.status == HeartbeatStatus.STALLED),
            "avg_health_score": round(avg_health_score, 3),
            "system_status": system_status,
            "timestamp": time.time()
        }
    
    def get_active_alerts(self) -> List[HeartbeatAlert]:
        """获取活跃告警列表"""
        return list(self.active_alerts.values())
    
    def resolve_alert(self, alert_id: str):
        """解决告警"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolved = True
            self.active_alerts[alert_id].timestamp = time.time()
            logger.info(f"告警 {alert_id} 已解决")


# 全局访问器
def get_heartbeat_monitor() -> HeartbeatMonitor:
    return HeartbeatMonitor()