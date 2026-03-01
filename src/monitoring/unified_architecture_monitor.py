#!/usr/bin/env python3
"""
统一架构监控系统
监控8个核心Agent的运行状态、性能指标和健康状态
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import psutil
import threading

from ..utils.unified_centers import get_unified_config_center
from ..utils.unified_threshold_manager import get_unified_threshold_manager
from ..agents.agent_coordinator import AgentCoordinator
from ..agents.reasoning_expert import ReasoningExpert
from ..agents.rag_agent import RAGExpert
from ..agents.tool_orchestrator import ToolOrchestrator
from ..agents.memory_manager import MemoryManager
from ..agents.learning_optimizer import LearningOptimizer
from ..agents.quality_controller import QualityController
from ..agents.security_guardian import SecurityGuardian

logger = logging.getLogger(__name__)


class UnifiedArchitectureMonitor:
    """统一架构监控系统"""

    def __init__(self):
        self.config_center = get_unified_config_center()
        self.threshold_manager = get_unified_threshold_manager()

        # 核心Agent列表
        self.core_agents = {
            'AgentCoordinator': AgentCoordinator,
            'ReasoningExpert': ReasoningExpert,
            'RAGExpert': RAGExpert,
            'ToolOrchestrator': ToolOrchestrator,
            'MemoryManager': MemoryManager,
            'LearningOptimizer': LearningOptimizer,
            'QualityController': QualityController,
            'SecurityGuardian': SecurityGuardian
        }

        # 监控状态
        self.monitoring_active = False
        self.monitoring_thread = None
        self.monitoring_interval = 30  # 30秒间隔

        # 监控数据
        self.agent_health_status = {}
        self.performance_metrics = {}
        self.system_metrics = {}
        self.alerts = []

        # 历史数据
        self.metrics_history = []
        self.max_history_size = 1000

        logger.info("✅ 统一架构监控系统初始化完成")

    def start_monitoring(self):
        """启动监控"""
        if self.monitoring_active:
            logger.warning("监控系统已在运行中")
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

        logger.info("🟢 统一架构监控系统已启动")

    def stop_monitoring(self):
        """停止监控"""
        if not self.monitoring_active:
            return

        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)

        logger.info("🔴 统一架构监控系统已停止")

    def _monitoring_loop(self):
        """监控主循环"""
        while self.monitoring_active:
            try:
                # 收集监控数据
                self._collect_agent_health()
                self._collect_performance_metrics()
                self._collect_system_metrics()
                self._check_alerts()

                # 保存历史数据
                self._save_metrics_snapshot()

                # 等待下一个监控周期
                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"监控循环异常: {e}", exc_info=True)
                time.sleep(5)  # 出错时等待5秒后重试

    def _collect_agent_health(self):
        """收集Agent健康状态"""
        current_time = datetime.now()

        for agent_name, agent_class in self.core_agents.items():
            try:
                # 检查Agent是否可以实例化
                agent_instance = agent_class()
                health_status = {
                    'agent_name': agent_name,
                    'status': 'healthy',
                    'last_check': current_time.isoformat(),
                    'response_time': None,
                    'error_count': 0,
                    'last_error': None
                }

                # 尝试执行健康检查
                start_time = time.time()
                # 这里可以添加具体的健康检查逻辑
                health_status['response_time'] = time.time() - start_time

            except Exception as e:
                health_status = {
                    'agent_name': agent_name,
                    'status': 'unhealthy',
                    'last_check': current_time.isoformat(),
                    'response_time': None,
                    'error_count': 1,
                    'last_error': str(e)
                }

            self.agent_health_status[agent_name] = health_status

    def _collect_performance_metrics(self):
        """收集性能指标"""
        current_time = datetime.now()

        # 模拟收集性能指标（实际应该从各个Agent收集）
        self.performance_metrics = {
            'timestamp': current_time.isoformat(),
            'agent_metrics': {},
            'system_metrics': {
                'cpu_usage': psutil.cpu_percent(interval=1),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent
            }
        }

        # 为每个Agent收集性能指标
        for agent_name in self.core_agents.keys():
            self.performance_metrics['agent_metrics'][agent_name] = {
                'request_count': 0,  # 应该从实际Agent收集
                'avg_response_time': 0.0,
                'error_rate': 0.0,
                'throughput': 0.0
            }

    def _collect_system_metrics(self):
        """收集系统级指标"""
        current_time = datetime.now()

        # 收集系统指标，处理权限限制
        system_metrics = {
            'timestamp': current_time.isoformat(),
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }

        # 尝试收集网络连接数（可能因权限限制失败）
        try:
            system_metrics['network_connections'] = len(psutil.net_connections())
        except (PermissionError, OSError):
            system_metrics['network_connections'] = None

        # 尝试收集负载平均值
        try:
            system_metrics['load_average'] = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        except (PermissionError, OSError):
            system_metrics['load_average'] = None

        self.system_metrics = system_metrics

    def _check_alerts(self):
        """检查告警条件"""
        current_alerts = []

        # 检查Agent健康状态
        for agent_name, health in self.agent_health_status.items():
            if health['status'] == 'unhealthy':
                current_alerts.append({
                    'type': 'agent_unhealthy',
                    'severity': 'critical',
                    'agent': agent_name,
                    'message': f"Agent {agent_name} 健康检查失败: {health['last_error']}",
                    'timestamp': health['last_check']
                })

        # 检查系统资源使用率
        if self.system_metrics.get('cpu_percent', 0) > 90:
            current_alerts.append({
                'type': 'high_cpu_usage',
                'severity': 'warning',
                'message': f"CPU使用率过高: {self.system_metrics['cpu_percent']:.1f}%",
                'timestamp': datetime.now().isoformat()
            })

        if self.system_metrics.get('memory_percent', 0) > 90:
            current_alerts.append({
                'type': 'high_memory_usage',
                'severity': 'warning',
                'message': f"内存使用率过高: {self.system_metrics['memory_percent']:.1f}%",
                'timestamp': datetime.now().isoformat()
            })

        self.alerts = current_alerts

    def _save_metrics_snapshot(self):
        """保存指标快照到历史记录"""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'agent_health': self.agent_health_status.copy(),
            'performance': self.performance_metrics.copy(),
            'system': self.system_metrics.copy(),
            'alerts': self.alerts.copy()
        }

        self.metrics_history.append(snapshot)

        # 限制历史记录大小
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]

    def get_current_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            'monitoring_active': self.monitoring_active,
            'last_update': datetime.now().isoformat(),
            'agent_health': self.agent_health_status,
            'performance_metrics': self.performance_metrics,
            'system_metrics': self.system_metrics,
            'active_alerts': self.alerts,
            'monitoring_interval': self.monitoring_interval
        }

    def get_health_summary(self) -> Dict[str, Any]:
        """获取健康摘要"""
        total_agents = len(self.core_agents)
        healthy_agents = sum(1 for h in self.agent_health_status.values() if h['status'] == 'healthy')
        unhealthy_agents = total_agents - healthy_agents

        return {
            'total_agents': total_agents,
            'healthy_agents': healthy_agents,
            'unhealthy_agents': unhealthy_agents,
            'health_percentage': (healthy_agents / total_agents * 100) if total_agents > 0 else 0,
            'alerts_count': len(self.alerts),
            'last_check': max((h['last_check'] for h in self.agent_health_status.values()), default=None)
        }

    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """获取性能报告"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # 筛选指定时间范围内的历史数据
        recent_history = [
            h for h in self.metrics_history
            if datetime.fromisoformat(h['timestamp']) > cutoff_time
        ]

        if not recent_history:
            return {'error': '没有足够的历史数据'}

        # 计算性能统计
        agent_performance = {}
        system_performance = {
            'cpu_avg': sum(h['system'].get('cpu_percent', 0) for h in recent_history) / len(recent_history),
            'memory_avg': sum(h['system'].get('memory_percent', 0) for h in recent_history) / len(recent_history),
            'disk_avg': sum(h['system'].get('disk_percent', 0) for h in recent_history) / len(recent_history)
        }

        return {
            'time_range_hours': hours,
            'data_points': len(recent_history),
            'system_performance': system_performance,
            'agent_performance': agent_performance,
            'generated_at': datetime.now().isoformat()
        }

    def export_monitoring_data(self, filepath: str):
        """导出监控数据"""
        data = {
            'export_time': datetime.now().isoformat(),
            'current_status': self.get_current_status(),
            'health_summary': self.get_health_summary(),
            'performance_report_24h': self.get_performance_report(24),
            'metrics_history': self.metrics_history[-100:]  # 最近100个数据点
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"监控数据已导出到: {filepath}")


# 全局监控实例
_monitor_instance = None
_monitor_lock = threading.Lock()


def get_unified_architecture_monitor() -> UnifiedArchitectureMonitor:
    """获取统一架构监控实例"""
    global _monitor_instance

    if _monitor_instance is None:
        with _monitor_lock:
            if _monitor_instance is None:
                _monitor_instance = UnifiedArchitectureMonitor()

    return _monitor_instance


if __name__ == "__main__":
    # 测试监控系统
    monitor = get_unified_architecture_monitor()
    monitor.start_monitoring()

    try:
        # 运行10分钟测试
        print("🟢 监控系统启动，开始测试...")
        for i in range(20):  # 20次 * 30秒 = 10分钟
            time.sleep(30)
            status = monitor.get_current_status()
            summary = monitor.get_health_summary()
            print(f"检查点 {i+1}: {summary['healthy_agents']}/{summary['total_agents']} Agent健康，{len(status['active_alerts'])}个告警")

    except KeyboardInterrupt:
        print("\n⚠️ 收到中断信号，正在停止监控...")
    finally:
        monitor.stop_monitoring()
        print("✅ 监控系统已停止")
