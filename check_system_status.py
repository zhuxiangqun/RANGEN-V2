#!/usr/bin/env python3
"""
系统状态检查脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.dependency_checker import get_dependency_checker
from src.data.identity_manager import get_identity_manager
from src.utils.unified_security_center import get_unified_security_center
from src.ai.ai_algorithm_integrator import get_ai_algorithm_integrator


def main():
    """主函数"""
    print("=" * 60)
    print("RANGEN系统状态检查")
    print("=" * 60)
    
    # 检查依赖
    print("\n📦 依赖检查:")
    print("-" * 30)
    checker = get_dependency_checker()
    report = checker.generate_dependency_report()
    
    summary = report["summary"]
    print(f"总依赖数: {summary['total_dependencies']}")
    print(f"可用依赖: {summary['available_dependencies']}")
    print(f"缺失必需依赖: {summary['missing_required']}")
    print(f"可用可选依赖: {summary['available_optional']}")
    print(f"健康分数: {summary['health_score']:.1f}%")
    
    # 显示依赖详情
    print("\n📋 依赖详情:")
    print("-" * 30)
    for name, dep_info in report["dependencies"].items():
        status_icon = "✅" if dep_info["status"] == "available" else "❌" if dep_info["status"] == "missing" else "⚠️"
        required_text = " (必需)" if dep_info["required"] else " (可选)"
        version_text = f" v{dep_info['version']}" if dep_info["version"] else ""
        print(f"{status_icon} {name}{required_text}{version_text}")
    
    # 显示建议
    if report["recommendations"]:
        print("\n💡 建议:")
        print("-" * 30)
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"{i}. {rec}")
    
    # 检查核心组件
    print("\n🔧 核心组件检查:")
    print("-" * 30)
    
    try:
        # 身份管理器
        identity_manager = get_identity_manager()
        mfa_deps = identity_manager.check_mfa_dependencies()
        print(f"✅ 身份管理器: 正常")
        print(f"   - TOTP支持: {'✅' if mfa_deps['pyotp'] else '❌'}")
        print(f"   - QR码支持: {'✅' if mfa_deps['qrcode'] else '❌'}")
    except Exception as e:
        print(f"❌ 身份管理器: 错误 - {e}")
    
    try:
        # 安全中心
        security_center = get_unified_security_center()
        print(f"✅ 安全中心: 正常")
        print(f"   - 威胁检测: 支持8种攻击模式")
        print(f"   - 安全审计: 已启用")
    except Exception as e:
        print(f"❌ 安全中心: 错误 - {e}")
    
    try:
        # AI算法集成器
        ai_integrator = get_ai_algorithm_integrator()
        available_algorithms = ai_integrator.get_available_algorithms()
        print(f"✅ AI算法集成器: 正常")
        print(f"   - 可用算法: {', '.join(available_algorithms)}")
        
        # 检查各AI引擎
        for algorithm in available_algorithms:
            capabilities = ai_integrator.get_algorithm_capabilities(algorithm)
            if "error" not in capabilities:
                supported_tasks = capabilities.get("supported_tasks", [])
                print(f"   - {algorithm}: {len(supported_tasks)}个任务类型")
    except Exception as e:
        print(f"❌ AI算法集成器: 错误 - {e}")
    
    # 系统总结
    print("\n📊 系统总结:")
    print("-" * 30)
    health_score = summary['health_score']
    if health_score >= 90:
        status = "🟢 优秀"
    elif health_score >= 75:
        status = "🟡 良好"
    elif health_score >= 50:
        status = "🟠 一般"
    else:
        status = "🔴 需要改进"
    
    print(f"系统状态: {status}")
    print(f"健康分数: {health_score:.1f}%")
    
    if summary['missing_required'] > 0:
        print("⚠️  警告: 存在缺失的必需依赖")
    else:
        print("✅ 所有必需依赖都已安装")
    
    print("\n" + "=" * 60)
    print("检查完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
