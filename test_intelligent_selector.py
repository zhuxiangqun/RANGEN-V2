#!/usr/bin/env python3
"""Test intelligent tool selector with actual execution"""
import asyncio
import sys
sys.path.insert(0, '.')

async def test():
    from src.agents.tools.tool_initializer import initialize_tools
    from src.core.cli_executor import CLIExecutor
    from src.agents.intelligent_tool_selector import get_intelligent_tool_selector
    
    registry = initialize_tools()
    cli_executor = CLIExecutor()
    selector = get_intelligent_tool_selector(registry, cli_executor)
    
    tools = registry.get_all_tools()
    query = '打开 https://www.toutiao.com'
    
    result = await selector.analyze_and_select(query, tools)
    print(f'needs_new_tool: {result[0]}')
    print(f'tool_name: {result[1]}')
    print(f'tool_instance: {result[2]}')
    print(f'adaptation: {result[3]}')
    if result[3]:
        print(f'parameters: {result[3].parameters}')
        
    # Execute the tool if found
    if result[2] and result[3]:
        tool_instance = result[2]
        adaptation = result[3]
        base_tool = getattr(tool_instance, "base_tool", None) or tool_instance
        print(f"\nExecuting tool with params: {adaptation.parameters}")
        if hasattr(base_tool, "call"):
            exec_result = await base_tool.call(**adaptation.parameters)
            print(f"Execution result: {exec_result}")

asyncio.run(test())
