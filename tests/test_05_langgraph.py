#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 LangGraph 工作流节点"""

import sys
sys.path.insert(0, '.')

print('=== 测试 LangGraph 工作流节点 ===')

try:
    # 测试导入 LangGraph 核心依赖
    print('1. 测试导入 LangGraph 依赖...')
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    print('   ✓ LangGraph 核心依赖导入成功')
    
    # 测试导入 LangGraph 节点模块
    print('2. 测试导入 LangGraph 节点模块...')
    from src.core import langgraph_core_nodes
    from src.core import langgraph_reasoning_nodes
    print('   ✓ LangGraph 节点模块导入成功')
    
    # 检查可用的节点函数
    print('3. 检查可用节点...')
    node_functions = [name for name in dir(langgraph_core_nodes) 
                     if not name.startswith('_') and callable(getattr(langgraph_core_nodes, name))]
    print(f'   核心节点数量: {len(node_functions)}')
    print(f'   节点列表: {node_functions[:5]}...' if len(node_functions) > 5 else f'   节点列表: {node_functions}')
    
    # 测试工作流状态
    print('4. 测试工作流状态导入...')
    from src.core.reasoning_state import ReasoningState
    print('   ✓ ReasoningState 导入成功')
    
    print()
    print('=== LangGraph 工作流节点 测试通过 ✓ ===')
    sys.exit(0)
    
except Exception as e:
    print(f'✗ 测试失败: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
