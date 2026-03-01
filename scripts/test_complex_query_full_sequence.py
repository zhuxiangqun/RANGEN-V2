#!/usr/bin/env python3
"""
单独测试 Complex 查询完整智能体序列
用于验证 Chief Agent 协调完整智能体序列的功能
"""

import asyncio
import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
try:
    from dotenv import load_dotenv
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=False)
        print(f"✅ 已从 .env 文件加载环境变量: {env_path}")
except ImportError:
    print("⚠️  python-dotenv 未安装，无法加载 .env 文件")
except Exception as e:
    print(f"⚠️  加载 .env 文件失败: {e}")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_complex_query_full_sequence():
    """测试 Complex 查询完整智能体序列"""
    print("=" * 80)
    print("📝 测试: Complex 查询完整智能体序列")
    print("=" * 80)
    
    try:
        from src.core.langgraph_agent_nodes import AgentNodes
        from src.unified_research_system import UnifiedResearchSystem
        
        # 初始化系统和工作流
        print("🔧 初始化系统...")
        system = UnifiedResearchSystem()
        agent_nodes = AgentNodes(system=system)
        
        # 准备测试查询
        test_query = "Compare the economic policies of the United States and China in the 21st century"
        print(f"🔍 查询: {test_query}")
        
        # 准备测试状态（包含所有必需字段）
        initial_state: Dict[str, Any] = {
            'query': test_query,
            'route_path': 'complex',
            'complexity_score': 7.0,  # Complex 查询
            'needs_reasoning_chain': False,
            'context': {},
            'knowledge': [],
            'evidence': [],
            'errors': [],
            'metadata': {},
            'query_type': 'general',
            'user_context': {},
            'user_id': None,
            'session_id': None,
            'safety_check_passed': True,
            'sensitive_topics': [],
            'content_filter_applied': False,
            'answer': None,
            'final_answer': None,
            'confidence': 0.0,
            'citations': [],
            'task_complete': False,
            'error': None,
            'execution_time': 0.0,
            'retry_count': 0,
            'node_execution_times': {},
            'token_usage': {},
            'api_calls': {},
            'workflow_checkpoint_id': None
        }
        
        print(f"🔍 路由路径: {initial_state['route_path']}")
        print(f"🔍 复杂度: {initial_state['complexity_score']}")
        print("⏱️  开始执行完整智能体序列（超时：10分钟）...")
        
        start_time = time.time()
        
        # 执行 Chief Agent 节点（完整智能体序列）
        result_state = await asyncio.wait_for(
            agent_nodes.chief_agent_node(initial_state),
            timeout=600.0  # 10分钟超时
        )
        
        execution_time = time.time() - start_time
        
        # 详细日志输出
        print("\n" + "=" * 80)
        print("📊 执行结果")
        print("=" * 80)
        print(f"⏱️  执行时间: {execution_time:.2f}秒 ({execution_time/60:.2f}分钟)")
        print(f"✅ 任务完成: {result_state.get('task_complete', False)}")
        
        # 检查答案
        answer = result_state.get('answer', '')
        if answer:
            print(f"📝 答案长度: {len(answer)} 字符")
            print(f"📝 答案预览: {answer[:200]}...")
        else:
            print("⚠️ 答案为空")
        
        print(f"🎯 置信度: {result_state.get('confidence', 0):.2f}")
        
        # 检查错误信息
        if result_state.get('error'):
            print(f"❌ 错误信息: {result_state.get('error')}")
        if result_state.get('errors'):
            print(f"❌ 错误列表: {len(result_state.get('errors', []))} 个错误")
            for i, err in enumerate(result_state.get('errors', [])[:3]):
                print(f"   错误 {i+1}: {err.get('error', 'Unknown')[:100]}")
        
        # 检查是否使用了完整智能体序列
        metadata = result_state.get('metadata', {})
        coordination_result = metadata.get('coordination_result', {})
        
        if coordination_result.get('success'):
            print("✅ 完整智能体序列已启用")
            print(f"   协调置信度: {coordination_result.get('confidence', 0):.2f}")
            print(f"   处理时间: {coordination_result.get('processing_time', 0):.2f}秒")
        else:
            print("⚠️ 未检测到协调结果（可能使用了其他路径）")
        
        # 检查知识来源
        knowledge = result_state.get('knowledge', [])
        evidence = result_state.get('evidence', [])
        print(f"📚 知识来源: {len(knowledge)} 条")
        print(f"📄 证据: {len(evidence)} 条")
        
        # 验证结果
        success = (
            result_state.get('task_complete', False) and
            result_state.get('answer') is not None and
            len(result_state.get('answer', '')) > 0
        )
        
        print("\n" + "=" * 80)
        print("📊 测试总结")
        print("=" * 80)
        print(f"测试状态: {'✅ 通过' if success else '❌ 失败'}")
        print(f"执行时间: {execution_time:.2f}秒")
        print(f"任务完成: {result_state.get('task_complete', False)}")
        print(f"有答案: {result_state.get('answer') is not None}")
        print(f"答案长度: {len(result_state.get('answer', ''))} 字符")
        
        if not success:
            print("\n💡 可能原因:")
            if not result_state.get('task_complete', False):
                print("   - 任务未完成，可能遇到错误")
            if not result_state.get('answer'):
                print("   - 未生成答案")
            if result_state.get('error'):
                print(f"   - 错误: {result_state.get('error')}")
        
        return success
        
    except asyncio.TimeoutError:
        print("❌ 测试超时（10分钟）")
        print("💡 可能原因:")
        print("   - 网络连接慢")
        print("   - LLM API 响应慢")
        print("   - 完整智能体序列执行时间过长")
        print("💡 解决方案:")
        print("   - 检查网络连接")
        print("   - 检查 API 状态")
        print("   - 考虑增加超时时间")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_chief_agent_directly():
    """直接测试 Chief Agent（不通过节点）"""
    print("\n" + "=" * 80)
    print("📝 测试: 直接调用 Chief Agent")
    print("=" * 80)
    
    try:
        from src.unified_research_system import UnifiedResearchSystem
        
        system = UnifiedResearchSystem()
        
        # 检查 Chief Agent 是否可用
        chief_agent = None
        if hasattr(system, 'chief_agent'):
            chief_agent = system.chief_agent
        elif hasattr(system, '_chief_agent'):
            chief_agent = system._chief_agent
        elif hasattr(system, 'workflow') and hasattr(system.workflow, 'agent_nodes'):
            agent_nodes = system.workflow.agent_nodes
            if agent_nodes and hasattr(agent_nodes, 'chief_agent'):
                chief_agent = agent_nodes.chief_agent
        
        if not chief_agent:
            print("❌ Chief Agent 不可用")
            print("💡 系统可能未初始化 Chief Agent")
            print("💡 尝试等待系统初始化...")
            # 等待系统初始化
            await asyncio.sleep(2)
            if hasattr(system, 'chief_agent'):
                chief_agent = system.chief_agent
            elif hasattr(system, '_chief_agent'):
                chief_agent = system._chief_agent
        
        if not chief_agent:
            print("❌ Chief Agent 仍然不可用，跳过直接调用测试")
            return None
        
        test_query = "Compare the economic policies of the United States and China in the 21st century"
        print(f"🔍 查询: {test_query}")
        
        context = {
            'query': test_query,
            'route_path': 'complex',
            'complexity_score': 7.0,
            'user_context': {}
        }
        
        print("⏱️  开始执行 Chief Agent（超时：10分钟）...")
        start_time = time.time()
        
        result = await asyncio.wait_for(
            chief_agent.execute(context),
            timeout=600.0  # 10分钟超时
        )
        
        execution_time = time.time() - start_time
        
        print(f"⏱️  执行时间: {execution_time:.2f}秒")
        print(f"✅ 成功: {result.success}")
        print(f"🎯 置信度: {result.confidence:.2f}")
        
        if result.success:
            if isinstance(result.data, dict):
                answer = result.data.get('answer', result.data.get('final_answer', ''))
                print(f"📝 答案: {answer[:200] if answer else 'None'}...")
            else:
                print(f"📝 结果: {str(result.data)[:200] if result.data else 'None'}...")
        else:
            print(f"❌ 错误: {result.error}")
        
        return result.success
        
    except asyncio.TimeoutError:
        print("❌ 测试超时（10分钟）")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("🚀 Complex 查询完整智能体序列测试")
    print("=" * 80)
    
    # 测试1: 通过 Chief Agent 节点
    print("\n📝 测试1: 通过 Chief Agent 节点（完整智能体序列）")
    result1 = await test_complex_query_full_sequence()
    
    # 测试2: 直接调用 Chief Agent（可选）
    print("\n📝 测试2: 直接调用 Chief Agent（可选）")
    try:
        result2 = await test_chief_agent_directly()
    except Exception as e:
        print(f"⚠️ 直接调用测试跳过: {e}")
        result2 = None
    
    # 总结
    print("\n" + "=" * 80)
    print("📊 最终总结")
    print("=" * 80)
    print(f"通过节点测试: {'✅ 通过' if result1 else '❌ 失败'}")
    if result2 is not None:
        print(f"直接调用测试: {'✅ 通过' if result2 else '❌ 失败'}")
    
    if result1:
        print("\n✅ Complex 查询完整智能体序列测试通过！")
        return 0
    else:
        print("\n❌ Complex 查询完整智能体序列测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

