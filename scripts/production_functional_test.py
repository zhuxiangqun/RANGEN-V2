#!/usr/bin/env python3
"""
生产环境功能测试脚本
验证API密钥配置和Agent实际执行性能
"""

import sys
import os
import asyncio
import time
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 确保使用正常模式
os.environ['USE_LIGHTWEIGHT_RAG'] = 'false'

try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("⚠️ dotenv模块不可用，将直接使用环境变量")

async def test_api_keys():
    """测试API密钥配置"""
    print("🔑 测试API密钥配置...")
    print("-" * 40)

    results = {}

    # 检查API密钥
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')

    results['DEEPSEEK_API_KEY'] = {
        'configured': bool(deepseek_key),
        'length': len(deepseek_key) if deepseek_key else 0,
        'masked': f"{deepseek_key[:8]}..." if deepseek_key else None
    }

    results['OPENAI_API_KEY'] = {
        'configured': bool(openai_key),
        'length': len(openai_key) if openai_key else 0,
        'masked': f"{openai_key[:8]}..." if openai_key else None
    }

    for key_name, info in results.items():
        status = "✅ 已配置" if info['configured'] else "❌ 未配置"
        length_info = f"({info['length']}字符)" if info['configured'] else ""
        print(f"  {key_name}: {status} {length_info}")
        if info['configured'] and info.get('masked'):
            print(f"    密钥前缀: {info['masked']}")

    return results

async def test_agent_initialization():
    """测试Agent初始化"""
    print("\n🏗️ 测试Agent初始化...")
    print("-" * 40)

    results = {}

    try:
        from src.agents.rag_agent import RAGExpert
        rag_agent = RAGExpert()
        results['RAGExpert'] = {
            'success': True,
            'lightweight_mode': getattr(rag_agent, '_lightweight_mode', False),
            'config_center': hasattr(rag_agent, 'config_center'),
            'threshold_manager': hasattr(rag_agent, 'threshold_manager')
        }
        print("✅ RAGExpert初始化成功")
    except Exception as e:
        results['RAGExpert'] = {'success': False, 'error': str(e)}
        print(f"❌ RAGExpert初始化失败: {e}")

    try:
        from src.agents.reasoning_expert import ReasoningExpert
        reasoning_agent = ReasoningExpert()
        results['ReasoningExpert'] = {
            'success': True,
            'config_center': hasattr(reasoning_agent, 'config_center'),
            'threshold_manager': hasattr(reasoning_agent, 'threshold_manager'),
            'parallel_executor': hasattr(reasoning_agent, '_parallel_executor')
        }
        print("✅ ReasoningExpert初始化成功")
    except Exception as e:
        results['ReasoningExpert'] = {'success': False, 'error': str(e)}
        print(f"❌ ReasoningExpert初始化失败: {e}")

    try:
        from src.agents.agent_coordinator import AgentCoordinator
        coordinator = AgentCoordinator()
        results['AgentCoordinator'] = {
            'success': True,
            'config_center': hasattr(coordinator, 'config_center'),
            'threshold_manager': hasattr(coordinator, 'threshold_manager')
        }
        print("✅ AgentCoordinator初始化成功")
    except Exception as e:
        results['AgentCoordinator'] = {'success': False, 'error': str(e)}
        print(f"❌ AgentCoordinator初始化失败: {e}")

    return results

async def test_agent_execution():
    """测试Agent执行性能"""
    print("\n🧪 测试Agent执行性能...")
    print("-" * 40)

    results = {}

    # 测试用例
    test_cases = [
        {
            'agent': 'RAGExpert',
            'query': '什么是机器学习？',
            'context': {'use_cache': False, 'use_parallel': True}
        },
        {
            'agent': 'ReasoningExpert',
            'query': '分析机器学习的优缺点',
            'context': {'reasoning_type': 'causal', 'complexity': 'moderate'}
        },
        {
            'agent': 'AgentCoordinator',
            'query': '如何优化系统性能？',
            'context': {'priority': 'high', 'complexity': 'high'}
        }
    ]

    agents = {}
    try:
        from src.agents.rag_agent import RAGExpert
        agents['RAGExpert'] = RAGExpert()
    except:
        pass

    try:
        from src.agents.reasoning_expert import ReasoningExpert
        agents['ReasoningExpert'] = ReasoningExpert()
    except:
        pass

    try:
        from src.agents.agent_coordinator import AgentCoordinator
        agents['AgentCoordinator'] = AgentCoordinator()
    except:
        pass

    for test_case in test_cases:
        agent_name = test_case['agent']
        if agent_name not in agents:
            results[agent_name] = {'success': False, 'error': 'Agent未初始化'}
            print(f"❌ {agent_name}: Agent未初始化")
            continue

        agent = agents[agent_name]
        context = test_case['context'].copy()
        context['query'] = test_case['query']

        try:
            start_time = time.time()
            result = await agent.execute(context)
            execution_time = time.time() - start_time

            results[agent_name] = {
                'success': result.success,
                'execution_time': execution_time,
                'error': result.error if not result.success else None,
                'has_data': result.data is not None,
                'data_type': type(result.data).__name__ if result.data else None
            }

            status = "✅" if result.success else "❌"
            print(f"{status} {agent_name}: {execution_time:.2f}秒")

            if not result.success:
                print(f"    错误: {result.error}")

        except Exception as e:
            results[agent_name] = {'success': False, 'error': str(e)}
            print(f"❌ {agent_name}: 执行异常 - {e}")

    return results

async def test_unified_centers():
    """测试统一中心系统"""
    print("\n🎛️ 测试统一中心系统...")
    print("-" * 40)

    results = {}

    try:
        from src.utils.unified_centers import get_unified_config_center
        config_center = get_unified_config_center()
        results['config_center'] = {
            'success': True,
            'type': type(config_center).__name__
        }
        print("✅ 配置中心初始化成功")
    except Exception as e:
        results['config_center'] = {'success': False, 'error': str(e)}
        print(f"❌ 配置中心初始化失败: {e}")

    try:
        from src.utils.unified_threshold_manager import get_unified_threshold_manager
        threshold_manager = get_unified_threshold_manager()
        results['threshold_manager'] = {
            'success': True,
            'type': type(threshold_manager).__name__
        }
        print("✅ 阈值管理器初始化成功")
    except Exception as e:
        results['threshold_manager'] = {'success': False, 'error': str(e)}
        print(f"❌ 阈值管理器初始化失败: {e}")

    return results

async def generate_test_report(results):
    """生成测试报告"""
    print("\n📊 生成测试报告...")
    print("-" * 40)

    # 保存详细结果
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_file = f"production_test_results_{timestamp}.json"

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ 详细结果已保存到: {report_file}")

    # 生成摘要报告
    print("\n📋 测试摘要:")
    print("-" * 40)

    # API密钥状态
    api_keys = results.get('api_keys', {})
    configured_keys = sum(1 for k, v in api_keys.items() if v.get('configured'))
    print(f"🔑 API密钥: {configured_keys}/2 已配置")

    # Agent初始化
    agents = results.get('agents', {})
    initialized_agents = sum(1 for k, v in agents.items() if v.get('success'))
    print(f"🏗️ Agent初始化: {initialized_agents}/3 成功")

    # 统一中心
    centers = results.get('centers', {})
    working_centers = sum(1 for k, v in centers.items() if v.get('success'))
    print(f"🎛️ 统一中心: {working_centers}/2 正常")

    # Agent执行
    executions = results.get('executions', {})
    successful_executions = sum(1 for k, v in executions.items() if v.get('success'))
    print(f"🧪 Agent执行: {successful_executions}/3 成功")

    # 总体评估
    total_components = 2 + 3 + 2 + 3  # API keys + agents + centers + executions
    working_components = configured_keys + initialized_agents + working_centers + successful_executions

    success_rate = working_components / total_components * 100

    print(f"🎯 总体成功率: {success_rate:.1f}%")
    if success_rate >= 80:
        print("🎉 生产环境测试通过！系统运行正常")
    elif success_rate >= 60:
        print("⚠️ 生产环境测试基本通过，但存在一些问题需要关注")
    else:
        print("❌ 生产环境测试失败，需要修复关键问题")

    return report_file

async def main():
    """主测试流程"""
    print("🚀 开始生产环境功能测试")
    print("=" * 60)
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    print("=" * 60)

    results = {}

    try:
        # 1. 测试API密钥配置
        results['api_keys'] = await test_api_keys()

        # 2. 测试Agent初始化
        results['agents'] = await test_agent_initialization()

        # 3. 测试统一中心系统
        results['centers'] = await test_unified_centers()

        # 4. 测试Agent执行性能
        results['executions'] = await test_agent_execution()

        # 5. 生成测试报告
        report_file = await generate_test_report(results)

        print(f"\n✅ 生产环境测试完成！")
        print(f"📄 详细报告: {report_file}")

    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
