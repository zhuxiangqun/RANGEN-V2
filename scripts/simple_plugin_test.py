#!/usr/bin/env python3
"""
简单插件测试

测试插件框架的基本功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.capability_plugin_framework import (
    CapabilityPluginFramework,
    CapabilityMetadata,
    CapabilityType
)


class MockCapability:
    """模拟能力"""

    def __init__(self):
        self.initialized = False

    METADATA = CapabilityMetadata(
        capability_id="mock_capability",
        name="模拟能力",
        version="1.0.0",
        type=CapabilityType.ANALYSIS,
        description="用于测试的模拟能力",
        author="Test"
    )

    async def initialize(self, config):
        self.initialized = True
        return True

    async def execute(self, context):
        return {
            "result": f"Mock capability processed: {context.get('query', 'unknown')}",
            "confidence": 0.8
        }

    async def get_status(self):
        return {
            "initialized": self.initialized,
            "status": "ready"
        }


async def test_basic_plugin_framework():
    """测试基本插件框架功能"""
    print("🧪 测试插件框架基本功能")
    print("=" * 40)

    # 初始化框架
    framework = CapabilityPluginFramework()
    await framework.initialize_framework()

    # 注册模拟插件
    try:
        plugin_id = await framework.register_plugin_from_class(MockCapability, "mock_plugin")
        print(f"✅ 插件注册成功: {plugin_id}")
    except Exception as e:
        print(f"❌ 插件注册失败: {e}")
        return

    # 发现插件
    plugins = framework.discover_capabilities()
    print(f"📋 发现插件数量: {len(plugins)}")

    for plugin in plugins:
        print(f"  • {plugin.metadata.name} ({plugin.metadata.type.value})")

    # 执行能力
    try:
        result = await framework.execute_capability("mock_plugin", {
            "query": "Test query",
            "context": {"test": True}
        })
        print("✅ 能力执行成功:")
        print(f"     结果: {result}")
    except Exception as e:
        print(f"❌ 能力执行失败: {e}")

    # 清理
    await framework.shutdown_framework()

    print("🎉 插件框架测试完成")


async def main():
    """主函数"""
    try:
        await test_basic_plugin_framework()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
