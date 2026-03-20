#!/usr/bin/env python3
"""
简单测试技能描述优化器
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_optimizer():
    """测试技能描述优化器"""
    from src.services.skill_description_optimizer import SkillDescriptionOptimizer
    
    print("🔬 测试技能描述优化器")
    print("=" * 50)
    
    optimizer = SkillDescriptionOptimizer()
    
    test_cases = [
        {
            "name": "简单描述",
            "description": "代码审查助手",
            "category": "代码分析"
        },
        {
            "name": "中等描述", 
            "description": "创建一个代码审查助手，能够检查Python代码的质量、安全漏洞和性能问题",
            "category": "代码分析"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 测试用例 {i}: {test_case['name']}")
        print(f"   描述: {test_case['description']}")
        
        try:
            result = await optimizer.optimize_description(
                original_description=test_case['description'],
                skill_name=test_case['name'],
                skill_category=test_case['category']
            )
            
            print(f"   ✅ 优化成功")
            print(f"   原始: {result.original}")
            print(f"   优化后: {result.optimized}")
            print(f"   质量评分: {result.quality_score:.2f}")
            print(f"   改进项: {result.improvements}")
            
        except Exception as e:
            print(f"   ❌ 优化失败: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'=' * 50}")
    print("测试完成")

def main():
    """主函数"""
    try:
        asyncio.run(test_optimizer())
        print("\n🎉 所有测试通过！")
        return 0
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())