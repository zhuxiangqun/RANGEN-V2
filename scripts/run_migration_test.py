#!/usr/bin/env python3
"""
运行迁移测试的简单脚本
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

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
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            os.environ[key] = value
                print('✅ 已手动加载.env文件中的环境变量')
            except Exception as e:
                print(f'❌ 手动加载.env文件失败: {e}')
    else:
        print('⚠️ 未发现.env文件')

async def run_migration_test():
    """运行迁移测试"""
    print('🚀 开始KnowledgeRetrievalAgent迁移测试')
    print('=' * 60)

    # 加载环境变量
    load_env_file()

    # 检查API配置
    api_key = os.getenv('DEEPSEEK_API_KEY', '')
    if not api_key:
        print('❌ DEEPSEEK_API_KEY未设置，无法运行测试')
        return

    print(f'✅ API密钥已配置 (长度: {len(api_key)})')

    try:
        # 导入组件
        print('\\n📦 导入组件...')
        from src.agents.expert_agents import KnowledgeRetrievalAgent
        from src.agents.rag_agent import RAGExpert
        from src.adapters.knowledge_retrieval_agent_adapter import KnowledgeRetrievalAgentAdapter
        from src.strategies.gradual_replacement import GradualReplacementStrategy
        print('✅ 导入成功')

        # 创建实例
        print('\\n🤖 创建实例...')
        old_agent = KnowledgeRetrievalAgent()
        new_agent = RAGExpert()
        adapter = KnowledgeRetrievalAgentAdapter()
        strategy = GradualReplacementStrategy(old_agent, new_agent, adapter)
        print('✅ 创建成功')

        # 开始测试
        print('\\n🧪 开始测试...')
        test_rates = [0.0, 0.5, 1.0]  # 简化测试，只测试3个比例

        for rate in test_rates:
            print(f'\\n🔄 测试替换比例: {rate:.0%}')
            strategy.replacement_rate = rate

            # 每个比例测试2次
            for i in range(2):
                test_query = f'测试查询 {i+1}'

                context = {
                    'query': test_query,
                    'max_iterations': 1,
                    'use_tools': False,
                    'enable_knowledge_retrieval': False
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

        print('\\n🎉 KnowledgeRetrievalAgent迁移测试完成！')

    except Exception as e:
        print(f'❌ 测试过程中出错: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(run_migration_test())
