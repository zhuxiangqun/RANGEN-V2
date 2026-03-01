#!/usr/bin/env python3
"""
改进的系统测试 - 修复后的完整测试
"""

import time
import logging
import sys
import os
from typing import Dict, Any, List

# 添加路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_research_executor_improved():
    """改进的研究执行器测试"""
    print("🔍 测试研究执行器（改进版）...")
    
    try:
        from core.research_executor import ResearchExecutor, ResearchRequest
        
        executor = ResearchExecutor()
        
        # 初始化
        if not executor.initialize():
            print("❌ 研究执行器初始化失败")
            return False
        
        # 启动
        if not executor.start():
            print("❌ 研究执行器启动失败")
            return False
        
        # 测试基本功能
        request = ResearchRequest(
            query="测试查询",
            context={"test": True},
            user_id="test_user"
        )
        
        response = executor.execute_research(request)
        
        if not response or not response.result:
            print("❌ 研究执行失败")
            return False
        
        # 测试健康检查
        health = executor.health_check()
        if not health.get("healthy", False):
            print("❌ 健康检查失败")
            return False
        
        # 测试性能指标
        metrics = executor.get_metrics()
        if not metrics:
            print("❌ 无法获取性能指标")
            return False
        
        # 停止
        executor.stop()
        
        print(f"✅ 研究执行器测试成功")
        print(f"   - 置信度: {response.confidence:.2f}")
        print(f"   - 处理时间: {response.processing_time:.3f}s")
        print(f"   - 成功率: {health.get('success_rate', 0):.1f}%")
        return True
        
    except Exception as e:
        print(f"❌ 研究执行器测试失败: {e}")
        logger.exception("研究执行器测试异常")
        return False


def test_performance_optimizer_improved():
    """改进的性能优化器测试"""
    print("⚡ 测试性能优化器（改进版）...")
    
    try:
        from core.performance_optimizer import PerformanceOptimizer
        
        optimizer = PerformanceOptimizer()
        
        # 启动监控
        optimizer.start_monitoring(interval=0.1)
        time.sleep(0.3)
        
        # 测试函数优化
        def test_func(x):
            return x * x + 2 * x + 1
        
        result = optimizer.optimize_function(
            test_func, 
            optimizer.OptimizationStrategy.CACHING, 
            5
        )
        
        if not result.success:
            print("❌ 性能优化失败")
            return False
        
        # 获取报告
        report = optimizer.get_performance_report()
        if not report:
            print("❌ 无法获取性能报告")
            return False
        
        # 停止监控
        optimizer.stop_monitoring()
        
        print(f"✅ 性能优化器测试成功")
        print(f"   - 改进百分比: {result.improvement_percentage:.1f}%")
        print(f"   - 优化时间: {result.optimization_time:.3f}s")
        return True
        
    except Exception as e:
        print(f"❌ 性能优化器测试失败: {e}")
        logger.exception("性能优化器测试异常")
        return False


def test_security_enhancer_improved():
    """改进的安全增强器测试"""
    print("🔒 测试安全增强器（改进版）...")
    
    try:
        from core.security_enhancer import SecurityEnhancer
        
        security = SecurityEnhancer()
        
        # 测试输入验证
        test_cases = [
            ("正常输入", True),
            ("<script>alert('xss')</script>", False),
            ("SELECT * FROM users", False),
            ("正常输入<script>alert('test')</script>", False)
        ]
        
        validation_results = []
        for test_input, expected_valid in test_cases:
            result = security.validate_input(test_input)
            is_correct = result["valid"] == expected_valid
            validation_results.append(is_correct)
            print(f"   - 输入: '{test_input[:20]}...' -> 有效: {result['valid']} (期望: {expected_valid})")
        
        if not all(validation_results):
            print("❌ 输入验证测试失败")
            return False
        
        # 测试数据加密
        test_data = "敏感数据测试"
        encrypted = security.encrypt_data(test_data)
        decrypted = security.decrypt_data(encrypted)
        
        if decrypted != test_data:
            print("❌ 数据加密/解密失败")
            return False
        
        # 测试密码哈希
        password = "test_password_123"
        hash_result = security.hash_password(password)
        
        if not security.verify_password(password, hash_result["hash"], hash_result["salt"]):
            print("❌ 密码哈希验证失败")
            return False
        
        print(f"✅ 安全增强器测试成功")
        print(f"   - 输入验证: {sum(validation_results)}/{len(validation_results)} 通过")
        print(f"   - 数据加密: 成功")
        print(f"   - 密码哈希: 成功")
        return True
        
    except Exception as e:
        print(f"❌ 安全增强器测试失败: {e}")
        logger.exception("安全增强器测试异常")
        return False


def test_code_quality_enhancer_improved():
    """改进的代码质量增强器测试"""
    print("📝 测试代码质量增强器（改进版）...")
    
    try:
        from core.code_quality_enhancer import CodeQualityEnhancer
        
        quality_enhancer = CodeQualityEnhancer()
        
        # 测试文件分析
        test_file = "src/core/research_executor.py"
        if os.path.exists(test_file):
            metrics = quality_enhancer.analyze_file(test_file)
            
            if not metrics or metrics.quality_score < 0:
                print("❌ 代码质量分析失败")
                return False
            
            print(f"✅ 代码质量增强器测试成功")
            print(f"   - 质量分数: {metrics.quality_score:.1f}/100")
            print(f"   - 代码行数: {metrics.lines_of_code}")
            print(f"   - 圈复杂度: {metrics.cyclomatic_complexity}")
            print(f"   - 问题数量: {metrics.issues_count}")
            return True
        else:
            print(f"⚠️ 测试文件不存在: {test_file}")
            return False
        
    except Exception as e:
        print(f"❌ 代码质量增强器测试失败: {e}")
        logger.exception("代码质量增强器测试异常")
        return False


def test_agent_template_improved():
    """改进的智能体模板测试"""
    print("🤖 测试智能体模板（改进版）...")
    
    try:
        from agents.test_agent import TestAgent
        
        agent = TestAgent("test_agent_001")
        
        # 测试基本任务执行
        test_tasks = [
            "正常任务",
            "慢任务测试",
            ["列表", "任务", "测试"],
            {"key": "value", "type": "dict"}
        ]
        
        results = []
        for task in test_tasks:
            try:
                result = agent.execute_task(task)
                results.append(True)
                print(f"   - 任务类型: {type(task).__name__} -> 成功")
            except Exception as e:
                results.append(False)
                print(f"   - 任务类型: {type(task).__name__} -> 失败: {e}")
        
        # 测试错误处理
        try:
            error_result = agent.execute_task("error test")
            print("   - 错误处理: 未正确处理错误")
        except ValueError:
            print("   - 错误处理: 正确捕获错误")
            results.append(True)
        
        # 测试性能指标
        metrics = agent.get_performance_metrics()
        if not metrics:
            print("❌ 无法获取性能指标")
            return False
        
        # 测试统计信息
        stats = agent.get_test_statistics()
        
        success_rate = sum(results) / len(results) if results else 0
        
        print(f"✅ 智能体模板测试成功")
        print(f"   - 任务成功率: {success_rate:.1%}")
        print(f"   - 总任务数: {agent.execution_stats['total_tasks']}")
        print(f"   - 平均执行时间: {agent.execution_stats['average_execution_time']:.3f}s")
        return success_rate >= 0.8
        
    except Exception as e:
        print(f"❌ 智能体模板测试失败: {e}")
        logger.exception("智能体模板测试异常")
        return False


def test_intelligent_learning_improved():
    """改进的智能学习模块测试"""
    print("🧠 测试智能学习模块（改进版）...")
    
    try:
        from utils.truly_intelligent_learning import TrulyIntelligentLearning
        
        learning = TrulyIntelligentLearning()
        
        # 测试不同类型的数据学习
        test_data_sets = [
            ([1, 2, 3, 4, 5], {"type": "numeric_sequence"}),
            ("hello world", {"type": "text"}),
            ([1, 1, 2, 2, 3, 3], {"type": "repeated_pattern"}),
            (["a", "b", "c", "a", "b", "c"], {"type": "string_pattern"})
        ]
        
        learning_results = []
        for data, context in test_data_sets:
            result = learning.learn_from_data(data, context)
            learning_results.append(result.success)
            print(f"   - 数据类型: {context['type']} -> 学习成功: {result.success}")
        
        # 测试预测功能
        prediction = learning.predict([1, 2, 3])
        if not prediction or "predictions" not in prediction:
            print("❌ 预测功能失败")
            return False
        
        # 测试学习统计
        stats = learning.get_learning_stats()
        if not stats:
            print("❌ 无法获取学习统计")
            return False
        
        success_rate = sum(learning_results) / len(learning_results) if learning_results else 0
        
        print(f"✅ 智能学习模块测试成功")
        print(f"   - 学习成功率: {success_rate:.1%}")
        print(f"   - 学习模式数: {stats.get('total_patterns', 0)}")
        print(f"   - 预测结果数: {len(prediction.get('predictions', []))}")
        return success_rate >= 0.75
        
    except Exception as e:
        print(f"❌ 智能学习模块测试失败: {e}")
        logger.exception("智能学习模块测试异常")
        return False


def test_integration_workflow_improved():
    """改进的集成工作流测试"""
    print("🔄 测试集成工作流（改进版）...")
    
    try:
        from core.research_executor import ResearchExecutor, ResearchRequest
        from core.security_enhancer import SecurityEnhancer
        from core.performance_optimizer import PerformanceOptimizer
        from agents.test_agent import TestAgent
        
        # 初始化组件
        executor = ResearchExecutor()
        security = SecurityEnhancer()
        optimizer = PerformanceOptimizer()
        agent = TestAgent("integration_test_agent")
        
        # 1. 安全验证
        user_input = "用户查询：如何优化系统性能？"
        validation = security.validate_input(user_input)
        
        if not validation["valid"]:
            print("❌ 输入验证失败")
            return False
        
        # 2. 智能体处理
        agent_result = agent.execute_task(user_input)
        if not agent_result:
            print("❌ 智能体处理失败")
            return False
        
        # 3. 性能优化
        def research_function(query):
            return f"研究结果：{query}"
        
        optimized_result = optimizer.optimize_function(
            research_function,
            optimizer.OptimizationStrategy.CACHING,
            user_input
        )
        
        if not optimized_result.success:
            print("❌ 性能优化失败")
            return False
        
        # 4. 研究执行
        if not executor.initialize() or not executor.start():
            print("❌ 执行器初始化失败")
            return False
        
        request = ResearchRequest(
            query=user_input,
            context={"validated": True, "optimized": True, "agent_processed": True}
        )
        
        response = executor.execute_research(request)
        
        if not response or not response.result:
            print("❌ 研究执行失败")
            return False
        
        # 5. 清理
        executor.stop()
        
        print(f"✅ 集成工作流测试成功")
        print(f"   - 输入验证: 通过")
        print(f"   - 智能体处理: 通过")
        print(f"   - 性能优化: {optimized_result.improvement_percentage:.1f}% 改进")
        print(f"   - 研究执行: 置信度 {response.confidence:.2f}")
        return True
        
    except Exception as e:
        print(f"❌ 集成工作流测试失败: {e}")
        logger.exception("集成工作流测试异常")
        return False


def main():
    """主函数"""
    print("🚀 开始改进的系统测试")
    print("=" * 60)
    
    tests = [
        ("研究执行器", test_research_executor_improved),
        ("性能优化器", test_performance_optimizer_improved),
        ("安全增强器", test_security_enhancer_improved),
        ("代码质量增强器", test_code_quality_enhancer_improved),
        ("智能体模板", test_agent_template_improved),
        ("智能学习模块", test_intelligent_learning_improved),
        ("集成工作流", test_integration_workflow_improved)
    ]
    
    results = []
    start_time = time.time()
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append(result)
            status = "✅ 通过" if result else "❌ 失败"
            print(f"\n{test_name}: {status}")
        except Exception as e:
            print(f"\n{test_name}: ❌ 异常 - {e}")
            results.append(False)
            logger.exception(f"{test_name} 测试异常")
    
    # 统计结果
    total_time = time.time() - start_time
    success_count = sum(results)
    total_count = len(results)
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果统计:")
    print(f"  总测试数: {total_count}")
    print(f"  成功数: {success_count}")
    print(f"  失败数: {total_count - success_count}")
    print(f"  成功率: {success_rate:.1f}%")
    print(f"  总耗时: {total_time:.2f}秒")
    
    # 详细结果
    print(f"\n📋 详细结果:")
    for i, (test_name, _) in enumerate(tests):
        status = "✅ 通过" if results[i] else "❌ 失败"
        print(f"  {i+1}. {test_name}: {status}")
    
    if success_rate >= 80:
        print("\n🎉 系统测试通过！核心功能运行正常")
        return True
    elif success_rate >= 60:
        print("\n⚠️ 系统测试部分通过，需要进一步优化")
        return False
    else:
        print("\n❌ 系统测试失败，需要修复关键问题")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
