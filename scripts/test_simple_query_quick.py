#!/usr/bin/env python3
"""
快速测试 Simple 查询快速路径
用于诊断问题
"""

import asyncio
import os
import sys
from pathlib import Path

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

async def test_knowledge_retrieval():
    """测试知识检索服务"""
    print("=" * 80)
    print("📝 测试1: 知识检索服务")
    print("=" * 80)
    
    try:
        from src.services.knowledge_retrieval_service import KnowledgeRetrievalService
        
        service = KnowledgeRetrievalService()
        query = "What is the capital of France?"
        
        print(f"🔍 查询: {query}")
        print("⏱️  开始检索...")
        
        result = await asyncio.wait_for(
            service.execute({"query": query}, {}),
            timeout=30.0
        )
        
        if result and result.success:
            print(f"✅ 知识检索成功")
            if isinstance(result.data, dict):
                sources = result.data.get('sources', [])
                if not sources and 'knowledge' in result.data:
                    sources = result.data.get('knowledge', [])
            elif isinstance(result.data, list):
                sources = result.data
            else:
                sources = []
            
            print(f"📚 检索到 {len(sources)} 条知识")
            if sources:
                print(f"📄 第一条知识: {str(sources[0])[:200]}...")
            return True, sources
        else:
            print(f"❌ 知识检索失败: {result.error if result else 'Unknown error'}")
            return False, []
    except asyncio.TimeoutError:
        print("❌ 知识检索超时（30秒）")
        return False, []
    except Exception as e:
        print(f"❌ 知识检索异常: {e}")
        import traceback
        traceback.print_exc()
        return False, []

async def test_llm_integration():
    """测试 LLM 集成"""
    print("\n" + "=" * 80)
    print("📝 测试2: LLM 集成")
    print("=" * 80)
    
    api_key = os.getenv('DEEPSEEK_API_KEY', '')
    if not api_key:
        print("❌ DEEPSEEK_API_KEY 未设置")
        print("💡 解决方案:")
        print("   1. 在 .env 文件中设置 DEEPSEEK_API_KEY")
        print("   2. 或运行: export DEEPSEEK_API_KEY='your-api-key'")
        return False
    
    print(f"✅ API Key 已设置: {api_key[:10]}...")
    
    try:
        from src.core.llm_integration import LLMIntegration
        
        llm_config = {
            'llm_provider': 'deepseek',
            'api_key': api_key,
            'model': os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'),
            'base_url': os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
        }
        
        llm = LLMIntegration(llm_config)
        
        prompt = "What is the capital of France? Answer in one word."
        print(f"🔍 提示词: {prompt}")
        print("⏱️  开始调用 LLM...")
        
        # _call_llm 是同步方法，需要使用 asyncio.to_thread 包装
        try:
            answer = await asyncio.wait_for(
                asyncio.to_thread(llm._call_llm, prompt),
                timeout=60.0  # 增加到60秒超时
            )
        except asyncio.TimeoutError:
            print("❌ LLM 调用超时（60秒）")
            print("💡 可能原因:")
            print("   - 网络连接慢")
            print("   - API 响应慢")
            print("   - 检查网络连接和 API 状态")
            return False
        
        if answer and answer.strip():
            print(f"✅ LLM 调用成功")
            print(f"📝 答案: {answer.strip()}")
            return True
        else:
            print("❌ LLM 返回空答案")
            return False
    except asyncio.TimeoutError:
        print("❌ LLM 调用超时（30秒）")
        return False
    except Exception as e:
        print(f"❌ LLM 调用异常: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_fast_path():
    """测试快速路径"""
    print("\n" + "=" * 80)
    print("📝 测试3: 快速路径（完整流程）")
    print("=" * 80)
    
    try:
        from src.core.langgraph_agent_nodes import AgentNodes
        from src.unified_research_system import UnifiedResearchSystem
        from typing import Dict, Any
        
        system = UnifiedResearchSystem()
        agent_nodes = AgentNodes(system=system)
        
        query = "What is the capital of France?"
        initial_state: Dict[str, Any] = {
            'query': query,
            'route_path': 'simple',
            'complexity_score': 1.5,
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
        
        print(f"🔍 查询: {query}")
        print("⏱️  开始执行快速路径...")
        
        result_state = await asyncio.wait_for(
            agent_nodes._handle_simple_path(initial_state, query),
            timeout=300.0  # 5分钟超时
        )
        
        print(f"✅ 快速路径执行完成")
        print(f"📝 任务完成: {result_state.get('task_complete', False)}")
        print(f"📝 答案: {result_state.get('answer', 'None')[:200] if result_state.get('answer') else 'None'}")
        print(f"🎯 置信度: {result_state.get('confidence', 0):.2f}")
        
        if result_state.get('error'):
            print(f"⚠️ 错误信息: {result_state.get('error')}")
        
        return result_state.get('task_complete', False) and result_state.get('answer') is not None
    except asyncio.TimeoutError:
        print("❌ 快速路径执行超时（5分钟）")
        return False
    except Exception as e:
        print(f"❌ 快速路径执行异常: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("🚀 Simple 查询快速路径诊断测试")
    print("=" * 80)
    
    # 测试1: 知识检索
    retrieval_success, sources = await test_knowledge_retrieval()
    
    # 测试2: LLM 集成
    llm_success = await test_llm_integration()
    
    # 测试3: 快速路径（如果前两个都成功）
    if retrieval_success and llm_success:
        fast_path_success = await test_fast_path()
    else:
        print("\n" + "=" * 80)
        print("⚠️ 跳过快速路径测试（前置测试失败）")
        print("=" * 80)
        fast_path_success = False
    
    # 总结
    print("\n" + "=" * 80)
    print("📊 测试总结")
    print("=" * 80)
    print(f"知识检索: {'✅' if retrieval_success else '❌'}")
    print(f"LLM 集成: {'✅' if llm_success else '❌'}")
    print(f"快速路径: {'✅' if fast_path_success else '❌'}")
    
    if not retrieval_success:
        print("\n💡 知识检索失败，可能原因:")
        print("   - 知识库未初始化")
        print("   - 向量数据库连接失败")
        print("   - 运行: python scripts/build_vector_knowledge_base.sh")
    
    if not llm_success:
        print("\n💡 LLM 集成失败，可能原因:")
        print("   - API Key 未设置")
        print("   - 网络连接问题")
        print("   - 检查 .env 文件中的 DEEPSEEK_API_KEY")
    
    if retrieval_success and llm_success and not fast_path_success:
        print("\n💡 快速路径失败，但知识检索和 LLM 都正常")
        print("   - 检查快速路径实现逻辑")
        print("   - 查看详细错误日志")
    
    return 0 if (retrieval_success and llm_success and fast_path_success) else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

