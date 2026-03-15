#!/usr/bin/env python3
"""
增强版任务执行器注册表演示

展示增强版注册表的功能：
- 动态注册和发现
- 配置驱动管理
- 健康检查和监控
- 负载均衡和优先级
"""

import asyncio
import logging
from typing import Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DemoTaskExecutor:
    """演示任务执行器"""

    def __init__(self, name: str, task_types, version: str = "1.0.0"):
        self._name = name
        self._task_types = task_types
        self._version = version
        self.execution_count = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def supported_task_types(self):
        return self._task_types

    def get_info(self):
        """获取执行器信息"""
        from src.agents.enhanced_task_executor_registry import ExecutorInfo
        return ExecutorInfo(
            name=self._name,
            task_types=self._task_types,
            version=self._version,
            description=f"演示执行器 {self._name}",
            capabilities=["demo", "test"]
        )

    async def health_check(self) -> bool:
        """健康检查"""
        import random
        return random.random() < 0.9  # 90%成功率

    async def warmup(self) -> bool:
        """预热"""
        return True

    async def execute(self, task_input: Dict[str, Any]) -> Any:
        """执行任务"""
        import random
        import asyncio

        self.execution_count += 1

        # 模拟执行时间
        execution_time = random.uniform(0.1, 1.0)
        await asyncio.sleep(execution_time)

        # 模拟结果
        result = {
            'task_type': task_input.get('task_type'),
            'task_id': task_input.get('task_id'),
            'result': f"{self._name} 执行结果 #{self.execution_count}",
            'execution_time': execution_time,
            'quality_score': random.uniform(0.7, 0.95),
            'executor': self._name
        }

        logger.info(f"✅ {self._name} 执行完成: {result['result']}")
        return result

    def get_info(self):
        """获取执行器信息"""
        from src.agents.enhanced_task_executor_registry import ExecutorInfo
        from src.core.layered_architecture_types import TaskType

        return ExecutorInfo(
            name=self._name,
            task_types=self._task_types,
            version=self._version,
            description=f"演示执行器 {self._name}",
            capabilities=["demo", "test"],
            config_schema={}
        )

    async def health_check(self) -> bool:
        """健康检查"""
        # 简单的健康检查：随机成功率90%
        import random
        return random.random() < 0.9

    async def warmup(self) -> bool:
        """预热"""
        logger.info(f"🔥 {self._name} 预热中...")
        await asyncio.sleep(0.1)
        logger.info(f"✅ {self._name} 预热完成")
        return True


async def demo_registry_basic():
    """演示注册表基本功能"""

    logger.info("🎯 演示注册表基本功能")

    # 初始化注册表
    from src.agents.enhanced_task_executor_registry import initialize_enhanced_registry
    registry = await initialize_enhanced_registry()

    # 创建演示执行器
    from src.core.layered_architecture_types import TaskType

    executor1 = DemoTaskExecutor("DemoExecutor1", [TaskType.KNOWLEDGE_RETRIEVAL, TaskType.ANSWER_GENERATION])
    executor2 = DemoTaskExecutor("DemoExecutor2", [TaskType.REASONING, TaskType.ANALYSIS])

    # 注册执行器
    await registry.register_executor(executor1)
    await registry.register_executor(executor2)

    logger.info("✅ 执行器注册完成")

    # 列出执行器
    executors = registry.list_executors()
    logger.info(f"📋 注册表中的执行器: {len(executors)} 个")
    for executor in executors:
        logger.info(f"  - {executor['name']}: {executor['task_types']} (健康: {executor['healthy']})")


async def demo_task_execution():
    """演示任务执行"""

    logger.info("🎯 演示任务执行")

    from src.agents.enhanced_task_executor_registry import get_enhanced_registry
    from src.core.layered_architecture_types import TaskType

    registry = get_enhanced_registry()

    # 执行不同类型的任务
    tasks = [
        (TaskType.KNOWLEDGE_RETRIEVAL, "检索人工智能相关知识"),
        (TaskType.REASONING, "分析人工智能发展趋势"),
        (TaskType.ANSWER_GENERATION, "生成人工智能答案"),
        (TaskType.ANALYSIS, "分析查询复杂度")
    ]

    results = []
    for task_type, description in tasks:
        logger.info(f"📋 执行任务: {task_type.value} - {description}")

        task_input = {
            'task_id': f"task_{len(results) + 1}",
            'task_type': task_type.value,
            'description': description,
            'query': f"演示查询: {description}"
        }

        # 执行任务
        result = await registry.execute_task(task_type, task_input)

        results.append(result)

        if result.success:
            logger.info(f"✅ 任务成功: {result.result.get('result', 'N/A')}")
        else:
            logger.error(f"❌ 任务失败: {result.error}")

    # 显示统计信息
    stats = registry.get_stats()
    logger.info("📊 执行统计:")
    logger.info(f"  总执行数: {stats['total_executions']}")
    logger.info(f"  成功率: {stats['success_rate']:.1%}")
    logger.info(".1%")
    # 显示各执行器详情
    logger.info("📈 执行器详情:")
    for name, executor_stats in stats['executor_details'].items():
        logger.info(f"  {name}: 执行{executor_stats['total_executions']}次, 成功{executor_stats['successful_executions']}次")


async def demo_load_balancing():
    """演示负载均衡"""

    logger.info("🎯 演示负载均衡")

    from src.agents.enhanced_task_executor_registry import get_enhanced_registry
    from src.core.layered_architecture_types import TaskType

    registry = get_enhanced_registry()

    # 创建多个相同类型的执行器
    for i in range(3):
        executor = DemoTaskExecutor(f"LoadBalancedExecutor{i+1}", [TaskType.KNOWLEDGE_RETRIEVAL])
        await registry.register_executor(executor)

    # 执行多个相同类型的任务
    logger.info("🔄 执行10个相同类型的任务，观察负载均衡...")

    for i in range(10):
        task_input = {
            'task_id': f"load_balance_task_{i+1}",
            'task_type': TaskType.KNOWLEDGE_RETRIEVAL.value,
            'description': f"负载均衡测试任务 {i+1}"
        }

        result = await registry.execute_task(TaskType.KNOWLEDGE_RETRIEVAL, task_input)

        if result.success:
            executor_name = result.result.get('executor', 'unknown')
            logger.info(f"✅ 任务{i+1} 由 {executor_name} 执行")

    # 显示负载分布
    stats = registry.get_stats()
    logger.info("⚖️ 负载分布:")
    for name, executor_stats in stats['executor_details'].items():
        if 'LoadBalancedExecutor' in name:
            logger.info(f"  {name}: {executor_stats['total_executions']} 次执行")


async def demo_health_monitoring():
    """演示健康监控"""

    logger.info("🎯 演示健康监控")

    from src.agents.enhanced_task_executor_registry import get_enhanced_registry
    from src.core.layered_architecture_types import TaskType

    registry = get_enhanced_registry()

    # 检查初始健康状态
    executors = registry.list_executors()
    healthy_count = sum(1 for e in executors if e['healthy'])
    total_count = len(executors)

    logger.info(f"🏥 初始健康状态: {healthy_count}/{total_count} 个执行器健康")

    # 模拟执行器故障（通过多次执行让健康检查失败）
    logger.info("💥 模拟执行器故障...")

    # 执行大量任务，让健康检查随机失败
    for i in range(20):
        task_input = {
            'task_id': f"health_test_{i+1}",
            'task_type': TaskType.KNOWLEDGE_RETRIEVAL.value,
            'description': f"健康测试任务 {i+1}"
        }

        await registry.execute_task(TaskType.KNOWLEDGE_RETRIEVAL, task_input)

    # 再次检查健康状态
    executors = registry.list_executors()
    healthy_count = sum(1 for e in executors if e['healthy'])
    total_count = len(executors)

    logger.info(f"🏥 更新后健康状态: {healthy_count}/{total_count} 个执行器健康")

    # 显示失败的任务
    failed_tasks = [e for e in executors if not e['healthy']]
    if failed_tasks:
        logger.info("❌ 不健康的执行器:")
        for executor in failed_tasks:
            logger.info(f"  - {executor['name']}")


async def demo_registry_management():
    """演示注册表管理"""

    logger.info("🎯 演示注册表管理")

    from src.agents.enhanced_task_executor_registry import get_enhanced_registry
    from src.core.layered_architecture_types import TaskType

    registry = get_enhanced_registry()

    # 注册一个新执行器
    new_executor = DemoTaskExecutor("TempExecutor", [TaskType.CITATION])
    await registry.register_executor(new_executor)

    logger.info(f"✅ 注册新执行器: {new_executor.name}")

    # 验证可以执行新类型的任务
    task_input = {
        'task_id': 'citation_test',
        'task_type': TaskType.CITATION.value,
        'description': '测试引用生成'
    }

    result = await registry.execute_task(TaskType.CITATION, task_input)

    if result.success:
        logger.info(f"✅ 新任务类型执行成功: {result.result.get('result')}")
    else:
        logger.error(f"❌ 新任务类型执行失败: {result.error}")

    # 注销执行器
    success = registry.unregister_executor("TempExecutor")
    if success:
        logger.info("✅ 执行器注销成功")

    # 验证任务类型不再可用
    result = await registry.execute_task(TaskType.CITATION, task_input)
    if not result.success:
        logger.info("✅ 已确认任务类型不再可用")


async def main():
    """主函数"""

    print("🚀 增强版任务执行器注册表演示")
    print("=" * 50)

    try:
        # 演示基本功能
        await demo_registry_basic()

        print()

        # 演示任务执行
        await demo_task_execution()

        print()

        # 演示负载均衡
        await demo_load_balancing()

        print()

        # 演示健康监控
        await demo_health_monitoring()

        print()

        # 演示注册表管理
        await demo_registry_management()

        print("\n🎯 演示完成！")

        # 最终统计
        from src.agents.enhanced_task_executor_registry import get_enhanced_registry
        registry = get_enhanced_registry()
        final_stats = registry.get_stats()

        print("\n📊 最终统计:")
        print(f"总执行器数: {final_stats['total_executors']}")
        print(f"健康执行器数: {final_stats['healthy_executors']}")
        print(f"总执行次数: {final_stats['total_executions']}")
        print(".1%")
        print(f"支持的任务类型: {[t.value for t in final_stats['task_type_coverage']]}")

    except Exception as e:
        logger.error(f"❌ 演示失败: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
