#!/usr/bin/env python3
"""
测试统一服务器语法
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_syntax():
    """测试脚本语法"""
    print("测试统一服务器脚本语法...")

    try:
        # 尝试导入脚本
        import scripts.start_unified_server
        print("✅ 脚本导入成功")

        # 检查UnifiedServer类
        from scripts.start_unified_server import UnifiedServer
        print("✅ UnifiedServer类导入成功")

        # 检查main函数
        from scripts.start_unified_server import main
        print("✅ main函数导入成功")

        # 创建实例（不启动）
        server = UnifiedServer(port=8085)
        print("✅ UnifiedServer实例创建成功")

        return True

    except Exception as e:
        print(f"❌ 语法测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_syntax()
    if success:
        print("\n🎉 统一服务器语法测试通过！")
        print("💡 现在可以运行: python scripts/start_unified_server.py --port 8080")
    else:
        print("\n💥 统一服务器语法测试失败！")
        sys.exit(1)
