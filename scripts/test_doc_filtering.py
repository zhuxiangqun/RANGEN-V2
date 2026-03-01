#!/usr/bin/env python3
"""
测试文档筛选功能

验证文档筛选配置是否正常工作
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.manage_documentation_sync import DocumentationSyncManager


async def test_doc_filtering():
    """测试文档筛选功能"""
    print("🧪 测试文档筛选功能")
    print("=" * 50)

    # 创建管理器
    manager = DocumentationSyncManager()

    # 显示当前配置
    config = manager.config
    filter_mode = config.get('monitoring', {}).get('doc_filter_mode', 'all')
    print(f"📋 当前筛选模式: {filter_mode}")

    # 执行同步检查
    print("\n🔍 执行同步检查...")
    result = await manager.perform_full_sync_check()

    if 'error' in result:
        print(f"❌ 同步检查失败: {result['error']}")
        return

    # 显示结果
    print("✅ 同步检查完成")
    print(f"   - 同步状态: {result['sync_status']}")
    print(f"   - 变更数量: {result['changes_detected']}")
    print(f"   - 质量评分: {result.get('quality_score', 'N/A')}")
    print(f"   - 监控文档数: {len(result.get('monitored_docs', []))}")

    # 显示监控的文档
    if filter_mode != 'all':
        print(f"\n📚 当前监控的文档 ({filter_mode} 模式):")

        if filter_mode == 'selective':
            selective_docs = config.get('monitoring', {}).get('selective_docs', [])
            print(f"   选择性监控文档数量: {len(selective_docs)}")
            for doc in selective_docs[:5]:  # 只显示前5个
                print(f"   - {doc}")
            if len(selective_docs) > 5:
                print(f"   ... 还有 {len(selective_docs) - 5} 个文档")

        elif filter_mode == 'categorized':
            categorized = config.get('monitoring', {}).get('categorized_docs', {})
            for priority, docs in categorized.items():
                if docs:
                    print(f"   {priority}: {len(docs)} 个文档")
                    for doc in docs[:3]:  # 每类显示前3个
                        print(f"     - {doc}")
                    if len(docs) > 3:
                        print(f"     ... 还有 {len(docs) - 3} 个文档")

    print("\n✅ 测试完成")


async def show_available_configs():
    """显示可用的配置示例"""
    print("\n📖 可用的配置示例:")
    print("-" * 30)

    examples_file = Path(__file__).parent.parent / "config" / "documentation_sync_examples.yaml"
    if examples_file.exists():
        import yaml
        with open(examples_file, 'r', encoding='utf-8') as f:
            examples = yaml.safe_load(f)

        for config_name, config_data in examples.items():
            if config_name.endswith('_config'):
                mode = config_data.get('monitoring', {}).get('doc_filter_mode', 'unknown')
                print(f"• {config_name}: {mode} 模式")

                # 显示文档数量统计
                if mode == 'selective':
                    docs = config_data.get('monitoring', {}).get('selective_docs', [])
                    print(f"  └─ 监控文档数: {len(docs)}")
                elif mode == 'categorized':
                    categorized = config_data.get('monitoring', {}).get('categorized_docs', {})
                    total = sum(len(docs) for docs in categorized.values() if isinstance(docs, list))
                    print(f"  └─ 监控文档数: {total}")


if __name__ == "__main__":
    async def main():
        await test_doc_filtering()
        await show_available_configs()

    asyncio.run(main())
