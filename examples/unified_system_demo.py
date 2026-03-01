#!/usr/bin/env python3
"""
统一动态配置系统演示
展示如何利用现有的动态调整机制，扩展现有功能，统一接口
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.unified_dynamic_config_manager import get_unified_dynamic_config
from src.utils.intelligent_parameter_manager import get_intelligent_parameter_manager
from src.utils.unified_agent_config_interface import get_unified_agent_config_interface, AgentConfigContext

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demo_unified_dynamic_config():
    """演示统一动态配置管理器"""
    print("\n" + "="*60)
    print("演示：统一动态配置管理器")
    print("="*60)
    
    try:
        # 获取统一配置管理器实例
        unified_config = get_unified_dynamic_config()
        print("✅ 统一动态配置管理器初始化成功")
        
        # 演示基础动态参数获取
        print("\n📊 基础动态参数:")
        print(f"  上下文限制: {unified_config.get_dynamic_context_limit()}")
        print(f"  句子限制: {unified_config.get_dynamic_sentence_limit()}")
        print(f"  内容限制: {unified_config.get_dynamic_content_limit()}")
        print(f"  最小长度: {unified_config.get_dynamic_min_length()}")
        print(f"  相似度阈值: {unified_config.get_dynamic_similarity_threshold()}")
        
        # 演示查询复杂度更新
        print("\n🔄 更新查询复杂度...")
        unified_config.update_query_complexity(get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")))
        unified_config.update_query_type("quantitative")
        
        # 演示智能参数获取
        context = {
            'query_complexity': get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")),
            'query_type': 'quantitative',
            'system_load': 0.6
        }
        
        print("\n🧠 智能参数获取 (高复杂度查询):")
        intelligent_context_limit = unified_config.get_intelligent_parameter('context_limit', context)
        intelligent_sentence_limit = unified_config.get_intelligent_parameter('sentence_limit', context)
        print(f"  智能上下文限制: {intelligent_context_limit}")
        print(f"  智能句子限制: {intelligent_sentence_limit}")
        
        # 演示自适应参数集合
        print("\n🎯 自适应参数集合:")
        adaptive_params = unified_config.get_adaptive_parameters(context)
        for param_name, param_value in adaptive_params.items():
            print(f"  {param_name}: {param_value}")
        
        # 演示性能记录
        print("\n⏱️ 记录执行时间...")
        unified_config.record_execution_time(2.5)
        unified_config.record_execution_time(1.8)
        unified_config.record_execution_time(3.2)
        
        # 获取性能统计
        performance_stats = unified_config.get_performance_stats()
        print(f"  性能统计: {performance_stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ 统一动态配置管理器演示失败: {e}")
        return False

def demo_intelligent_parameter_manager():
    """演示智能参数管理器"""
    print("\n" + "="*60)
    print("演示：智能参数管理器")
    print("="*60)
    
    try:
        # 获取智能参数管理器实例
        intelligent_params = get_intelligent_parameter_manager()
        print("✅ 智能参数管理器初始化成功")
        
        # 演示参数获取
        print("\n📋 参数获取:")
        context_limit = intelligent_params.get_parameter('context_limit')
        sentence_limit = intelligent_params.get_parameter('sentence_limit')
        print(f"  上下文限制: {context_limit}")
        print(f"  句子限制: {sentence_limit}")
        
        # 演示上下文相关参数获取
        from src.utils.intelligent_parameter_manager import ParameterContext
        
        param_context = ParameterContext(
            query_type="quantitative",
            query_complexity=0.9,
            system_load=0.7
        )
        
        print("\n🧠 上下文相关参数获取:")
        contextual_context_limit = intelligent_params.get_parameter('context_limit', param_context)
        contextual_min_length = intelligent_params.get_parameter('min_length', param_context)
        print(f"  上下文相关上下文限制: {contextual_context_limit}")
        print(f"  上下文相关最小长度: {contextual_min_length}")
        
        # 演示参数设置
        print("\n⚙️ 设置新参数...")
        intelligent_params.set_parameter('custom_threshold', 0.85, 
                                      min_value=0.1, max_value=get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")), 
                                      description="自定义阈值参数")
        
        # 获取参数摘要
        param_summary = intelligent_params.get_parameter_summary()
        print(f"  参数摘要: {param_summary}")
        
        return True
        
    except Exception as e:
        print(f"❌ 智能参数管理器演示失败: {e}")
        return False

def demo_unified_agent_config_interface():
    """演示统一智能体配置接口"""
    print("\n" + "="*60)
    print("演示：统一智能体配置接口")
    print("="*60)
    
    try:
        # 获取统一智能体配置接口实例
        agent_config_interface = get_unified_agent_config_interface()
        print("✅ 统一智能体配置接口初始化成功")
        
        # 演示智能体配置获取
        print("\n🤖 获取智能体配置:")
        
        # 创建配置上下文
        agent_context = AgentConfigContext(
            agent_name="lead_researcher",
            task_type="research",
            query_complexity=get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")),
            system_load=0.6
        )
        
        lead_researcher_config = agent_config_interface.get_agent_config("lead_researcher", agent_context)
        print(f"  主研究员配置: {lead_researcher_config}")
        
        # 演示不同复杂度的配置
        print("\n🔄 不同复杂度的配置:")
        
        simple_context = AgentConfigContext(
            agent_name="search_agent",
            task_type="search",
            query_complexity=0.2,
            system_load=get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold"))
        )
        
        complex_context = AgentConfigContext(
            agent_name="search_agent",
            task_type="search",
            query_complexity=0.9,
            system_load=get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold"))
        )
        
        simple_config = agent_config_interface.get_agent_config("search_agent", simple_context)
        complex_config = agent_config_interface.get_agent_config("search_agent", complex_context)
        
        print(f"  简单查询配置: {simple_config}")
        print(f"  复杂查询配置: {complex_config}")
        
        # 演示性能更新
        print("\n⏱️ 更新智能体性能...")
        agent_config_interface.update_agent_performance("lead_researcher", 0.85, agent_context)
        
        # 获取优化建议
        print("\n💡 获取优化建议:")
        optimization_suggestions = agent_config_interface.get_agent_optimization_suggestions("lead_researcher")
        print(f"  优化建议数量: {len(optimization_suggestions)}")
        for suggestion in optimization_suggestions[:3]:  # 只显示前3个
            print(f"    - {suggestion}")
        
        # 获取综合摘要
        print("\n📊 获取综合摘要:")
        comprehensive_summary = agent_config_interface.get_comprehensive_agent_summary("lead_researcher")
        print(f"  摘要状态: {'成功' if 'error' not in comprehensive_summary else '失败'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 统一智能体配置接口演示失败: {e}")
        return False

def demo_system_integration():
    """演示系统集成"""
    print("\n" + "="*60)
    print("演示：系统集成")
    print("="*60)
    
    try:
        print("🔄 测试系统集成...")
        
        # 获取所有组件
        unified_config = get_unified_dynamic_config()
        intelligent_params = get_intelligent_parameter_manager()
        agent_config_interface = get_unified_agent_config_interface()
        
        print("✅ 所有组件初始化成功")
        
        # 测试参数一致性
        print("\n🔍 测试参数一致性:")
        
        # 从不同组件获取相同参数
        context_limit_1 = unified_config.get_dynamic_context_limit()
        context_limit_2 = intelligent_params.get_parameter('context_limit')
        
        print(f"  统一配置管理器上下文限制: {context_limit_1}")
        print(f"  智能参数管理器上下文限制: {context_limit_2}")
        print(f"  参数一致: {'✅' if context_limit_1 == context_limit_2 else '❌'}")
        
        # 测试智能参数获取的一致性
        context = {'query_complexity': 0.7, 'query_type': 'research', 'system_load': get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))}
        
        intelligent_context_limit_1 = unified_config.get_intelligent_parameter('context_limit', context)
        from src.utils.intelligent_parameter_manager import ParameterContext
        intelligent_context_limit_2 = intelligent_params.get_parameter('context_limit', 
            ParameterContext(query_type='research', query_complexity=0.7, system_load=get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))))
        
        print(f"  统一配置管理器智能上下文限制: {intelligent_context_limit_1}")
        print(f"  智能参数管理器智能上下文限制: {intelligent_context_limit_2}")
        print(f"  智能参数一致: {'✅' if intelligent_context_limit_1 == intelligent_context_limit_2 else '❌'}")
        
        # 测试智能体配置接口
        agent_context = AgentConfigContext(
            agent_name="test_agent",
            task_type="test",
            query_complexity=0.6,
            system_load=0.4
        )
        
        agent_config = agent_config_interface.get_agent_config("test_agent", agent_context)
        print(f"\n  测试智能体配置: {agent_config}")
        
        print("\n✅ 系统集成测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 系统集成演示失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 统一动态配置系统演示开始")
    print("本演示展示如何利用现有的动态调整机制，扩展现有功能，统一接口")
    
    # 运行各个演示
    demos = [
        ("统一动态配置管理器", demo_unified_dynamic_config),
        ("智能参数管理器", demo_intelligent_parameter_manager),
        ("统一智能体配置接口", demo_unified_agent_config_interface),
        ("系统集成", demo_system_integration)
    ]
    
    results = []
    for demo_name, demo_func in demos:
        try:
            result = demo_func()
            results.append((demo_name, result))
        except Exception as e:
            print(f"❌ {demo_name} 演示异常: {e}")
            results.append((demo_name, False))
    
    # 显示结果摘要
    print("\n" + "="*60)
    print("演示结果摘要")
    print("="*60)
    
    success_count = 0
    for demo_name, result in results:
        status = "✅ 成功" if result else "❌ 失败"
        print(f"  {demo_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n总体结果: {success_count}/{len(results)} 个演示成功")
    
    if success_count == len(results):
        print("🎉 所有演示都成功完成！系统修复成功！")
    else:
        print("⚠️ 部分演示失败，需要进一步检查")
    
    return success_count == len(results)

if __name__ == "__main__":
    main()
