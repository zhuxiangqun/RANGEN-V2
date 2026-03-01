#!/usr/bin/env python3
"""
测试分层架构适配器

验证新旧架构间的兼容性和性能比较功能。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.layered_architecture_adapter import (
    LayeredArchitectureAdapter,
    AdapterConfiguration,
    get_layered_architecture_adapter
)


async def test_basic_adapter_functionality():
    """测试基本适配器功能"""
    print("🧪 测试分层架构适配器基本功能")
    print("=" * 50)

    # 创建适配器
    config = AdapterConfiguration(
        use_new_architecture=True,
        enable_performance_comparison=False
    )
    adapter = LayeredArchitectureAdapter(config)

    # 测试查询处理
    test_queries = [
        "What is Python?",  # 简单查询
        "Compare machine learning and deep learning approaches",  # 复杂查询
        "Explain quantum computing in detail"  # 推理密集查询
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 测试查询 {i}: {query[:50]}...")

        try:
            result = await adapter.process_query(query)

            print("  ✅ 处理成功"            print(f"     使用的架构: {result['architecture_used']}")
            print(f"     回答长度: {len(result.get('answer', ''))}")
            print(".2f"            print(f"     执行指标: {len(result.get('execution_metrics', {}))} 项")

        except Exception as e:
            print(f"  ❌ 处理失败: {e}")

    print("\n📊 当前指标:")
    metrics = adapter._get_current_metrics()
    print(f"   新架构调用: {metrics['layered_calls']}")
    print(f"   旧架构调用: {metrics['legacy_calls']}")
    print(".1f"
async def test_architecture_switching():
    """测试架构切换功能"""
    print("\n🔄 测试架构切换功能")
    print("=" * 30)

    adapter = LayeredArchitectureAdapter()

    # 测试强制使用新架构
    adapter.switch_architecture(True)
    result1 = await adapter.process_query("Test query for new architecture")
    print(f"强制新架构: {result1['architecture_used']}")

    # 测试强制使用旧架构
    adapter.switch_architecture(False)
    result2 = await adapter.process_query("Test query for legacy architecture")
    print(f"强制旧架构: {result2['architecture_used']}")

    # 重置为自动选择
    adapter.switch_architecture(True)


async def test_gradual_rollout():
    """测试渐进式发布"""
    print("\n📈 测试渐进式发布")
    print("=" * 30)

    adapter = LayeredArchitectureAdapter()

    # 设置50%的发布比例
    adapter.configure_rollout(50.0)

    # 执行多次查询，统计新架构使用率
    new_architecture_count = 0
    total_queries = 20

    for i in range(total_queries):
        result = await adapter.process_query(f"Test query {i}")
        if result['architecture_used'] == 'layered':
            new_architecture_count += 1

    actual_percentage = (new_architecture_count / total_queries) * 100
    print(".1f"    print(f"预期: ~50%, 实际: {actual_percentage:.1f}%")


async def test_fallback_mechanism():
    """测试回退机制"""
    print("\n🔙 测试回退机制")
    print("=" * 30)

    # 创建一个配置了回退的适配器
    config = AdapterConfiguration(
        use_new_architecture=True,
        fallback_to_legacy=True
    )
    adapter = LayeredArchitectureAdapter(config)

    # 测试正常情况
    try:
        result = await adapter.process_query("Normal test query")
        print(f"正常情况: {result['architecture_used']}")
    except Exception as e:
        print(f"正常情况异常: {e}")

    print("✅ 适配器功能测试完成")


async def test_migration_recommendations():
    """测试迁移建议"""
    print("\n📋 测试迁移建议")
    print("=" * 30)

    adapter = LayeredArchitectureAdapter()

    # 模拟一些调用历史
    for i in range(150):  # 创建足够的样本
        try:
            await adapter.process_query(f"Sample query {i}")
        except:
            pass  # 忽略错误，专注于测试逻辑

    # 获取迁移建议
    recommendations = adapter.get_migration_recommendations()

    print("迁移建议:"    print(f"   准备完全迁移: {recommendations['ready_for_full_migration']}")
    print(".1f"    print(f"   性能提升: {recommendations.get('performance_benefits', {})}")
    print(f"   下一步行动: {recommendations.get('next_steps', [])}")


async def main():
    """主测试函数"""
    print("🚀 开始分层架构适配器测试")
    print("=" * 50)

    try:
        await test_basic_adapter_functionality()
        await test_architecture_switching()
        await test_gradual_rollout()
        await test_fallback_mechanism()
        await test_migration_recommendations()

        print("\n🎉 所有测试完成！")

    except KeyboardInterrupt:
        print("\n收到中断信号，正在退出...")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
