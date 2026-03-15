#!/usr/bin/env python3
"""
异步性能基准测试快速验证脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_async_compatibility():
    """测试异步兼容性"""
    try:
        # 检查是否已经在事件循环中
        try:
            loop = asyncio.get_running_loop()
            print("⚠️  检测到已在运行的事件循环中")

            # 尝试导入nest_asyncio
            try:
                import nest_asyncio
                print("✅ nest_asyncio 已安装")
                nest_asyncio.apply()
                print("✅ nest_asyncio 已应用")
                return True
            except ImportError:
                print("❌ nest_asyncio 未安装")
                print("💡 请运行: pip install nest-asyncio")
                return False

        except RuntimeError:
            print("✅ 没有运行中的事件循环，可以安全运行异步代码")
            return True

    except Exception as e:
        print(f"❌ 兼容性检查失败: {e}")
        return False

def test_import():
    """测试导入"""
    try:
        from scripts.run_performance_benchmark import run_async_main
        print("✅ 成功导入异步性能基准测试脚本")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 异步性能基准测试兼容性检查")
    print("=" * 50)

    # 测试导入
    import_ok = test_import()
    if not import_ok:
        sys.exit(1)

    # 测试异步兼容性
    async_ok = test_async_compatibility()
    if not async_ok:
        sys.exit(1)

    print("\n✅ 所有检查通过！现在可以运行异步性能基准测试")
    print("\n运行命令:")
    print("python3 scripts/run_performance_benchmark.py")
