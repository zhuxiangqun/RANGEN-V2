#!/usr/bin/env python3
"""
生成测试调用数据

通过模拟请求来生成调用数据，帮助替换比例增加。
"""

import asyncio
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.strategies.gradual_replacement import GradualReplacementStrategy
from scripts.start_gradual_replacement import AGENT_MAPPING, import_class, create_replacement_strategy

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def generate_test_calls(
    source_agent_name: str,
    num_requests: int = 100,
    batch_size: int = 10,
    delay_between_batches: float = 1.0
):
    """
    生成测试调用数据
    
    Args:
        source_agent_name: 源Agent名称
        num_requests: 总请求数
        batch_size: 每批请求数
        delay_between_batches: 批次间延迟（秒）
    """
    logger.info("=" * 80)
    logger.info(f"开始生成测试调用数据: {source_agent_name}")
    logger.info("=" * 80)
    logger.info(f"总请求数: {num_requests}")
    logger.info(f"批次大小: {batch_size}")
    logger.info(f"批次间延迟: {delay_between_batches}秒")
    logger.info("=" * 80)
    
    # 创建逐步替换策略
    strategy = await create_replacement_strategy(
        source_agent_name=source_agent_name,
        initial_rate=0.01  # 使用1%的初始替换比例
    )
    
    if strategy is None:
        logger.error("❌ 无法创建逐步替换策略")
        return
    
    # 测试查询列表
    test_queries = [
        "什么是人工智能？",
        "解释一下机器学习的基本概念",
        "如何优化系统性能？",
        "什么是深度学习？",
        "解释一下神经网络的工作原理",
        "如何提高代码质量？",
        "什么是自然语言处理？",
        "解释一下强化学习",
        "如何设计一个好的API？",
        "什么是分布式系统？",
    ]
    
    success_count = 0
    failure_count = 0
    
    # 分批生成请求
    for batch_start in range(0, num_requests, batch_size):
        batch_end = min(batch_start + batch_size, num_requests)
        batch_num = (batch_start // batch_size) + 1
        total_batches = (num_requests + batch_size - 1) // batch_size
        
        logger.info(f"\n📦 批次 {batch_num}/{total_batches}: 请求 {batch_start+1}-{batch_end}")
        
        for i in range(batch_start, batch_end):
            query_idx = i % len(test_queries)
            test_context = {
                "query": test_queries[query_idx],
                "session_id": f"test_session_{i+1}"
            }
            
            try:
                result = await strategy.execute_with_gradual_replacement(test_context)
                executed_by = result.get("_executed_by", "unknown")
                replacement_rate = result.get("_replacement_rate", 0.0)
                
                if result.get("success", True):
                    success_count += 1
                    logger.debug(f"  ✅ 请求 {i+1}: 由 {executed_by} 执行成功 (替换比例: {replacement_rate:.0%})")
                else:
                    failure_count += 1
                    logger.warning(f"  ⚠️  请求 {i+1}: 由 {executed_by} 执行失败")
                    
            except Exception as e:
                failure_count += 1
                logger.error(f"  ❌ 请求 {i+1} 执行异常: {e}")
        
        # 批次间延迟
        if batch_end < num_requests:
            await asyncio.sleep(delay_between_batches)
    
    # 获取最终统计信息
    stats = strategy.get_replacement_stats()
    
    logger.info("\n" + "=" * 80)
    logger.info("📊 最终统计信息")
    logger.info("=" * 80)
    logger.info(f"总请求数: {num_requests}")
    logger.info(f"成功数: {success_count}")
    logger.info(f"失败数: {failure_count}")
    logger.info(f"成功率: {success_count/num_requests:.2%}")
    logger.info("")
    logger.info(f"替换比例: {stats['replacement_rate']:.0%}")
    logger.info(f"新Agent成功率: {stats['new_agent_success_rate']:.2%}")
    logger.info(f"旧Agent成功率: {stats['old_agent_success_rate']:.2%}")
    logger.info(f"新Agent总调用数: {stats['new_agent_total_calls']}")
    logger.info(f"旧Agent总调用数: {stats['old_agent_total_calls']}")
    logger.info("")
    logger.info(f"是否应该增加替换比例: {'✅ 是' if stats['should_increase_rate'] else '❌ 否'}")
    
    if stats['should_increase_rate']:
        logger.info("🎉 条件满足！替换比例可以增加了！")
    else:
        logger.info("⏸️  条件未满足，需要:")
        if stats['new_agent_total_calls'] < 100:
            logger.info(f"   - 更多调用: 当前 {stats['new_agent_total_calls']}/100")
        if stats['new_agent_success_rate'] < 0.95:
            logger.info(f"   - 更高成功率: 当前 {stats['new_agent_success_rate']:.2%}/95%")
    
    logger.info("=" * 80)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="生成测试调用数据")
    parser.add_argument(
        "--agent",
        type=str,
        default="ReActAgent",
        help="Agent名称 (默认: ReActAgent)"
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=100,
        help="总请求数 (默认: 100)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="每批请求数 (默认: 10)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="批次间延迟（秒）(默认: 1.0)"
    )
    
    args = parser.parse_args()
    
    asyncio.run(generate_test_calls(
        source_agent_name=args.agent,
        num_requests=args.requests,
        batch_size=args.batch_size,
        delay_between_batches=args.delay
    ))


if __name__ == "__main__":
    main()

