#!/usr/bin/env python3
"""
测试统一服务器
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_unified_server():
    """测试统一服务器初始化"""
    print("测试统一服务器...")

    try:
        from scripts.start_unified_server import UnifiedServer

        # 创建统一服务器实例（不启动，只测试初始化）
        server = UnifiedServer(port=8085)

        # 模拟初始化（不真正启动服务）
        print("✅ UnifiedServer 创建成功")

        # 检查必要的属性
        assert hasattr(server, 'port'), "缺少 port 属性"
        assert server.port == 8085, "端口设置不正确"
        print("✅ 服务器属性检查通过")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_unified_server()
    if success:
        print("\n🎉 统一服务器测试通过！")
        print("💡 现在可以运行: python scripts/start_unified_server.py --port 8080")
    else:
        print("\n💥 统一服务器测试失败！")
        sys.exit(1)
