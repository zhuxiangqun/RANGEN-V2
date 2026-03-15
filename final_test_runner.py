#!/usr/bin/env python3
"""
最终测试运行器 - 直接在Python中执行所有操作
"""

import asyncio
import sys
import os
import time

def main():
    # 设置项目路径
    project_root = "/Users/syu/workdata/person/zy/RANGEN-main(syu-python)"
    sys.path.insert(0, project_root)
    os.chdir(project_root)

    print('🚀 开始KnowledgeRetrievalAgent迁移测试')
    print('=' * 60)

    # 手动加载.env文件
    env_file = '.env'
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        os.environ[key] = value
            print('✅ 已加载.env文件中的环境变量')
        except Exception as e:
            print(f'❌ 加载.env文件失败: {e}')
            return
    else:
        print('❌ 未发现.env文件')
        return

    # 检查API配置
    api_key = os.getenv('DEEPSEEK_API_KEY', '')
    if not api_key:
        print('❌ DEEPSEEK_API_KEY未设置，无法运行测试')
        return

    print(f'✅ API密钥已配置 (长度: {len(api_key)})')

    # 运行异步测试
    asyncio.run(run_async_test())

async def run_async_test():
    try:
        # 导入组件
        print('\n📦 导入组件...')
        from src.agents.expert_agents import KnowledgeRetrievalAgent
        from src.agents.rag_agent import RAGExpert
        from src.adapters.knowledge_retrieval_agent_adapter import KnowledgeRetrievalAgentAdapter
        from src.strategies.gradual_replacement import GradualReplacementStrategy
        print('✅ 导入成功')

        # 创建实例
        print('\n🤖 创建实例...')
        old_agent = KnowledgeRetrievalAgent()
        new_agent = RAGExpert()
        adapter = KnowledgeRetrievalAgentAdapter()
        strategy = GradualReplacementStrategy(old_agent, new_agent, adapter)
        print('✅ 创建成功')

        # 开始测试
        print('\n🧪 开始测试...')
        test_rates = [0.0, 0.5, 1.0]

        for rate in test_rates:
            print(f'\n🔄 测试替换比例: {rate:.0%}')
            strategy.replacement_rate = rate

            # 每个比例测试1次
            test_query = f'简单测试查询 - 比例{rate:.0%}'

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

                print(f'   {status_icon} {agent_icon} {executed_by}: {duration:.3f}s')
                print(f'      查询: {test_query}')

            except Exception as e:
                print(f'   ❌ 执行失败: {str(e)[:100]}...')

            # 短暂延迟
            await asyncio.sleep(1.0)

        print('\n🎉 KnowledgeRetrievalAgent迁移测试完成！')

    except Exception as e:
        print(f'❌ 测试过程中出错: {str(e)[:100]}...')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
