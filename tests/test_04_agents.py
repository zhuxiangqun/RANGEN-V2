#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 Agent 基类和推理引擎"""

import sys
sys.path.insert(0, '.')

print('=== 测试 Agent 基类和推理引擎 ===')

try:
    # 测试导入 Agent 相关模块
    print('1. 测试导入 Agent 相关模块...')
    from src.agents.base_agent import BaseAgent
    from src.agents.reasoning_agent import ReasoningAgent
    from src.agents.react_agent import ReActAgent
    print('   ✓ BaseAgent, ReasoningAgent, ReActAgent 导入成功')
    
    # 测试导入推理引擎
    print('2. 测试导入推理引擎...')
    from src.services.reasoning_engines import ReasoningEngineFactory
    print('   ✓ ReasoningEngineFactory 导入成功')
    
    # 测试工具注册
    print('3. 测试工具注册系统...')
    from src.agents.tools.tool_registry import ToolRegistry
    registry = ToolRegistry()
    tools = registry.list_tools()
    print(f'   ✓ 已注册工具数量: {len(tools)}')
    print(f'   工具列表: {tools}')
    
    # 测试 ChiefAgent
    print('4. 测试 ChiefAgent 导入...')
    from src.agents.chief_agent import ChiefAgent
    print('   ✓ ChiefAgent 导入成功')
    
    print()
    print('=== Agent 基类和推理引擎 测试通过 ✓ ===')
    sys.exit(0)
    
except Exception as e:
    print(f'✗ 测试失败: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
