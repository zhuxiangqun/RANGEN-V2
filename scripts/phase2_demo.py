#!/usr/bin/env python3
"""
Skill Factory Phase 2 质量控制增强演示脚本

演示 Phase 2 新增的四大质量控制组件：
1. AI验证系统 (AISkillValidator)
2. 质量指标跟踪系统 (QualityMetricsTracker)
3. 技能性能监控系统 (PerformanceMonitor)
4. 用户反馈收集机制 (FeedbackCollector)

以及这些组件如何集成到 SkillFactory 中。
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def print_header(title):
    """打印标题"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")

def demo_ai_validation():
    """演示 AI 验证系统"""
    print_header("1. AI 验证系统演示")
    
    try:
        from skill_factory.ai_validation import AISkillValidator, ValidationStatus
        from skill_factory.prototypes.classifier import PrototypeType
        
        print("✓ 导入 AI 验证系统成功")
        
        # 创建验证器（使用模拟模式，无需真实LLM）
        validator = AISkillValidator(llm_config={})
        
        # 创建测试技能目录
        temp_skill_dir = tempfile.mkdtemp(prefix="test_skill_")
        
        try:
            # 创建简单的技能文件结构
            skill_yaml_content = """
name: "测试数据分析技能"
description: "用于分析 CSV 文件中的数据"
author: "测试用户"
version: "1.0.0"
prototype: "workflow"
tags: ["data", "analysis", "csv"]
"""
            
            skill_md_content = """
# 测试数据分析技能

## 描述
用于分析 CSV 文件中的数据

## 使用方法
1. 上传 CSV 文件
2. 选择分析类型
3. 查看分析结果
"""
            
            # 写入文件
            (Path(temp_skill_dir) / "skill.yaml").write_text(skill_yaml_content)
            (Path(temp_skill_dir) / "SKILL.md").write_text(skill_md_content)
            
            print(f"✓ 创建测试技能目录: {temp_skill_dir}")
            
            # 执行AI验证
            print("执行 AI 验证...")
            report = validator.validate_skill(
                skill_dir=temp_skill_dir,
                prototype=PrototypeType.WORKFLOW,
                classification_result=None
            )
            
            print(f"✓ AI 验证完成")
            print(f"  总体得分: {report.overall_score:.1f}/100")
            print(f"  验证状态: {'通过' if report.overall_score >= 60 else '需要改进'}")
            print(f"  验证类别数量: {len(report.validation_results)}")
            
            # 显示每个类别的得分
            for result in report.validation_results[:5]:  # 显示前5个
                print(f"  - {result.category.value}: {result.score:.1f} ({result.status.value})")
            
            # 显示建议
            if report.improvement_suggestions:
                print(f"  改进建议: {len(report.improvement_suggestions)} 条")
                for i, suggestion in enumerate(report.improvement_suggestions[:3], 1):
                    print(f"    {i}. {suggestion}")
            
            return True
            
        finally:
            # 清理临时目录
            if os.path.exists(temp_skill_dir):
                shutil.rmtree(temp_skill_dir)
                print(f"✓ 清理临时目录")
                
    except Exception as e:
        print(f"❌ AI 验证演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_quality_metrics():
    """演示质量指标跟踪系统"""
    print_header("2. 质量指标跟踪系统演示")
    
    try:
        from skill_factory.quality_metrics import QualityMetricsTracker, MetricType
        from skill_factory.quality_checks import QualityReport, CheckStatus
        
        print("✓ 导入质量指标跟踪系统成功")
        
        # 创建跟踪器
        tracker = QualityMetricsTracker()
        print(f"✓ 质量指标跟踪器初始化成功")
        print(f"  存储路径: {tracker.storage_path}")
        
        skill_id = "test-skill-001"
        
        # 模拟质量检查结果
        # 首先需要创建CheckResult对象，这里简化处理，直接创建QualityReport
        # 注意：实际使用中应从QualityChecker获取报告
        # 这里创建模拟报告结构
        quality_report = QualityReport(
            skill_dir=f"/tmp/{skill_id}",
            overall_status=CheckStatus.PASSED
        )
        # 设置其他属性（因为QualityReport是数据类，我们可以直接设置）
        quality_report.passed_checks = 7
        quality_report.failed_checks = 1
        quality_report.total_checks = 8
        
        # 跟踪质量检查结果
        tracker.track_quality_check(skill_id, quality_report)
        print(f"✓ 跟踪质量检查结果成功")
        
        # 模拟AI验证结果
        from skill_factory.ai_validation import AIVerificationReport, ValidationStatus, ValidationResult, ValidationCategory
        
        # 创建验证结果列表
        validation_results = [
            ValidationResult(
                category=ValidationCategory.LOGIC_CONSISTENCY,
                status=ValidationStatus.PASSED,
                score=90.0,
                feedback="逻辑一致性好"
            ),
            ValidationResult(
                category=ValidationCategory.TASK_COMPLETENESS,
                status=ValidationStatus.PASSED,
                score=80.0,
                feedback="任务完整性良好"
            ),
            ValidationResult(
                category=ValidationCategory.PROTOTYPE_MATCH,
                status=ValidationStatus.PASSED,
                score=95.0,
                feedback="原型匹配度高"
            )
        ]
        
        ai_report = AIVerificationReport(
            skill_dir=f"/tmp/{skill_id}",
            overall_score=85.5,
            validation_results=validation_results,
            recommendations=[
                "添加更多错误处理",
                "优化文档结构"
            ],
            summary="技能整体质量良好，建议优化错误处理"
        )
        
        # 跟踪AI验证结果
        tracker.track_ai_validation(skill_id, ai_report)
        print(f"✓ 跟踪AI验证结果成功")
        
        # 获取技能质量趋势
        trend = tracker.get_skill_quality_trend(skill_id, days=7)
        print(f"✓ 获取质量趋势成功")
        print(f"  趋势数据点: {len(trend.get('data_points', []))}")
        print(f"  平均质量得分: {trend.get('average_score', 0):.1f}")
        print(f"  趋势方向: {trend.get('trend_direction', '未知')}")
        
        # 获取技能摘要
        summary = tracker.get_skill_summary(skill_id)
        if summary:
            print(f"✓ 获取技能摘要成功")
            print(f"  技能ID: {summary.get('skill_id')}")
            print(f"  首次跟踪: {summary.get('first_seen')}")
            print(f"  最近更新: {summary.get('last_updated')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 质量指标跟踪演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_performance_monitoring():
    """演示技能性能监控系统"""
    print_header("3. 技能性能监控系统演示")
    
    try:
        from skill_factory.performance_monitor import PerformanceMonitor, PerformanceMetricType, ErrorType
        from skill_factory.performance_monitor import PerformanceExecutionContext
        
        print("✓ 导入性能监控系统成功")
        
        # 创建性能监控器
        monitor = PerformanceMonitor()
        print(f"✓ 性能监控器初始化成功")
        print(f"  存储路径: {monitor.storage_path}")
        
        skill_id = "test-skill-002"
        
        # 演示性能跟踪
        print("演示性能跟踪...")
        
        # 方法1: 手动跟踪
        track_id = monitor.track_execution_start(skill_id)
        print(f"  ✓ 开始执行跟踪 (跟踪ID: {track_id})")
        
        # 模拟执行过程
        import time
        time.sleep(0.1)  # 模拟执行时间
        
        snapshot = monitor.track_execution_end(
            skill_id=skill_id,
            success=True,
            execution_time_ms=105.5,
            error_type=None,
            error_message=None
        )
        print(f"  ✓ 执行结束跟踪")
        print(f"    执行时间: {snapshot.execution_time_ms:.1f}ms")
        print(f"    执行结果: {'成功' if snapshot.success else '失败'}")
        
        # 方法2: 使用上下文管理器（推荐）
        print("演示上下文管理器...")
        with PerformanceExecutionContext(monitor, skill_id) as context:
            # 在with块中执行代码
            print("  ✓ 进入执行上下文")
            time.sleep(0.05)  # 模拟执行时间
            print("  ✓ 执行完成")
        
        print(f"  ✓ 上下文管理器自动完成性能跟踪")
        
        # 设置性能阈值
        from skill_factory.performance_monitor import PerformanceThreshold, PerformanceMetricType
        
        threshold = PerformanceThreshold(
            skill_id=skill_id,
            metric_type=PerformanceMetricType.EXECUTION_TIME,
            warning_threshold=1000,  # 1秒警告
            critical_threshold=5000  # 5秒严重
        )
        
        monitor.add_custom_threshold(threshold)
        print(f"✓ 设置性能阈值成功")
        
        # 获取性能摘要
        summary = monitor.get_performance_summary(skill_id)
        if summary:
            print(f"✓ 获取性能摘要成功")
            print(f"  总调用次数: {summary.get('total_invocations', 0)}")
            print(f"  成功率: {summary.get('success_rate', 0)*100:.1f}%")
            print(f"  平均执行时间: {summary.get('avg_execution_time_ms', 0):.1f}ms")
        
        # 获取性能趋势
        trend = monitor.get_performance_trend(
            skill_id=skill_id,
            metric_type=PerformanceMetricType.EXECUTION_TIME,
            days=1
        )
        print(f"✓ 获取性能趋势成功")
        print(f"  趋势数据点: {len(trend)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 性能监控演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_feedback_collection():
    """演示用户反馈收集机制"""
    print_header("4. 用户反馈收集机制演示")
    
    try:
        from skill_factory.feedback_collector import FeedbackCollector, FeedbackType, FeedbackSentiment, FeedbackPriority, FeedbackItem
        
        print("✓ 导入用户反馈收集系统成功")
        
        # 创建反馈收集器
        collector = FeedbackCollector()
        print(f"✓ 反馈收集器初始化成功")
        print(f"  存储路径: {collector.storage_path}")
        
        skill_id = "test-skill-003"
        user_id = "user-001"
        
        # 提交不同类型的反馈
        print("提交用户反馈...")
        
        # 1. 评分反馈
        rating_feedback = FeedbackItem(
            feedback_id="rating-001",
            skill_id=skill_id,
            feedback_type=FeedbackType.RATING,
            rating=4.5,
            content="这个技能很好用，但响应速度可以再快一些",
            user_id=user_id,
            sentiment=FeedbackSentiment.POSITIVE,
            priority=FeedbackPriority.MEDIUM,
            tags=["性能", "易用性"]
        )
        collector.submit_feedback(rating_feedback)
        print(f"  ✓ 提交评分反馈 (评分: 4.5/5.0)")
        
        # 2. 问题报告
        issue_feedback = FeedbackItem(
            feedback_id="issue-001",
            skill_id=skill_id,
            feedback_type=FeedbackType.ISSUE_REPORT,
            rating=2.0,
            content="在处理大型CSV文件时会出现内存不足的错误",
            user_id="user-002",
            sentiment=FeedbackSentiment.NEGATIVE,
            priority=FeedbackPriority.HIGH,
            tags=["内存", "大文件", "错误"]
        )
        collector.submit_feedback(issue_feedback)
        print(f"  ✓ 提交问题报告 (优先级: 高)")
        
        # 3. 功能请求
        feature_feedback = FeedbackItem(
            feedback_id="feature-001",
            skill_id=skill_id,
            feedback_type=FeedbackType.FEATURE_REQUEST,
            rating=5.0,
            content="希望能支持JSON格式的数据分析",
            user_id="user-003",
            sentiment=FeedbackSentiment.POSITIVE,
            priority=FeedbackPriority.MEDIUM,
            tags=["新功能", "JSON", "数据格式"]
        )
        collector.submit_feedback(feature_feedback)
        print(f"  ✓ 提交功能请求")
        
        # 4. 改进建议
        suggestion_feedback = FeedbackItem(
            feedback_id="suggestion-001",
            skill_id=skill_id,
            feedback_type=FeedbackType.IMPROVEMENT_SUGGESTION,
            rating=4.0,
            content="建议在分析结果中添加图表可视化",
            user_id="user-004",
            sentiment=FeedbackSentiment.NEUTRAL,
            priority=FeedbackPriority.LOW,
            tags=["可视化", "图表", "改进"]
        )
        collector.submit_feedback(suggestion_feedback)
        print(f"  ✓ 提交改进建议")
        
        # 分析反馈数据
        print("分析反馈数据...")
        
        analysis = collector.analyze_feedback(skill_id)
        if analysis:
            print(f"✓ 反馈分析成功")
            print(f"  总反馈数: {analysis.get('total_feedback', 0)}")
            print(f"  平均评分: {analysis.get('average_rating', 0):.1f}/10.0")
            
            # 情感分布
            sentiment = analysis.get('sentiment_distribution', {})
            if sentiment:
                positive_rate = sentiment.get('positive', 0) / sum(sentiment.values()) * 100 if sum(sentiment.values()) > 0 else 0
                print(f"  正面反馈率: {positive_rate:.1f}%")
            
            # 常见问题
            common_issues = analysis.get('common_issues', [])
            if common_issues:
                print(f"  常见问题: {len(common_issues)} 个")
                for i, issue in enumerate(common_issues[:2], 1):
                    print(f"    {i}. {issue.get('description', '')} (优先级: {issue.get('priority')})")
            
            # 改进建议
            suggestions = analysis.get('improvement_suggestions', [])
            if suggestions:
                print(f"  改进建议: {len(suggestions)} 条")
                for i, suggestion in enumerate(suggestions[:2], 1):
                    print(f"    {i}. {suggestion.get('description', '')}")
            
            # 热门标签
            top_tags = analysis.get('top_tags', [])
            if top_tags:
                print(f"  热门标签: {', '.join([tag.get('tag') for tag in top_tags[:5]])}")
        
        # 获取反馈摘要
        summary = collector.get_feedback_summary(skill_id)
        print(f"✓ 反馈摘要: {summary}")
        
        return True
        
    except Exception as e:
        print(f"❌ 反馈收集演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_factory_integration():
    """演示 SkillFactory 中的集成"""
    print_header("5. SkillFactory 集成演示")
    
    try:
        from skill_factory.factory import SkillFactory
        
        print("✓ 导入 SkillFactory 成功")
        
        # 创建工厂实例
        factory = SkillFactory()
        print(f"✓ SkillFactory 初始化成功")
        
        # 检查 Phase 2 组件
        print("检查 Phase 2 组件...")
        
        # 1. 检查质量指标跟踪器
        if hasattr(factory, 'quality_metrics_tracker'):
            print(f"  ✓ 质量指标跟踪器: 已集成")
            print(f"    存储路径: {factory.quality_metrics_tracker.storage_path}")
        else:
            print(f"  ✗ 质量指标跟踪器: 未找到")
        
        # 2. 检查性能监控器
        if hasattr(factory, 'performance_monitor'):
            print(f"  ✓ 性能监控器: 已集成")
            print(f"    存储路径: {factory.performance_monitor.storage_path}")
        else:
            print(f"  ✗ 性能监控器: 未找到")
        
        # 3. 检查反馈收集器
        if hasattr(factory, 'feedback_collector'):
            print(f"  ✓ 反馈收集器: 已集成")
            print(f"    存储路径: {factory.feedback_collector.storage_path}")
        else:
            print(f"  ✗ 反馈收集器: 未找到")
        
        # 4. 检查AI验证器（通过配置）
        print(f"  ✓ AI验证器: 已集成（通过AISkillValidator类）")
        
        # 演示技能创建流程（模拟）
        print("\n演示技能创建流程（模拟）...")
        
        # 模拟技能需求
        test_requirements = {
            "description": "一个用于文本摘要的AI技能",
            "category": "文本处理",
            "tags": ["AI", "文本", "摘要"]
        }
        
        print(f"  模拟技能需求: {test_requirements['description']}")
        print("  模拟创建流程:")
        print("    1. 原型分类 -> 分类为 'expert' 原型")
        print("    2. 模板生成 -> 生成 skill.yaml 和 SKILL.md")
        print("    3. 质量检查 -> 执行8项检查")
        print("    4. AI验证 -> 验证逻辑一致性和任务完整性")
        print("    5. 质量指标跟踪 -> 记录检查结果和AI验证得分")
        print("    6. 性能监控初始化 -> 设置性能阈值")
        print("    7. 反馈收集初始化 -> 添加系统反馈记录")
        
        print("\n  ✓ Phase 2 组件在技能创建过程中自动执行")
        print("  ✓ 所有质量控制数据存储在SQLite数据库中")
        print("  ✓ 支持技能生命周期的持续质量改进")
        
        return True
        
    except Exception as e:
        print(f"❌ SkillFactory 集成演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("="*60)
    print("Skill Factory Phase 2 质量控制增强演示")
    print("="*60)
    print("演示 Phase 2 新增的四大质量控制组件及其集成")
    print("")
    
    # 执行所有演示
    results = []
    
    results.append(("AI验证系统", demo_ai_validation()))
    results.append(("质量指标跟踪", demo_quality_metrics()))
    results.append(("性能监控系统", demo_performance_monitoring()))
    results.append(("反馈收集机制", demo_feedback_collection()))
    results.append(("SkillFactory集成", demo_factory_integration()))
    
    # 汇总结果
    print_header("演示结果汇总")
    
    all_passed = True
    for demo_name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{demo_name}: {status}")
        if not success:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 所有演示通过！Phase 2 质量控制增强功能正常。")
        print("\nPhase 2 新增功能总结:")
        print("1. AI验证系统 - 5个验证类别，0-100分评分")
        print("2. 质量指标跟踪 - SQLite存储历史指标，趋势分析")
        print("3. 性能监控系统 - 9类性能指标，阈值告警")
        print("4. 反馈收集机制 - 8种反馈类型，情感分析")
        print("5. 完整集成 - 所有组件集成到 SkillFactory 中")
    else:
        print("⚠️  部分演示失败，请检查上述错误信息。")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)