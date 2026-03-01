"""
异步组件管理器 - 管理所有系统组件的生命周期和依赖关系
提供统一的组件注册、初始化、管理和清理功能
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Union, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
import weakref
import threading

logger = logging.getLogger(__name__)


class ComponentType(Enum):
    """组件类型枚举"""
    CONFIG = "config"
    LLM_CLIENT = "llm_client"
    MEMORY = "memory"
    AGENT = "agent"
    UTILITY = "utility"
    PLUGIN = "plugin"
    CUSTOM = "custom"


class ComponentState(Enum):
    """组件状态枚举"""
    UNREGISTERED = "unregistered"
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"
    DESTROYED = "destroyed"


@dataclass
class ComponentMetadata:
    """组件元数据"""
    name: str
    component_type: ComponentType
    state: ComponentState
    dependencies: List[str]
    factory_func: Optional[Callable] = None
    factory_args: tuple = ()
    factory_kwargs: Dict[str, Any] = field(default_factory=dict)
    instance: Optional[Any] = None
    created_at: Optional[float] = None
    initialized_at: Optional[float] = None
    error_message: Optional[str] = None
    cleanup_func: Optional[Callable] = None
    priority: int = 0  # 初始化优先级，数字越小优先级越高


class AsyncComponentManager:
    """异步组件管理器"""

    def __init__(self):
        self.components: Dict[str, ComponentMetadata] = {}
        self.component_instances: Dict[str, Any] = {}
        self.dependency_graph: Dict[str, List[str]] = {}
        self._registry_lock = asyncio.Lock()
        self._initialization_lock = asyncio.Lock()
        self._shutdown_lock = asyncio.Lock()
        self._is_shutting_down = False
        self._initialization_order: List[str] = []

    async def register_component(self, name: str, component_type: ComponentType,
                               factory_func: Optional[Callable] = None,
                               dependencies: Optional[List[str]] = None,
                               factory_args: tuple = (),
                               factory_kwargs: Optional[Dict[str, Any]] = None,
                               cleanup_func: Optional[Callable] = None,
                               priority: int = 0) -> None:
        """注册组件"""
        async with self._registry_lock:
            if name in self.components:
                logger.warning("组件 {name} 已存在，跳过注册")
                return

            metadata = ComponentMetadata(
                name=name,
                component_type=component_type,
                state=ComponentState.REGISTERED,
                dependencies=dependencies or [],
                factory_func=factory_func,
                factory_args=factory_args or (),
                factory_kwargs=factory_kwargs or {},
                cleanup_func=cleanup_func,
                priority=priority
            )

            self.components[name] = metadata
            self.dependency_graph[name] = dependencies or []

            logger.info("✅ 组件 {name} ({component_type.value}) 注册成功")

    async def initialize_component(self, name: str) -> Any:
        """初始化组件"""
        async with self._initialization_lock:
            if self._is_shutting_down:
                raise RuntimeError("系统正在关闭，无法初始化组件")

            if name not in self.components:
                raise ValueError(f"组件 {name} 未注册")

            metadata = self.components[name]

            if metadata.state == ComponentState.READY:
                return metadata.instance

            if metadata.state == ComponentState.INITIALIZING:
                while metadata.state == ComponentState.INITIALIZING:
                    await asyncio.sleep(0.1)
                return metadata.instance

            if not await self._check_dependencies(name):
                raise RuntimeError(f"组件 {name} 的依赖未满足")

            try:
                metadata.state = ComponentState.INITIALIZING
                metadata.created_at = time.time()

                if metadata.factory_func:
                    if asyncio.iscoroutinefunction(metadata.factory_func):
                        instance = await metadata.factory_func(*metadata.factory_args, **metadata.factory_kwargs)
                    else:
                        loop = asyncio.get_event_loop()
                        instance = await loop.run_in_executor(
                            None, metadata.factory_func, *metadata.factory_args, **metadata.factory_kwargs
                        )
                else:
                    instance = None

                metadata.instance = instance
                metadata.initialized_at = time.time()
                metadata.state = ComponentState.READY
                self.component_instances[name] = instance

                logger.info("✅ 组件 {name} 初始化成功")
                return instance

            except Exception as e:
                metadata.state = ComponentState.ERROR
                metadata.error_message = str(e)
                logger.error("❌ 组件 {name} 初始化失败: {e}")
                raise

    async def get_component(self, name: str, auto_initialize: bool = True) -> Any:
        """获取组件实例"""
        if name not in self.components:
            raise ValueError(f"组件 {name} 未注册")

        metadata = self.components[name]

        if metadata.state == ComponentState.READY:
            return metadata.instance

        if auto_initialize and metadata.state == ComponentState.REGISTERED:
            return await self.initialize_component(name)

        if metadata.state == ComponentState.ERROR:
            raise RuntimeError(f"组件 {name} 处于错误状态: {metadata.error_message}")

        raise RuntimeError(f"组件 {name} 状态不正确: {metadata.state}")

    async def initialize_all_components(self) -> None:
        """初始化所有组件"""
        logger.info("🔄 开始初始化所有组件...")

        self._initialization_order = self._calculate_initialization_order()

        for component_name in self._initialization_order:
            try:
                await self.initialize_component(component_name)
            except Exception as e:
                logger.error("❌ 组件 {component_name} 初始化失败: {e}")

        logger.info("✅ 所有组件初始化完成")

    def _calculate_initialization_order(self) -> List[str]:
        """计算组件初始化顺序（拓扑排序 + 优先级）"""
        visited = set()
        temp_visited = set()
        order = []

        def dfs(node):
            if node in temp_visited:
                raise RuntimeError(f"检测到循环依赖: {node}")
            if node in visited:
                return

            temp_visited.add(node)

            for dep in self.dependency_graph.get(node, []):
                dfs(dep)

            temp_visited.remove(node)
            visited.add(node)
            order.append(node)

        sorted_components = sorted(
            self.components.keys(),
            key=lambda x: self.components[x].priority
        )

        for component_name in sorted_components:
            dfs(component_name)

        return order

    async def _check_dependencies(self, component_name: str) -> bool:
        """检查组件依赖是否满足"""
        dependencies = self.dependency_graph.get(component_name, [])
        for dep in dependencies:
            if dep not in self.components:
                logger.warning("组件 {component_name} 的依赖 {dep} 未注册")
                return False

            dep_metadata = self.components[dep]
            if dep_metadata.state != ComponentState.READY:
                logger.warning("组件 {component_name} 的依赖 {dep} 未就绪: {dep_metadata.state}")
                return False

        return True

    async def shutdown_component(self, name: str) -> None:
        """关闭单个组件"""
        if name not in self.components:
            return

        metadata = self.components[name]

        if metadata.state in [ComponentState.SHUTTING_DOWN, ComponentState.DESTROYED]:
            return

        try:
            metadata.state = ComponentState.SHUTTING_DOWN

            if metadata.cleanup_func:
                if asyncio.iscoroutinefunction(metadata.cleanup_func):
                    await metadata.cleanup_func(metadata.instance)
                else:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, metadata.cleanup_func, metadata.instance)

            if metadata.instance and hasattr(metadata.instance, 'cleanup'):
                if asyncio.iscoroutinefunction(metadata.instance.cleanup):
                    await metadata.instance.cleanup()
                else:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, metadata.instance.cleanup)

            metadata.state = ComponentState.DESTROYED
            if name in self.component_instances:
                del self.component_instances[name]

            logger.info("✅ 组件 {name} 关闭成功")

        except Exception as e:
            logger.error("❌ 组件 {name} 关闭失败: {e}")

    async def shutdown_all_components(self) -> None:
        """关闭所有组件"""
        async with self._shutdown_lock:
            if self._is_shutting_down:
                return

            self._is_shutting_down = True
            logger.info("🔄 开始关闭所有组件...")

            shutdown_order = list(reversed(self._initialization_order))

            for component_name in shutdown_order:
                await self.shutdown_component(component_name)

            logger.info("✅ 所有组件关闭完成")

    def get_component_status(self, name: str) -> Optional[Dict[str, Any]]:
        """获取组件状态"""
        if name not in self.components:
            return None

        metadata = self.components[name]
        return {
            "name": metadata.name,
            "type": metadata.component_type.value,
            "state": metadata.state.value,
            "dependencies": metadata.dependencies,
            "created_at": metadata.created_at,
            "initialized_at": metadata.initialized_at,
            "error_message": metadata.error_message,
            "priority": metadata.priority
        }

    def get_all_components_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有组件状态"""
        result = {}
        for name in self.components:
            status = self.get_component_status(name)
            if status is not None:
                result[name] = status
        return result

    def get_component_dependencies(self, name: str) -> List[str]:
        """获取组件依赖"""
        return self.dependency_graph.get(name, [])
    
    async def restart_component(self, name: str) -> bool:
        """重启组件"""
        try:
            if name not in self.components:
                logger.warning(f"组件 {name} 不存在")
                return False
            
            logger.info(f"🔄 重启组件 {name}...")
            
            # 先关闭组件
            await self.shutdown_component(name)
            
            # 重新初始化组件
            await self.initialize_component(name)
            
            logger.info(f"✅ 组件 {name} 重启成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 组件 {name} 重启失败: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            health_status = {
                "overall_status": "healthy",
                "total_components": len(self.components),
                "ready_components": 0,
                "error_components": 0,
                "component_details": {},
                "timestamp": time.time()
            }
            
            for name, metadata in self.components.items():
                component_health = {
                    "name": name,
                    "type": metadata.component_type.value,
                    "state": metadata.state.value,
                    "status": "healthy"
                }
                
                if metadata.state == ComponentState.READY:
                    health_status["ready_components"] += 1
                elif metadata.state == ComponentState.ERROR:
                    health_status["error_components"] += 1
                    component_health["status"] = "unhealthy"
                    component_health["error"] = metadata.error_message
                
                health_status["component_details"][name] = component_health
            
            # 计算整体状态
            if health_status["error_components"] > 0:
                health_status["overall_status"] = "degraded"
            if health_status["ready_components"] == 0:
                health_status["overall_status"] = "unhealthy"
            
            return health_status
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "overall_status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def get_component_metrics(self) -> Dict[str, Any]:
        """获取组件指标"""
        try:
            metrics = {
                "total_components": len(self.components),
                "by_type": {},
                "by_state": {},
                "dependency_count": 0,
                "average_priority": 0.0
            }
            
            # 按类型统计
            for metadata in self.components.values():
                component_type = metadata.component_type.value
                metrics["by_type"][component_type] = metrics["by_type"].get(component_type, 0) + 1
            
            # 按状态统计
            for metadata in self.components.values():
                state = metadata.state.value
                metrics["by_state"][state] = metrics["by_state"].get(state, 0) + 1
            
            # 计算依赖数量
            total_deps = sum(len(deps) for deps in self.dependency_graph.values())
            metrics["dependency_count"] = total_deps
            
            # 计算平均优先级
            if self.components:
                total_priority = sum(metadata.priority for metadata in self.components.values())
                metrics["average_priority"] = total_priority / len(self.components)
            
            return metrics
            
        except Exception as e:
            logger.error(f"获取组件指标失败: {e}")
            return {"error": str(e)}
    
    async def cleanup_failed_components(self) -> int:
        """清理失败的组件"""
        try:
            failed_components = []
            
            for name, metadata in self.components.items():
                if metadata.state == ComponentState.ERROR:
                    failed_components.append(name)
            
            for name in failed_components:
                await self.shutdown_component(name)
                del self.components[name]
                if name in self.component_instances:
                    del self.component_instances[name]
            
            logger.info(f"✅ 清理了 {len(failed_components)} 个失败组件")
            return len(failed_components)
            
        except Exception as e:
            logger.error(f"清理失败组件失败: {e}")
            return 0
    
    def get_manager_status(self) -> Dict[str, Any]:
        """获取管理器状态"""
        try:
            return {
                "initialized": True,
                "total_components": len(self.components),
                "is_shutting_down": self._is_shutting_down,
                "initialization_order": self._initialization_order.copy(),
                "dependency_graph_size": len(self.dependency_graph),
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"获取管理器状态失败: {e}")
            return {
                "initialized": False,
                "error": str(e),
                "timestamp": time.time()
            }

    def get_component_dependents(self, name: str) -> List[str]:
        """获取依赖该组件的组件列表"""
        dependents = []
        for comp_name, deps in self.dependency_graph.items():
            if name in deps:
                dependents.append(comp_name)
        return dependents

async def test_component_manager():
    """测试组件管理器"""

    class MockConfigManager:
        def __init__(self):
            self.config = {"test": "value"}

        async def cleanup(self):
            print("ConfigManager cleanup")

    class MockLLMClient:
        def __init__(self, config_manager):
            self.config = config_manager.config

        async def cleanup(self):
            print("LLMClient cleanup")

    class MockMemory:
        def __init__(self, config_manager):
            self.config = config_manager.config

        async def cleanup(self):
            print("Memory cleanup")

    try:
        manager = AsyncComponentManager()

        await manager.register_component(
            "config_manager", ComponentType.CONFIG,
            factory_func=MockConfigManager,
            priority=0
        )

        config_manager = await manager.get_component("config_manager")

        await manager.register_component(
            "llm_client", ComponentType.LLM_CLIENT,
            factory_func=lambda: MockLLMClient(config_manager),
            dependencies=["config_manager"],
            priority=1
        )

        await manager.register_component(
            "memory", ComponentType.MEMORY,
            factory_func=lambda: MockMemory(config_manager),
            dependencies=["config_manager"],
            priority=1
        )

        await manager.initialize_all_components()

        status = manager.get_all_components_status()
        print("组件状态:", status)

        config_manager = await manager.get_component("config_manager")
        llm_client = await manager.get_component("llm_client")
        memory = await manager.get_component("memory")

        print(f"Config: {config_manager.config}")
        print(f"LLM Client config: {llm_client.config}")
        print(f"Memory config: {memory.config}")

        await manager.shutdown_all_components()

        print("✅ 组件管理器测试完成")

    except Exception as e:
        logger.error("测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(test_component_manager())
