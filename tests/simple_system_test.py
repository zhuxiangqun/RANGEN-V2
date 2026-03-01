#!/usr/bin/env python3
"""
简化系统测试 - 验证核心功能
"""

import time
import logging
import sys
import os
from typing import Dict, Any

# 添加路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入核心组件
from core.research_executor import ResearchExecutor, ResearchRequest
from core.performance_optimizer import PerformanceOptimizer
from core.security_enhancer import SecurityEnhancer
from core.code_quality_enhancer import CodeQualityEnhancer
from agents.agent_template import AgentTemplate
from utils.truly_intelligent_learning import TrulyIntelligentLearning


def test_research_executor():
    """测试研究执行器"""
    print("🔍 测试研究执行器...")
    
    try:
        executor = ResearchExecutor()
        
        # 初始化
        if not executor.initialize():
            print("❌ 研究执行器初始化失败")
            return False
        
        # 启动
        if not executor.start():
            print("❌ 研究执行器启动失败")
            return False
        
        # 执行测试
        request = ResearchRequest(
            query="测试查询",
            context={"test": True},
            user_id="test_user"
        )
        
        response = executor.execute_research(request)
        
        if not response or not response.result:
            print("❌ 研究执行失败")
            return False
        
        # 健康检查
        health = executor.health_check()
        if not health.get("healthy", False):
            print("❌ 健康检查失败")
            return False
        
        # 停止
        executor.stop()
        
        print(f"✅ 研究执行器测试成功 - 置信度: {response.confidence:.2f}")
        return True
        
    except Exception as e:
        print(f"❌ 研究执行器测试失败: {e}")
        return False


def test_performance_optimizer():
    """测试性能优化器"""
    print("⚡ 测试性能优化器...")
    
    try:
        optimizer = PerformanceOptimizer()
        
        # 启动监控
        optimizer.start_monitoring(interval=0.1)
        time.sleep(0.2)
        
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
        
        print(f"✅ 性能优化器测试成功 - 改进: {result.improvement_percentage:.1f}%")
        return True
        
    except Exception as e:
        print(f"❌ 性能优化器测试失败: {e}")
        return False


def test_security_enhancer():
    """测试安全增强器"""
    print("🔒 测试安全增强器...")
    
    try:
        security = SecurityEnhancer()
        
        # 测试输入验证
        test_input = "正常输入"
        validation = security.validate_input(test_input)
        
        if not validation["valid"]:
            print("❌ 输入验证失败")
            return False
        
        # 测试数据加密
        test_data = "敏感数据"
        encrypted = security.encrypt_data(test_data)
        decrypted = security.decrypt_data(encrypted)
        
        if decrypted != test_data:
            print("❌ 数据加密/解密失败")
            return False
        
        # 测试密码哈希
        password = "test_password"
        hash_result = security.hash_password(password)
        
        if not security.verify_password(password, hash_result["hash"], hash_result["salt"]):
            print("❌ 密码哈希验证失败")
            return False
        
        print("✅ 安全增强器测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 安全增强器测试失败: {e}")
        return False


def test_code_quality_enhancer():
    """测试代码质量增强器"""
    print("📝 测试代码质量增强器...")
    
    try:
        quality_enhancer = CodeQualityEnhancer()
        
        # 测试文件分析
        test_file = "src/core/research_executor.py"
        metrics = quality_enhancer.analyze_file(test_file)
        
        if not metrics or metrics.quality_score < 0:
            print("❌ 代码质量分析失败")
            return False
        
        print(f"✅ 代码质量增强器测试成功 - 质量分数: {metrics.quality_score:.1f}")
        return True
        
    except Exception as e:
        print(f"❌ 代码质量增强器测试失败: {e}")
        return False


def test_agent_template():
    """测试智能体模板"""
    print("🤖 测试智能体模板...")
    
    try:
        agent = AgentTemplate()
        
        # 测试任务执行
        test_task = "测试任务"
        result = agent.execute_task(test_task)
        
        if not result:
            print("❌ 智能体任务执行失败")
            return False
        
        # 测试性能指标
        metrics = agent.get_performance_metrics()
        if not metrics:
            print("❌ 无法获取性能指标")
            return False
        
        print("✅ 智能体模板测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 智能体模板测试失败: {e}")
        return False


def test_intelligent_learning():
    """测试智能学习模块"""
    print("🧠 测试智能学习模块...")
    
    try:
        learning = TrulyIntelligentLearning()
        
        # 测试学习
        test_data = [1, 2, 3, 4, 5]
        context = {"test": True}
        
        result = learning.learn_from_data(test_data, context)
        
        if not result.success:
            print("❌ 智能学习失败")
            return False
        
        # 测试预测
        prediction = learning.predict([1, 2, 3])
        if not prediction or "predictions" not in prediction:
            print("❌ 预测功能失败")
            return False
        
        print(f"✅ 智能学习模块测试成功 - 置信度: {result.confidence:.2f}")
        return True
        
    except Exception as e:
        print(f"❌ 智能学习模块测试失败: {e}")
        return False


def main():
    """主函数"""
    print("🚀 开始简化系统测试")
    print("=" * 50)
    
    tests = [
        test_research_executor,
        test_performance_optimizer,
        test_security_enhancer,
        test_code_quality_enhancer,
        test_agent_template,
        test_intelligent_learning
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 异常: {e}")
            results.append(False)
        print()
    
    # 统计结果
    success_count = sum(results)
    total_count = len(results)
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    
    print("=" * 50)
    print(f"📊 测试结果统计:")
    print(f"  总测试数: {total_count}")
    print(f"  成功数: {success_count}")
    print(f"  失败数: {total_count - success_count}")
    print(f"  成功率: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 系统测试通过！核心功能运行正常")
    elif success_rate >= 60:
        print("⚠️ 系统测试部分通过，需要进一步优化")
    else:
        print("❌ 系统测试失败，需要修复关键问题")
    
    return success_rate >= 60


if __name__ == "__main__":
    main()
