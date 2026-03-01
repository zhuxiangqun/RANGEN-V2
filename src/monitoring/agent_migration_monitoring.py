#!/usr/bin/env python3
"""
Agent迁移稳定性监控系统
专门监控逐步替换Agent的性能表现、替换率变化和系统稳定性
"""

import asyncio
import time
import threading
import logging
import json
import psutil
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
from pathlib import Path
import statistics

from src.utils.logging_helper import get_module_logger, ModuleType

logger = logging.getLogger(__name__)


@dataclass
class AgentMigrationMetrics:
    """Agent迁移指标"""
    agent_name: str
    timestamp: datetime

    # 替换统计
    replacement_rate: float
    new_agent_calls: int
    old_agent_calls: int
    total_calls: int

    # 性能指标
    avg_response_time: float
    success_rate: float
    error_rate: float

    # 资源使用
    cpu_usage: float
    memory_usage: float

    # 稳定性指标
    performance_variance: float
    error_trend: List[float]


@dataclass
class MigrationStabilityReport:
    """迁移稳定性报告"""
    report_id: str
    timestamp: datetime
    monitoring_period: timedelta

    # 总体统计
    total_agents_monitored: int
    agents_with_issues: int
    overall_stability_score: float

    # Agent详情
    agent_reports: Dict[str, Dict[str, Any]]

    # 建议
    recommendations: List[str]

    # 异常事件
    anomalies: List[Dict[str, Any]]


class AgentMigrationMonitor:
    """Agent迁移稳定性监控器"""

    def __init__(self, monitoring_interval: int = 60):
        """
        初始化监控器

        Args:
            monitoring_interval: 监控间隔(秒)
        """
        self.monitoring_interval = monitoring_interval
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None

        # 监控数据存储
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.current_metrics: Dict[str, AgentMigrationMetrics] = {}

        # 告警规则
        self.alert_rules = self._initialize_alert_rules()

        # 报告存储
        self.reports: List[MigrationStabilityReport] = []

        # 配置
        self.data_dir = Path("data/migration_monitoring")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Agent迁移稳定性监控器初始化完成")

    def _initialize_alert_rules(self) -> Dict[str, Dict[str, Any]]:
        """初始化告警规则"""
        return {
            'high_error_rate': {
                'name': '高错误率告警',
                'threshold': 0.05,  # 5%错误率
                'severity': 'warning'
            },
            'performance_degradation': {
                'name': '性能下降告警',
                'threshold': 1.5,  # 响应时间增加50%
                'severity': 'warning'
            },
            'replacement_rate_stuck': {
                'name': '替换率停滞告警',
                'threshold': 3600,  # 1小时无变化
                'severity': 'info'
            },
            'memory_usage_high': {
                'name': '内存使用过高',
                'threshold': 0.8,  # 80%内存使用率
                'severity': 'warning'
            }
        }

    async def start_monitoring(self):
        """启动监控"""
        if self.is_running:
            logger.warning("监控器已经在运行中")
            return

        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()

        logger.info(f"Agent迁移稳定性监控已启动，监控间隔: {self.monitoring_interval}秒")

    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        logger.info("Agent迁移稳定性监控已停止")

    def _monitoring_loop(self):
        """监控主循环"""
        while self.is_running:
            try:
                asyncio.run(self._collect_metrics())
                asyncio.run(self._check_alerts())
                self._save_metrics()

                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"监控循环异常: {e}", exc_info=True)
                time.sleep(5)  # 出错后短暂等待再试

    async def _collect_metrics(self):
        """收集指标"""
        try:
            # 收集逐步替换Agent的指标
            agents_to_monitor = [
                'ChiefAgentWrapper',
                'AnswerGenerationAgentWrapper',
                'LearningSystemWrapper',
                'StrategicChiefAgentWrapper',
                'PromptEngineeringAgentWrapper',
                'ContextEngineeringAgentWrapper',
                'OptimizedKnowledgeRetrievalAgentWrapper'
            ]

            for agent_name in agents_to_monitor:
                metrics = await self._collect_agent_metrics(agent_name)
                if metrics:
                    self.current_metrics[agent_name] = metrics
                    self.metrics_history[agent_name].append(metrics)

        except Exception as e:
            logger.error(f"收集指标异常: {e}", exc_info=True)

    async def _collect_agent_metrics(self, agent_name: str) -> Optional[AgentMigrationMetrics]:
        """收集单个Agent的指标"""
        try:
            # 这里应该从实际的Agent包装器实例收集数据
            # 由于无法直接访问实例，我们使用模拟数据作为示例

            # 获取系统资源使用情况
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent

            # 模拟Agent指标（实际实现中应该从包装器获取）
            replacement_rate = 0.01  # 默认1%
            new_agent_calls = 10
            old_agent_calls = 990
            total_calls = new_agent_calls + old_agent_calls

            # 模拟性能指标
            avg_response_time = 2.5 + (replacement_rate * 0.5)  # 新Agent可能稍慢
            success_rate = 0.95 + (replacement_rate * 0.03)  # 新Agent可能更稳定
            error_rate = 1.0 - success_rate

            # 计算性能方差
            recent_metrics = list(self.metrics_history[agent_name])[-10:]  # 最近10个数据点
            if recent_metrics:
                response_times = [m.avg_response_time for m in recent_metrics]
                performance_variance = statistics.variance(response_times) if len(response_times) > 1 else 0
            else:
                performance_variance = 0

            return AgentMigrationMetrics(
                agent_name=agent_name,
                timestamp=datetime.now(),
                replacement_rate=replacement_rate,
                new_agent_calls=new_agent_calls,
                old_agent_calls=old_agent_calls,
                total_calls=total_calls,
                avg_response_time=avg_response_time,
                success_rate=success_rate,
                error_rate=error_rate,
                cpu_usage=cpu_percent,
                memory_usage=memory_percent,
                performance_variance=performance_variance,
                error_trend=[0.05, 0.04, 0.03, 0.05, 0.04]  # 模拟错误趋势
            )

        except Exception as e:
            logger.error(f"收集{agent_name}指标异常: {e}")
            return None

    async def _check_alerts(self):
        """检查告警"""
        for agent_name, metrics in self.current_metrics.items():
            await self._check_agent_alerts(agent_name, metrics)

    async def _check_agent_alerts(self, agent_name: str, metrics: AgentMigrationMetrics):
        """检查单个Agent的告警"""
        # 检查错误率
        if metrics.error_rate > self.alert_rules['high_error_rate']['threshold']:
            self._trigger_alert(
                'high_error_rate',
                agent_name,
                f"{agent_name}错误率过高: {metrics.error_rate:.1%}",
                metrics.error_rate,
                self.alert_rules['high_error_rate']['threshold']
            )

        # 检查性能下降
        recent_metrics = list(self.metrics_history[agent_name])[-5:]  # 最近5个数据点
        if len(recent_metrics) >= 2:
            baseline_time = recent_metrics[0].avg_response_time
            current_time = metrics.avg_response_time
            if current_time > baseline_time * self.alert_rules['performance_degradation']['threshold']:
                self._trigger_alert(
                    'performance_degradation',
                    agent_name,
                    f"{agent_name}性能下降: {current_time:.2f}s vs {baseline_time:.2f}s",
                    current_time / baseline_time,
                    self.alert_rules['performance_degradation']['threshold']
                )

        # 检查内存使用
        if metrics.memory_usage > self.alert_rules['memory_usage_high']['threshold']:
            self._trigger_alert(
                'memory_usage_high',
                agent_name,
                f"{agent_name}内存使用过高: {metrics.memory_usage:.1%}",
                metrics.memory_usage,
                self.alert_rules['memory_usage_high']['threshold']
            )

    def _trigger_alert(self, rule_name: str, agent_name: str, message: str,
                      actual_value: float, threshold: float):
        """触发告警"""
        severity = self.alert_rules[rule_name]['severity']

        logger.warning(f"🚨 [{severity.upper()}] {rule_name}: {message}")

        # 这里可以扩展为发送邮件、Slack通知等
        # 现在只记录到日志

    def _save_metrics(self):
        """保存指标数据"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_{timestamp}.json"
            filepath = self.data_dir / filename

            data = {
                'timestamp': timestamp,
                'metrics': {}
            }

            for agent_name, metrics in self.current_metrics.items():
                data['metrics'][agent_name] = {
                    'replacement_rate': metrics.replacement_rate,
                    'new_agent_calls': metrics.new_agent_calls,
                    'old_agent_calls': metrics.old_agent_calls,
                    'total_calls': metrics.total_calls,
                    'avg_response_time': metrics.avg_response_time,
                    'success_rate': metrics.success_rate,
                    'error_rate': metrics.error_rate,
                    'cpu_usage': metrics.cpu_usage,
                    'memory_usage': metrics.memory_usage,
                    'performance_variance': metrics.performance_variance
                }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        except Exception as e:
            logger.error(f"保存指标数据异常: {e}")

    async def generate_stability_report(self, monitoring_period: timedelta = timedelta(hours=1)) -> MigrationStabilityReport:
        """生成稳定性报告"""
        try:
            report_id = f"stability_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 计算总体统计
            total_agents = len(self.current_metrics)
            agents_with_issues = 0
            stability_scores = []

            agent_reports = {}

            for agent_name, metrics in self.current_metrics.items():
                # 分析Agent稳定性
                stability_score = self._calculate_agent_stability_score(metrics)
                stability_scores.append(stability_score)

                # 检查是否有问题
                has_issues = (
                    metrics.error_rate > 0.05 or
                    metrics.memory_usage > 0.8 or
                    stability_score < 0.7
                )

                if has_issues:
                    agents_with_issues += 1

                agent_reports[agent_name] = {
                    'stability_score': stability_score,
                    'current_metrics': {
                        'replacement_rate': metrics.replacement_rate,
                        'error_rate': metrics.error_rate,
                        'avg_response_time': metrics.avg_response_time,
                        'memory_usage': metrics.memory_usage
                    },
                    'has_issues': has_issues,
                    'recommendations': self._generate_agent_recommendations(metrics)
                }

            overall_stability_score = statistics.mean(stability_scores) if stability_scores else 0

            # 生成建议
            recommendations = self._generate_overall_recommendations(
                total_agents, agents_with_issues, overall_stability_score
            )

            # 检测异常事件
            anomalies = self._detect_anomalies()

            report = MigrationStabilityReport(
                report_id=report_id,
                timestamp=datetime.now(),
                monitoring_period=monitoring_period,
                total_agents_monitored=total_agents,
                agents_with_issues=agents_with_issues,
                overall_stability_score=overall_stability_score,
                agent_reports=agent_reports,
                recommendations=recommendations,
                anomalies=anomalies
            )

            self.reports.append(report)

            # 保存报告
            self._save_stability_report(report)

            return report

        except Exception as e:
            logger.error(f"生成稳定性报告异常: {e}", exc_info=True)
            return None

    def _calculate_agent_stability_score(self, metrics: AgentMigrationMetrics) -> float:
        """计算Agent稳定性评分"""
        try:
            # 基于多个指标计算综合评分
            error_score = max(0, 1 - metrics.error_rate * 20)  # 错误率评分
            performance_score = max(0, 1 - metrics.performance_variance)  # 性能稳定性评分
            resource_score = max(0, 1 - metrics.memory_usage)  # 资源使用评分
            success_score = metrics.success_rate  # 成功率评分

            # 加权平均
            weights = [0.3, 0.2, 0.2, 0.3]
            scores = [error_score, performance_score, resource_score, success_score]

            stability_score = sum(w * s for w, s in zip(weights, scores))
            return min(1.0, max(0.0, stability_score))

        except Exception as e:
            logger.error(f"计算稳定性评分异常: {e}")
            return 0.5

    def _generate_agent_recommendations(self, metrics: AgentMigrationMetrics) -> List[str]:
        """生成Agent特定建议"""
        recommendations = []

        if metrics.error_rate > 0.05:
            recommendations.append("错误率偏高，建议检查新Agent的错误处理逻辑")

        if metrics.avg_response_time > 3.0:
            recommendations.append("响应时间较长，建议优化新Agent的性能")

        if metrics.memory_usage > 0.8:
            recommendations.append("内存使用过高，建议检查内存泄漏问题")

        if metrics.replacement_rate < 0.01:
            recommendations.append("替换率过低，建议逐步增加替换比例")

        if not recommendations:
            recommendations.append("Agent运行正常，继续监控")

        return recommendations

    def _generate_overall_recommendations(self, total_agents: int, agents_with_issues: int,
                                        overall_score: float) -> List[str]:
        """生成总体建议"""
        recommendations = []

        if overall_score < 0.7:
            recommendations.append("整体稳定性评分较低，建议暂停替换率增加，重点排查问题")

        if agents_with_issues > total_agents * 0.3:
            recommendations.append("过多Agent存在问题，建议回滚部分替换或进行深度调试")

        if overall_score > 0.9:
            recommendations.append("系统运行稳定，可以考虑增加替换率")

        recommendations.append("建议定期查看详细的稳定性报告以监控趋势变化")

        return recommendations

    def _detect_anomalies(self) -> List[Dict[str, Any]]:
        """检测异常事件"""
        anomalies = []

        for agent_name, history in self.metrics_history.items():
            if len(history) < 5:
                continue

            recent_metrics = list(history)[-5:]

            # 检测错误率突然上升
            error_rates = [m.error_rate for m in recent_metrics]
            if len(error_rates) >= 3:
                recent_avg = statistics.mean(error_rates[-3:])
                earlier_avg = statistics.mean(error_rates[:-3]) if len(error_rates) > 3 else error_rates[0]

                if recent_avg > earlier_avg * 2 and recent_avg > 0.1:
                    anomalies.append({
                        'type': 'error_rate_spike',
                        'agent': agent_name,
                        'description': f"{agent_name}错误率突然上升: {earlier_avg:.1%} → {recent_avg:.1%}",
                        'severity': 'high',
                        'timestamp': datetime.now()
                    })

        return anomalies

    def _save_stability_report(self, report: MigrationStabilityReport):
        """保存稳定性报告"""
        try:
            filename = f"stability_report_{report.report_id}.json"
            filepath = self.data_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'report_id': report.report_id,
                    'timestamp': report.timestamp.isoformat(),
                    'monitoring_period_seconds': report.monitoring_period.total_seconds(),
                    'total_agents_monitored': report.total_agents_monitored,
                    'agents_with_issues': report.agents_with_issues,
                    'overall_stability_score': report.overall_stability_score,
                    'agent_reports': report.agent_reports,
                    'recommendations': report.recommendations,
                    'anomalies': [
                        {
                            'type': a['type'],
                            'agent': a['agent'],
                            'description': a['description'],
                            'severity': a['severity'],
                            'timestamp': a['timestamp'].isoformat()
                        }
                        for a in report.anomalies
                    ]
                }, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"稳定性报告已保存: {filepath}")

        except Exception as e:
            logger.error(f"保存稳定性报告异常: {e}")

    def get_monitoring_summary(self) -> Dict[str, Any]:
        """获取监控摘要"""
        return {
            'is_running': self.is_running,
            'monitoring_interval': self.monitoring_interval,
            'agents_monitored': list(self.current_metrics.keys()),
            'total_reports': len(self.reports),
            'data_directory': str(self.data_dir),
            'last_metrics_timestamp': max(
                (m.timestamp for m in self.current_metrics.values()),
                default=None
            )
        }


# 全局监控器实例
_monitor = None


def get_migration_monitor() -> AgentMigrationMonitor:
    """获取全局迁移监控器实例"""
    global _monitor
    if _monitor is None:
        _monitor = AgentMigrationMonitor()
    return _monitor


async def start_migration_monitoring():
    """启动迁移监控"""
    monitor = get_migration_monitor()
    await monitor.start_monitoring()


def stop_migration_monitoring():
    """停止迁移监控"""
    monitor = get_migration_monitor()
    monitor.stop_monitoring()


async def generate_stability_report() -> Optional[MigrationStabilityReport]:
    """生成稳定性报告"""
    monitor = get_migration_monitor()
    return await monitor.generate_stability_report()


def get_monitoring_summary() -> Dict[str, Any]:
    """获取监控摘要"""
    monitor = get_migration_monitor()
    return monitor.get_monitoring_summary()
