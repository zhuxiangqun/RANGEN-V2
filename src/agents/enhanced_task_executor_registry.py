"""
增强版任务执行器注册表

提供动态注册、发现、配置和监控任务执行器的完整解决方案
"""

import logging
import importlib
import inspect
from typing import Dict, List, Any, Optional, Type, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from src.core.layered_architecture_types import TaskType, TaskResult

logger = logging.getLogger(__name__)


@dataclass
class ExecutorConfig:
    """执行器配置"""
    name: str
    module_path: str
    class_name: str
    enabled: bool = True
    priority: int = 0
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ExecutorInfo:
    """执行器信息"""
    name: str
    task_types: List[TaskType]
    version: str = "1.0.0"
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)


class TaskExecutor(ABC):
    """任务执行器抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """执行器名称"""
        pass

    @property
    @abstractmethod
    def supported_task_types(self) -> List[TaskType]:
        """支持的任务类型"""
        pass

    @abstractmethod
    async def execute(self, task_input: Dict[str, Any]) -> Any:
        """执行任务"""
        pass

    @abstractmethod
    def get_info(self) -> ExecutorInfo:
        """获取执行器信息"""
        pass

    async def health_check(self) -> bool:
        """健康检查"""
        return True

    async def warmup(self) -> bool:
        """预热"""
        return True


class EnhancedTaskExecutorRegistry:
    """
    增强版任务执行器注册表

    特性：
    - 动态注册和发现
    - 配置驱动
    - 健康检查和监控
    - 优先级和负载均衡
    - 插件化架构
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 注册表存储
        self._executors: Dict[str, TaskExecutor] = {}
        self._task_type_mapping: Dict[TaskType, List[str]] = {}
        self._configs: Dict[str, ExecutorConfig] = {}

        # 监控和统计
        self._execution_stats: Dict[str, Dict[str, Any]] = {}
        self._health_status: Dict[str, bool] = {}

        # 自动发现的执行器
        self._auto_discovery_patterns = [
            "src.agents.executors.*",
            "src.services.*_service"
        ]

    async def initialize(self):
        """初始化注册表"""
        self.logger.info("🚀 初始化增强版任务执行器注册表")

        # 注册内置执行器
        await self._register_builtin_executors()

        # 自动发现执行器
        await self._auto_discover_executors()

        # 执行健康检查
        await self._perform_health_checks()

        # 预热执行器
        await self._warmup_executors()

        self.logger.info(f"✅ 注册表初始化完成，注册了 {len(self._executors)} 个执行器")

    async def register_executor(
        self,
        executor: TaskExecutor,
        config: Optional[ExecutorConfig] = None
    ) -> bool:
        """注册执行器"""

        executor_name = executor.name

        try:
            # 检查是否已注册
            if executor_name in self._executors:
                self.logger.warning(f"⚠️ 执行器 {executor_name} 已存在，将被替换")

            # 注册执行器
            self._executors[executor_name] = executor

            # 更新任务类型映射
            for task_type in executor.supported_task_types:
                if task_type not in self._task_type_mapping:
                    self._task_type_mapping[task_type] = []
                self._task_type_mapping[task_type].append(executor_name)

            # 保存配置
            if config:
                self._configs[executor_name] = config

            # 初始化统计信息
            self._execution_stats[executor_name] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "average_execution_time": 0.0,
                "last_execution_time": None,
                "error_rate": 0.0
            }

            self.logger.info(f"✅ 注册执行器: {executor_name} (支持: {[t.value for t in executor.supported_task_types]})")

            return True

        except Exception as e:
            self.logger.error(f"❌ 注册执行器 {executor_name} 失败: {e}")
            return False

    def unregister_executor(self, executor_name: str) -> bool:
        """注销执行器"""

        if executor_name not in self._executors:
            self.logger.warning(f"⚠️ 执行器 {executor_name} 不存在")
            return False

        try:
            # 移除任务类型映射
            executor = self._executors[executor_name]
            for task_type in executor.supported_task_types:
                if task_type in self._task_type_mapping:
                    self._task_type_mapping[task_type] = [
                        name for name in self._task_type_mapping[task_type]
                        if name != executor_name
                    ]
                    if not self._task_type_mapping[task_type]:
                        del self._task_type_mapping[task_type]

            # 移除注册表条目
            del self._executors[executor_name]
            if executor_name in self._configs:
                del self._configs[executor_name]
            if executor_name in self._execution_stats:
                del self._execution_stats[executor_name]
            if executor_name in self._health_status:
                del self._health_status[executor_name]

            self.logger.info(f"✅ 注销执行器: {executor_name}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 注销执行器 {executor_name} 失败: {e}")
            return False

    def get_executor(self, task_type: TaskType, executor_name: Optional[str] = None) -> Optional[TaskExecutor]:
        """获取执行器"""

        if executor_name:
            # 指定执行器名称
            return self._executors.get(executor_name)

        # 根据任务类型选择执行器
        candidates = self._task_type_mapping.get(task_type, [])

        if not candidates:
            self.logger.warning(f"⚠️ 没有找到支持任务类型 {task_type.value} 的执行器")
            return None

        # 选择健康且负载最低的执行器
        healthy_candidates = [
            name for name in candidates
            if self._health_status.get(name, False)
        ]

        if not healthy_candidates:
            self.logger.warning(f"⚠️ 没有健康的执行器支持任务类型 {task_type.value}")
            return None

        # 简单的负载均衡：选择执行次数最少的
        selected_name = min(
            healthy_candidates,
            key=lambda name: self._execution_stats[name]["total_executions"]
        )

        return self._executors[selected_name]

    async def execute_task(
        self,
        task_type: TaskType,
        task_input: Dict[str, Any],
        executor_name: Optional[str] = None,
        timeout: float = 30.0
    ) -> TaskResult:
        """执行任务"""

        import asyncio
        import time

        start_time = time.time()

        try:
            # 获取执行器
            executor = self.get_executor(task_type, executor_name)
            if not executor:
                return TaskResult(
                    task_id=task_input.get('task_id', 'unknown'),
                    task_type=task_type,
                    success=False,
                    error=f"未找到支持任务类型 {task_type.value} 的执行器"
                )

            executor_name = executor.name

            # 执行任务（带超时）
            result = await asyncio.wait_for(
                executor.execute(task_input),
                timeout=timeout
            )

            execution_time = time.time() - start_time

            # 更新统计信息
            self._update_execution_stats(executor_name, True, execution_time)

            # 构造任务结果
            task_result = TaskResult(
                task_id=task_input.get('task_id', 'unknown'),
                task_type=task_type,
                success=True,
                result=result,
                execution_time=execution_time,
                quality_score=getattr(result, 'quality_score', 0.8),
                metadata={
                    "executor": executor_name,
                    "execution_time": execution_time
                }
            )

            return task_result

        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            error_msg = f"任务执行超时 ({timeout}s)"
            self.logger.error(f"❌ {error_msg}")

            if executor:
                self._update_execution_stats(executor.name, False, execution_time)

            return TaskResult(
                task_id=task_input.get('task_id', 'unknown'),
                task_type=task_type,
                success=False,
                error=error_msg,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"任务执行失败: {e}"
            self.logger.error(f"❌ {error_msg}", exc_info=True)

            if executor:
                self._update_execution_stats(executor.name, False, execution_time)

            return TaskResult(
                task_id=task_input.get('task_id', 'unknown'),
                task_type=task_type,
                success=False,
                error=str(e),
                execution_time=execution_time
            )

    def list_executors(self) -> List[Dict[str, Any]]:
        """列出所有执行器"""

        result = []
        for name, executor in self._executors.items():
            info = executor.get_info()
            stats = self._execution_stats.get(name, {})
            health = self._health_status.get(name, False)
            config = self._configs.get(name)

            result.append({
                "name": name,
                "task_types": [t.value for t in info.task_types],
                "version": info.version,
                "description": info.description,
                "capabilities": info.capabilities,
                "healthy": health,
                "stats": stats,
                "config": config.config if config else {},
                "enabled": config.enabled if config else True
            })

        return result

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""

        total_executors = len(self._executors)
        healthy_executors = sum(1 for h in self._health_status.values() if h)
        total_executions = sum(stats["total_executions"] for stats in self._execution_stats.values())
        successful_executions = sum(stats["successful_executions"] for stats in self._execution_stats.values())

        return {
            "total_executors": total_executors,
            "healthy_executors": healthy_executors,
            "health_rate": healthy_executors / total_executors if total_executors > 0 else 0,
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
            "task_type_coverage": list(self._task_type_mapping.keys()),
            "executor_details": {
                name: stats for name, stats in self._execution_stats.items()
            }
        }

    async def _register_builtin_executors(self):
        """注册内置执行器"""

        # 导入模拟执行器
        try:
            from src.agents.task_executor_adapter import MockTaskExecutor

            # 为所有任务类型注册模拟执行器
            for task_type in TaskType:
                mock_executor = MockTaskExecutor(task_type.value)
                await self.register_executor(mock_executor)

            self.logger.info("✅ 内置模拟执行器注册完成")

        except ImportError:
            self.logger.warning("⚠️ 无法导入模拟执行器")

    async def _auto_discover_executors(self):
        """自动发现执行器"""

        # 这里可以实现自动发现逻辑
        # 扫描指定模块路径，查找TaskExecutor子类
        self.logger.info("🔍 执行器自动发现功能（待实现）")

    async def _perform_health_checks(self):
        """执行健康检查"""

        self.logger.info("🏥 执行器健康检查")

        for name, executor in self._executors.items():
            try:
                healthy = await executor.health_check()
                self._health_status[name] = healthy

                if healthy:
                    self.logger.debug(f"✅ 执行器 {name} 健康检查通过")
                else:
                    self.logger.warning(f"⚠️ 执行器 {name} 健康检查失败")

            except Exception as e:
                self.logger.error(f"❌ 执行器 {name} 健康检查异常: {e}")
                self._health_status[name] = False

    async def _warmup_executors(self):
        """预热执行器"""

        self.logger.info("🔥 执行器预热")

        for name, executor in self._executors.items():
            try:
                success = await executor.warmup()
                if success:
                    self.logger.debug(f"✅ 执行器 {name} 预热成功")
                else:
                    self.logger.warning(f"⚠️ 执行器 {name} 预热失败")

            except Exception as e:
                self.logger.error(f"❌ 执行器 {name} 预热异常: {e}")

    def _update_execution_stats(self, executor_name: str, success: bool, execution_time: float):
        """更新执行统计"""

        if executor_name not in self._execution_stats:
            return

        stats = self._execution_stats[executor_name]
        stats["total_executions"] += 1
        stats["last_execution_time"] = execution_time

        if success:
            stats["successful_executions"] += 1
        else:
            stats["failed_executions"] += 1

        # 更新错误率
        total = stats["total_executions"]
        failed = stats["failed_executions"]
        stats["error_rate"] = failed / total if total > 0 else 0

        # 更新平均执行时间（指数移动平均）
        alpha = 0.1  # 平滑因子
        current_avg = stats["average_execution_time"]
        stats["average_execution_time"] = alpha * execution_time + (1 - alpha) * current_avg


# 全局注册表实例
_global_enhanced_registry = None

def get_enhanced_registry() -> EnhancedTaskExecutorRegistry:
    """获取增强版执行器注册表实例"""
    global _global_enhanced_registry
    if _global_enhanced_registry is None:
        _global_enhanced_registry = EnhancedTaskExecutorRegistry()
    return _global_enhanced_registry

async def initialize_enhanced_registry() -> EnhancedTaskExecutorRegistry:
    """初始化增强版注册表"""
    registry = get_enhanced_registry()
    await registry.initialize()
    return registry
