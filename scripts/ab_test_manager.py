#!/usr/bin/env python3
"""
A/B测试管理工具

管理ML模型的A/B测试：
- 创建A/B测试
- 查看测试结果
- 判断获胜者
- 结束测试
"""
import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(dotenv_path=project_root / '.env')


def create_ab_test(model_name: str, variant_a: str, variant_b: str, traffic_split: float = 0.5):
    """创建A/B测试"""
    try:
        from src.core.reasoning.engine import RealReasoningEngine
        engine = RealReasoningEngine()
        
        if not hasattr(engine, 'continuous_learning') or not engine.continuous_learning:
            print("❌ 持续学习系统未启用")
            return
        
        cl_system = engine.continuous_learning
        
        success = cl_system.create_ab_test(model_name, variant_a, variant_b, traffic_split)
        
        if success:
            print(f"✅ A/B测试已创建")
            print(f"   模型: {model_name}")
            print(f"   变体A: {variant_a}")
            print(f"   变体B: {variant_b}")
            print(f"   流量分割: {traffic_split * 100:.0f}% / {(1 - traffic_split) * 100:.0f}%")
        else:
            print(f"❌ A/B测试创建失败")
    except Exception as e:
        print(f"❌ 创建A/B测试失败: {e}")


def list_ab_tests():
    """列出所有A/B测试"""
    try:
        from src.core.reasoning.engine import RealReasoningEngine
        engine = RealReasoningEngine()
        
        if not hasattr(engine, 'continuous_learning') or not engine.continuous_learning:
            print("❌ 持续学习系统未启用")
            return
        
        cl_system = engine.continuous_learning
        
        if not cl_system.ab_tests:
            print("📭 没有活跃的A/B测试")
            return
        
        print(f"\n📋 A/B测试列表 ({len(cl_system.ab_tests)} 个):\n")
        
        for test_id, test in cl_system.ab_tests.items():
            status = test.get("status", "unknown")
            status_icon = "🟢" if status == "active" else "🔴"
            
            print(f"   {status_icon} {test_id}")
            print(f"      模型: {test.get('model_name')}")
            print(f"      变体A: {test.get('variant_a')}")
            print(f"      变体B: {test.get('variant_b')}")
            print(f"      状态: {status}")
            print(f"      创建时间: {test.get('created_at', 'N/A')}")
            
            metrics_a = test["metrics"]["variant_a"]
            metrics_b = test["metrics"]["variant_b"]
            
            print(f"      变体A: {metrics_a.get('requests', 0)} 请求, {metrics_a.get('success', 0)} 成功")
            print(f"      变体B: {metrics_b.get('requests', 0)} 请求, {metrics_b.get('success', 0)} 成功")
            print()
    except Exception as e:
        print(f"❌ 列出A/B测试失败: {e}")


def show_ab_test_results(test_id: str):
    """显示A/B测试结果"""
    try:
        from src.core.reasoning.engine import RealReasoningEngine
        engine = RealReasoningEngine()
        
        if not hasattr(engine, 'continuous_learning') or not engine.continuous_learning:
            print("❌ 持续学习系统未启用")
            return
        
        cl_system = engine.continuous_learning
        
        test = cl_system.get_ab_test_results(test_id)
        if not test:
            print(f"❌ A/B测试不存在: {test_id}")
            return
        
        print(f"\n📊 A/B测试结果: {test_id}\n")
        print(f"   模型: {test.get('model_name')}")
        print(f"   变体A: {test.get('variant_a')}")
        print(f"   变体B: {test.get('variant_b')}")
        print(f"   状态: {test.get('status')}")
        print(f"   创建时间: {test.get('created_at')}")
        
        metrics_a = test["metrics"]["variant_a"]
        metrics_b = test["metrics"]["variant_b"]
        
        print(f"\n   变体A指标:")
        print(f"     请求数: {metrics_a.get('requests', 0)}")
        print(f"     成功数: {metrics_a.get('success', 0)}")
        success_rate_a = metrics_a.get('success', 0) / max(metrics_a.get('requests', 1), 1) * 100
        print(f"     成功率: {success_rate_a:.1f}%")
        print(f"     平均置信度: {metrics_a.get('avg_confidence', 0):.3f}")
        
        print(f"\n   变体B指标:")
        print(f"     请求数: {metrics_b.get('requests', 0)}")
        print(f"     成功数: {metrics_b.get('success', 0)}")
        success_rate_b = metrics_b.get('success', 0) / max(metrics_b.get('requests', 1), 1) * 100
        print(f"     成功率: {success_rate_b:.1f}%")
        print(f"     平均置信度: {metrics_b.get('avg_confidence', 0):.3f}")
        
        # 判断获胜者
        winner = cl_system.get_ab_test_winner(test_id)
        if winner:
            print(f"\n   🏆 获胜者: {winner}")
        else:
            print(f"\n   ⏳ 数据不足，无法判断获胜者（需要至少100个请求）")
        
        print()
    except Exception as e:
        print(f"❌ 显示A/B测试结果失败: {e}")


def end_ab_test(test_id: str):
    """结束A/B测试"""
    try:
        from src.core.reasoning.engine import RealReasoningEngine
        engine = RealReasoningEngine()
        
        if not hasattr(engine, 'continuous_learning') or not engine.continuous_learning:
            print("❌ 持续学习系统未启用")
            return
        
        cl_system = engine.continuous_learning
        
        if test_id not in cl_system.ab_tests:
            print(f"❌ A/B测试不存在: {test_id}")
            return
        
        cl_system.ab_tests[test_id]["status"] = "ended"
        print(f"✅ A/B测试已结束: {test_id}")
    except Exception as e:
        print(f"❌ 结束A/B测试失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="A/B测试管理工具")
    parser.add_argument("action", choices=["create", "list", "show", "end"],
                       help="操作类型")
    parser.add_argument("--test-id", type=str, help="测试ID（用于show和end操作）")
    parser.add_argument("--model", type=str, help="模型名称（用于create操作）")
    parser.add_argument("--variant-a", type=str, help="变体A版本（用于create操作）")
    parser.add_argument("--variant-b", type=str, help="变体B版本（用于create操作）")
    parser.add_argument("--traffic-split", type=float, default=0.5, help="流量分割比例（用于create操作，默认0.5）")
    
    args = parser.parse_args()
    
    if args.action == "create":
        if not args.model or not args.variant_a or not args.variant_b:
            print("❌ 创建A/B测试需要: --model, --variant-a, --variant-b")
            return
        create_ab_test(args.model, args.variant_a, args.variant_b, args.traffic_split)
    elif args.action == "list":
        list_ab_tests()
    elif args.action == "show":
        if not args.test_id:
            print("❌ 显示结果需要: --test-id")
            return
        show_ab_test_results(args.test_id)
    elif args.action == "end":
        if not args.test_id:
            print("❌ 结束测试需要: --test-id")
            return
        end_ab_test(args.test_id)


if __name__ == "__main__":
    main()

