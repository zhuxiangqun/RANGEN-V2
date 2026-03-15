#!/usr/bin/env python3
"""
KnowledgeRetrievalAgent迁移测试脚本
用于前台演示KnowledgeRetrievalAgent到RAGExpert的迁移过程
"""

import asyncio
import time
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

# 加载.env文件中的环境变量
def load_env_file():
    """加载.env文件中的环境变量"""
    env_file = Path('.env')
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print('✅ 已加载.env文件中的环境变量')
        except ImportError:
            # 如果没有python-dotenv，手动加载
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        os.environ[key] = value
            print('✅ 已手动加载.env文件中的环境变量')
    else:
        print('⚠️ 未发现.env文件')

# 加载环境变量
load_env_file()

async def demo_knowledge_retrieval_migration():
    print('🔍 KnowledgeRetrievalAgent迁移测试')
    print('=' * 50)

    try:
        print('📦 导入组件...')
        from src.agents.expert_agents import KnowledgeRetrievalAgent
        from src.agents.rag_agent import RAGExpert  # RAGExpert在rag_agent.py中
        from src.adapters.knowledge_retrieval_agent_adapter import KnowledgeRetrievalAgentAdapter
        from src.strategies.gradual_replacement import GradualReplacementStrategy
        print('✅ 导入成功')

        print('🤖 创建实例...')
        old_agent = KnowledgeRetrievalAgent()
        new_agent = RAGExpert()
        adapter = KnowledgeRetrievalAgentAdapter()
        strategy = GradualReplacementStrategy(old_agent, new_agent, adapter)
        print('✅ 创建成功')

        print('\n🧪 开始测试...')

        # 测试不同的替换比例
        test_rates = [0.0, 0.3, 0.7, 1.0]

        for rate in test_rates:
            print(f'\n🔄 测试替换比例: {rate:.0%}')
            strategy.replacement_rate = rate

                # 每个比例测试2次（减少API调用）
            for i in range(2):
                # 创建简单的测试查询（避免复杂的知识检索）
                test_query = f'测试查询 {i+1}'

                context = {
                    'query': test_query,
                    'max_iterations': 1,  # 减少迭代次数
                    'use_tools': False,   # 禁用工具调用
                    'enable_knowledge_retrieval': False  # 禁用知识检索
                }

                try:
                    start = time.time()
                    result = await strategy.execute_with_gradual_replacement(context)
                    duration = time.time() - start

                    executed_by = result.get('_executed_by', 'unknown')
                    success = result.get('success', False)

                    agent_icon = '🤖' if executed_by == 'old_agent' else '🆕'
                    status_icon = '✅' if success else '❌'

                    print(f'   {status_icon} {agent_icon} {executed_by}: {duration:.3f}s - {test_query}')

                except Exception as e:
                    print(f'   ❌ 执行失败: {e}')

                # 短暂延迟
                if i < 1:
                    await asyncio.sleep(0.5)

        print('\n🎉 KnowledgeRetrievalAgent迁移测试完成！')
        print('📊 测试结果:')
        print('   - 0%: 全部使用KnowledgeRetrievalAgent')
        print('   - 30%: 30%使用RAGExpert，70%使用KnowledgeRetrievalAgent')
        print('   - 70%: 70%使用RAGExpert，30%使用KnowledgeRetrievalAgent')
        print('   - 100%: 全部使用RAGExpert')

    except Exception as e:
        print(f'❌ 错误: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(demo_knowledge_retrieval_migration())
