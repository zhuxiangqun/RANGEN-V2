#!/usr/bin/env python3
"""
一键运行迁移测试 - 无需shell命令
"""

import asyncio
import sys
import os
import time

# 自动设置环境
project_root = "/Users/syu/workdata/person/zy/RANGEN-main(syu-python)"
sys.path.insert(0, project_root)
os.chdir(project_root)

async def main():
    print('🚀 KnowledgeRetrievalAgent迁移测试')
    print('=' * 60)

    # 加载.env文件
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")
        print('✅ 环境变量已加载')
    except Exception as e:
        print(f'❌ 环境变量加载失败: {e}')
        return

    # 检查API密钥
    api_key = os.getenv('DEEPSEEK_API_KEY', '')
    if not api_key:
        print('❌ API密钥未设置')
        return
    print(f'✅ API密钥已配置 (长度: {len(api_key)})')

    try:
        # 导入组件
        from src.agents.expert_agents import KnowledgeRetrievalAgent
        from src.agents.rag_agent import RAGExpert
        from src.adapters.knowledge_retrieval_agent_adapter import KnowledgeRetrievalAgentAdapter
        from src.strategies.gradual_replacement import GradualReplacementStrategy
        print('✅ 组件导入成功')

        # 创建实例
        old_agent = KnowledgeRetrievalAgent()
        new_agent = RAGExpert()
        adapter = KnowledgeRetrievalAgentAdapter()
        strategy = GradualReplacementStrategy(old_agent, new_agent, adapter)
        print('✅ 实例创建成功')

        print('\n🧪 开始测试...\n')

        # 测试不同比例
        for rate in [0.0, 0.5, 1.0]:
            print(f'🔄 测试替换比例: {rate:.0%}')
            strategy.replacement_rate = rate

            context = {
                'query': f'测试查询 - 比例{rate:.0%}',
                'max_iterations': 1,
                'use_tools': False,
                'enable_knowledge_retrieval': False
            }

            start = time.time()
            result = await strategy.execute_with_gradual_replacement(context)
            duration = time.time() - start

            executed_by = result.get('_executed_by', 'unknown')
            success = result.get('success', False)

            agent_icon = '🤖' if executed_by == 'old_agent' else '🆕'
            status_icon = '✅' if success else '❌'

            print(f'   {status_icon} {agent_icon} {executed_by}: {duration:.3f}s')
            await asyncio.sleep(1.0)

        print('\n🎉 测试完成！')

    except Exception as e:
        print(f'❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
