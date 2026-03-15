"""
量化指标采集与分析服务
Quantitative Metrics Collection and Analysis Service

核心功能：
1. 多维度指标采集 - 性能、用户行为、系统健康
2. 时序数据存储 - 高效的时间序列数据管理
3. 指标分析与报表 - 自动生成分析报告
4. 告警与监控 - 异常检测和告警触发
5. 量化决策支持 - 基于数据的智能决策

V3理念量化衡量标准：
- 能力生命周期管理指标
- 能力组合与编排指标
- 安全与治理指标
- 系统自进化指标
- 开放性与扩展性指标
"""

import logging
import time
import json
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
from datetime import datetime, timedelta
from threading import Lock
import threading

logger = logging.getLogger(__name__)


class MetricCategory(str, Enum):
    """指标类别"""
    PERFORMANCE = "performance"         # 性能指标
    CAPABILITY = "capability"           # 能力指标
    SECURITY = "security"               # 安全指标
    EVOLUTION = "evolution"             # 进化指标
    USER_BEHAVIOR = "user_behavior"     # 用户行为指标
    SYSTEM_HEALTH = "system_health"     # 系统健康指标


class MetricUnit(str, Enum):
    """指标单位"""
    MS = "milliseconds"       # 毫秒
    COUNT = "count"           # 次数
    PERCENT = "percent"       # 百分比
    BYTES = "bytes"           # 字节
    RATIO = "ratio"           # 比率


@dataclass
class MetricDefinition:
    """指标定义"""
    name: str
    category: MetricCategory
    unit: MetricUnit
    description: str
    tags: List[str] = field(default_factory=list)
    
    # 量化标准（来自V3报告）
    v3_dimension: str = ""              # V3维度
    v3_target: float = 0.0             # 目标值
    v3_baseline: float = 0.0            # 基准值


@dataclass
class MetricValue:
    """指标值"""
    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricAnalysis:
    """指标分析结果"""
    metric_name: str
    current_value: float
    baseline_value: float
    target_value: float
    trend: str                          # "improving", "stable", "declining"
    change_percent: float
    status: str                         # "good", "warning", "critical"
    recommendations: List[str] = field(default_factory=list)


class MetricsCollector:
    """指标采集器"""
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.definitions: Dict[str, MetricDefinition] = {}
        self.lock = Lock()
        
        # 初始化默认指标定义
        self._init_default_definitions()
        
        # 后台清理线程
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._running = True
        self._cleanup_thread.start()
        
        logger.info("指标采集器初始化完成")
    
    def _init_default_definitions(self) -> None:
        """初始化默认指标定义"""
        definitions = [
            # 能力生命周期管理指标
            MetricDefinition(
                name="capability_creation_time",
                category=MetricCategory.CAPABILITY,
                unit=MetricUnit.MS,
                description="能力创建平均时间",
                v3_dimension="能力生命周期管理",
                v3_target=60.0,  # 40%减少目标
                v3_baseline=100.0
            ),
            MetricDefinition(
                name="capability_reuse_rate",
                category=MetricCategory.CAPABILITY,
                unit=MetricUnit.PERCENT,
                description="能力复用率",
                v3_dimension="能力生命周期管理",
                v3_target=70.0,
                v3_baseline=30.0
            ),
            MetricDefinition(
                name="duplicate_capability_blocked",
                category=MetricCategory.CAPABILITY,
                unit=MetricUnit.PERCENT,
                description="重复能力拦截率",
                v3_dimension="能力生命周期管理",
                v3_target=85.0,
                v3_baseline=0.0
            ),
            
            # 能力组合与编排指标
            MetricDefinition(
                name="smart_recommendation_acceptance",
                category=MetricCategory.CAPABILITY,
                unit=MetricUnit.PERCENT,
                description="智能组合推荐采纳率",
                v3_dimension="能力组合与编排",
                v3_target=60.0,
                v3_baseline=0.0
            ),
            MetricDefinition(
                name="composition_creation_time",
                category=MetricCategory.CAPABILITY,
                unit=MetricUnit.MS,
                description="组合创建时间",
                v3_dimension="能力组合与编排",
                v3_target=50.0,  # 50%减少
                v3_baseline=100.0
            ),
            MetricDefinition(
                name="dynamic_adjustment_accuracy",
                category=MetricCategory.CAPABILITY,
                unit=MetricUnit.PERCENT,
                description="动态调整准确率",
                v3_dimension="能力组合与编排",
                v3_target=80.0,
                v3_baseline=0.0
            ),
            
            # 安全与治理指标
            MetricDefinition(
                name="security_incident_rate",
                category=MetricCategory.SECURITY,
                unit=MetricUnit.PERCENT,
                description="安全事件发生率",
                v3_dimension="安全与治理",
                v3_target=20.0,  # 80%降低
                v3_baseline=100.0
            ),
            MetricDefinition(
                name="governance_automation_coverage",
                category=MetricCategory.SECURITY,
                unit=MetricUnit.PERCENT,
                description="治理自动化覆盖率",
                v3_dimension="安全与治理",
                v3_target=90.0,
                v3_baseline=20.0
            ),
            MetricDefinition(
                name="compliance_pass_rate",
                category=MetricCategory.SECURITY,
                unit=MetricUnit.PERCENT,
                description="合规检查通过率",
                v3_dimension="安全与治理",
                v3_target=95.0,
                v3_baseline=0.0
            ),
            
            # 系统自进化指标
            MetricDefinition(
                name="performance_optimization_auto_rate",
                category=MetricCategory.EVOLUTION,
                unit=MetricUnit.PERCENT,
                description="性能优化自动化率",
                v3_dimension="系统自进化",
                v3_target=70.0,
                v3_baseline=0.0
            ),
            MetricDefinition(
                name="user_satisfaction",
                category=MetricCategory.EVOLUTION,
                unit=MetricUnit.PERCENT,
                description="用户满意度",
                v3_dimension="系统自进化",
                v3_target=200.0,  # 2倍提升
                v3_baseline=100.0
            ),
            MetricDefinition(
                name="maintenance_cost_reduction",
                category=MetricCategory.EVOLUTION,
                unit=MetricUnit.PERCENT,
                description="维护成本降低",
                v3_dimension="系统自进化",
                v3_target=50.0,
                v3_baseline=0.0
            ),
            
            # 性能指标
            MetricDefinition(
                name="response_time_p95",
                category=MetricCategory.PERFORMANCE,
                unit=MetricUnit.MS,
                description="P95响应时间",
                v3_dimension="性能",
                v3_target=3500.0,
                v3_baseline=5000.0
            ),
            MetricDefinition(
                name="request_latency",
                category=MetricCategory.PERFORMANCE,
                unit=MetricUnit.MS,
                description="请求延迟",
                v3_dimension="性能",
                v3_target=3200.0,
                v3_baseline=5000.0
            ),
            MetricDefinition(
                name="concurrent_support",
                category=MetricCategory.PERFORMANCE,
                unit=MetricUnit.COUNT,
                description="并发支持数",
                v3_dimension="性能",
                v3_target=1000.0,
                v3_baseline=500.0
            ),
            MetricDefinition(
                name="sandbox_start_time",
                category=MetricCategory.PERFORMANCE,
                unit=MetricUnit.MS,
                description="沙箱启动时间",
                v3_dimension="性能",
                v3_target=800.0,
                v3_baseline=1000.0
            ),
            MetricDefinition(
                name="knowledge_retrieval_latency",
                category=MetricCategory.PERFORMANCE,
                unit=MetricUnit.MS,
                description="知识检索延迟",
                v3_dimension="性能",
                v3_target=1500.0,
                v3_baseline=2000.0
            ),
            
            # 系统健康指标
            MetricDefinition(
                name="system_uptime",
                category=MetricCategory.SYSTEM_HEALTH,
                unit=MetricUnit.PERCENT,
                description="系统可用性",
                v3_dimension="系统健康",
                v3_target=99.9,
                v3_baseline=99.0
            ),
            MetricDefinition(
                name="error_rate",
                category=MetricCategory.SYSTEM_HEALTH,
                unit=MetricUnit.PERCENT,
                description="错误率",
                v3_dimension="系统健康",
                v3_target=1.0,
                v3_baseline=5.0
            ),
        ]
        
        for definition in definitions:
            self.definitions[definition.name] = definition
    
    def record(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """记录指标值"""
        with self.lock:
            metric_value = MetricValue(
                name=name,
                value=value,
                tags=tags or {}
            )
            self.metrics[name].append(metric_value)
    
    def get_values(
        self,
        name: str,
        since: Optional[float] = None,
        limit: int = 100
    ) -> List[MetricValue]:
        """获取指标值"""
        with self.lock:
            values = list(self.metrics.get(name, []))
        
        if since:
            values = [v for v in values if v.timestamp >= since]
        
        return values[-limit:]
    
    def get_latest(self, name: str) -> Optional[MetricValue]:
        """获取最新指标值"""
        with self.lock:
            values = self.metrics.get(name)
            if values:
                return values[-1]
        return None
    
    def get_statistics(self, name: str, since: Optional[float] = None) -> Dict[str, float]:
        """获取指标统计"""
        values = self.get_values(name, since, limit=1000)
        
        if not values:
            return {}
        
        numeric_values = [v.value for v in values]
        
        return {
            'count': len(numeric_values),
            'latest': numeric_values[-1] if numeric_values else 0,
            'min': min(numeric_values) if numeric_values else 0,
            'max': max(numeric_values) if numeric_values else 0,
            'avg': sum(numeric_values) / len(numeric_values) if numeric_values else 0,
            'sum': sum(numeric_values),
            'first_value': numeric_values[0] if numeric_values else 0,
            'last_timestamp': values[-1].timestamp if values else 0
        }
    
    def _cleanup_loop(self) -> None:
        """清理过期数据"""
        while self._running:
            try:
                time.sleep(60)  # 每分钟检查一次
                cutoff = time.time() - (self.retention_hours * 3600)
                
                with self.lock:
                    for name in self.metrics:
                        values = self.metrics[name]
                        # 移除过期的值
                        while values and values[0].timestamp < cutoff:
                            values.popleft()
                            
            except Exception as e:
                logger.error(f"清理线程错误: {e}")
    
    def stop(self) -> None:
        """停止采集器"""
        self._running = False
        logger.info("指标采集器已停止")


class MetricsAnalyzer:
    """指标分析器"""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        self.alert_callbacks: List[Callable] = []
    
    def analyze(self, metric_name: str, time_window_hours: int = 1) -> MetricAnalysis:
        """分析单个指标"""
        definition = self.collector.definitions.get(metric_name)
        if not definition:
            return MetricAnalysis(
                metric_name=metric_name,
                current_value=0,
                baseline_value=0,
                target_value=0,
                trend="unknown",
                change_percent=0,
                status="unknown",
                recommendations=["指标定义不存在"]
            )
        
        # 获取时间窗口内的数据
        since = time.time() - (time_window_hours * 3600)
        stats = self.collector.get_statistics(metric_name, since)
        
        current_value = stats.get('avg', 0)
        baseline_value = definition.v3_baseline
        target_value = definition.v3_target
        
        # 计算变化百分比
        if baseline_value > 0:
            change_percent = ((current_value - baseline_value) / baseline_value) * 100
        else:
            change_percent = 0
        
        # 判断趋势
        trend = self._determine_trend(metric_name, since)
        
        # 判断状态
        status = self._determine_status(definition, current_value, baseline_value, target_value)
        
        # 生成建议
        recommendations = self._generate_recommendations(
            definition, current_value, baseline_value, target_value, status
        )
        
        return MetricAnalysis(
            metric_name=metric_name,
            current_value=current_value,
            baseline_value=baseline_value,
            target_value=target_value,
            trend=trend,
            change_percent=change_percent,
            status=status,
            recommendations=recommendations
        )
    
    def _determine_trend(self, metric_name: str, since: float) -> str:
        """判断趋势"""
        # 比较最近10%和较早10%的平均值
        values = self.collector.get_values(metric_name, since, limit=100)
        
        if len(values) < 20:
            return "stable"
        
        mid = len(values) // 2
        recent_avg = sum(v.value for v in values[mid:]) / (len(values) - mid)
        earlier_avg = sum(v.value for v in values[:mid]) / mid
        
        if earlier_avg == 0:
            return "stable"
        
        change = (recent_avg - earlier_avg) / earlier_avg
        
        # 对于某些指标，越小越好
        inverted_metrics = ['response_time_p95', 'error_rate', 'request_latency', 
                           'knowledge_retrieval_latency', 'capability_creation_time']
        
        if metric_name in inverted_metrics:
            if change < -0.1:
                return "improving"
            elif change > 0.1:
                return "declining"
        else:
            if change > 0.1:
                return "improving"
            elif change < -0.1:
                return "declining"
        
        return "stable"
    
    def _determine_status(
        self,
        definition: MetricDefinition,
        current: float,
        baseline: float,
        target: float
    ) -> str:
        """判断状态"""
        # 对于某些指标，越小越好
        inverted_metrics = ['response_time_p95', 'error_rate', 'request_latency', 
                           'knowledge_retrieval_latency', 'capability_creation_time',
                           'sandbox_start_time', 'maintenance_cost_reduction']
        
        if definition.name in inverted_metrics:
            # 越小越好的指标
            if target > 0:
                progress = (baseline - current) / (baseline - target)
            else:
                progress = 1.0 if current <= target else 0.0
        else:
            # 越大越好的指标
            if baseline > 0:
                progress = (current - baseline) / (target - baseline)
            else:
                progress = 1.0 if current >= target else 0.0
        
        if progress >= 0.8:
            return "good"
        elif progress >= 0.5:
            return "warning"
        else:
            return "critical"
    
    def _generate_recommendations(
        self,
        definition: MetricDefinition,
        current: float,
        baseline: float,
        target: float,
        status: str
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if status == "critical":
            recommendations.append(f"⚠️ {definition.name} 处于临界状态，需要立即关注")
            
            if definition.v3_dimension == "能力生命周期管理":
                recommendations.append("建议检查能力创建流程，识别瓶颈")
            elif definition.v3_dimension == "能力组合与编排":
                recommendations.append("建议优化能力组合算法，提升推荐准确度")
            elif definition.v3_dimension == "安全与治理":
                recommendations.append("建议检查安全策略，加强治理自动化")
            elif definition.v3_dimension == "系统自进化":
                recommendations.append("建议检查进化引擎配置，优化自学习策略")
                
        elif status == "warning":
            recommendations.append(f"📊 {definition.name} 需要优化")
            
        else:
            recommendations.append(f"✅ {definition.name} 表现良好")
        
        return recommendations
    
    def generate_report(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """生成综合报告"""
        analyses = {}
        
        for metric_name in self.collector.definitions:
            analyses[metric_name] = self.analyze(metric_name, time_window_hours)
        
        # 汇总统计
        category_scores = defaultdict(lambda: {'good': 0, 'warning': 0, 'critical': 0})
        
        for metric_name, analysis in analyses.items():
            definition = self.collector.definitions.get(metric_name)
            if definition:
                category_scores[definition.category.value][analysis.status] += 1
        
        return {
            'timestamp': datetime.now().isoformat(),
            'time_window_hours': time_window_hours,
            'analyses': {
                name: {
                    'current_value': a.current_value,
                    'baseline_value': a.baseline_value,
                    'target_value': a.target_value,
                    'trend': a.trend,
                    'change_percent': a.change_percent,
                    'status': a.status,
                    'recommendations': a.recommendations
                }
                for name, a in analyses.items()
            },
            'category_summary': dict(category_scores),
            'overall_health': self._calculate_overall_health(analyses)
        }
    
    def _calculate_overall_health(self, analyses: Dict[str, MetricAnalysis]) -> str:
        """计算整体健康度"""
        if not analyses:
            return "unknown"
        
        status_counts = {'good': 0, 'warning': 0, 'critical': 0}
        
        for analysis in analyses.values():
            if analysis.status in status_counts:
                status_counts[analysis.status] += 1
        
        total = sum(status_counts.values())
        
        if status_counts['critical'] > 0:
            return "critical"
        elif status_counts['warning'] > status_counts['good']:
            return "warning"
        else:
            return "good"
    
    def register_alert_callback(self, callback: Callable) -> None:
        """注册告警回调"""
        self.alert_callbacks.append(callback)
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """检查告警"""
        alerts = []
        
        for metric_name in self.collector.definitions:
            analysis = self.analyze(metric_name)
            
            if analysis.status == "critical":
                alert = {
                    'level': 'critical',
                    'metric': metric_name,
                    'message': f"{metric_name} 处于临界状态",
                    'current_value': analysis.current_value,
                    'target_value': analysis.target_value,
                    'recommendations': analysis.recommendations
                }
                alerts.append(alert)
                
                # 触发回调
                for callback in self.alert_callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        logger.error(f"告警回调错误: {e}")
        
        return alerts


class MetricsService:
    """指标服务 - 统一入口"""
    
    def __init__(self, retention_hours: int = 24):
        self.collector = MetricsCollector(retention_hours)
        self.analyzer = MetricsAnalyzer(self.collector)
        
        logger.info("指标服务初始化完成")
    
    def record(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """记录指标"""
        self.collector.record(name, value, tags)
    
    def get(self, name: str, since: Optional[float] = None, limit: int = 100) -> List[MetricValue]:
        """获取指标"""
        return self.collector.get_values(name, since, limit)
    
    def get_latest(self, name: str) -> Optional[MetricValue]:
        """获取最新指标"""
        return self.collector.get_latest(name)
    
    def get_stats(self, name: str, since: Optional[float] = None) -> Dict[str, float]:
        """获取统计"""
        return self.collector.get_statistics(name, since)
    
    def analyze(self, metric_name: str, time_window_hours: int = 1) -> MetricAnalysis:
        """分析指标"""
        return self.analyzer.analyze(metric_name, time_window_hours)
    
    def generate_report(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """生成报告"""
        return self.analyzer.generate_report(time_window_hours)
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """检查告警"""
        return self.analyzer.check_alerts()
    
    def get_v3_metrics_summary(self) -> Dict[str, Any]:
        """获取V3指标摘要"""
        dimensions = defaultdict(list)
        
        for name, definition in self.collector.definitions.items():
            if definition.v3_dimension:
                dimensions[definition.v3_dimension].append(name)
        
        summary = {}
        for dimension, metrics in dimensions.items():
            analyses = [self.analyzer.analyze(m) for m in metrics]
            
            good_count = sum(1 for a in analyses if a.status == 'good')
            total = len(analyses)
            
            summary[dimension] = {
                'total_metrics': total,
                'good_metrics': good_count,
                'health_percent': (good_count / total * 100) if total > 0 else 0,
                'overall_status': 'good' if good_count > total/2 else 'warning'
            }
        
        return summary
    
    def stop(self) -> None:
        """停止服务"""
        self.collector.stop()


# 全局实例
_metrics_service: Optional[MetricsService] = None


def get_metrics_service(retention_hours: int = 24) -> MetricsService:
    """获取指标服务实例"""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MetricsService(retention_hours)
    return _metrics_service


def create_metrics_service(retention_hours: int = 24) -> MetricsService:
    """创建指标服务实例"""
    return MetricsService(retention_hours)
