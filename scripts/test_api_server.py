#!/usr/bin/env python3
"""
测试API服务器启动
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from src.core.dynamic_config_system import DynamicRoutingManager

async def test_api_server():
    """测试API服务器"""
    print("🧪 测试API服务器启动...")

    # 设置测试端口
    os.environ['DYNAMIC_CONFIG_API_PORT'] = '8082'
    os.environ['DYNAMIC_CONFIG_WEB_PORT'] = '8083'

    try:
        # 创建配置管理器
        manager = DynamicRoutingManager(enable_advanced_features=False)
        print("✅ 配置管理器创建成功")

        # 等待几秒让服务器启动
        print("⏳ 等待服务器启动...")
        await asyncio.sleep(2)

        # 测试API连接
        import aiohttp
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get('http://localhost:8082/') as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ API服务器响应正常: {data.get('name', 'Unknown')}")
                        return True
                    else:
                        print(f"❌ API服务器响应异常: {response.status}")
                        return False
            except Exception as e:
                print(f"❌ 无法连接到API服务器: {e}")
                return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_api_server())
    sys.exit(0 if success else 1)
