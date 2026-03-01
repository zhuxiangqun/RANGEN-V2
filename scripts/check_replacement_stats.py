#!/usr/bin/env python3
"""
检查逐步替换统计信息

查看指定Agent的逐步替换统计信息。
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.strategies.gradual_replacement import GradualReplacementStrategy
from scripts.start_gradual_replacement import AGENT_MAPPING, import_class, create_replacement_strategy
import asyncio


async def check_stats(source_agent_name: str):
    """检查统计信息"""
    if source_agent_name not in AGENT_MAPPING:
        print(f"❌ 不支持的Agent: {source_agent_name}")
        print(f"支持的Agent: {', '.join(AGENT_MAPPING.keys())}")
        return
    
    print("=" * 80)
    print(f"逐步替换统计信息: {source_agent_name}")
    print("=" * 80)
    
    # 创建策略（用于获取统计信息）
    strategy = await create_replacement_strategy(
        source_agent_name=source_agent_name,
        initial_rate=0.0
    )
    
    if strategy is None:
        print("❌ 无法创建策略")
        return
    
    # 获取统计信息
    stats = strategy.get_replacement_stats()
    
    print(f"\n📊 替换统计:")
    print(f"   源Agent: {stats['old_agent']}")
    print(f"   目标Agent: {stats['new_agent']}")
    print(f"   当前替换比例: {stats['replacement_rate']:.0%}")
    print(f"\n📈 成功率:")
    print(f"   新Agent成功率: {stats['new_agent_success_rate']:.2%}")
    print(f"   旧Agent成功率: {stats['old_agent_success_rate']:.2%}")
    print(f"\n📞 调用统计:")
    print(f"   新Agent总调用数: {stats['new_agent_total_calls']}")
    print(f"   旧Agent总调用数: {stats['old_agent_total_calls']}")
    print(f"\n🎯 建议:")
    print(f"   是否应该增加替换比例: {'✅ 是' if stats['should_increase_rate'] else '❌ 否'}")
    print(f"   是否应该完成替换: {'✅ 是' if stats['should_complete'] else '❌ 否'}")
    
    # 检查日志文件
    log_file = Path(f"logs/replacement_progress_{source_agent_name}.log")
    if log_file.exists():
        print(f"\n📝 日志文件: {log_file}")
        print(f"   文件大小: {log_file.stat().st_size} 字节")
        # 读取最后几行
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if lines:
                print(f"   最后更新: {lines[-1].strip()}")
    else:
        print(f"\n📝 日志文件: {log_file} (不存在)")
    
    print("=" * 80)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="检查逐步替换统计信息")
    parser.add_argument(
        "--agent",
        required=True,
        help="Agent名称 (例如: ReActAgent, KnowledgeRetrievalAgent)"
    )
    
    args = parser.parse_args()
    
    asyncio.run(check_stats(args.agent))


if __name__ == "__main__":
    main()

