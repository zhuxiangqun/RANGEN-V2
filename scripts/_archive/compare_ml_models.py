#!/usr/bin/env python3
"""
模型性能对比工具

对比不同模型版本的性能，用于A/B测试和模型选择。
"""
import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(dotenv_path=project_root / '.env')


def compare_models(model_name: str, version_a: str = None, version_b: str = None):
    """对比两个模型版本"""
    print("=" * 80)
    print(f"模型性能对比: {model_name}")
    print("=" * 80)
    
    # 初始化推理引擎
    try:
        from src.core.reasoning.engine import RealReasoningEngine
        engine = RealReasoningEngine()
        print(f"\n✅ 推理引擎已初始化")
    except Exception as e:
        print(f"\n❌ 推理引擎初始化失败: {e}")
        return
    
    # 检查持续学习系统
    if not hasattr(engine, 'continuous_learning') or not engine.continuous_learning:
        print(f"\n❌ 持续学习系统未启用")
        return
    
    cl_system = engine.continuous_learning
    
    # 获取模型版本信息
    if version_a:
        version_info_a = cl_system.get_model_version(model_name, version_a)
    else:
        version_info_a = cl_system.get_model_version(model_name)
        version_a = version_info_a.get("version", "latest") if version_info_a else "latest"
    
    if version_b:
        version_info_b = cl_system.get_model_version(model_name, version_b)
    else:
        # 获取所有版本，选择倒数第二个
        all_versions = cl_system.list_model_versions(model_name)
        if len(all_versions) >= 2:
            version_b = all_versions[1].get("version")
            version_info_b = cl_system.get_model_version(model_name, version_b)
        else:
            print(f"\n⚠️ 只有一个版本，无法对比")
            return
    
    if not version_info_a or not version_info_b:
        print(f"\n❌ 无法获取版本信息")
        return
    
    print(f"\n📊 对比版本:")
    print(f"   版本A: {version_a}")
    print(f"   版本B: {version_b}")
    
    # 检查A/B测试
    ab_tests = [test_id for test_id, test in cl_system.ab_tests.items() 
                if test.get("model_name") == model_name and test.get("status") == "active"]
    
    if ab_tests:
        print(f"\n🔬 找到活跃的A/B测试: {len(ab_tests)} 个")
        for test_id in ab_tests:
            test = cl_system.get_ab_test_results(test_id)
            if test:
                print(f"\n   测试ID: {test_id}")
                print(f"   变体A: {test.get('variant_a')}")
                print(f"   变体B: {test.get('variant_b')}")
                print(f"   流量分割: {test.get('traffic_split', 0.5) * 100:.0f}% / {(1 - test.get('traffic_split', 0.5)) * 100:.0f}%")
                
                metrics_a = test["metrics"]["variant_a"]
                metrics_b = test["metrics"]["variant_b"]
                
                print(f"\n   变体A指标:")
                print(f"     请求数: {metrics_a.get('requests', 0)}")
                print(f"     成功数: {metrics_a.get('success', 0)}")
                print(f"     成功率: {metrics_a.get('success', 0) / max(metrics_a.get('requests', 1), 1) * 100:.1f}%")
                print(f"     平均置信度: {metrics_a.get('avg_confidence', 0):.3f}")
                
                print(f"\n   变体B指标:")
                print(f"     请求数: {metrics_b.get('requests', 0)}")
                print(f"     成功数: {metrics_b.get('success', 0)}")
                print(f"     成功率: {metrics_b.get('success', 0) / max(metrics_b.get('requests', 1), 1) * 100:.1f}%")
                print(f"     平均置信度: {metrics_b.get('avg_confidence', 0):.3f}")
                
                # 判断获胜者
                winner = cl_system.get_ab_test_winner(test_id)
                if winner:
                    print(f"\n   🏆 当前获胜者: {winner}")
                else:
                    print(f"\n   ⏳ 数据不足，无法判断获胜者")
    else:
        print(f"\n⚠️ 没有找到活跃的A/B测试")
    
    # 对比版本信息
    print(f"\n📋 版本信息对比:")
    print(f"\n   版本A ({version_a}):")
    print(f"     注册时间: {version_info_a.get('registered_at', 'N/A')}")
    print(f"     最后训练: {version_info_a.get('last_training', 'N/A')}")
    
    print(f"\n   版本B ({version_b}):")
    print(f"     注册时间: {version_info_b.get('registered_at', 'N/A')}")
    print(f"     最后训练: {version_info_b.get('last_training', 'N/A')}")
    
    print(f"\n{'='*80}")
    print("✅ 模型对比完成！")
    print(f"{'='*80}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="模型性能对比工具")
    parser.add_argument("model", type=str, help="模型名称")
    parser.add_argument("--version-a", type=str, help="版本A（默认：最新版本）")
    parser.add_argument("--version-b", type=str, help="版本B（默认：上一个版本）")
    
    args = parser.parse_args()
    
    compare_models(args.model, args.version_a, args.version_b)


if __name__ == "__main__":
    main()

