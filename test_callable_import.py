#!/usr/bin/env python3
"""
测试 Callable 导入问题
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("开始测试导入...")

try:
    print("1. 测试 typing.Callable...")
    from typing import Callable
    print("   ✅ Callable 导入成功")

    print("2. 测试 dynamic_config_system...")
    from src.core.dynamic_config_system import DynamicConfigManager
    print("   ✅ dynamic_config_system 导入成功")

    print("3. 测试 intelligent_router...")
    from src.core.intelligent_router import IntelligentRouter
    print("   ✅ intelligent_router 导入成功")

    print("4. 测试实例化...")
    router = IntelligentRouter(enable_advanced_features=False)
    print("   ✅ IntelligentRouter 实例化成功")

    print("\n🎉 所有测试通过！")

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
