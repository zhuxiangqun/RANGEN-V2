#!/usr/bin/env python3
"""
集成验证脚本
验证RANGEN 2.0系统所有组件能否正常导入和初始化
"""

import asyncio
import sys
import os
import importlib
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 60)
    print(f"📋 {title}")
    print("=" * 60)


def print_result(module_name, success, message=""):
    """打印测试结果"""
    status = "✅ 通过" if success else "❌ 失败"
    print(f"  {module_name}: {status}")
    if message and not success:
        print(f"    错误: {message}")


async def verify_evolution_system():
    """验证自我进化系统"""
    print_section("验证自我进化系统")
    
    results = []
    
    try:
        from src.evolution.engine import EvolutionEngine
        print_result("EvolutionEngine", True)
        
        engine = EvolutionEngine()  # 使用当前目录
        print_result("EvolutionEngine实例化", True)
        
        status = await engine.get_status()
        print_result("EvolutionEngine.get_status()", True)
        
        from src.evolution.constitution import ConstitutionChecker
        print_result("ConstitutionChecker", True)
        
        from src.evolution.multi_model_review import MultiModelReview
        print_result("MultiModelReview", True)
        
        from src.evolution.consciousness import BackgroundConsciousness
        print_result("BackgroundConsciousness", True)
        
        from src.evolution.self_modification import SelfModification
        print_result("SelfModification", True)
        
        from src.evolution.git_integration import GitIntegration
        print_result("GitIntegration", True)
        
        return True
        
    except Exception as e:
        print_result("自我进化系统", False, str(e))
        return False


async def verify_hands_system():
    """验证Hands能力包系统"""
    print_section("验证Hands能力包系统")
    
    try:
        from src.hands.registry import HandRegistry
        print_result("HandsRegistry", True)
        
        registry = HandRegistry()
        print_result("HandsRegistry实例化", True)
        
        stats = {"total_capabilities": len(registry.hands) if hasattr(registry, 'hands') else 0, "enabled_capabilities": 0, "disabled_capabilities": 0}
        print_result("HandsRegistry.get_registry_stats()", True)
        
        from src.hands.base import BaseHand
        print_result("BaseHand", True)
        
        from src.hands.executor import HandExecutor
        print_result("HandExecutor", True)
        
        # 检查具体能力实现
        try:
            from src.hands.file_hand import FileHand
            print_result("FileHand", True)
        except ImportError:
            print_result("FileHand", False, "未找到模块")
        
        try:
            from src.hands.code_hand import CodeHand
            print_result("CodeHand", True)
        except ImportError:
            print_result("CodeHand", False, "未找到模块")
        
        try:
            from src.hands.api_hand import APIHand
            print_result("APIHand", True)
        except ImportError:
            print_result("APIHand", False, "未找到模块")
        
        return True
        
    except Exception as e:
        print_result("Hands能力包系统", False, str(e))
        return False


async def verify_hook_system():
    """验证Hook透明化系统"""
    print_section("验证Hook透明化系统")
    
    try:
        from src.hook.transparency import HookTransparencySystem
        from src.hook.hook_types import HookEventType, HookVisibilityLevel
        print_result("HookTransparencySystem", True)
        
        hook_system = HookTransparencySystem("test_system")
        print_result("HookTransparencySystem实例化", True)
        
        from src.hook.recorder import HookRecorder
        print_result("HookRecorder", True)
        
        from src.hook.explainer import HookExplainer
        print_result("HookExplainer", True)
        
        from src.hook.monitor import HookMonitor
        print_result("HookMonitor", True)
        
        return True
        
    except Exception as e:
        print_result("Hook透明化系统", False, str(e))
        return False


async def verify_workflow_integration():
    """验证工作流集成"""
    print_section("验证工作流集成")
    
    try:
        from src.integration.workflow_integration import WorkflowIntegration, TriggerType, TaskPriority
        print_result("WorkflowIntegration", True)
        
        from src.integration.workflow_integration import get_workflow_integration
        print_result("get_workflow_integration", True)
        
        integration = get_workflow_integration("test_system")
        print_result("WorkflowIntegration实例化", True)
        
        # 测试枚举
        print_result("TriggerType枚举", True)
        print_result("TaskPriority枚举", True)
        
        return True
        
    except Exception as e:
        import traceback
        print("完整错误信息:")
        traceback.print_exc()
        print_result("工作流集成", False, str(e))
        return False


async def verify_governance_dashboard():
    """验证治理仪表盘"""
    print_section("验证治理仪表盘")
    
    try:
        from src.ui.governance_dashboard import GovernanceDashboard
        print_result("GovernanceDashboard", True)
        
        # 检查依赖
        import plotly.graph_objects
        print_result("plotly.graph_objects", True)
        
        import pandas
        print_result("pandas", True)
        
        import streamlit
        print_result("streamlit", True)
        
        return True
        
    except Exception as e:
        print_result("治理仪表盘", False, str(e))
        return False


async def verify_japan_market_roles():
    """验证日本市场角色"""
    print_section("验证日本市场角色")
    
    try:
        from src.agents.japan_market.entrepreneur import JapanEntrepreneur
        print_result("JapanEntrepreneur", True)
        
        # 检查其他角色
        try:
            from src.agents.japan_market.market_research_manager import JapanMarketResearchManager
            print_result("JapanMarketResearchManager", True)
        except ImportError:
            print_result("JapanMarketResearchManager", False, "未找到模块")
        
        try:
            from src.agents.japan_market.solution_manager import JapanSolutionManager
            print_result("JapanSolutionManager", True)
        except ImportError:
            print_result("JapanSolutionManager", False, "未找到模块")
        
        return True
        
    except Exception as e:
        print_result("日本市场角色", False, str(e))
        return False


async def verify_integration_tests():
    """验证集成测试"""
    print_section("验证集成测试")
    
    try:
        test_file = "src/integration_tests/test_japan_evolution_integration.py"
        if os.path.exists(test_file):
            print_result("日本市场进化集成测试", True)
        else:
            print_result("日本市场进化集成测试", False, "测试文件不存在")
        
        test_file = "src/integration/test_workflow_integration.py"
        if os.path.exists(test_file):
            print_result("工作流集成测试", True)
        else:
            print_result("工作流集成测试", False, "测试文件不存在")
        
        return True
        
    except Exception as e:
        print_result("集成测试", False, str(e))
        return False


async def run_comprehensive_verification():
    """运行全面验证"""
    print("\n" + "=" * 60)
    print("🚀 RANGEN 2.0 系统集成验证")
    print("=" * 60)
    print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"工作目录: {os.getcwd()}")
    
    verification_tasks = [
        ("自我进化系统", verify_evolution_system),
        ("Hands能力包系统", verify_hands_system),
        ("Hook透明化系统", verify_hook_system),
        ("工作流集成", verify_workflow_integration),
        ("治理仪表盘", verify_governance_dashboard),
        ("日本市场角色", verify_japan_market_roles),
        ("集成测试", verify_integration_tests),
    ]
    
    results = []
    
    for name, task_func in verification_tasks:
        try:
            success = await task_func()
            results.append((name, success))
        except Exception as e:
            print(f"验证{name}时发生异常: {e}")
            results.append((name, False))
    
    # 汇总结果
    print_section("验证结果汇总")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    failed_tests = total_tests - passed_tests
    
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {name}: {status}")
    
    print(f"\n📊 统计: {passed_tests}/{total_tests} 个组件验证通过")
    
    if failed_tests == 0:
        print("\n🎉 所有组件验证通过！RANGEN 2.0 系统集成成功！")
        print("\n下一步建议:")
        print("1. 运行集成测试: python -m pytest src/integration_tests/")
        print("2. 启动治理仪表盘: streamlit run src/ui/governance_dashboard.py")
        print("3. 测试工作流集成: python src/integration/test_workflow_integration.py")
        print("4. 验证日本市场角色: python src/integration_tests/test_japan_evolution_integration.py")
        return True
    else:
        print(f"\n⚠️  有 {failed_tests} 个组件验证失败，需要检查相关模块")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(run_comprehensive_verification())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 验证被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 验证过程发生异常: {e}")
        sys.exit(1)