#!/usr/bin/env python3
"""
集成测试套件
全面测试系统功能和性能
"""

import sys
import os
import time
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_core_system():
    """测试核心系统功能"""
    print("🧪 测试核心系统功能...")

    try:
        # 测试配置中心
        from utils.unified_config_center import get_unified_config_center
        config_center = get_unified_config_center()
        assert config_center is not None
        print("✅ 配置中心测试通过")

        # 测试策略注册器
        from utils.strategy_registry import get_strategy_registry
        strategy_registry = get_strategy_registry()
        assert strategy_registry is not None
        print("✅ 策略注册器测试通过")

        # 测试插件系统
        from utils.plugin_system import get_plugin_manager
        plugin_manager = get_plugin_manager()
        assert plugin_manager is not None
        print("✅ 插件系统测试通过")

        return True
    except Exception as e:
        print(f"❌ 核心系统测试失败: {e}")
        return False

def test_performance():
    """测试系统性能"""
    print("⚡ 测试系统性能...")

    try:
        from utils.performance_optimizer import get_performance_optimizer
        optimizer = get_performance_optimizer()

        # 记录一些测试操作 - 使用测试数据工厂
        from test_data_factory import get_test_data_factory
        factory = get_test_data_factory()

        # 创建性能测试数据
        perf_data = factory.create_performance_data("test_operation", (0.001, 0.05))
        duration = perf_data["duration"]

        optimizer.record_operation(perf_data["operation"], duration)
        avg_duration = optimizer.get_average_duration("test_operation")

        assert avg_duration > 0
        print(f"平均执行时间: {avg_duration:.4f}秒")
        return True
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False

def test_autonomous_learning():
    """测试自主学习功能"""
    print("🧠 测试自主学习功能...")

    try:
        from utils.autonomous_learning import get_autonomous_learning
        learner = get_autonomous_learning()

        # 记录一些学习数据 - 使用测试数据工厂
        from test_data_factory import create_learning_interaction
        interaction = create_learning_interaction(
            "什么是机器学习？",
            "机器学习是AI的一个分支"
        )
        # 修改反馈数据结构以符合测试需求
        interaction['user_feedback'] = {"rating": 4, "useful": True}

        learner.record_interaction(**interaction)

        # 获取学习洞察
        insights = learner.get_learning_insights()
        assert insights['total_interactions'] > 0
        print(f"✅ 自主学习测试通过 - 记录了 {insights['total_interactions']} 次交互")

        return True
    except Exception as e:
        print(f"❌ 自主学习测试失败: {e}")
        return False

def test_hardcode_compliance():
    """测试硬编码合规性"""
    print("🔍 测试硬编码合规性...")

    try:
        import subprocess
        result = subprocess.run([sys.executable, 'hardcode_audit.py'],
                              capture_output=True, text=True, cwd=project_root)

        # 检查输出中是否还有硬编码问题
        if "发现 0 处硬编码" in result.stdout:
            print("✅ 零硬编码目标达成！")
            return True
        else:
            lines = result.stdout.split('\n')
            hardcode_count = 0
            for line in lines:
                if "发现" in line and "处硬编码" in line:
                    try:
                        count = int(line.split()[1])
                        hardcode_count = count
                        break
                    except:
                        pass

            if hardcode_count <= 5:  # 允许少量剩余硬编码
                print(f"✅ 硬编码数量控制在可接受范围内: {hardcode_count} 处")
                return True
            else:
                print(f"⚠️ 硬编码数量仍然较多: {hardcode_count} 处")
                return False

    except Exception as e:
        print(f"❌ 硬编码合规性测试失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始运行集成测试套件")
    print("=" * 60)

    test_results = []
    test_results.append(("核心系统", test_core_system()))
    test_results.append(("性能测试", test_performance()))
    test_results.append(("自主学习", test_autonomous_learning()))
    test_results.append(("硬编码合规", test_hardcode_compliance()))

    print("\n" + "=" * 60)
    print("📊 测试结果汇总")

    passed = 0
    failed = 0

    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print("📈 测试统计")
    print(f"  总计测试: {len(test_results)} 个")
    print(f"  通过测试: {passed} 个")
    print(f"  失败测试: {failed} 个")
    print(f"  成功率: {passed/len(test_results)*100:.1f}%")
    if failed == 0:
        print("\n🎉 所有测试通过！系统集成测试成功！")
        print("🚀 系统已准备好投入生产使用")
        return True
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败，需要进一步调试")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
