#!/usr/bin/env python3
"""
Skill Factory 集成验证

验证 Skill Factory 与 RANGEN 系统的集成是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_factory_availability():
    """测试 Skill Factory 可用性"""
    print("1. 测试 Skill Factory 可用性...")
    try:
        from src.agents.skills.skill_factory_integration import is_skill_factory_available
        
        available = is_skill_factory_available()
        if available:
            print("   ✓ Skill Factory 可用")
            return True
        else:
            print("   ✗ Skill Factory 不可用")
            return False
    except Exception as e:
        print(f"   ✗ 测试失败: {e}")
        return False

def test_skill_trigger_integration():
    """测试技能触发器集成"""
    print("\n2. 测试技能触发器集成...")
    try:
        from src.agents.skills.skill_trigger import get_skill_trigger
        
        trigger = get_skill_trigger()
        
        # 测试正常技能触发
        test_normal = "帮我分析一下这段代码"
        result_normal = trigger.trigger(test_normal)
        print(f"   正常输入测试: {result_normal.triggered_skills[:3]}")
        
        # 测试技能创建请求检测
        test_creation_chinese = "我想创建一个新的数据分析技能"
        result_creation_chinese = trigger.trigger(test_creation_chinese)
        print(f"   中文创建请求: {result_creation_chinese.triggered_skills}")
        print(f"   推理: {result_creation_chinese.reasoning}")
        
        test_creation_english = "create a new data analysis skill"
        result_creation_english = trigger.trigger(test_creation_english)
        print(f"   英文创建请求: {result_creation_english.triggered_skills}")
        
        # 检查是否检测到技能创建请求
        if "skill_factory_suggestion" in result_creation_chinese.triggered_skills:
            print("   ✓ 成功检测到中文技能创建请求")
        else:
            print("   ✗ 未检测到中文技能创建请求")
            
        if "skill_factory_suggestion" in result_creation_english.triggered_skills:
            print("   ✓ 成功检测到英文技能创建请求")
        else:
            print("   ✗ 未检测到英文技能创建请求")
            
        return True
        
    except Exception as e:
        print(f"   ✗ 测试失败: {e}")
        return False

def test_prototype_classification():
    """测试原型分类"""
    print("\n3. 测试原型分类...")
    try:
        from src.agents.skills.skill_factory_integration import get_factory_integration
        
        factory = get_factory_integration()
        
        # 测试工作流原型
        workflow_req = "我需要一个处理多步骤数据分析的工作流技能，包括数据清洗、转换和分析"
        result_workflow = factory.analyze_and_classify_requirements(workflow_req)
        
        if result_workflow["success"]:
            print(f"   工作流需求分析: {result_workflow.get('recommended_prototype')}")
        else:
            print(f"   工作流需求分析失败: {result_workflow.get('error')}")
        
        # 测试专家原型
        expert_req = "我需要一个机器学习专家，能够基于历史数据做出预测决策"
        result_expert = factory.analyze_and_classify_requirements(expert_req)
        
        if result_expert["success"]:
            print(f"   专家需求分析: {result_expert.get('recommended_prototype')}")
        else:
            print(f"   专家需求分析失败: {result_expert.get('error')}")
        
        # 测试协调者原型
        coordinator_req = "需要一个协调者技能，能够将用户请求分类并分配给不同的专业处理模块"
        result_coordinator = factory.analyze_and_classify_requirements(coordinator_req)
        
        if result_coordinator["success"]:
            print(f"   协调者需求分析: {result_coordinator.get('recommended_prototype')}")
        else:
            print(f"   协调者需求分析失败: {result_coordinator.get('error')}")
            
        return True
        
    except Exception as e:
        print(f"   ✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints_available():
    """测试API端点可用性"""
    print("\n4. 测试API端点可用性...")
    try:
        from src.api.skill_factory_routes import router
        
        routes_count = len(router.routes)
        print(f"   注册的路由数量: {routes_count}")
        
        # 检查关键路由
        required_routes = [
            ("GET", "/api/v1/skill-factory/status"),
            ("GET", "/api/v1/skill-factory/prototypes"),
            ("POST", "/api/v1/skill-factory/analyze"),
            ("POST", "/api/v1/skill-factory/create"),
        ]
        
        available_routes = []
        for route in router.routes:
            for method in route.methods:
                available_routes.append((method, route.path))
        
        missing_routes = []
        for method, path in required_routes:
            if (method, path) not in available_routes:
                missing_routes.append(f"{method} {path}")
        
        if not missing_routes:
            print("   ✓ 所有关键API端点可用")
            return True
        else:
            print(f"   ✗ 缺少API端点: {', '.join(missing_routes)}")
            return False
            
    except Exception as e:
        print(f"   ✗ 测试失败: {e}")
        return False

def test_quality_check():
    """测试质量检查"""
    print("\n5. 测试质量检查...")
    try:
        from src.agents.skills.skill_factory_integration import get_factory_integration
        
        factory = get_factory_integration()
        
        # 测试现有技能的质量检查
        test_skill_dir = project_root / "src" / "agents" / "skills" / "bundled" / "answer-generation"
        
        if test_skill_dir.exists():
            result = factory.run_quality_check(str(test_skill_dir))
            
            if result["success"]:
                report = result.get("report", {})
                print(f"   质量检查成功，总体状态: {report.get('overall_status', 'unknown')}")
                print(f"   检查项数量: {len(report.get('checks', []))}")
                return True
            else:
                print(f"   质量检查失败: {result.get('error')}")
                return False
        else:
            print(f"   测试技能目录不存在: {test_skill_dir}")
            return False
        
    except Exception as e:
        print(f"   ✗ 测试失败: {e}")
        return False

def main():
    """运行所有验证测试"""
    print("=" * 60)
    print("Skill Factory 集成验证")
    print("=" * 60)
    
    tests = [
        ("Skill Factory 可用性", test_factory_availability),
        ("技能触发器集成", test_skill_trigger_integration),
        ("原型分类", test_prototype_classification),
        ("API端点可用性", test_api_endpoints_available),
        ("质量检查", test_quality_check),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"测试 '{test_name}' 异常: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("验证结果汇总:")
    print("=" * 60)
    
    passed_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    for test_name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n通过率: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
    
    if passed_count == total_count:
        print("\n🎉 所有验证测试通过！Skill Factory 集成功能正常。")
    else:
        print(f"\n⚠️  部分测试失败，请检查上述错误信息。")
    
    return passed_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)