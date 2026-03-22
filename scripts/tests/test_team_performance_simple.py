#!/usr/bin/env python3
"""
简单测试团队绩效评估器功能
验证新创建的团队绩效评估器是否正常工作
"""

import sys
import os
import asyncio
import logging
import time
from unittest.mock import Mock, MagicMock
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(level=logging.WARNING)  # 减少日志输出
logger = logging.getLogger(__name__)

async def test_basic_functionality():
    """测试基本功能"""
    logger.info("测试团队绩效评估器基本功能...")
    
    try:
        # 导入评估器
        from src.agents.team_performance_evaluator import (
            TeamPerformanceEvaluator,
            TeamPerformanceMetrics,
            PerformanceBottleneck,
            OptimizationRecommendation
        )
        
        # 创建模拟的Agent性能跟踪器
        mock_tracker = MagicMock()
        mock_tracker.get_performance_stats.return_value = MagicMock(
            __dict__={
                "total_tasks": 100,
                "successful_tasks": 85,
                "failed_tasks": 15,
                "avg_response_time": 1.2,
                "avg_processing_time": 3.5,
                "success_rate": 0.85
            }
        )
        mock_tracker.get_health_indicators.return_value = {
            "health_score": 78.5,
            "health_status": "good"
        }
        mock_tracker._last_activity = time.time() - 60  # 60秒前活跃
        mock_tracker._snapshots = [1, 2, 3]  # 模拟快照列表
        
        # 创建模拟的多Agent协调器
        mock_coordinator = Mock()
        mock_coordinator.get_collaboration_stats.return_value = {
            "total_collaborations": 50,
            "successful_collaborations": 45,
            "failed_collaborations": 5,
            "avg_collaboration_time": 10.5,
            "active_collaborations": 3,
            "pending_collaborations": 2
        }
        
        # 创建模拟的增强协作协调器
        mock_enhanced = Mock()
        mock_enhanced.get_performance_report.return_value = {
            "total_collaborations": 50,
            "average_efficiency": 0.78,
            "recent_efficiency_history": [0.75, 0.80, 0.78, 0.82, 0.76],
            "active_consensus_rounds": 2,
            "message_history_size": 150
        }
        
        # 创建团队绩效评估器
        evaluator = TeamPerformanceEvaluator(team_id="test_team_001")
        
        # 注入模拟的依赖
        evaluator.agent_trackers = {"agent_001": mock_tracker, "agent_002": mock_tracker}
        evaluator.coordinator = mock_coordinator
        evaluator.enhanced_coordinator = mock_enhanced
        
        # 测试性能评估
        logger.info("正在评估团队绩效...")
        metrics = await evaluator.evaluate_team_performance()
        
        # 验证返回的指标
        assert isinstance(metrics, TeamPerformanceMetrics)
        assert metrics.team_id == "test_team_001"
        assert metrics.total_agents == 2
        assert metrics.active_agents == 2  # 两个模拟Agent都是活跃的
        
        # 验证基础指标
        logger.info(f"团队绩效指标:")
        logger.info(f"  - 团队ID: {metrics.team_id}")
        logger.info(f"  - 总Agent数: {metrics.total_agents}")
        logger.info(f"  - 活跃Agent数: {metrics.active_agents}")
        logger.info(f"  - 总协作次数: {metrics.total_collaborations}")
        logger.info(f"  - 成功协作率: {metrics.collaboration_success_rate:.2%}")
        logger.info(f"  - 平均协作时间: {metrics.avg_collaboration_time:.2f}秒")
        logger.info(f"  - 任务完成率: {metrics.avg_task_completion_rate:.2%}")
        
        # 验证效率指标
        logger.info(f"  - 通信效率: {metrics.communication_efficiency:.2%}")
        logger.info(f"  - 协调效率: {metrics.coordination_efficiency:.2%}")
        logger.info(f"  - 资源利用率: {metrics.resource_utilization:.2%}")
        logger.info(f"  - 负载均衡分数: {metrics.load_balance_score:.2%}")
        
        # 验证质量指标
        logger.info(f"  - 结果质量: {metrics.result_quality:.2%}")
        logger.info(f"  - 冲突解决率: {metrics.conflict_resolution_rate:.2%}")
        logger.info(f"  - 共识达成率: {metrics.consensus_achievement_rate:.2%}")
        
        # 验证综合评分
        logger.info(f"  - 综合评分: {metrics.overall_score:.2f}/100")
        logger.info(f"  - 健康状态: {metrics.health_status}")
        
        # 测试报告生成
        logger.info("正在生成性能报告...")
        report = evaluator.generate_performance_report(format="dict")
        assert isinstance(report, dict)
        assert "team_id" in report
        assert "overall_score" in report
        
        logger.info("✓ 团队绩效评估器基本功能测试通过！")
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        return False

async def test_data_classes():
    """测试数据类"""
    logger.info("测试数据类...")
    
    try:
        from src.agents.team_performance_evaluator import (
            TeamPerformanceMetrics,
            PerformanceBottleneck,
            OptimizationRecommendation
        )
        
        # 测试TeamPerformanceMetrics
        metrics = TeamPerformanceMetrics(
            team_id="test_team",
            total_agents=3,
            active_agents=2,
            overall_score=85.5,
            health_status="excellent"
        )
        assert metrics.team_id == "test_team"
        assert metrics.total_agents == 3
        assert metrics.active_agents == 2
        assert metrics.overall_score == 85.5
        assert metrics.health_status == "excellent"
        
        # 测试PerformanceBottleneck
        bottleneck = PerformanceBottleneck(
            bottleneck_id="test_bottleneck",
            bottleneck_type="agent",
            severity="high",
            severity_score=0.7,
            description="测试瓶颈",
            affected_agents=["agent1", "agent2"],
            metrics_impacted=["response_time", "success_rate"],
            root_cause="资源不足",
            estimated_impact=0.6,
            recommendations=["增加资源", "优化配置"]
        )
        assert bottleneck.bottleneck_id == "test_bottleneck"
        assert bottleneck.bottleneck_type == "agent"
        assert bottleneck.severity == "high"
        assert bottleneck.severity_score == 0.7
        
        # 测试OptimizationRecommendation
        recommendation = OptimizationRecommendation(
            recommendation_id="test_recommendation",
            priority="high",
            category="agent_optimization",
            description="测试建议",
            expected_benefit=0.8,
            implementation_cost=0.3,
            roi_score=0.8/0.3,
            implementation_steps=["步骤1", "步骤2"],
            prerequisites=["前提条件"],
            validation_metrics=["metric1", "metric2"]
        )
        assert recommendation.recommendation_id == "test_recommendation"
        assert recommendation.priority == "high"
        assert recommendation.category == "agent_optimization"
        
        logger.info("✓ 数据类测试通过！")
        return True
        
    except Exception as e:
        logger.error(f"数据类测试失败: {e}", exc_info=True)
        return False

async def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("团队绩效评估器简单测试套件")
    logger.info("=" * 60)
    
    # 运行数据类测试
    data_class_passed = await test_data_classes()
    
    # 运行基本功能测试
    basic_passed = await test_basic_functionality()
    
    # 汇总结果
    logger.info("=" * 60)
    logger.info("测试结果汇总:")
    logger.info(f"  - 数据类测试: {'通过' if data_class_passed else '失败'}")
    logger.info(f"  - 基本功能测试: {'通过' if basic_passed else '失败'}")
    
    all_passed = data_class_passed and basic_passed
    
    if all_passed:
        logger.info("✓ 所有测试通过！团队绩效评估器功能正常。")
    else:
        logger.error("✗ 部分测试失败，请检查日志。")
    
    return all_passed

if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    
    # 根据测试结果退出
    sys.exit(0 if success else 1)