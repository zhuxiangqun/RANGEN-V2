#!/usr/bin/env python3
"""
启动逐步替换策略

为指定的Agent启动逐步替换，从低替换比例开始，逐步增加。
"""

import asyncio
import sys
import argparse
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.strategies.gradual_replacement import GradualReplacementStrategy

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Agent映射表
AGENT_MAPPING = {
    "ReActAgent": {
        "old_class": "src.agents.react_agent.ReActAgent",
        "adapter_class": "src.adapters.react_agent_adapter.ReActAgentAdapter",
        "target_agent": "ReasoningExpert"
    },
    "KnowledgeRetrievalAgent": {
        "old_class": "src.agents.expert_agents.KnowledgeRetrievalAgent",
        "adapter_class": "src.adapters.knowledge_retrieval_agent_adapter.KnowledgeRetrievalAgentAdapter",
        "target_agent": "RAGExpert"
    },
    "RAGAgent": {
        "old_class": "src.agents.rag_agent.RAGAgent",
        "adapter_class": "src.adapters.rag_agent_adapter.RAGAgentAdapter",
        "target_agent": "RAGExpert"
    },
    "CitationAgent": {
        "old_class": "src.agents.expert_agents.CitationAgent",
        "adapter_class": "src.adapters.citation_agent_adapter.CitationAgentAdapter",
        "target_agent": "QualityController"
    },
    "ChiefAgent": {
        "old_class": "src.agents.chief_agent.ChiefAgent",
        "adapter_class": "src.adapters.chief_agent_adapter.ChiefAgentAdapter",
        "target_agent": "AgentCoordinator"
    },
}


def import_class(class_path: str):
    """动态导入类"""
    module_path, class_name = class_path.rsplit(".", 1)
    module = __import__(module_path, fromlist=[class_name])
    return getattr(module, class_name)


async def create_replacement_strategy(
    source_agent_name: str,
    initial_rate: float = 0.01,
    increase_step: float = 0.1
) -> Optional[GradualReplacementStrategy]:
    """创建逐步替换策略"""
    if source_agent_name not in AGENT_MAPPING:
        logger.error(f"❌ 不支持的Agent: {source_agent_name}")
        logger.info(f"支持的Agent: {', '.join(AGENT_MAPPING.keys())}")
        return None
    
    mapping = AGENT_MAPPING[source_agent_name]
    
    try:
        # 导入旧Agent
        OldAgentClass = import_class(mapping["old_class"])
        old_agent = OldAgentClass()
        logger.info(f"✅ 旧Agent初始化成功: {source_agent_name}")
        
        # 导入适配器
        AdapterClass = import_class(mapping["adapter_class"])
        adapter = AdapterClass()
        logger.info(f"✅ 适配器初始化成功: {source_agent_name} → {mapping['target_agent']}")
        
        # 获取新Agent（通过适配器）
        new_agent = adapter.target_agent
        logger.info(f"✅ 新Agent初始化成功: {mapping['target_agent']}")
        
        # 创建逐步替换策略
        strategy = GradualReplacementStrategy(
            old_agent=old_agent,
            new_agent=new_agent,
            adapter=adapter
        )
        
        # 设置初始替换比例
        strategy.replacement_rate = initial_rate
        logger.info(f"✅ 逐步替换策略创建成功，初始替换比例: {initial_rate:.0%}")
        
        return strategy
        
    except Exception as e:
        logger.error(f"❌ 创建逐步替换策略失败: {e}", exc_info=True)
        return None


async def simulate_requests(strategy: GradualReplacementStrategy, num_requests: int = 10):
    """模拟请求以测试替换策略"""
    logger.info(f"🔄 开始模拟 {num_requests} 个请求...")
    
    test_context = {
        "query": "测试查询：逐步替换策略测试",
        "session_id": "test_session"
    }
    
    for i in range(num_requests):
        try:
            result = await strategy.execute_with_gradual_replacement(test_context)
            executed_by = result.get("_executed_by", "unknown")
            replacement_rate = result.get("_replacement_rate", 0.0)
            logger.debug(f"请求 {i+1}: 由 {executed_by} 执行 (替换比例: {replacement_rate:.0%})")
        except Exception as e:
            logger.error(f"请求 {i+1} 执行失败: {e}")
    
    # 获取统计信息
    stats = strategy.get_replacement_stats()
    logger.info(f"📊 统计信息:")
    logger.info(f"   替换比例: {stats['replacement_rate']:.0%}")
    logger.info(f"   新Agent成功率: {stats['new_agent_success_rate']:.2%}")
    logger.info(f"   旧Agent成功率: {stats['old_agent_success_rate']:.2%}")
    logger.info(f"   新Agent总调用数: {stats['new_agent_total_calls']}")
    logger.info(f"   旧Agent总调用数: {stats['old_agent_total_calls']}")
    logger.info(f"   是否应该增加替换比例: {stats['should_increase_rate']}")
    logger.info(f"   是否应该完成替换: {stats['should_complete']}")


async def monitor_and_adjust(
    strategy: GradualReplacementStrategy,
    check_interval: float = 120.0,
    increase_step: float = 0.1,
    max_rate: float = 1.0
):
    """监控并自动调整替换比例"""
    logger.info(f"🔄 开始监控逐步替换...")
    logger.info(f"   检查间隔: {check_interval}秒 ({check_interval/60:.1f}分钟)")
    logger.info(f"   增加步长: {increase_step:.0%}")
    logger.info(f"   最大替换比例: {max_rate:.0%}")
    
    iteration = 0
    
    while strategy.replacement_rate < max_rate:
        iteration += 1
        logger.info(f"\n{'='*60}")
        logger.info(f"第 {iteration} 次检查 (替换比例: {strategy.replacement_rate:.0%})")
        logger.info(f"{'='*60}")
        
        # 获取统计信息
        stats = strategy.get_replacement_stats()
        
        logger.info(f"📊 当前统计:")
        logger.info(f"   替换比例: {stats['replacement_rate']:.0%}")
        logger.info(f"   新Agent成功率: {stats['new_agent_success_rate']:.2%}")
        logger.info(f"   新Agent总调用数: {stats['new_agent_total_calls']}")
        
        # 检查是否应该增加替换比例
        if strategy.should_increase_rate():
            old_rate = strategy.replacement_rate
            new_rate = strategy.increase_replacement_rate(step=increase_step)
            logger.info(f"✅ 替换比例已增加: {old_rate:.0%} → {new_rate:.0%}")
        else:
            logger.info(f"⏸️  暂不增加替换比例 (需要成功率≥95%且至少100次调用)")
        
        # 检查是否应该完成替换
        if strategy.should_complete_replacement():
            logger.info(f"🎉 替换已完成！可以移除旧Agent代码")
            break
        
        # 等待下一次检查
        logger.info(f"⏳ 等待 {check_interval/60:.1f} 分钟后进行下一次检查...")
        await asyncio.sleep(check_interval)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="启动逐步替换策略")
    parser.add_argument(
        "--source",
        required=True,
        help="源Agent名称 (例如: ReActAgent, KnowledgeRetrievalAgent)"
    )
    parser.add_argument(
        "--target",
        help="目标Agent名称 (可选，会自动从映射表获取)"
    )
    parser.add_argument(
        "--initial-rate",
        type=float,
        default=0.01,
        help="初始替换比例 (默认: 0.01, 即1%%)"
    )
    parser.add_argument(
        "--increase-step",
        type=float,
        default=0.1,
        help="每次增加的步长 (默认: 0.1, 即10%%)"
    )
    parser.add_argument(
        "--check-interval",
        type=float,
        default=120.0,
        help="检查间隔（秒）(默认: 120, 即2分钟)"
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="测试模式：只运行少量请求测试，不启动监控"
    )
    parser.add_argument(
        "--test-requests",
        type=int,
        default=10,
        help="测试模式下的请求数量 (默认: 10)"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("逐步替换策略启动")
    print("=" * 80)
    print(f"源Agent: {args.source}")
    print(f"初始替换比例: {args.initial_rate:.0%}")
    print(f"增加步长: {args.increase_step:.0%}")
    print(f"检查间隔: {args.check_interval}秒 ({args.check_interval/60:.1f}分钟)")
    print("=" * 80)
    
    # 创建逐步替换策略
    strategy = await create_replacement_strategy(
        source_agent_name=args.source,
        initial_rate=args.initial_rate,
        increase_step=args.increase_step
    )
    
    if strategy is None:
        logger.error("❌ 无法创建逐步替换策略，退出")
        sys.exit(1)
    
    if args.test_mode:
        # 测试模式：只运行少量请求
        logger.info("🧪 测试模式：运行少量请求测试")
        await simulate_requests(strategy, num_requests=args.test_requests)
        logger.info("✅ 测试完成")
    else:
        # 正常模式：启动监控
        logger.info("🚀 正常模式：启动监控和自动调整")
        try:
            await monitor_and_adjust(
                strategy=strategy,
                check_interval=args.check_interval,
                increase_step=args.increase_step,
                max_rate=1.0
            )
        except KeyboardInterrupt:
            logger.info("\n⚠️  用户中断，停止监控")
            stats = strategy.get_replacement_stats()
            logger.info(f"📊 最终统计:")
            logger.info(f"   替换比例: {stats['replacement_rate']:.0%}")
            logger.info(f"   新Agent成功率: {stats['new_agent_success_rate']:.2%}")


if __name__ == "__main__":
    asyncio.run(main())

