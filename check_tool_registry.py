#!/usr/bin/env python3
"""检查工具注册表"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 60)
print("检查工具注册表")
print("=" * 60)

try:
    from src.agents.tools.tool_registry import get_tool_registry
    
    registry = get_tool_registry()
    tools = registry.get_all_tools()
    
    print(f"\n✅ 工具注册表正常")
    print(f"   工具数量: {len(tools)}")
    
    for tool in tools[:10]:
        name = getattr(tool, 'tool_name', 'unknown')
        desc = getattr(tool, 'description', '')[:50]
        print(f"   - {name}: {desc}...")
    
except Exception as e:
    print(f"\n❌ 失败: {e}")
    import traceback
    traceback.print_exc()
