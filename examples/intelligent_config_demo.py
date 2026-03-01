#!/usr/bin/env python3
"""
智能动态配置使用示例
展示如何在实际系统中使用智能动态配置管理器
"""

import asyncio
import time
import random
from datetime import datetime
from typing import Dict, Any

# 导入智能配置管理器
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.intelligent_config_manager import (
    get_intelligent_config, 
    record_task_performance, 
    TaskMetrics,
    intelligent_config_manager,
    ConfigAdjustmentStrategy
)

class SmartAgent:
    """使用智能动态配置的智能体示例"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.execution_count = 0
    
    async def execute_task(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务，使用智能动态配置"""
        start_time = time.time()
        
        # 获取智能动态配置
        dynamic_config = get_intelligent_config(self.agent_name, task_context)
        print(f"🔧 智能体 {self.agent_name} 动态配置: {dynamic_config}")
        
        # 模拟任务执行
        execution_time = random.uniform(1, 5)  # 模拟执行时间
        await asyncio.sleep(execution_time)
        
        # 模拟成功率（基于配置质量）
        success_rate = self._calculate_success_rate(dynamic_config, task_context)
        success = random.random() < success_rate
        
        # 计算资源消耗
        resource_consumption = self._calculate_resource_consumption(dynamic_config)
        
        # 记录任务指标
        task_metrics = TaskMetrics(
            complexity_score=task_context.get("complexity", get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value"))),
            execution_time=time.time() - start_time,
            success_rate=success_rate,
            resource_consumption=resource_consumption,
            error_rate=get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")) - success_rate
        )
        
        record_task_performance(self.agent_name, task_metrics)
        
        self.execution_count += 1
        
        return {
            "success": success,
            "execution_time": execution_time,
            "config_used": dynamic_config,
            "performance_metrics": task_metrics
        }
    
    def _calculate_success_rate(self, config: Dict[str, Any], context: Dict[str, Any]) -> float:
        """基于配置和上下文计算成功率"""
        base_rate = get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold"))
        
        # 根据配置参数调整成功率
        if config.get("max_iterations", get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit"))) > 15:
            base_rate += 0.1  # 更多迭代次数提高成功率
        
        if config.get("temperature", 0.1) < 0.2:
            base_rate += 0.05  # 较低温度提高稳定性
        
        # 根据任务复杂度调整
        complexity = context.get("complexity", get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")))
        if complexity > get_smart_config("DEFAULT_TWO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_two_value")):
            base_rate -= 0.2  # 高复杂度任务成功率降低
        
        return max(0.1, min(get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")), base_rate))
    
    def _calculate_resource_consumption(self, config: Dict[str, Any]) -> float:
        """计算资源消耗"""
        base_consumption = get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit"))  # MB
        
        # 根据配置调整资源消耗
        memory_limit = config.get("memory_limit", 256)
        concurrent_tasks = config.get("concurrent_tasks", 1)
        
        return base_consumption * (memory_limit / 256) * concurrent_tasks

async def demo_basic_usage():
    """基础使用示例"""
    print("🚀 智能动态配置基础使用示例")
    print("=" * 50)
    
    # 创建智能体
    reasoning_agent = SmartAgent("reasoning_agent")
    analysis_agent = SmartAgent("analysis_agent")
    
    # 执行简单任务
    simple_task = {
        "query": "什么是人工智能？",
        "complexity": get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")),
        "domain": "general"
    }
    
    print(f"📝 执行简单任务: {simple_task['query']}")
    result1 = await reasoning_agent.execute_task(simple_task)
    print(f"✅ 任务结果: {result1['success']}")
    
    # 执行复杂任务
    complex_task = {
        "query": "请详细分析量子计算在密码学中的应用，包括Shor算法、Grover算法等，并讨论其对现有加密标准的影响",
        "complexity": 2.5,
        "domain": "technical",
        "required_agents": ["reasoning", "analysis", "citation"]
    }
    
    print(f"\n📝 执行复杂任务: {complex_task['query'][self._get_dynamic_context_limit()]}...")
    result2 = await reasoning_agent.execute_task(complex_task)
    print(f"✅ 任务结果: {result2['success']}")
    
    # 查看系统状态
    status = intelligent_config_manager.get_system_status()
    print(f"\n📊 系统状态:")
    print(f"  调整因子: {status['adjustment_factors']}")
    print(f"  成功率: {status['performance_history']['success_rate']:.2%}")

async def demo_adaptive_behavior():
    """自适应行为示例"""
    print("\n🧠 智能动态配置自适应行为示例")
    print("=" * 50)
    
    agent = SmartAgent("analysis_agent")
    
    # 模拟不同复杂度的任务序列
    tasks = [
        {"query": "简单查询", "complexity": get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")), "domain": "general"},
        {"query": "中等复杂度查询", "complexity": 1.5, "domain": "academic"},
        {"query": "高复杂度查询", "complexity": 2.8, "domain": "technical"},
        {"query": "超高复杂度查询", "complexity": 3.0, "domain": "scientific"},
    ]
    
    for i, task in enumerate(tasks, 1):
        print(f"\n🔄 第{i}轮任务: {task['query']}")
        
        # 执行任务
        result = await agent.execute_task(task)
        
        # 显示配置变化
        print(f"   复杂度: {task['complexity']}")
        print(f"   成功率: {result['performance_metrics'].success_rate:.2%}")
        print(f"   执行时间: {result['execution_time']:.2f}s")
        
        # 等待一段时间让系统调整
        await asyncio.sleep(2)

async def demo_strategy_switching():
    """策略切换示例"""
    print("\n⚙️ 智能动态配置策略切换示例")
    print("=" * 50)
    
    agent = SmartAgent("citation_agent")
    
    # 测试不同策略
    strategies = [
        ("conservative", "保守策略"),
        ("aggressive", "激进策略"),
        ("adaptive", "自适应策略"),
        ("learning", "学习策略")
    ]
    
    for strategy_name, strategy_desc in strategies:
        print(f"\n🎯 切换到{strategy_desc}")
        strategy_enum = ConfigAdjustmentStrategy(strategy_name)
        intelligent_config_manager.set_adjustment_strategy(strategy_enum)
        
        # 执行相同任务
        task = {
            "query": "测试查询",
            "complexity": 1.5,
            "domain": "academic"
        }
        
        result = await agent.execute_task(task)
        print(f"   配置: {result['config_used']}")
        print(f"   成功率: {result['performance_metrics'].success_rate:.2%}")
        
        await asyncio.sleep(1)

async def demo_performance_monitoring():
    """性能监控示例"""
    print("\n📈 智能动态配置性能监控示例")
    print("=" * 50)
    
    agents = [
        SmartAgent("reasoning_agent"),
        SmartAgent("analysis_agent"),
        SmartAgent("citation_agent")
    ]
    
    # 执行多轮任务
    for round_num in range(5):
        print(f"\n🔄 第{round_num + 1}轮性能测试")
        
        for agent in agents:
            task = {
                "query": f"第{round_num + 1}轮测试查询",
                "complexity": random.uniform(get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")), 2.5),
                "domain": random.choice(["general", "academic", "technical"])
            }
            
            result = await agent.execute_task(task)
            print(f"  {agent.agent_name}: 成功率={result['performance_metrics'].success_rate:.2%}")
        
        # 显示系统状态
        status = intelligent_config_manager.get_system_status()
        print(f"  系统成功率: {status['performance_history']['success_rate']:.2%}")
        print(f"  CPU使用率: {status['system_metrics']['cpu_usage']:.1%}")
        
        await asyncio.sleep(1)

async def main():
    """主函数"""
    print("🎯 智能动态配置系统演示")
    print("=" * 60)
    
    # 等待系统初始化
    print("⏳ 等待智能配置管理器初始化...")
    await asyncio.sleep(3)
    
    # 运行各种演示
    await demo_basic_usage()
    await demo_adaptive_behavior()
    await demo_strategy_switching()
    await demo_performance_monitoring()
    
    # 最终状态报告
    print("\n📋 最终系统状态报告")
    print("=" * 50)
    final_status = intelligent_config_manager.get_system_status()
    
    print(f"总执行次数: {final_status['performance_history']['total_executions']}")
    print(f"整体成功率: {final_status['performance_history']['success_rate']:.2%}")
    print(f"当前调整策略: {final_status['adjustment_strategy']}")
    print(f"学习率: {final_status['learning_params']['learning_rate']:.3f}")
    print(f"探索率: {final_status['learning_params']['exploration_rate']:.3f}")
    
    print("\n🎉 智能动态配置演示完成！")

if __name__ == "__main__":
    asyncio.run(main()) 