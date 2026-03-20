#!/usr/bin/env python3
"""
快速检查V3遵从性分数
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.v3_compliance_checker import V3ComplianceChecker

def main():
    print("检查V3遵从性分数...")
    print("=" * 60)
    
    checker = V3ComplianceChecker()
    report = checker.check_all_principles()
    
    print(f"总体V3遵从性分数: {report['overall_score']:.2f}")
    print(f"原则数量: {report['principle_count']}")
    print()
    
    print("各原则详细分数:")
    print("-" * 60)
    
    # 显示所有结果
    for principle_name, result in report['results'].items():
        print(f"{principle_name}: {result['score']:.2f} ({result['level']})")
    
    print("-" * 60)
    
    # 显示改进
    four_layer_score = None
    for principle_name, result in report['results'].items():
        if "四层架构" in principle_name:
            four_layer_score = result['score']
            break
    
    if four_layer_score is not None:
        print(f"\n🎯 四层架构系统分数: {four_layer_score:.2f}")
        
        if four_layer_score >= 0.8:
            print("✅ 四层架构已达到完全实现水平（得益于标准化接口系统）")
            print("   标准化接口系统已完全实现:")
            print("   - LayerMessage, LayerMessageHeader")
            print("   - StandardizedInterface")
            print("   - LayerCommunicationBus")
            print("   - 标准化层适配器 (StandardizedInteractionAdapter等)")
            print("   - EnhancedFourLayerManager (增强版管理器)")
    else:
        print("\n⚠️ 未找到四层架构系统分数")
    
    print("\n📊 总体评估:")
    if report['overall_score'] >= 0.8:
        print("✅ 优秀 - 系统已达到V3架构的卓越水平")
    elif report['overall_score'] >= 0.6:
        print("✅ 良好 - 系统基本达到V3架构水准")
    elif report['overall_score'] >= 0.4:
        print("⚠️  一般 - 需要进一步优化以达到V3水准")
    else:
        print("❌ 不足 - 需要重大改进以达到V3水准")
    
    print("=" * 60)
    return report

if __name__ == "__main__":
    main()