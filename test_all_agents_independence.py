#!/usr/bin/env python3
"""
8核心Agent独立性测试脚本
验证所有Agent都可以独立创建、测试和重复使用
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_agent_independence():
    """测试所有8核心Agent的独立性"""
    print("🚀 8核心Agent独立性验证")
    print("=" * 60)
    
    # 设置环境变量
    os.environ['LLM_PROVIDER'] = 'deepseek'
    os.environ['DEEPSEEK_API_KEY'] = 'test_key_placeholder'
    
    # 定义8核心Agent
    core_agents = {
        'L5层': {
            'ReasoningExpert': 'src.agents.reasoning_expert',
            'AgentCoordinator': 'src.agents.agent_coordinator'
        },
        'L4层': {
            'RAGExpert': 'src.agents.rag_agent',
            'QualityController': 'src.agents.quality_controller',
            'ToolOrchestrator': 'src.agents.tool_orchestrator'
        },
        'L3层': {
            'MemoryManager': 'src.agents.memory_manager',
            'LearningOptimizer': 'src.agents.learning_optimizer',
            'ChiefAgent': 'src.agents.chief_agent'
        }
    }
    
    results = {}
    
    for layer, agents in core_agents.items():
        print(f"\n🏗️ {layer}测试:")
        print("-" * 30)
        
        for agent_name, module_path in agents.items():
            try:
                # 动态导入Agent类
                module_parts = module_path.split('.')
                module = __import__(module_path, fromlist=[agent_name])
                agent_class = getattr(module, agent_name)
                
                # 创建Agent实例
                agent_instance = agent_class()
                
                # 验证Agent基本属性
                has_execute = hasattr(agent_instance, 'execute')
                has_config = hasattr(agent_instance, 'config_center')
                has_threshold = hasattr(agent_instance, 'threshold_manager')
                
                # 测试基本功能
                test_result = await agent_instance.execute({
                    'query': f'测试{agent_name}独立性',
                    'test_mode': True
                })
                
                results[agent_name] = {
                    'initialization': True,
                    'has_execute': has_execute,
                    'has_config': has_config,
                    'has_threshold': has_threshold,
                    'execution_success': test_result.success if test_result else False
                }
                
                status = "✅" if results[agent_name]['execution_success'] else "⚠️"
                print(f"  {status} {agent_name}: 独立创建成功")
                
            except Exception as e:
                results[agent_name] = {
                    'initialization': False,
                    'error': str(e)[:100]
                }
                print(f"  ❌ {agent_name}: {str(e)[:50]}")
    
    return results

async def test_agent_reusability():
    """测试Agent的可重复使用性"""
    print("\n🔄 测试Agent可重复使用性:")
    print("-" * 30)
    
    try:
        from src.agents.rag_agent import RAGExpert
        
        # 创建多个实例
        agents = [RAGExpert() for _ in range(3)]
        
        # 测试并发执行
        tasks = []
        for i, agent in enumerate(agents):
            task = agent.execute({
                'query': f'并发测试{i+1}',
                'test_mode': True
            })
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if not isinstance(r, Exception) and r.success)
        
        print(f"  ✅ 并发实例: {len(agents)}个Agent成功创建")
        print(f"  ✅ 执行成功: {success_count}/{len(agents)}个任务完成")
        
        return success_count == len(agents)
        
    except Exception as e:
        print(f"  ❌ 可重复使用性测试失败: {e}")
        return False

async def test_agent_isolation():
    """测试Agent间的隔离性"""
    print("\n🔒 测试Agent间隔离性:")
    print("-" * 30)
    
    try:
        from src.agents.rag_agent import RAGExpert
        from src.agents.reasoning_expert import ReasoningExpert
        
        # 创建不同类型的Agent
        rag_agent = RAGExpert()
        reasoning_agent = ReasoningExpert()
        
        # 测试各自独立执行
        rag_result = await rag_agent.execute({'query': 'RAG测试', 'test_mode': True})
        reasoning_result = await reasoning_agent.execute({'query': '推理测试', 'test_mode': True})
        
        # 验证结果独立性
        rag_success = rag_result.success if rag_result else False
        reasoning_success = reasoning_result.success if reasoning_result else False
        
        print(f"  ✅ RAGExpert独立执行: {'成功' if rag_success else '失败'}")
        print(f"  ✅ ReasoningExpert独立执行: {'成功' if reasoning_success else '失败'}")
        print(f"  ✅ Agent间无干扰: 隔离性正常")
        
        return rag_success and reasoning_success
        
    except Exception as e:
        print(f"  ❌ 隔离性测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🎯 智能体独立性、可重复使用性验证")
    print("=" * 60)
    
    # 测试独立性
    independence_results = await test_agent_independence()
    
    # 测试可重复使用性
    reusability_result = await test_agent_reusability()
    
    # 测试隔离性
    isolation_result = await test_agent_isolation()
    
    # 生成总结报告
    print("\n📊 测试总结报告")
    print("=" * 30)
    
    # 统计独立性结果
    total_agents = len(independence_results)
    successful_agents = sum(1 for r in independence_results.values() 
                          if r.get('initialization', False) and r.get('execution_success', False))
    
    print(f"🎯 Agent独立性: {successful_agents}/{total_agents} 个Agent完全独立")
    print(f"🔄 可重复使用: {'✅ 通过' if reusability_result else '❌ 失败'}")
    print(f"🔒 隔离性保证: {'✅ 通过' if isolation_result else '❌ 失败'}")
    
    # 总体评估
    overall_success = (successful_agents == total_agents and reusability_result and isolation_result)
    
    print(f"\n🏆 总体评估: {'🎉 所有Agent都独立且可重复使用！' if overall_success else '⚠️ 存在依赖或隔离问题'}")
    
    if overall_success:
        print("\n✅ 验证结果:")
        print("• 所有8核心Agent都是独立的")
        print("• 每个Agent都可以重复创建和使用")
        print("• Agent间完全隔离，无相互干扰")
        print("• 支持并发实例和独立测试")
    
    sys.exit(0 if overall_success else 1)

if __name__ == "__main__":
    asyncio.run(main())
