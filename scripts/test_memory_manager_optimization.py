#!/usr/bin/env python3
"""
MemoryManager优化效果测试脚本

测试内容：
1. 智能压缩算法效果
2. 关联网络优化功能
3. 自适应记忆管理
4. 多策略检索性能
"""

import asyncio
import time
import logging
from src.agents.memory_manager import MemoryManager, MemoryType

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_memory_manager():
    """测试MemoryManager功能"""
    print("=" * 60)
    print("🧠 MemoryManager智能记忆管理测试")
    print("=" * 60)

    # 初始化记忆管理器
    memory_manager = MemoryManager()

    # 测试数据
    test_memories = [
        {
            "content": "Python是一种高级编程语言，由Guido van Rossum在1991年创建。它具有简洁明了的语法，支持面向对象、函数式和过程式编程 paradigms。",
            "memory_type": "semantic",
            "description": "Python语言介绍"
        },
        {
            "content": "机器学习是人工智能的一个子集，它使用算法和统计模型让计算机系统能够从数据中学习和改进，而无需显式编程。",
            "memory_type": "semantic",
            "description": "机器学习定义"
        },
        {
            "content": "深度学习是机器学习的一个子集，使用多层神经网络来模拟人脑处理信息的方式。它在图像识别、自然语言处理等领域取得了重大突破。",
            "memory_type": "semantic",
            "description": "深度学习介绍"
        },
        {
            "content": "今天上午我学习了Python的基础语法，包括变量、数据类型、控制流和函数定义。遇到了一个关于作用域的问题，通过查阅文档解决了。",
            "memory_type": "episodic",
            "description": "学习经历记录"
        },
        {
            "content": "在数据科学项目中，经常需要处理大量文本数据。常用的预处理步骤包括：分词、去停用词、词干提取、词形还原等。",
            "memory_type": "procedural",
            "description": "文本预处理流程"
        }
    ]

    # 存储测试记忆
    print("\n📝 存储测试记忆...")
    stored_ids = []

    for memory_data in test_memories:
        result = await memory_manager.execute({
            "action": "store",
            "content": memory_data["content"],
            "memory_type": memory_data["memory_type"]
        })

        if result.success:
            memory_id = result.data["memory_id"]
            stored_ids.append(memory_id)
            print(f"✅ 记忆已存储: {memory_id} - {memory_data['description']}")
        else:
            print(f"❌ 记忆存储失败: {memory_data['description']} - {result.error}")

    # 创建记忆关联
    print("\n🔗 创建记忆关联...")
    if len(stored_ids) >= 3:
        # 将编程相关的记忆关联起来
        await memory_manager.execute({
            "action": "associate",
            "source_id": stored_ids[0],  # Python介绍
            "target_id": stored_ids[3],  # 学习经历
            "link_type": "learning_experience",
            "strength": 0.8
        })

        await memory_manager.execute({
            "action": "associate",
            "source_id": stored_ids[1],  # 机器学习
            "target_id": stored_ids[2],  # 深度学习
            "link_type": "subfield_relationship",
            "strength": 0.9
        })

        print("✅ 记忆关联已创建")

    # 等待压缩操作
    print("\n⏳ 等待记忆压缩和维护...")
    await asyncio.sleep(2)

    # 测试检索功能
    test_queries = [
        "Python编程语言",
        "机器学习和深度学习",
        "文本数据处理",
        "学习经历"
    ]

    print("\n🔍 测试记忆检索...")
    for query in test_queries:
        print(f"\n   查询: '{query}'")

        start_time = time.time()
        result = await memory_manager.execute({
            "action": "retrieve",
            "query": query,
            "limit": 3
        })
        execution_time = time.time() - start_time

        if result.success:
            memories = result.data.get("memories", [])
            print(f"   ⏱️ 检索耗时: {execution_time:.3f}秒")
            print(f"   📊 检索到 {len(memories)} 条记忆:")

            for i, memory in enumerate(memories, 1):
                memory_type = memory.get('memory_type', 'unknown')
                importance = memory.get('importance_score', 0)
                retrieval_type = memory.get('retrieval_type', 'unknown')
                content_preview = str(memory.get('content', ''))[:80] + "..."

                print(f"     {i}. [{memory_type}] {content_preview}")
                print(f"        重要性: {importance:.2f}, 检索类型: {retrieval_type}")

        else:
            print(f"   ❌ 检索失败: {result.error}")

    # 获取统计信息
    print("\n📊 记忆管理统计:")
    stats_result = await memory_manager.execute({"action": "stats"})

    if stats_result.success:
        stats = stats_result.data
        print(f"   总记忆数: {stats['total_memories']}")
        print(f"   当前记忆数: {stats['current_memory_count']}")
        print(f"   压缩记忆数: {stats['compressed_memories']}")
        print(f"   总关联数: {stats['total_associations']}")
        print(f"   缓存大小: {stats['cache_size']}")
        print(f"   缓存命中数: {stats['cache_hits']}")
        print(f"   检索操作数: {stats['retrieval_operations']}")
        print(f"   平均重要性分数: {stats['avg_importance_score']:.2f}")
        print(f"   平均压缩率: {stats['compression_ratio_avg']:.2f}")
        cache_hit_rate = stats.get('cache_hit_rate', 0.0)
        print(f"   缓存命中率: {cache_hit_rate:.3f}")
        # 记忆类型分布
        if 'memory_types' in stats:
            print("   记忆类型分布:")
            for mem_type, count in stats['memory_types'].items():
                print(f"     - {mem_type}: {count} 条")

    # 测试压缩效果
    print("\n🗜️  测试压缩功能...")
    compress_result = await memory_manager.execute({"action": "compress"})

    if compress_result.success:
        print("✅ 压缩操作完成")

        # 再次获取统计信息
        updated_stats = await memory_manager.execute({"action": "stats"})
        if updated_stats.success:
            new_stats = updated_stats.data
            compressed_count = new_stats.get('compressed_memories', 0)
            avg_compression_ratio = new_stats.get('compression_ratio_avg', 1.0)
            print(f"   压缩后记忆数: {compressed_count}")
            print(f"   平均压缩率: {avg_compression_ratio:.2f}")
    # 关闭记忆管理器
    memory_manager.shutdown()

    print("\n✅ MemoryManager测试完成！")

if __name__ == "__main__":
    asyncio.run(test_memory_manager())
