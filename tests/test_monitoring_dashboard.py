"""
监控仪表板服务测试
"""
import pytest
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.monitoring_dashboard_service import (
    MonitoringDashboardService,
    AlertLevel,
    MetricType,
    AlertConfig,
    MetricData,
    Alert,
    DashboardConfig,
    get_monitoring_dashboard_service
)


class TestMonitoringDashboardService:
    """测试监控仪表板服务"""

    def setup_method(self):
        """每个测试前设置"""
        self.service = MonitoringDashboardService()

    def test_service_initialization(self):
        """测试服务初始化"""
        assert self.service is not None
        assert len(self.service.alert_configs) > 0

    def test_record_metric(self):
        """测试记录指标"""
        metric = MetricData(
            metric_type=MetricType.RESPONSE_TIME,
            value=100.0,
            timestamp=time.time()
        )
        
        self.service.record_metric(metric)
        
        assert self.service.stats['total_metrics_received'] == 1

    def test_record_response_time(self):
        """测试记录响应时间"""
        self.service.record_response_time(100.0, 'model_a')
        
        metrics = self.service.get_current_metrics()
        assert len(metrics) > 0

    def test_record_success_rate(self):
        """测试记录成功率"""
        self.service.record_success_rate(0.95, 'model_a')
        
        history = self.service.get_metric_history(MetricType.SUCCESS_RATE)
        assert len(history) > 0

    def test_record_cost(self):
        """测试记录成本"""
        self.service.record_cost(10.0, 'model_a')
        
        overview = self.service._get_cost_overview()
        assert 'total_cost_24h' in overview

    def test_get_metric_history(self):
        """测试获取指标历史"""
        for i in range(5):
            self.service.record_response_time(100.0 + i * 10)
        
        history = self.service.get_metric_history(MetricType.RESPONSE_TIME)
        assert len(history) >= 5

    def test_get_metric_history_with_window(self):
        """测试带时间窗口的指标历史"""
        self.service.record_response_time(100.0)
        
        history = self.service.get_metric_history(
            MetricType.RESPONSE_TIME,
            time_window_seconds=1
        )
        
        assert isinstance(history, list)

    def test_get_current_metrics_filter(self):
        """测试过滤当前指标"""
        self.service.record_response_time(100.0, 'model_a')
        self.service.record_response_time(200.0, 'model_b')
        
        metrics_a = self.service.get_current_metrics(filter_model='model_a')
        assert all(m.model_id == 'model_a' for m in metrics_a)

    def test_dashboard_summary(self):
        """测试仪表板摘要"""
        self.service.record_response_time(100.0)
        self.service.record_success_rate(0.95)
        
        summary = self.service.get_dashboard_summary()
        
        assert 'timestamp' in summary
        assert 'stats' in summary
        assert 'system_status' in summary

    def test_system_status_healthy(self):
        """测试系统状态正常"""
        self.service.record_response_time(100.0)
        self.service.record_success_rate(0.99)
        
        summary = self.service.get_dashboard_summary()
        assert summary['system_status'] in ['healthy', 'warning', 'critical']


class TestAlertManagement:
    """测试告警管理"""

    def setup_method(self):
        """每个测试前设置"""
        self.service = MonitoringDashboardService()

    def test_add_alert_config(self):
        """测试添加告警配置"""
        config = AlertConfig(
            metric_type=MetricType.RESPONSE_TIME,
            threshold=5000.0,
            alert_level=AlertLevel.WARNING
        )
        
        key = self.service.add_alert_config(config)
        assert key is not None

    def test_get_active_alerts(self):
        """测试获取活动告警"""
        alerts = self.service.get_active_alerts()
        assert isinstance(alerts, list)

    def test_acknowledge_alert(self):
        """测试确认告警"""
        metric = MetricData(
            metric_type=MetricType.RESPONSE_TIME,
            value=6000.0,
            timestamp=time.time(),
            model_id='test_model'
        )
        
        self.service.record_metric(metric)
        
        alerts = self.service.get_active_alerts()
        if alerts:
            alert = alerts[0]
            result = self.service.acknowledge_alert(alert.id)
            assert result is True

    def test_alert_history(self):
        """测试告警历史"""
        history = self.service.get_alert_history(limit=10)
        assert isinstance(history, list)


class TestAlertConfig:
    """测试告警配置"""

    def test_default_configs(self):
        """测试默认配置"""
        config = DashboardConfig()
        
        assert len(config.default_alert_configs) > 0
        
        response_time_config = next(
            (c for c in config.default_alert_configs 
             if c.metric_type == MetricType.RESPONSE_TIME),
            None
        )
        assert response_time_config is not None
        assert response_time_config.threshold == 5000.0

    def test_alert_config_creation(self):
        """测试告警配置创建"""
        config = AlertConfig(
            metric_type=MetricType.SUCCESS_RATE,
            threshold=0.9,
            alert_level=AlertLevel.CRITICAL,
            duration_seconds=300
        )
        
        assert config.enabled is True
        assert config.cooldown_seconds == 300


class TestMetricData:
    """测试指标数据"""

    def test_metric_data_creation(self):
        """测试指标数据创建"""
        metric = MetricData(
            metric_type=MetricType.TOKEN_USAGE,
            value=1000.0,
            timestamp=time.time(),
            model_id='model_a',
            metadata={'test': 'value'}
        )
        
        assert metric.value == 1000.0
        assert metric.model_id == 'model_a'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
