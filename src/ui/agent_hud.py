#!/usr/bin/env python3
"""
Agent HUD - RANGEN Agent 实时状态面板
借鉴 Claude HUD 设计理念

Claude HUD 核心原理:
1. 利用 Claude Code 的原生 statusline API
2. 从 stdin JSON 解析上下文使用百分比
3. 解析 transcript JSONL 获取工具活动和 Agent 状态
4. 实时更新 (~300ms)

RANGEN 适配:
- 利用 EventStream 获取实时事件
- 利用 MetricsService 获取上下文使用情况
- 利用 AgentState 追踪 Agent 状态
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class ContextHealth(Enum):
    """上下文健康状态"""
    HEALTHY = "healthy"      # < 60%
    WARNING = "warning"      # 60-85%
    CRITICAL = "critical"    # > 85%


@dataclass
class ToolActivity:
    """工具活动"""
    tool_name: str
    status: str  # running, completed, error
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    success: bool = True
    error: Optional[str] = None


@dataclass
class AgentStatus:
    """Agent 状态"""
    agent_id: str
    agent_type: str
    status: str  # running, completed, failed
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    current_action: str = ""
    progress: tuple = (0, 0)  # (completed, total)


@dataclass
class HUDMetrics:
    """HUD 指标"""
    # 上下文
    context_usage_percent: float = 0.0
    context_tokens: int = 0
    max_tokens: int = 200000
    
    # 使用量
    usage_percent: float = 0.0
    usage_reset_at: Optional[datetime] = None
    
    # Agent 状态
    active_agents: List[AgentStatus] = field(default_factory=list)
    
    # 工具活动
    recent_tools: List[ToolActivity] = field(default_factory=list)
    
    # Todo 进度
    todo_progress: tuple = (0, 0)  # (completed, total)
    
    # 会话
    session_duration: float = 0.0
    session_start: Optional[datetime] = None
    
    # 错误
    error_count: int = 0
    last_error: Optional[str] = None


class AgentHUD:
    """
    RANGEN Agent HUD - 实时状态面板
    
    借鉴 Claude HUD 的设计:
    - 上下文健康度可视化 (绿→黄→红)
    - 工具活动追踪
    - Agent 状态显示
    - Todo 进度追踪
    """
    
    def __init__(self, update_interval: float = 0.3):
        """
        初始化 HUD
        
        Args:
            update_interval: 更新间隔 (秒)，默认 300ms
        """
        self.update_interval = update_interval
        self._running = False
        self._update_task: Optional[asyncio.Task] = None
        
        # 事件队列
        self._event_queue: asyncio.Queue = asyncio.Queue()
        
        # 指标
        self._metrics = HUDMetrics()
        self._metrics_lock = asyncio.Lock()
        
        # 事件历史 (用于统计)
        self._tool_history: deque = deque(maxlen=100)
        self._agent_history: deque = deque(maxlen=50)
        
        # 回调函数
        self._render_callback: Optional[Callable] = None
        self._metrics_callback: Optional[Callable] = None
        
        # 上次更新时间
        self._last_update: datetime = datetime.now()
    
    async def start(self):
        """启动 HUD 更新循环"""
        if self._running:
            return
        
        self._running = True
        self._metrics.session_start = datetime.now()
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("Agent HUD 已启动")
    
    async def stop(self):
        """停止 HUD 更新循环"""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        logger.info("Agent HUD 已停止")
    
    async def _update_loop(self):
        """HUD 更新循环"""
        while self._running:
            try:
                await self._collect_events()
                await self._update_metrics()
                await self._notify_callbacks()
                await asyncio.sleep(self.update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"HUD 更新循环错误: {e}")
    
    async def _collect_events(self):
        """收集事件"""
        # 从 EventStream 收集事件
        # 这里应该订阅 EventStream 的事件
        pass
    
    async def _update_metrics(self):
        """更新指标"""
        async with self._metrics_lock:
            # 更新会话时长
            if self._metrics.session_start:
                self._metrics.session_duration = (
                    datetime.now() - self._metrics.session_start
                ).total_seconds()
            
            # 更新工具历史中的活动时长
            now = datetime.now()
            for tool in self._metrics.recent_tools:
                if tool.end_time is None and tool.status == "running":
                    tool.duration = (now - tool.start_time).total_seconds()
            
            # 清理已完成的活动
            self._metrics.recent_tools = [
                t for t in self._metrics.recent_tools
                if t.status == "running" or 
                (t.end_time and (now - t.end_time).total_seconds() < 60)
            ]
    
    async def _notify_callbacks(self):
        """通知回调函数"""
        if self._render_callback:
            try:
                await self._render_callback(self._metrics)
            except Exception as e:
                logger.error(f"HUD 渲染回调错误: {e}")
        
        if self._metrics_callback:
            try:
                self._metrics_callback(self._metrics)
            except Exception as e:
                logger.error(f"HUD 指标回调错误: {e}")
    
    # ==================== 事件记录 ====================
    
    def record_tool_start(self, tool_name: str, tool_id: str = "") -> ToolActivity:
        """记录工具开始"""
        activity = ToolActivity(
            tool_name=tool_name,
            status="running",
            start_time=datetime.now()
        )
        
        self._tool_history.append({
            "event": "tool_start",
            "tool": tool_name,
            "time": datetime.now()
        })
        
        # 添加到当前活动
        self._metrics.recent_tools.append(activity)
        
        return activity
    
    def record_tool_complete(
        self, 
        tool_name: str, 
        success: bool = True,
        error: Optional[str] = None
    ):
        """记录工具完成"""
        now = datetime.now()
        
        for tool in reversed(self._metrics.recent_tools):
            if tool.tool_name == tool_name and tool.status == "running":
                tool.status = "completed" if success else "error"
                tool.end_time = now
                tool.duration = (now - tool.start_time).total_seconds()
                tool.success = success
                tool.error = error
                
                if not success:
                    self._metrics.error_count += 1
                    self._metrics.last_error = f"{tool_name}: {error}"
                
                break
        
        self._tool_history.append({
            "event": "tool_complete",
            "tool": tool_name,
            "success": success,
            "time": datetime.now()
        })
    
    def record_agent_start(
        self, 
        agent_id: str, 
        agent_type: str = "",
        description: str = ""
    ) -> AgentStatus:
        """记录 Agent 开始"""
        status = AgentStatus(
            agent_id=agent_id,
            agent_type=agent_type,
            status="running",
            start_time=datetime.now(),
            current_action=description
        )
        
        self._metrics.active_agents.append(status)
        self._agent_history.append({
            "event": "agent_start",
            "agent_id": agent_id,
            "time": datetime.now()
        })
        
        return status
    
    def record_agent_complete(
        self, 
        agent_id: str, 
        status: str = "completed"
    ):
        """记录 Agent 完成"""
        now = datetime.now()
        
        for agent in self._metrics.active_agents:
            if agent.agent_id == agent_id and agent.status == "running":
                agent.status = status
                agent.end_time = now
                agent.duration = (now - agent.start_time).total_seconds()
                break
        
        self._agent_history.append({
            "event": "agent_complete",
            "agent_id": agent_id,
            "status": status,
            "time": datetime.now()
        })
    
    def update_context_usage(self, tokens: int, max_tokens: int = 200000):
        """更新上下文使用情况"""
        self._metrics.context_tokens = tokens
        self._metrics.max_tokens = max_tokens
        self._metrics.context_usage_percent = (tokens / max_tokens * 100) if max_tokens > 0 else 0
    
    def update_todo_progress(self, completed: int, total: int):
        """更新 Todo 进度"""
        self._metrics.todo_progress = (completed, total)
    
    def record_error(self, error: str):
        """记录错误"""
        self._metrics.error_count += 1
        self._metrics.last_error = error
    
    # ==================== 状态获取 ====================
    
    def get_context_health(self) -> ContextHealth:
        """获取上下文健康状态"""
        percent = self._metrics.context_usage_percent
        if percent < 60:
            return ContextHealth.HEALTHY
        elif percent < 85:
            return ContextHealth.WARNING
        else:
            return ContextHealth.CRITICAL
    
    def get_context_color(self) -> str:
        """获取上下文健康度颜色"""
        health = self.get_context_health()
        if health == ContextHealth.HEALTHY:
            return "green"
        elif health == ContextHealth.WARNING:
            return "yellow"
        else:
            return "red"
    
    def get_active_agent_count(self) -> int:
        """获取活跃 Agent 数量"""
        return len([a for a in self._metrics.active_agents if a.status == "running"])
    
    async def get_metrics(self) -> HUDMetrics:
        """获取当前指标"""
        async with self._metrics_lock:
            return HUDMetrics(
                context_usage_percent=self._metrics.context_usage_percent,
                context_tokens=self._metrics.context_tokens,
                max_tokens=self._metrics.max_tokens,
                usage_percent=self._metrics.usage_percent,
                usage_reset_at=self._metrics.usage_reset_at,
                active_agents=list(self._metrics.active_agents),
                recent_tools=list(self._metrics.recent_tools),
                todo_progress=self._metrics.todo_progress,
                session_duration=self._metrics.session_duration,
                session_start=self._metrics.session_start,
                error_count=self._metrics.error_count,
                last_error=self._metrics.last_error
            )
    
    # ==================== 渲染 ====================
    
    def set_render_callback(self, callback: Callable):
        """设置渲染回调"""
        self._render_callback = callback
    
    def set_metrics_callback(self, callback: Callable):
        """设置指标回调"""
        self._metrics_callback = callback
    
    def render_status_bar(self, metrics: Optional[HUDMetrics] = None) -> str:
        """
        渲染状态栏
        
        格式示例:
        Context █████░░░░░ 45% | Usage ██░░░░░░░░ 25% (1h 30m / 5h)
        """
        if metrics is None:
            metrics = self._metrics
        
        # 上下文条
        percent = metrics.context_usage_percent
        color = self.get_context_color()
        bar = "█" * int(percent / 5) + "░" * (20 - int(percent / 5))
        context_line = f"Context {bar} {percent:.0f}%"
        
        # 使用量条
        usage_bar = "█" * int(metrics.usage_percent / 5) + "░" * (20 - int(metrics.usage_percent / 5))
        
        # 会话时长
        duration_str = self._format_duration(metrics.session_duration)
        usage_line = f"Usage {usage_bar} {metrics.usage_percent:.0f}% ({duration_str})"
        
        return f"{context_line} | {usage_line}"
    
    def render_tool_activity(self, metrics: Optional[HUDMetrics] = None) -> str:
        """渲染工具活动"""
        if metrics is None:
            metrics = self._metrics
        
        if not metrics.recent_tools:
            return ""
        
        lines = []
        for tool in metrics.recent_tools[-5:]:  # 最近5个
            icon = "✓" if tool.success else "✗" if tool.status == "error" else "◐"
            lines.append(f"{icon} {tool.tool_name}: {tool.duration:.1f}s")
        
        return "\n".join(lines)
    
    def render_agent_status(self, metrics: Optional[HUDMetrics] = None) -> str:
        """渲染 Agent 状态"""
        if metrics is None:
            metrics = self._metrics
        
        if not metrics.active_agents:
            return ""
        
        lines = []
        for agent in metrics.active_agents:
            icon = "◐" if agent.status == "running" else "✓" if agent.status == "completed" else "✗"
            duration = self._format_duration(agent.duration) if agent.duration else "..."
            lines.append(f"{icon} {agent.agent_type or agent.agent_id}: {agent.current_action} ({duration})")
        
        return "\n".join(lines)
    
    def render_todo_progress(self, metrics: Optional[HUDMetrics] = None) -> str:
        """渲染 Todo 进度"""
        if metrics is None:
            metrics = self._metrics
        
        completed, total = metrics.todo_progress
        if total == 0:
            return ""
        
        percent = completed / total * 100
        bar = "▓" * int(percent / 5) + "░" * (20 - int(percent / 5))
        
        return f"▸ Task Progress ({completed}/{total}) {bar} {percent:.0f}%"
    
    def render_full_hud(self, metrics: Optional[HUDMetrics] = None) -> str:
        """渲染完整的 HUD"""
        if metrics is None:
            metrics = self._metrics
        
        lines = []
        
        # 第一行: 核心状态
        lines.append(self.render_status_bar(metrics))
        lines.append("")
        
        # 工具活动
        tool_lines = self.render_tool_activity(metrics)
        if tool_lines:
            lines.append("🔧 工具活动:")
            lines.append(tool_lines)
            lines.append("")
        
        # Agent 状态
        agent_lines = self.render_agent_status(metrics)
        if agent_lines:
            lines.append("🤖 Agent 状态:")
            lines.append(agent_lines)
            lines.append("")
        
        # Todo 进度
        todo_line = self.render_todo_progress(metrics)
        if todo_line:
            lines.append(todo_line)
        
        # 错误
        if metrics.last_error:
            lines.append(f"❌ 错误: {metrics.last_error}")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_duration(seconds: float) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.0f}m"
        else:
            return f"{seconds/3600:.1f}h"


# ==================== Streamlit 渲染器 ====================

def render_hud_streamlit(hud: AgentHUD, metrics: Optional[HUDMetrics] = None):
    """
    在 Streamlit 中渲染 HUD
    
    借鉴 Claude HUD 的 UI 设计:
    - 使用 emoji 表示状态
    - 进度条可视化
    - 实时更新
    """
    import streamlit as st
    
    # 获取指标
    if metrics is None:
        import asyncio
        metrics = asyncio.get_event_loop().run_until_complete(hud.get_metrics())
    
    # 第一行: 核心状态
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    
    # 上下文健康度
    with col1:
        health = hud.get_context_health()
        color = hud.get_context_color()
        percent = metrics.context_usage_percent
        
        st.markdown(f"**上下文** `{'🟢' if color=='green' else '🟡' if color=='yellow' else '🔴'} {percent:.0f}%**")
        st.progress(percent / 100)
        st.caption(f"{metrics.context_tokens:,}/{metrics.max_tokens:,} tokens")
    
    # 使用量
    with col2:
        st.markdown(f"**使用量** `{metrics.usage_percent:.0f}%**")
        st.progress(metrics.usage_percent / 100)
        if metrics.usage_reset_at:
            reset_str = metrics.usage_reset_at.strftime("%H:%M")
            st.caption(f"重置于 {reset_str}")
    
    # Agent 数量
    with col3:
        active = hud.get_active_agent_count()
        st.metric("活跃Agent", active)
    
    # 执行时间
    with col4:
        duration = AgentHUD._format_duration(metrics.session_duration)
        st.metric("执行时间", duration)
    
    # 工具活动
    if metrics.recent_tools:
        with st.expander("🔧 工具活动", expanded=False):
            for tool in metrics.recent_tools[-5:]:
                icon = "✅" if tool.success else "❌" if tool.status == "error" else "⏳"
                st.markdown(f"{icon} **{tool.tool_name}** - {tool.duration:.2f}s")
    
    # Todo 进度
    if metrics.todo_progress[1] > 0:
        completed, total = metrics.todo_progress
        st.progress(completed / total, text=f"任务进度: {completed}/{total}")
    
    # 错误
    if metrics.last_error:
        st.error(f"❌ {metrics.last_error}")
