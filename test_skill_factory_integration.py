#!/usr/bin/env python3
"""
Skill Factory Phase 2集成测试
测试新集成的技能质量评估组件
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_skill_factory_integration():
    """测试Skill Factory Phase 2集成"""
    print("🧪 开始测试Skill Factory Phase 2集成")
    print("=" * 60)
    
    try:
        # 1. 导入测试
        from skill_factory.factory import SkillFactory
        print("✅ SkillFactory导入成功")
        
        # 2. 创建工厂实例
        factory = SkillFactory()
        print("✅ SkillFactory实例创建成功")
        
        # 3. 检查新组件是否初始化
        has_quality_evaluator = hasattr(factory, 'skill_quality_evaluator')
        has_description_optimizer = hasattr(factory, 'skill_description_optimizer')
        has_benchmark_system = hasattr(factory, 'skill_benchmark_system')
        
        print(f"📊 组件检查:")
        print(f"  - skill_quality_evaluator: {'✅' if has_quality_evaluator else '❌'}")
        print(f"  - skill_description_optimizer: {'✅' if has_description_optimizer else '❌'}")
        print(f"  - skill_benchmark_system: {'✅' if has_benchmark_system else '❌'}")
        
        if not (has_quality_evaluator and has_description_optimizer and has_benchmark_system):
            print("❌ 组件初始化检查失败")
            return False
        
        # 4. 测试需求
        test_requirements = {
            "name": "test-code-review-skill",
            "description": "创建一个代码审查助手，能够检查Python代码的质量、安全漏洞和性能问题",
            "author": "Test User",
            "domain": "software development"
        }
        
        print(f"\n🔧 测试技能创建:")
        print(f"  名称: {test_requirements['name']}")
        print(f"  描述: {test_requirements['description'][:50]}...")
        
        # 5. 创建技能
        output_dir = "skill_factory/test_output"
        os.makedirs(output_dir, exist_ok=True)
        
        result = factory.create_skill(test_requirements, output_dir)
        
        print(f"\n📋 创建结果:")
        print(f"  成功: {'✅' if result.success else '❌'}")
        print(f"  技能ID: {result.skill_id}")
        print(f"  原型: {result.prototype.value}")
        
        if result.errors:
            print(f"  错误: {result.errors}")
        
        if result.warnings:
            print(f"  警告: {result.warnings[:3]}")  # 只显示前3个警告
        
        # 6. 检查metadata中的Phase 2字段
        print(f"\n📈 Phase 2集成检查:")
        
        if "description_optimization" in result.metadata:
            opt_data = result.metadata["description_optimization"]
            print(f"  ✅ 技能描述优化: 质量评分 {opt_data.get('quality_score', 'N/A')}")
        
        if "skill_quality_assessment" in result.metadata:
            qual_data = result.metadata["skill_quality_assessment"]
            print(f"  ✅ 技能质量评估: 质量评分 {qual_data.get('quality_score', 'N/A')}")
        
        if "benchmark_results" in result.metadata:
            bench_data = result.metadata["benchmark_results"]
            print(f"  ✅ 性能基准测试: 总体评分 {bench_data.get('overall_score', 'N/A')}")
        
        # 7. 检查phase2_integration
        if "phase2_integration" in result.metadata:
            phase2_data = result.metadata["phase2_integration"]
            print(f"  ✅ Phase 2集成状态:")
            print(f"     - 技能质量评估器集成: {phase2_data.get('skill_quality_evaluator_integrated', False)}")
            print(f"     - 技能描述优化器集成: {phase2_data.get('skill_description_optimizer_integrated', False)}")
            print(f"     - 技能基准测试系统集成: {phase2_data.get('skill_benchmark_system_integrated', False)}")
        
        # 8. 检查开发阶段
        print(f"\n🚀 开发阶段完成:")
        for stage in result.development_stages:
            status_icon = "✅" if stage.status in ["completed", "completed_with_warnings"] else "⏳"
            print(f"  {status_icon} {stage.name}: {stage.status}")
        
        print(f"\n{'=' * 60}")
        print(f"📊 测试总结:")
        print(f"  总阶段数: {len(result.development_stages)}")
        print(f"  完成阶段: {sum(1 for s in result.development_stages if s.status in ['completed', 'completed_with_warnings'])}")
        
        # 清理测试输出
        if os.path.exists(output_dir):
            import shutil
            shutil.rmtree(output_dir)
            print(f"🧹 已清理测试输出目录: {output_dir}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🔬 Skill Factory Phase 2集成测试")
    print("基于Anthropic skill-creator原理的三元评估系统集成测试")
    print()
    
    # 运行测试
    success = asyncio.run(test_skill_factory_integration())
    
    if success:
        print("\n🎉 所有测试通过！Skill Factory Phase 2集成成功。")
    else:
        print("\n❌ 测试失败，请检查集成问题。")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()