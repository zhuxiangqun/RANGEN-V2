#!/usr/bin/env python3
"""
临时迁移测试脚本
用于前台演示ReActAgent迁移过程
"""

import asyncio
import time
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

async def demo():
    print('🔍 简化前台迁移测试')
    print('=' * 50)

    try:
        print('📦 导入组件...')
        from src.agents.react_agent import ReActAgent
        from src.agents.reasoning_expert import ReasoningExpert
        from src.adapters.react_agent_adapter import ReActAgentAdapter
        from src.strategies.gradual_replacement import GradualReplacementStrategy
        print('✅ 导入成功')

        print('🤖 创建实例...')
        old_agent = ReActAgent('DemoAgent', use_intelligent_config=False)
        new_agent = ReasoningExpert()
        adapter = ReActAgentAdapter()
        strategy = GradualReplacementStrategy(old_agent, new_agent, adapter)
        print('✅ 创建成功')

        print('\n🧪 开始测试...')

        # 测试3种替换比例
        for rate in [0.0, 0.5, 1.0]:
            print(f'\n🔄 测试替换比例: {rate:.0%}')
            strategy.replacement_rate = rate

            for i in range(2):
                context = {'query': f'测试 {i+1}', 'max_iterations': 1, 'use_tools': False}

                start = time.time()
                result = await strategy.execute_with_gradual_replacement(context)
                duration = time.time() - start

                executed_by = result.get('_executed_by', 'unknown')
                success = result.get('success', False)

                agent_icon = '🤖' if executed_by == 'old_agent' else '🆕'
                status_icon = '✅' if success else '❌'

                print(f'   {status_icon} {agent_icon} {executed_by}: {duration:.3f}s')

        print('\n🎉 测试完成！')

    except Exception as e:
        print(f'❌ 错误: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(demo())
