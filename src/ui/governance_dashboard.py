#!/usr/bin/env python3
"""
治理仪表盘模块
提供系统状态、健康度、警报、事件日志的可视化界面
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
import asyncio
import json
import sys
import os

try:
    import plotly.graph_objects as go
    import plotly.express as px
except ImportError:
    go = None
    px = None

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.hook.transparency import HookTransparencySystem
from src.hook.hook_types import HookVisibilityLevel, HookEventType
from src.hook.explainer import HookExplainer
from src.hook.monitor import HookMonitor, SystemHealthStatus, AlertSeverity
from src.integration.workflow_integration import get_workflow_integration
from src.evolution.engine import EvolutionEngine
from src.hands.registry import HandRegistry
from src.services.logging_service import get_logger
from src.core.monitoring.heartbeat_monitor import get_heartbeat_monitor, HeartbeatStatus


logger = get_logger(__name__)


class GovernanceDashboard:
    """治理仪表盘"""
    
    def __init__(self):
        self.system_name = "rangen_system"
        
        # 初始化组件
        self.hook_system = HookTransparencySystem(self.system_name)
        self.hook_explainer = HookExplainer(self.system_name)
        self.hook_monitor = HookMonitor(self.system_name)
        self.workflow_integration = get_workflow_integration(self.system_name)
        self.evolution_engine = EvolutionEngine()  # 使用当前目录
        self.hands_registry = HandRegistry()
        self.heartbeat_monitor = get_heartbeat_monitor()  # 心跳监控器
        
        # 初始化状态
        self.initialized = False
        self.refresh_interval = 10  # 默认刷新间隔（秒）
        
        logger.info("治理仪表盘初始化")
    
    async def initialize(self):
        """初始化仪表盘组件"""
        try:
            # 初始化Hook系统
            await self.hook_system.recorder.initialize()
            
            # 启动心跳监控
            await self.heartbeat_monitor.start_monitoring()
            logger.info("心跳监控已启动")
            
            self.initialized = True
            logger.info("治理仪表盘初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"治理仪表盘初始化失败: {e}")
            return False
    
    async def get_system_overview(self):
        """获取系统概览"""
        try:
            # 获取系统健康状态
            health_report = await self.hook_monitor.get_system_health()
            
            # 获取警报统计
            alert_stats = await self.hook_monitor.get_alert_count()
            
            # 获取事件统计（最近24小时）
            recent_events = await self.hook_system.recorder.get_events_by_time_range(hours=24)
            
            # 获取工作流统计
            workflow_stats = await self.workflow_integration.get_system_stats()
            
            # 获取进化引擎状态
            evolution_status = await self.evolution_engine.get_status()
            
            # 获取Hands能力统计
            hands_stats = self.hands_registry.get_registry_stats()
            
            overview = {
                "timestamp": datetime.now().isoformat(),
                "system_health": health_report.get("system_health", "unknown"),
                "health_report": health_report,
                "alert_stats": alert_stats,
                "event_stats": {
                    "total_24h": len(recent_events),
                    "by_type": self._count_events_by_type(recent_events),
                    "by_visibility": self._count_events_by_visibility(recent_events)
                },
                "workflow_stats": workflow_stats,
                "evolution_status": evolution_status,
                "hands_stats": hands_stats,
                "recommendations": health_report.get("recommendations", [])
            }
            
            return overview
            
        except Exception as e:
            logger.error(f"获取系统概览失败: {e}")
            return {}
    
    async def get_recent_events(self, limit: int = 50):
        """获取最近事件"""
        try:
            events = await self.hook_system.recorder.get_events_by_time_range(hours=24)
            
            # 排序和限制
            sorted_events = sorted(events, key=lambda x: x.timestamp, reverse=True)
            recent_events = sorted_events[:limit]
            
            # 生成事件数据
            event_data = []
            for event in recent_events:
                # 生成解释（如果可用）
                explanation = await self.hook_explainer.explain_event(event)
                
                event_data.append({
                    "event_id": event.event_id,
                    "timestamp": event.timestamp,
                    "event_type": event.event_type.value,
                    "source": event.source,
                    "visibility": event.visibility.value if event.visibility else "system",
                    "data_summary": self._summarize_event_data(event.data),
                    "explanation": explanation.get("simple_explanation", "") if explanation else ""
                })
            
            return event_data
            
        except Exception as e:
            logger.error(f"获取最近事件失败: {e}")
            return []
    
    async def get_active_alerts(self):
        """获取活跃警报"""
        try:
            alerts = await self.hook_monitor.get_active_alerts()
            
            alert_data = []
            for alert in alerts:
                alert_data.append({
                    "alert_id": alert.alert_id,
                    "alert_type": alert.alert_type.value,
                    "severity": alert.severity.value,
                    "timestamp": alert.timestamp,
                    "message": alert.message,
                    "source_event_id": alert.source_event_id,
                    "acknowledged": alert.acknowledged,
                    "resolved": alert.resolved,
                    "affected_components": alert.affected_components
                })
            
            # 按严重程度排序
            severity_order = {
                AlertSeverity.CRITICAL: 0,
                AlertSeverity.ERROR: 1,
                AlertSeverity.WARNING: 2,
                AlertSeverity.INFO: 3
            }
            
            alert_data.sort(key=lambda x: severity_order.get(AlertSeverity(x["severity"]), 4))
            return alert_data
            
        except Exception as e:
            logger.error(f"获取活跃警报失败: {e}")
            return []
    
    async def get_performance_metrics(self, hours: int = 24):
        """获取性能指标"""
        try:
            # 获取事件统计
            events = await self.hook_system.recorder.get_events_by_time_range(hours=hours)
            
            # 按小时分组
            hourly_counts = {}
            for event in events:
                event_time = datetime.fromisoformat(event.timestamp)
                hour_key = event_time.strftime("%Y-%m-%d %H:00")
                
                if hour_key not in hourly_counts:
                    hourly_counts[hour_key] = {
                        "total": 0,
                        "by_type": {},
                        "errors": 0
                    }
                
                hourly_counts[hour_key]["total"] += 1
                
                # 按类型计数
                event_type = event.event_type.value
                hourly_counts[hour_key]["by_type"][event_type] = hourly_counts[hour_key]["by_type"].get(event_type, 0) + 1
                
                # 错误计数
                if event.event_type == HookEventType.ERROR_OCCURRED:
                    hourly_counts[hour_key]["errors"] += 1
            
            # 转换为列表并排序
            hourly_data = []
            for hour_key, counts in hourly_counts.items():
                hourly_data.append({
                    "hour": hour_key,
                    "total_events": counts["total"],
                    "error_count": counts["errors"],
                    "error_rate": counts["errors"] / counts["total"] if counts["total"] > 0 else 0,
                    "event_types": json.dumps(counts["by_type"])
                })
            
            hourly_data.sort(key=lambda x: x["hour"])
            
            # 获取工作流性能
            workflow_stats = await self.workflow_integration.get_system_stats()
            
            metrics = {
                "hourly_data": hourly_data,
                "workflow_performance": {
                    "total_tasks": workflow_stats["task_statistics"]["total_tasks"],
                    "completed_tasks": workflow_stats["task_statistics"]["completed_tasks"],
                    "failed_tasks": workflow_stats["task_statistics"]["failed_tasks"],
                    "success_rate": workflow_stats["task_statistics"]["completed_tasks"] / workflow_stats["task_statistics"]["total_tasks"] if workflow_stats["task_statistics"]["total_tasks"] > 0 else 0,
                    "active_tasks": workflow_stats["task_statistics"]["active_tasks"],
                    "pending_tasks": workflow_stats["task_statistics"]["pending_tasks"]
                },
                "time_range_hours": hours,
                "generated_at": datetime.now().isoformat()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"获取性能指标失败: {e}")
            return {}
    
    async def get_evolution_status(self):
        """获取进化状态"""
        try:
            status = await self.evolution_engine.get_status()
            
            # 获取进化计划
            plans = await self.evolution_engine.get_pending_plans()
            executed_plans = await self.evolution_engine.get_executed_plans()
            
            evolution_data = {
                "engine_status": status,
                "pending_plans": len(plans),
                "executed_plans": len(executed_plans),
                "recent_plans": [],
                "constitution_checks": []
            }
            
            # 最近执行的计划（最多5个）
            for plan in executed_plans[-5:]:
                evolution_data["recent_plans"].append({
                    "plan_id": plan.get("id", "unknown"),
                    "goal": plan.get("goal", "未指定"),
                    "status": plan.get("status", "unknown"),
                    "executed_at": plan.get("executed_at", "unknown"),
                    "result": plan.get("result", {}).get("summary", "未记录结果")
                })
            
            # 获取宪法检查事件
            constitution_events = await self.hook_system.recorder.get_events_by_type(HookEventType.CONSTITUTION_CHECK.value, limit=10)
            for event in constitution_events:
                evolution_data["constitution_checks"].append({
                    "timestamp": event.timestamp,
                    "plan_id": event.data.get("plan_id", "unknown"),
                    "compliance": event.data.get("check_result", {}).get("compliance", False),
                    "score": event.data.get("check_result", {}).get("score", 0),
                    "issues": len(event.data.get("check_result", {}).get("issues", []))
                })
            
            return evolution_data
            
        except Exception as e:
            logger.error(f"获取进化状态失败: {e}")
            return {}
    
    async def get_hands_capabilities(self):
        """获取Hands能力状态"""
        try:
            stats = self.hands_registry.get_registry_stats()
            capabilities = self.hands_registry.get_all_capabilities()
            
            capabilities_data = {
                "total_capabilities": stats.get("total_capabilities", 0),
                "enabled_capabilities": stats.get("enabled_capabilities", 0),
                "disabled_capabilities": stats.get("disabled_capabilities", 0),
                "capability_list": []
            }
            
            for capability in capabilities:
                capabilities_data["capability_list"].append({
                    "name": capability.name,
                    "description": capability.description,
                    "enabled": True,
                    "usage_count": 0,
                    "last_used": "从未使用",
                    "category": capability.category.value if hasattr(capability.category, 'value') else str(capability.category)
                })
            
            return capabilities_data
            
        except Exception as e:
            logger.error(f"获取Hands能力状态失败: {e}")
            return {}
    
    async def get_heartbeat_status(self):
        """获取心跳监控状态"""
        try:
            # 获取系统健康摘要
            system_health = self.heartbeat_monitor.get_system_health_summary()
            
            # 获取所有Agent心跳数据
            all_heartbeats = self.heartbeat_monitor.get_all_heartbeats()
            
            # 获取活跃告警
            active_alerts = self.heartbeat_monitor.get_active_alerts()
            
            # 准备心跳数据
            heartbeat_data = {
                "system_health": system_health,
                "agent_heartbeats": [],
                "active_alerts": [],
                "timestamp": datetime.now().isoformat()
            }
            
            # 处理Agent心跳数据
            for agent_id, heartbeat in all_heartbeats.items():
                # 将HeartbeatStatus枚举转换为字符串
                status_str = heartbeat.status.value if isinstance(heartbeat.status, HeartbeatStatus) else str(heartbeat.status)
                
                heartbeat_data["agent_heartbeats"].append({
                    "agent_id": heartbeat.agent_id,
                    "agent_type": heartbeat.agent_type,
                    "status": status_str,
                    "health_score": heartbeat.health_score,
                    "last_activity": datetime.fromtimestamp(heartbeat.last_activity).isoformat() if heartbeat.last_activity else "unknown",
                    "heartbeat_age": time.time() - heartbeat.heartbeat_timestamp if heartbeat.heartbeat_timestamp else 0,
                    "capabilities_count": len(heartbeat.capabilities),
                    "tags": heartbeat.tags
                })
            
            # 处理告警数据
            for alert in active_alerts:
                heartbeat_data["active_alerts"].append({
                    "alert_id": alert.alert_id,
                    "agent_id": alert.agent_id,
                    "alert_type": alert.alert_type,
                    "message": alert.message,
                    "severity": alert.severity,
                    "timestamp": datetime.fromtimestamp(alert.timestamp).isoformat() if alert.timestamp else "unknown",
                    "resolved": alert.resolved
                })
            
            return heartbeat_data
            
        except Exception as e:
            logger.error(f"获取心跳监控状态失败: {e}")
            return {
                "system_health": {},
                "agent_heartbeats": [],
                "active_alerts": [],
                "timestamp": datetime.now().isoformat()
            }
    
    async def acknowledge_alert(self, alert_id: str, user: str = "dashboard_user"):
        """确认警报"""
        try:
            success = await self.hook_monitor.acknowledge_alert(alert_id, user)
            return success
        except Exception as e:
            logger.error(f"确认警报失败: {e}")
            return False
    
    async def resolve_alert(self, alert_id: str, resolution_note: str = ""):
        """解决警报"""
        try:
            success = await self.hook_monitor.resolve_alert(alert_id, resolution_note)
            return success
        except Exception as e:
            logger.error(f"解决警报失败: {e}")
            return False
    
    async def get_event_details(self, event_id: str):
        """获取事件详情"""
        try:
            event = await self.hook_system.recorder.get_event_by_id(event_id)
            if not event:
                return None
            
            explanation = await self.hook_explainer.explain_event(event)
            
            event_details = {
                "event_id": event.event_id,
                "timestamp": event.timestamp,
                "event_type": event.event_type.value,
                "source": event.source,
                "visibility": event.visibility.value if event.visibility else "system",
                "data": event.data,
                "explanation": explanation,
                "formatted_timestamp": datetime.fromisoformat(event.timestamp).strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return event_details
            
        except Exception as e:
            logger.error(f"获取事件详情失败: {e}")
            return None
    
    # 辅助方法
    def _count_events_by_type(self, events):
        """按类型统计事件"""
        type_counts = {}
        for event in events:
            event_type = event.event_type.value
            type_counts[event_type] = type_counts.get(event_type, 0) + 1
        
        return type_counts
    
    def _count_events_by_visibility(self, events):
        """按可见性级别统计事件"""
        visibility_counts = {}
        for event in events:
            visibility = event.visibility.value if event.visibility else "system"
            visibility_counts[visibility] = visibility_counts.get(visibility, 0) + 1
        
        return visibility_counts
    
    def _summarize_event_data(self, data):
        """摘要事件数据"""
        if not data:
            return "无数据"
        
        # 根据事件类型提取关键信息
        summary_parts = []
        
        if isinstance(data, dict):
            # 提取关键字段
            for key in ["query", "message", "error_type", "agent", "plan_id", "hand"]:
                if key in data:
                    value = data[key]
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    summary_parts.append(f"{key}: {value}")
                    break
        
        if summary_parts:
            return "; ".join(summary_parts[:3])
        else:
            # 返回数据大小的简单表示
            data_str = str(data)
            if len(data_str) > 100:
                return f"数据大小: {len(data_str)} 字符"
            else:
                return data_str


def run_dashboard():
    """运行治理仪表盘"""
    st.set_page_config(
        page_title="RANGEN Governance Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("📊 RANGEN 治理仪表盘")
    st.markdown("实时监控系统状态、健康度、警报和性能指标")
    
    # 初始化仪表盘
    dashboard = GovernanceDashboard()
    
    # 侧边栏
    with st.sidebar:
        st.header("仪表盘设置")
        
        refresh_interval = st.slider(
            "刷新间隔 (秒)",
            min_value=5,
            max_value=60,
            value=10,
            step=5,
            help="自动刷新数据的时间间隔"
        )
        
        time_range = st.selectbox(
            "时间范围",
            options=["1小时", "6小时", "12小时", "24小时", "7天"],
            index=3,
            help="显示数据的时间范围"
        )
        
        st.divider()
        
        if st.button("🔄 立即刷新", use_container_width=True):
            st.rerun()
        
        if st.button("🚨 查看所有警报", use_container_width=True):
            st.session_state.selected_tab = "alerts"
            st.rerun()
        
        if st.button("📈 性能分析", use_container_width=True):
            st.session_state.selected_tab = "performance"
            st.rerun()
        
        if st.button("🧬 进化状态", use_container_width=True):
            st.session_state.selected_tab = "evolution"
            st.rerun()
        
        if st.button("🏛️ 旨意看板", use_container_width=True):
            st.session_state.selected_tab = "imperial_board"
            st.rerun()
        
        st.divider()
        st.markdown("### 系统信息")
        st.caption(f"系统名称: RANGEN V2")
        st.caption(f"仪表盘版本: 1.0.0")
        st.caption(f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 主内容区域 - 标签页
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 系统概览",
        "🚨 警报中心",
        "📈 性能指标",
        "🧬 进化状态",
        "🛠️ Hands能力",
        "📈 使用分析与建议",
        "🏛️ 旨意看板"
    ])
    
    # 异步数据获取
    async def load_data() -> Dict[str, Any]:
        try:
            # 初始化仪表盘
            if not dashboard.initialized:
                await dashboard.initialize()
            
            # 并行获取数据
            overview_task = dashboard.get_system_overview()
            alerts_task = dashboard.get_active_alerts()
            events_task = dashboard.get_recent_events(limit=20)
            metrics_task = dashboard.get_performance_metrics(hours=24)
            evolution_task = dashboard.get_evolution_status()
            hands_task = dashboard.get_hands_capabilities()
            heartbeat_task = dashboard.get_heartbeat_status()
            
            # 等待所有任务完成
            overview, alerts, events, metrics, evolution, hands, heartbeat = await asyncio.gather(
                overview_task, alerts_task, events_task, metrics_task, evolution_task, hands_task, heartbeat_task,
                return_exceptions=True
            )
            
            return {
                "overview": overview if not isinstance(overview, Exception) else {},
                "alerts": alerts if not isinstance(alerts, Exception) else [],
                "events": events if not isinstance(events, Exception) else [],
                "metrics": metrics if not isinstance(metrics, Exception) else {},
                "evolution": evolution if not isinstance(evolution, Exception) else {},
                "hands": hands if not isinstance(hands, Exception) else {},
                "heartbeat": heartbeat if not isinstance(heartbeat, Exception) else {}
            }
            
        except Exception as e:
            logger.error(f"加载仪表盘数据失败: {e}")
            return {}
    
    # 运行异步任务
    data = asyncio.run(load_data())
    
    # 标签页1: 系统概览
    with tab1:
        st.header("系统概览")
        
        if not data.get("overview"):
            st.warning("无法加载系统概览数据")
        else:
            overview = data["overview"]
            
            # 关键指标卡片
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # 系统健康状态
                health_status = overview.get("system_health", "unknown")
                health_colors = {
                    "healthy": "🟢",
                    "degraded": "🟡",
                    "critical": "🔴",
                    "evolving": "🟣",
                    "learning": "🔵",
                    "maintenance": "🟠"
                }
                health_icon = health_colors.get(health_status, "⚪")
                
                st.metric(
                    label="系统健康状态",
                    value=f"{health_icon} {health_status.upper()}",
                    delta=None
                )
            
            with col2:
                # 活跃警报
                alert_stats = overview.get("alert_stats", {})
                active_alerts = alert_stats.get("total", 0)
                critical_alerts = alert_stats.get("by_severity", {}).get("critical", 0)
                
                alert_color = "green" if active_alerts == 0 else "orange" if critical_alerts == 0 else "red"
                
                st.metric(
                    label="活跃警报",
                    value=active_alerts,
                    delta=f"关键: {critical_alerts}",
                    delta_color="inverse"
                )
            
            with col3:
                # 24小时事件
                event_stats = overview.get("event_stats", {})
                total_events = event_stats.get("total_24h", 0)
                
                st.metric(
                    label="24小时事件",
                    value=total_events,
                    delta=None
                )
            
            with col4:
                # 工作流任务
                workflow_stats = overview.get("workflow_stats", {}).get("task_statistics", {})
                active_tasks = workflow_stats.get("active_tasks", 0)
                pending_tasks = workflow_stats.get("pending_tasks", 0)
                
                st.metric(
                    label="活跃/待处理任务",
                    value=f"{active_tasks}/{pending_tasks}",
                    delta=None
                )
            
            st.divider()
            
            # 详细状态
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.subheader("健康报告")
                health_report = overview.get("health_report", {})
                
                if health_report:
                    # 性能指标
                    perf_metrics = health_report.get("performance_metrics", {})
                    
                    if perf_metrics:
                        st.markdown("#### 性能指标")
                        st.metric("错误率", f"{perf_metrics.get('error_rate', 0):.1%}")
                        st.metric("成功率", f"{perf_metrics.get('success_rate', 0):.1%}")
                        st.metric("平均延迟", f"{perf_metrics.get('average_latency_seconds', 0):.2f}s")
                    
                    # 组件状态
                    component_status = health_report.get("component_status", {})
                    if component_status:
                        st.markdown("#### 组件状态")
                        st.metric("总组件数", component_status.get("total_components", 0))
                        st.metric("健康组件", component_status.get("healthy_components", 0))
                        st.metric("异常组件", component_status.get("unhealthy_components", 0))
                
            with col_right:
                st.subheader("最近事件摘要")
                events = data.get("events", [])[:10]
                
                if events:
                    for event in events:
                        with st.expander(f"{event['timestamp']} - {event['event_type']}", expanded=False):
                            st.markdown(f"**来源**: {event['source']}")
                            st.markdown(f"**可见性**: {event['visibility']}")
                            st.markdown(f"**摘要**: {event['data_summary']}")
                            if event['explanation']:
                                st.markdown(f"**解释**: {event['explanation']}")
                else:
                    st.info("暂无事件数据")
            
            # 建议
            recommendations = overview.get("recommendations", [])
            if recommendations:
                st.divider()
                st.subheader("建议")
                
                for i, recommendation in enumerate(recommendations[:3], 1):
                    st.markdown(f"{i}. {recommendation}")
    
    # 标签页2: 警报中心
    with tab2:
        st.header("警报中心")
        
        alerts = data.get("alerts", [])
        
        if not alerts:
            st.success("🎉 当前没有活跃警报")
        else:
            # 警报统计
            critical_count = len([a for a in alerts if a["severity"] == "critical" and not a["resolved"]])
            error_count = len([a for a in alerts if a["severity"] == "error" and not a["resolved"]])
            warning_count = len([a for a in alerts if a["severity"] == "warning" and not a["resolved"]])
            
            col1, col2, col3 = st.columns(3)
            col1.metric("关键警报", critical_count, delta_color="inverse")
            col2.metric("错误警报", error_count, delta_color="inverse")
            col3.metric("警告警报", warning_count, delta_color="inverse")
            
            st.divider()
            
            # 警报列表
            st.subheader("活跃警报列表")
            
            for alert in alerts:
                if alert["resolved"]:
                    continue
                
                severity_icons = {
                    "critical": "🔴",
                    "error": "🟠",
                    "warning": "🟡",
                    "info": "🔵"
                }
                
                severity_icon = severity_icons.get(alert["severity"], "⚪")
                acknowledged_status = "✅ 已确认" if alert["acknowledged"] else "❌ 未确认"
                
                with st.container(border=True):
                    col1, col2, col3 = st.columns([1, 3, 1])
                    
                    with col1:
                        st.markdown(f"### {severity_icon}")
                        st.markdown(f"**{alert['severity'].upper()}**")
                    
                    with col2:
                        st.markdown(f"**{alert['message']}**")
                        st.caption(f"时间: {alert['timestamp']}")
                        st.caption(f"类型: {alert['alert_type']}")
                        
                        if alert["affected_components"]:
                            st.caption(f"影响组件: {', '.join(alert['affected_components'])}")
                    
                    with col3:
                        st.caption(f"状态: {acknowledged_status}")
                        
                        # 操作按钮
                        if not alert["acknowledged"]:
                            if st.button("确认", key=f"ack_{alert['alert_id']}", use_container_width=True):
                                asyncio.run(dashboard.acknowledge_alert(alert["alert_id"], "dashboard_user"))
                                st.rerun()
                        
                        if st.button("解决", key=f"resolve_{alert['alert_id']}", use_container_width=True):
                            asyncio.run(dashboard.resolve_alert(alert["alert_id"], "通过仪表盘手动解决"))
                            st.rerun()
            
            # 已解决的警报
            resolved_alerts = [a for a in alerts if a["resolved"]]
            if resolved_alerts:
                st.divider()
                with st.expander("查看已解决的警报", expanded=False):
                    for alert in resolved_alerts:
                        st.markdown(f"✅ **{alert['message']}**")
                        st.caption(f"解决时间: {alert.get('metadata', {}).get('resolved_at', '未知')}")
    
    # 标签页3: 性能指标
    with tab3:
        st.header("性能指标")
        
        metrics = data.get("metrics", {})
        
        if not metrics:
            st.warning("无法加载性能指标数据")
        else:
            # 工作流性能
            workflow_perf = metrics.get("workflow_performance", {})
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("总任务数", workflow_perf.get("total_tasks", 0))
            col2.metric("成功率", f"{workflow_perf.get('success_rate', 0):.1%}")
            col3.metric("失败任务", workflow_perf.get("failed_tasks", 0))
            col4.metric("待处理任务", workflow_perf.get("pending_tasks", 0))
            
            st.divider()
            
            # 事件趋势图
            hourly_data = metrics.get("hourly_data", [])
            if hourly_data:
                st.subheader("事件趋势 (24小时)")
                
                df = pd.DataFrame(hourly_data)
                df["hour"] = pd.to_datetime(df["hour"])
                
                # 创建事件趋势图
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=df["hour"],
                    y=df["total_events"],
                    mode="lines+markers",
                    name="总事件数",
                    line=dict(color="blue", width=2)
                ))
                
                fig.add_trace(go.Scatter(
                    x=df["hour"],
                    y=df["error_count"],
                    mode="lines+markers",
                    name="错误事件",
                    line=dict(color="red", width=2)
                ))
                
                fig.update_layout(
                    title="事件趋势图",
                    xaxis_title="时间",
                    yaxis_title="事件数量",
                    hovermode="x unified",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 错误率图
                st.subheader("错误率趋势")
                
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    x=df["hour"],
                    y=df["error_rate"] * 100,
                    mode="lines+markers",
                    name="错误率 (%)",
                    line=dict(color="orange", width=2),
                    fill="tozeroy"
                ))
                
                fig2.update_layout(
                    title="错误率趋势",
                    xaxis_title="时间",
                    yaxis_title="错误率 (%)",
                    hovermode="x unified",
                    height=300
                )
                
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("暂无小时级数据")
    
    # 标签页4: 进化状态
    with tab4:
        st.header("进化状态")
        
        evolution = data.get("evolution", {})
        
        if not evolution:
            st.warning("无法加载进化状态数据")
        else:
            # 进化引擎状态
            engine_status = evolution.get("engine_status", {})
            
            col1, col2, col3 = st.columns(3)
            col1.metric("引擎状态", engine_status.get("status", "unknown"))
            col2.metric("待处理计划", evolution.get("pending_plans", 0))
            col3.metric("已执行计划", evolution.get("executed_plans", 0))
            
            st.divider()
            
            # 最近执行的计划
            recent_plans = evolution.get("recent_plans", [])
            if recent_plans:
                st.subheader("最近执行的计划")
                
                for plan in recent_plans:
                    with st.container(border=True):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.markdown(f"**计划目标**: {plan['goal']}")
                            st.caption(f"计划ID: {plan['plan_id']}")
                        
                        with col2:
                            status_color = {
                                "completed": "green",
                                "failed": "red",
                                "executing": "blue",
                                "proposed": "gray"
                            }.get(plan["status"], "gray")
                            
                            st.markdown(f"**状态**: :{status_color}[{plan['status'].upper()}]")
                            st.caption(f"执行时间: {plan['executed_at']}")
                
                st.divider()
            
            # 宪法检查记录
            constitution_checks = evolution.get("constitution_checks", [])
            if constitution_checks:
                st.subheader("宪法检查记录")
                
                df_checks = pd.DataFrame(constitution_checks)
                if not df_checks.empty:
                    df_checks["timestamp"] = pd.to_datetime(df_checks["timestamp"])
                    df_checks = df_checks.sort_values("timestamp", ascending=False)
                    
                    # 显示表格
                    st.dataframe(
                        df_checks[["timestamp", "plan_id", "compliance", "score", "issues"]],
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("暂无宪法检查记录")
    
    # 标签页5: Hands能力
    with tab5:
        st.header("Hands能力状态")
        
        hands = data.get("hands", {})
        
        if not hands:
            st.warning("无法加载Hands能力数据")
        else:
            # 能力统计
            col1, col2, col3 = st.columns(3)
            col1.metric("总能力数", hands.get("total_capabilities", 0))
            col2.metric("启用能力", hands.get("enabled_capabilities", 0))
            col3.metric("禁用能力", hands.get("disabled_capabilities", 0))
            
            st.divider()
            
            # 能力列表
            capability_list = hands.get("capability_list", [])
            if capability_list:
                st.subheader("能力列表")
                
                # 按类别分组
                categories = {}
                for capability in capability_list:
                    category = capability.get("category", "未分类")
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(capability)
                
                for category, capabilities in categories.items():
                    with st.expander(f"{category} ({len(capabilities)}个能力)", expanded=True):
                        for capability in capabilities:
                            enabled_status = "✅ 启用" if capability["enabled"] else "❌ 禁用"
                            
                            with st.container(border=True):
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    st.markdown(f"**{capability['name']}**")
                                    st.caption(capability["description"])
                                
                                with col2:
                                    st.caption(enabled_status)
                                    st.caption(f"使用次数: {capability['usage_count']}")
                                    st.caption(f"最后使用: {capability['last_used']}")
            else:
                st.info("暂无能力数据")
    
    # 标签页7: 旨意看板 (任务卡片和心跳监控)
    with tab7:
        st.header("🏛️ 旨意看板")
        st.markdown("基于唐朝三省六部制架构的任务卡片和Agent心跳监控")
        
        heartbeat_data = data.get("heartbeat", {})
        
        if not heartbeat_data:
            st.warning("无法加载心跳监控数据")
        else:
            # 系统健康摘要
            system_health = heartbeat_data.get("system_health", {})
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                system_status = system_health.get("system_status", "unknown")
                status_colors = {
                    "healthy": "🟢",
                    "degraded": "🟡",
                    "warning": "🟠",
                    "error": "🔴",
                    "unknown": "⚪"
                }
                status_icon = status_colors.get(system_status, "⚪")
                st.metric("系统状态", f"{status_icon} {system_status.upper()}")
            
            with col2:
                total_agents = system_health.get("total_agents", 0)
                st.metric("总Agent数", total_agents)
            
            with col3:
                active_agents = system_health.get("active_agents", 0)
                st.metric("活跃Agent", active_agents)
            
            with col4:
                avg_health_score = system_health.get("avg_health_score", 0)
                st.metric("平均健康分", f"{avg_health_score:.1%}")
            
            st.divider()
            
            # Agent状态卡片
            st.subheader("Agent状态卡片")
            
            agent_heartbeats = heartbeat_data.get("agent_heartbeats", [])
            if agent_heartbeats:
                # 按状态分组
                agents_by_status = {}
                for agent in agent_heartbeats:
                    status = agent.get("status", "unknown")
                    if status not in agents_by_status:
                        agents_by_status[status] = []
                    agents_by_status[status].append(agent)
                
                # 状态标签和颜色
                status_config = {
                    "active": {"label": "活跃", "color": "🟢", "badge": "success"},
                    "idle": {"label": "空闲", "color": "🟡", "badge": "warning"},
                    "warning": {"label": "警告", "color": "🟠", "badge": "warning"},
                    "error": {"label": "错误", "color": "🔴", "badge": "error"},
                    "stalled": {"label": "停滞", "color": "⚫", "badge": "off"}
                }
                
                # 显示状态列
                cols = st.columns(len(status_config))
                status_keys = list(status_config.keys())
                
                for idx, status_key in enumerate(status_keys):
                    with cols[idx]:
                        config = status_config.get(status_key, {})
                        agents = agents_by_status.get(status_key, [])
                        
                        st.markdown(f"### {config.get('color', '⚪')} {config.get('label', status_key)}")
                        st.markdown(f"**{len(agents)} 个Agent**")
                        
                        if agents:
                            with st.expander(f"查看详情 ({len(agents)}个)", expanded=False):
                                for agent in agents:
                                    with st.container(border=True):
                                        # Agent卡片
                                        col_a1, col_a2 = st.columns([3, 1])
                                        with col_a1:
                                            st.markdown(f"**{agent['agent_id']}**")
                                            st.caption(f"类型: {agent['agent_type']}")
                                            st.caption(f"能力数: {agent['capabilities_count']}")
                                        
                                        with col_a2:
                                            health_score = agent.get('health_score', 0)
                                            health_color = "green" if health_score > 0.7 else "orange" if health_score > 0.4 else "red"
                                            st.markdown(f":{health_color}[{health_score:.0%}]")
                                            st.caption(f"年龄: {agent.get('heartbeat_age', 0):.0f}s")
                
                st.divider()
                
                # 详细表格视图
                st.subheader("详细Agent状态")
                
                # 转换为DataFrame
                df_agents = pd.DataFrame(agent_heartbeats)
                if not df_agents.empty:
                    # 重命名列
                    df_display = df_agents.copy()
                    df_display['状态'] = df_display['status'].map(
                        lambda x: status_config.get(x, {}).get('label', x)
                    )
                    
                    # 选择显示的列
                    display_cols = ['agent_id', 'agent_type', '状态', 'health_score', 
                                   'heartbeat_age', 'capabilities_count', 'last_activity']
                    
                    # 过滤存在的列
                    available_cols = [col for col in display_cols if col in df_display.columns]
                    
                    if available_cols:
                        st.dataframe(
                            df_display[available_cols],
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                'agent_id': 'Agent ID',
                                'agent_type': '类型',
                                'health_score': st.column_config.ProgressColumn(
                                    '健康分',
                                    help="Agent健康分数 (0-1)",
                                    format="%.2f",
                                    min_value=0,
                                    max_value=1
                                ),
                                'heartbeat_age': '心跳年龄(s)',
                                'capabilities_count': '能力数',
                                'last_activity': '最后活动'
                            }
                        )
            else:
                st.info("暂无Agent心跳数据")
            
            st.divider()
            
            # 心跳告警
            st.subheader("心跳告警")
            
            active_alerts = heartbeat_data.get("active_alerts", [])
            if active_alerts:
                # 按严重程度分组
                alerts_by_severity = {}
                for alert in active_alerts:
                    severity = alert.get("severity", "info")
                    if severity not in alerts_by_severity:
                        alerts_by_severity[severity] = []
                    alerts_by_severity[severity].append(alert)
                
                # 显示告警
                for severity in ["critical", "warning", "info"]:
                    alerts = alerts_by_severity.get(severity, [])
                    if alerts:
                        severity_icons = {
                            "critical": "🔴",
                            "warning": "🟠",
                            "info": "🔵"
                        }
                        
                        with st.expander(f"{severity_icons.get(severity, '⚪')} {severity.upper()} 告警 ({len(alerts)}个)", 
                                       expanded=severity=="critical"):
                            for alert in alerts:
                                with st.container(border=True):
                                    col_a1, col_a2 = st.columns([4, 1])
                                    with col_a1:
                                        st.markdown(f"**{alert['message']}**")
                                        st.caption(f"Agent: {alert['agent_id']}")
                                        st.caption(f"时间: {alert['timestamp']}")
                                    
                                    with col_a2:
                                        if st.button("解决", key=f"resolve_hb_{alert['alert_id']}", 
                                                   use_container_width=True):
                                            # 这里可以添加解决告警的逻辑
                                            st.success(f"已标记解决: {alert['alert_id']}")
                                            st.rerun()
            else:
                st.success("🎉 当前没有心跳告警")
            
            st.divider()
            
            # 系统建议
            st.subheader("系统建议")
            
            if system_health.get("system_status") == "error":
                st.error("⚠️ 系统处于错误状态，建议立即检查错误Agent")
            elif system_health.get("system_status") == "warning":
                st.warning("⚠️ 系统处于警告状态，建议关注警告Agent")
            elif system_health.get("system_status") == "degraded":
                st.warning("⚠️ 系统性能下降，建议优化资源分配")
            elif system_health.get("system_status") == "healthy":
                st.success("✅ 系统运行正常")
            
            # 具体建议
            suggestions = []
            
            error_count = system_health.get("error_agents", 0)
            if error_count > 0:
                suggestions.append(f"有 {error_count} 个Agent处于错误状态，需要立即处理")
            
            warning_count = system_health.get("warning_agents", 0)
            if warning_count > 0:
                suggestions.append(f"有 {warning_count} 个Agent处于警告状态，建议关注")
            
            stalled_count = system_health.get("stalled_agents", 0)
            if stalled_count > 0:
                suggestions.append(f"有 {stalled_count} 个Agent心跳停滞，可能需要重启")
            
            avg_health = system_health.get("avg_health_score", 0)
            if avg_health < 0.7:
                suggestions.append(f"平均健康分数较低 ({avg_health:.1%})，建议系统优化")
            
            if suggestions:
                for i, suggestion in enumerate(suggestions, 1):
                    st.markdown(f"{i}. {suggestion}")
            else:
                st.info("系统运行良好，暂无优化建议")
    
    # 页脚
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption(f"数据更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with col2:
        st.caption("仪表盘版本: 1.0.0")
    
    with col3:
        if st.button("🔄 手动刷新数据"):
            st.rerun()


if __name__ == "__main__":
    run_dashboard()