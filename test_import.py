#!/usr/bin/env python3
"""测试导入"""

import sys
import os
sys.path.insert(0, '.')

print("测试WorkflowIntegration导入...")
try:
    from src.integration.workflow_integration import WorkflowIntegration
    print('✅ WorkflowIntegration导入成功')
    integration = WorkflowIntegration('test')
    print('✅ WorkflowIntegration实例化成功')
except Exception as e:
    print(f'❌ 错误: {e}')
    import traceback
    traceback.print_exc()

print("\n测试EvolutionEngine导入...")
try:
    from src.evolution.engine import EvolutionEngine
    print('✅ EvolutionEngine导入成功')
    engine = EvolutionEngine()
    print('✅ EvolutionEngine实例化成功')
except Exception as e:
    print(f'❌ 错误: {e}')
    import traceback
    traceback.print_exc()

print("\n测试HandRegistry导入...")
try:
    from src.hands.registry import HandRegistry
    print('✅ HandRegistry导入成功')
    registry = HandRegistry()
    print('✅ HandRegistry实例化成功')
except Exception as e:
    print(f'❌ 错误: {e}')
    import traceback
    traceback.print_exc()

print("\n测试HookTransparencySystem导入...")
try:
    from src.hook.transparency import HookTransparencySystem
    print('✅ HookTransparencySystem导入成功')
    hook = HookTransparencySystem('test')
    print('✅ HookTransparencySystem实例化成功')
except Exception as e:
    print(f'❌ 错误: {e}')
    import traceback
    traceback.print_exc()