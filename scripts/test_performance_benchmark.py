#!/usr/bin/env python3
"""
测试性能基准测试功能
"""

import asyncio
import sys
from pathlib import Path

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_benchmark():
    """测试基准测试功能"""
    print("🧪 测试性能基准测试系统")
    print("=" * 50)

    try:
        from src.benchmark.performance_benchmark_system import (
            get_benchmark_system,
            run_performance_benchmark
        )

        print("✅ 导入成功")

        # 测试创建基准系统
        system = get_benchmark_system()
        print("✅ 基准测试系统创建成功")

        # 测试场景数量
        scenarios = len(system.test_scenarios)
        print(f"✅ 支持 {scenarios} 个测试场景")

        # 测试运行简单场景（模拟）
        print("\n🚀 运行轻负载测试 (模拟)...")

        # 这里只是测试导入和初始化，实际运行可能需要更长的时间
        print("✅ 所有测试准备就绪！")

        print("\n💡 要运行实际测试，请使用:")
        print("   python3 scripts/run_performance_benchmark.py")
        print("   然后选择选项 2 (轻负载测试)")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_benchmark())
