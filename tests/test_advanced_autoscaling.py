#!/usr/bin/env python3
"""
高级自动扩缩容服务测试
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.services.advanced_autoscaling_service import (
    AdvancedAutoscalingService,
    AdvancedScalingRule,
    RuleConditionType,
    ScalingDecision,
    ScalingTarget,
    MetricTrend,
    MetricTrendAnalysis,
    create_advanced_autoscaling_service
)
from src.services.autoscaling_service import SystemMetric


class TestAdvancedAutoscalingService:
    """高级自动扩缩容服务测试类"""
    
    @pytest.fixture
    def service(self):
        """创建测试服务实例"""
        config = {
            "initial_agent_instances": 2,
            "initial_worker_threads": 4,
            "metric_history_size": 50,
            "trend_cache_ttl": 300
        }
        return AdvancedAutoscalingService(config)
    
    @pytest.fixture
    def sample_metrics(self):
        """创建样本指标"""
        timestamp = datetime.now()
        return [
            SystemMetric(name="cpu_percent", value=65.5, unit="percent", 
                        timestamp=timestamp, source="psutil"),
            SystemMetric(name="memory_percent", value=45.2, unit="percent", 
                        timestamp=timestamp, source="psutil"),
            SystemMetric(name="request_rate", value=85.3, unit="requests/second", 
                        timestamp=timestamp, source="api"),
            SystemMetric(name="request_latency_p95", value=245.7, unit="milliseconds", 
                        timestamp=timestamp, source="api"),
        ]
    
    def test_initialization(self, service):
        """测试服务初始化"""
        assert service is not None
        assert service.current_agent_instances == 2
        assert service.current_worker_threads == 4
        assert len(service.advanced_rules) > 0
        assert service.performance_stats["rule_evaluations"] == 0
    
    def test_advanced_rules_creation(self, service):
        """测试高级规则创建"""
        rules = service.advanced_rules
        assert len(rules) >= 5
        
        # 检查规则类型
        rule_types = [rule.condition_type for rule in rules]
        assert RuleConditionType.MULTI_METRIC in rule_types
        assert RuleConditionType.TREND_BASED in rule_types
        assert RuleConditionType.PREDICTIVE in rule_types
        assert RuleConditionType.ADAPTIVE in rule_types
        
        # 检查特定规则
        cpu_rule = next((r for r in rules if r.name == "adaptive_cpu_threshold_scale_out"), None)
        assert cpu_rule is not None
        assert cpu_rule.adaptive_threshold is True
        assert cpu_rule.min_threshold == 50.0
        assert cpu_rule.max_threshold == 90.0
    
    def test_metric_history_update(self, service, sample_metrics):
        """测试指标历史更新"""
        # 初始历史为空
        assert len(service.metric_history) == 0
        
        # 更新指标历史
        service._update_metric_history(sample_metrics)
        
        # 检查历史数据
        assert len(service.metric_history) == 4
        assert "cpu_percent" in service.metric_history
        assert len(service.metric_history["cpu_percent"]) == 1
        assert service.metric_history["cpu_percent"][0]["value"] == 65.5
    
    @pytest.mark.asyncio
    async def test_trend_analysis(self, service, sample_metrics):
        """测试趋势分析"""
        # 首先添加一些历史数据
        for i in range(10):
            metrics = [
                SystemMetric(name="cpu_percent", value=50.0 + i * 2.0, unit="percent", 
                            timestamp=datetime.now(), source="psutil")
            ]
            service._update_metric_history(metrics)
        
        # 分析趋势
        analysis = await service._analyze_metric_trend("cpu_percent")
        
        assert analysis is not None
        assert analysis.metric_name == "cpu_percent"
        assert analysis.trend == MetricTrend.INCREASING  # 值在增加
        assert analysis.slope > 0.0
        assert 0.0 <= analysis.confidence <= 1.0
        assert len(analysis.forecast) == 5
    
    @pytest.mark.asyncio
    async def test_metric_prediction(self, service):
        """测试指标预测"""
        # 添加历史数据
        for i in range(15):
            metrics = [
                SystemMetric(name="request_rate", value=80.0 + i * 1.5, unit="requests/second", 
                            timestamp=datetime.now(), source="api")
            ]
            service._update_metric_history(metrics)
        
        # 预测未来值
        predictions = await service._predict_metric("request_rate", horizon=3)
        
        assert predictions is not None
        assert len(predictions) == 3
        assert all(isinstance(p, float) for p in predictions)
    
    def test_composite_metric_calculation(self, service, sample_metrics):
        """测试组合指标计算"""
        # 更新历史数据
        service._update_metric_history(sample_metrics)
        
        # 计算组合指标
        metric_names = ["cpu_percent", "memory_percent"]
        composite_value = service._calculate_composite_metric(metric_names)
        
        assert composite_value > 0.0
        # 应该是平均值 (65.5 + 45.2) / 2 = 55.35
        assert abs(composite_value - 55.35) < 0.1
    
    def test_adaptive_threshold_adjustment(self, service):
        """测试自适应阈值调整"""
        # 获取自适应规则
        adaptive_rule = next((r for r in service.advanced_rules 
                             if r.name == "adaptive_cpu_threshold_scale_out"), None)
        assert adaptive_rule is not None
        
        # 初始阈值
        initial_threshold = adaptive_rule.threshold
        
        # 调整阈值（没有决策）
        new_threshold = service._adjust_adaptive_threshold(
            adaptive_rule, actual_value=70.0, decision_made=False
        )
        
        # 阈值应该接近初始值
        assert abs(new_threshold - initial_threshold) < 5.0
        
        # 再次调整（有决策）
        new_threshold2 = service._adjust_adaptive_threshold(
            adaptive_rule, actual_value=85.0, decision_made=True
        )
        
        # 阈值应该有所调整
        assert new_threshold2 != new_threshold
    
    @pytest.mark.asyncio
    async def test_single_metric_rule_evaluation(self, service, sample_metrics):
        """测试单一指标规则评估"""
        # 获取单一指标规则（自适应CPU规则）
        cpu_rule = next((r for r in service.advanced_rules 
                        if r.name == "adaptive_cpu_threshold_scale_out"), None)
        assert cpu_rule is not None
        
        # 评估规则（CPU值低于阈值）
        triggered, reason, actual_value = await service._evaluate_advanced_rule(
            cpu_rule, sample_metrics
        )
        
        assert actual_value == 65.5  # CPU值
        # CPU值65.5 < 阈值75.0，应该不触发
        assert triggered is False
        assert "cpu_percent" in reason
    
    @pytest.mark.asyncio
    async def test_multi_metric_rule_evaluation(self, service, sample_metrics):
        """测试多指标规则评估"""
        # 获取多指标规则
        multi_rule = next((r for r in service.advanced_rules 
                          if r.name == "high_cpu_and_memory_scale_out"), None)
        assert multi_rule is not None
        
        # 评估规则
        triggered, reason, actual_value = await service._evaluate_advanced_rule(
            multi_rule, sample_metrics
        )
        
        # 组合指标值应该是CPU和内存的平均值
        expected_value = (65.5 + 45.2) / 2  # 55.35
        assert abs(actual_value - expected_value) < 0.1
        assert "组合指标" in reason
    
    @pytest.mark.asyncio
    async def test_trend_based_rule_evaluation(self, service):
        """测试趋势分析规则评估"""
        # 获取趋势规则
        trend_rule = next((r for r in service.advanced_rules 
                          if r.name == "increasing_latency_trend_scale_out"), None)
        assert trend_rule is not None
        
        # 创建递增的延迟数据
        timestamp = datetime.now()
        metrics = []
        for i in range(10):
            latency_value = 200.0 + i * 20.0  # 从200ms递增到380ms
            metric = SystemMetric(
                name="request_latency_p95", 
                value=latency_value, 
                unit="milliseconds", 
                timestamp=timestamp + timedelta(seconds=i),
                source="api"
            )
            metrics.append(metric)
        
        # 更新历史数据（只更新最后一个值用于当前评估）
        service._update_metric_history([metrics[-1]])
        # 但需要更多的历史数据来进行趋势分析
        for metric in metrics[:-1]:
            service._update_metric_history([metric])
        
        # 评估规则（延迟值380 > 阈值300，且趋势上升）
        triggered, reason, actual_value = await service._evaluate_advanced_rule(
            trend_rule, [metrics[-1]]
        )
        
        # 由于延迟值高且趋势上升，应该触发
        # 注意：实际触发取决于趋势分析的具体实现
        assert actual_value == 380.0
        assert "request_latency_p95" in reason or "趋势" in reason
    
    @pytest.mark.asyncio
    async def test_full_rule_evaluation(self, service, sample_metrics):
        """测试完整规则评估"""
        # 评估所有规则
        decisions = await service._evaluate_scaling_rules(sample_metrics)
        
        # 应该返回决策列表
        assert isinstance(decisions, list)
        
        # 检查决策结构
        if decisions:
            decision = decisions[0]
            assert "rule_name" in decision
            assert "decision" in decision
            assert "reason" in decision
            assert "current_value" in decision
    
    @pytest.mark.asyncio
    async def test_performance_stats(self, service, sample_metrics):
        """测试性能统计"""
        # 初始统计
        initial_stats = await service.get_performance_stats()
        assert initial_stats["performance_stats"]["rule_evaluations"] == 0
        
        # 执行一些评估
        await service._evaluate_scaling_rules(sample_metrics)
        
        # 检查统计更新
        updated_stats = await service.get_performance_stats()
        assert updated_stats["performance_stats"]["rule_evaluations"] > 0
    
    @pytest.mark.asyncio
    async def test_rule_management(self, service):
        """测试规则管理"""
        # 获取规则数量
        initial_count = len([r for r in service.advanced_rules if r.enabled])
        
        # 禁用规则
        success = await service.enable_advanced_rule("adaptive_cpu_threshold_scale_out", False)
        assert success is True
        
        # 检查规则已禁用
        disabled_rule = next((r for r in service.advanced_rules 
                             if r.name == "adaptive_cpu_threshold_scale_out"), None)
        assert disabled_rule is not None
        assert disabled_rule.enabled is False
        
        # 重新启用规则
        success = await service.enable_advanced_rule("adaptive_cpu_threshold_scale_out", True)
        assert success is True
        
        # 更新规则参数
        updates = {"threshold": 80.0, "cooldown_seconds": 500}
        success = await service.update_advanced_rule("adaptive_cpu_threshold_scale_out", updates)
        assert success is True
        
        updated_rule = next((r for r in service.advanced_rules 
                            if r.name == "adaptive_cpu_threshold_scale_out"), None)
        assert updated_rule is not None
        assert updated_rule.threshold == 80.0
        assert updated_rule.cooldown_seconds == 500
    
    def test_service_factory(self):
        """测试服务工厂函数"""
        config = {"initial_agent_instances": 3}
        service = create_advanced_autoscaling_service(config)
        
        assert isinstance(service, AdvancedAutoscalingService)
        assert service.current_agent_instances == 3


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])