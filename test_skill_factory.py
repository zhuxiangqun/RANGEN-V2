#!/usr/bin/env python3
"""
使用系统SkillFactory创建Skill并评估

流程：
1. 使用SkillFactory创建4个新Skill (calculator, multimodal, browser, file_read)
2. 使用SkillQualityEvaluator评估每个Skill
3. 输出评估报告
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 添加skill_factory到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "skill_factory"))


async def create_skill_with_factory():
    """使用SkillFactory创建Skill"""
    print("=" * 60)
    print("步骤1: 使用SkillFactory创建Skill")
    print("=" * 60)
    
    from skill_factory.factory import SkillFactory
    
    factory = SkillFactory()
    
    # 定义4个新Skill的需求
    skills_requirements = [
        {
            "name": "calculator-skill",
            "description": "数学计算工具，执行各种数学运算，包括基本算术和高级数学函数",
            "use_cases": ["计算数学表达式", "单位转换", "数据分析"],
            "complexity": "low"
        },
        {
            "name": "multimodal-skill", 
            "description": "多模态处理工具，处理图像、音频、视频等内容",
            "use_cases": ["图像识别", "视频处理", "音频分析"],
            "complexity": "medium"
        },
        {
            "name": "browser-skill",
            "description": "浏览器自动化工具，自动化网页操作和测试",
            "use_cases": ["网页自动化", "表单填写", "截图"],
            "complexity": "medium"
        },
        {
            "name": "file-read-skill",
            "description": "文件读取工具，读取各种格式的文件内容",
            "use_cases": ["读取文本", "解析CSV/JSON", "文档处理"],
            "complexity": "low"
        }
    ]
    
    output_dir = "src/agents/skills/bundled"
    results = []
    
    for req in skills_requirements:
        print(f"\n[创建] {req['name']}...")
        
        result = factory.create_skill(req, output_dir)
        
        results.append({
            "name": req["name"],
            "result": result
        })
        
        if result.success:
            print(f"    ✅ 成功创建: {result.skill_dir}")
            print(f"    原型类型: {result.prototype}")
            print(f"    开发阶段: {len(result.development_stages)} 个")
        else:
            print(f"    ❌ 创建失败: {result.errors}")
    
    return results


async def evaluate_skills(skills_results):
    """使用SkillQualityEvaluator评估Skill"""
    print("\n" + "=" * 60)
    print("步骤2: 使用SkillQualityEvaluator评估")
    print("=" * 60)
    
    from src.services.skill_quality_evaluator import SkillQualityEvaluator, SkillData
    
    evaluator = SkillQualityEvaluator()
    
    evaluation_results = []
    
    for skill_info in skills_results:
        name = skill_info["name"]
        result = skill_info["result"]
        
        if not result.success:
            print(f"\n[跳过] {name} (创建失败)")
            continue
        
        print(f"\n[评估] {name}...")
        
        # 构建SkillData
        skill_data = SkillData(
            skill_id=name,
            name=name,
            description=f"{name} - AI生成的Skill",
            category="utility",
            complexity="moderate",
            input_format={"type": "object"},
            output_format={"type": "object"},
            examples=[],
            dependencies=[],
            metadata={"source": "skill_factory"}
        )
        
        # 评估
        report = await evaluator.evaluate_skill(skill_data)
        
        evaluation_results.append({
            "name": name,
            "report": report
        })
        
        print(f"    ✅ 评估完成")
        print(f"    总体得分: {report.overall_score:.2f}/100")
        print(f"    创新性: {report.innovation_score:.2f}/100")
        print(f"    可用性: {report.usability_score:.2f}/100")
        print(f"    质量: {report.quality_score:.2f}/100")
    
    return evaluation_results


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🎯 SkillFactory创建 + 质量评估测试")
    print("=" * 60)
    
    try:
        # 步骤1: 创建Skill
        skills_results = await create_skill_with_factory()
        
        # 步骤2: 评估Skill
        evaluation_results = await evaluate_skills(skills_results)
        
        # 总结
        print("\n" + "=" * 60)
        print("📊 评估结果总结")
        print("=" * 60)
        
        for eval_result in evaluation_results:
            name = eval_result["name"]
            report = eval_result["report"]
            print(f"\n{name}:")
            print(f"  总体得分: {report.overall_score:.2f}/100")
            print(f"  创新性: {report.innovation_score:.2f}/100")
            print(f"  可用性: {report.usability_score:.2f}/100")
            print(f"  质量: {report.quality_score:.2f}/100")
        
        print("\n" + "=" * 60)
        print("✅ 完成!")
        print("=" * 60)
        
    except ImportError as e:
        print(f"\n❌ 导入错误: {e}")
        print("请确保 skill_factory 模块已正确安装")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
