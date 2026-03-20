#!/usr/bin/env python3
"""
Skill Factory 技能创建测试

测试使用 Skill Factory 创建新技能的完整流程
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_workflow_skill_creation():
    """测试创建工作流技能"""
    print("1. 测试创建工作流技能...")
    
    try:
        from src.agents.skills.skill_factory_integration import get_factory_integration
        
        factory = get_factory_integration()
        
        # 创建工作流技能需求
        workflow_requirements = {
            "name": "data-analysis-workflow",
            "description": "多步骤数据分析工作流，包括数据清洗、转换、分析和可视化",
            "use_cases": [
                "处理结构化数据",
                "生成分析报告", 
                "数据可视化"
            ],
            "target_users": ["数据分析师", "业务分析师", "数据科学家"],
            "complexity": "high",
            "tools_needed": ["pandas", "numpy", "matplotlib", "scikit-learn"],
            "integration_points": ["数据源API", "数据库", "报表系统"]
        }
        
        print(f"   技能名称: {workflow_requirements['name']}")
        print(f"   技能描述: {workflow_requirements['description']}")
        
        result = factory.create_and_register_skill(
            workflow_requirements,
            workflow_requirements["name"]
        )
        
        if result["success"]:
            print(f"   ✓ 技能创建成功")
            print(f"   原型类型: {result.get('prototype_type')}")
            print(f"   技能目录: {result.get('skill_dir')}")
            
            # 验证技能文件
            skill_dir = Path(result.get("skill_dir", ""))
            if skill_dir.exists():
                skill_yaml = skill_dir / "skill.yaml"
                skill_md = skill_dir / "SKILL.md"
                
                if skill_yaml.exists():
                    print(f"   ✓ skill.yaml 文件存在")
                    # 读取并显示部分内容
                    with open(skill_yaml, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(f"   YAML文件大小: {len(content)} 字符")
                
                if skill_md.exists():
                    print(f"   ✓ SKILL.md 文件存在")
                
                return True
            else:
                print(f"   ✗ 技能目录不存在: {skill_dir}")
                return False
        else:
            print(f"   ✗ 技能创建失败: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"   ✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_expert_skill_creation():
    """测试创建专家技能"""
    print("\n2. 测试创建专家技能...")
    
    try:
        from src.agents.skills.skill_factory_integration import get_factory_integration
        
        factory = get_factory_integration()
        
        # 创建专家技能需求
        expert_requirements = {
            "name": "ml-prediction-expert",
            "description": "机器学习预测专家，基于历史数据构建预测模型并提供决策建议",
            "use_cases": [
                "销售预测",
                "客户流失预测",
                "风险评分"
            ],
            "target_users": ["数据科学家", "业务分析师", "风险经理"],
            "complexity": "high",
            "tools_needed": ["scikit-learn", "tensorflow", "pandas", "numpy"],
            "integration_points": ["数据仓库", "模型部署平台", "监控系统"]
        }
        
        print(f"   技能名称: {expert_requirements['name']}")
        print(f"   技能描述: {expert_requirements['description']}")
        
        result = factory.create_and_register_skill(
            expert_requirements,
            expert_requirements["name"]
        )
        
        if result["success"]:
            print(f"   ✓ 技能创建成功")
            print(f"   原型类型: {result.get('prototype_type')}")
            print(f"   技能目录: {result.get('skill_dir')}")
            
            # 验证技能文件
            skill_dir = Path(result.get("skill_dir", ""))
            if skill_dir.exists():
                print(f"   ✓ 技能目录存在: {skill_dir}")
                
                # 运行质量检查
                quality_result = factory.run_quality_check(str(skill_dir))
                if quality_result["success"]:
                    print(f"   ✓ 质量检查成功")
                    print(f"   检查状态: {'通过' if quality_result.get('passed') else '未通过'}")
                else:
                    print(f"   ✗ 质量检查失败: {quality_result.get('error')}")
                
                return True
            else:
                print(f"   ✗ 技能目录不存在")
                return False
        else:
            print(f"   ✗ 技能创建失败: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"   ✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prototype_analysis():
    """测试原型分析功能"""
    print("\n3. 测试原型分析功能...")
    
    try:
        from src.agents.skills.skill_factory_integration import get_factory_integration
        
        factory = get_factory_integration()
        
        # 测试不同需求的原型分析
        test_cases = [
            {
                "name": "工作流需求",
                "text": "需要一个多步骤数据处理流程，包括数据验证、清洗、转换和加载到数据库"
            },
            {
                "name": "专家需求", 
                "text": "需要一个机器学习专家，能够选择最佳算法并调参优化模型性能"
            },
            {
                "name": "协调者需求",
                "text": "需要一个协调者，将用户请求分类并分配给不同的处理模块"
            },
            {
                "name": "质量门需求",
                "text": "需要一个质量检查工具，验证代码质量、安全性和性能"
            },
            {
                "name": "MCP集成需求",
                "text": "需要集成外部API工具，调用天气数据API并格式化结果"
            }
        ]
        
        for test_case in test_cases:
            result = factory.analyze_and_classify_requirements(test_case["text"])
            
            if result["success"]:
                print(f"   {test_case['name']}: {result.get('recommended_prototype')} (置信度: {result.get('confidence', 0):.2f})")
            else:
                print(f"   {test_case['name']}: 分析失败 - {result.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ 测试失败: {e}")
        return False

def test_skill_trigger_detection():
    """测试技能触发器检测"""
    print("\n4. 测试技能触发器检测...")
    
    try:
        from src.agents.skills.skill_trigger import get_skill_trigger
        
        trigger = get_skill_trigger()
        
        test_inputs = [
            ("我想创建一个数据分析工作流", True),
            ("帮我开发一个机器学习预测模型", True),
            ("需要添加一个新的技能来处理图片", True),
            ("分析一下这段代码的性能", False),
            ("帮我查一下资料", False),
            ("create a new skill for data visualization", True),
            ("add skill to process documents", True),
            ("how to use existing skills", False)
        ]
        
        correct_detections = 0
        total_tests = len(test_inputs)
        
        for input_text, should_detect in test_inputs:
            result = trigger.trigger(input_text)
            detected = "skill_factory_suggestion" in result.triggered_skills
            
            if detected == should_detect:
                correct_detections += 1
                status = "✓"
            else:
                status = "✗"
            
            print(f"   {status} '{input_text}' -> 检测: {detected}, 期望: {should_detect}")
        
        accuracy = correct_detections / total_tests
        print(f"   准确率: {correct_detections}/{total_tests} ({accuracy:.1%})")
        
        return accuracy >= 0.8  # 至少80%准确率
        
    except Exception as e:
        print(f"   ✗ 测试失败: {e}")
        return False

def test_factory_statistics():
    """测试工厂统计信息"""
    print("\n5. 测试工厂统计信息...")
    
    try:
        from src.agents.skills.skill_factory_integration import get_factory_integration
        
        factory = get_factory_integration()
        
        result = factory.get_statistics()
        
        if result["success"]:
            stats = result.get("statistics", {})
            print(f"   已生成技能总数: {stats.get('total_generated', 0)}")
            print(f"   已注册技能总数: {stats.get('total_registered', 0)}")
            
            if stats.get("generated_skills"):
                print(f"   生成的技能: {', '.join(stats['generated_skills'][:5])}")
            
            if stats.get("registered_skills"):
                print(f"   注册的技能: {', '.join(stats['registered_skills'][:5])}")
            
            return True
        else:
            print(f"   ✗ 获取统计信息失败: {result.get('error')}")
            return False
        
    except Exception as e:
        print(f"   ✗ 测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 70)
    print("Skill Factory 技能创建测试")
    print("=" * 70)
    
    tests = [
        ("创建工作流技能", test_workflow_skill_creation),
        ("创建专家技能", test_expert_skill_creation),
        ("原型分析功能", test_prototype_analysis),
        ("技能触发器检测", test_skill_trigger_detection),
        ("工厂统计信息", test_factory_statistics),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{test_name}:")
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"测试 '{test_name}' 异常: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 70)
    print("测试结果汇总:")
    print("=" * 70)
    
    passed_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    for test_name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n通过率: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
    
    if passed_count == total_count:
        print("\n🎉 所有技能创建测试通过！Skill Factory 功能完整可用。")
    else:
        print(f"\n⚠️  部分测试失败，请检查上述错误信息。")
    
    return passed_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)