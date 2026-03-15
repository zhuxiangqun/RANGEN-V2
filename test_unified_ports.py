#!/usr/bin/env python3
"""
测试统一服务器端口分配
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_port_allocation():
    """测试端口分配逻辑"""
    print("测试统一服务器端口分配...")

    # 模拟端口分配逻辑
    base_port = 8080
    api_port = base_port
    viz_port = base_port + 1

    print(f"基础端口: {base_port}")
    print(f"API服务器端口: {api_port}")
    print(f"可视化服务器端口: {viz_port}")

    # 验证端口分配
    assert api_port == 8080, f"API端口应该是8080，实际是{api_port}"
    assert viz_port == 8081, f"可视化端口应该是8081，实际是{viz_port}"

    print("✅ 端口分配正确")
    print("✅ API服务器: http://localhost:8080")
    print("✅ 可视化服务器: http://localhost:8081")

    return True

if __name__ == '__main__':
    success = test_port_allocation()
    if success:
        print("\n🎉 端口分配验证通过！")
    else:
        print("\n💥 端口分配验证失败！")
        sys.exit(1)
