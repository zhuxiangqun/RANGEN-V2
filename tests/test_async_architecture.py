"""
异步架构测试 - 验证统一异步架构的功能
"""
import asyncio
import pytest
from typing import Dict, Any, List

from src.utils.dependency_container import (
    DependencyContainer
)

# 本地模拟缺失的函数和类
class ServiceType:
    ASYNC = "async"
    SYNC = "sync"
    HYBRID = "hybrid"

def register_service(service_type, implementation, name=None):
    pass

def get_service(service_type, name=None):
    pass

async def get_service_async(service_type, name=None):
    pass
from src.interfaces.core_interfaces import IAgent, IConfigManager, IThresholdManager
from src.interfaces.async_interfaces import IAsyncAgent, IAsyncService

class MockAsyncService:
    """模拟异步服务"""
    
    def __init__(self):
        self._initialized = False
        self._ready = False
    
    async def initialize(self) -> bool:
        await asyncio.sleep(0.1)  # 模拟异步初始化
        self._initialized = True
        self._ready = True
        return True
    
    async def shutdown(self) -> bool:
        await asyncio.sleep(0.1)  # 模拟异步关闭
        self._initialized = False
        self._ready = False
        return True
    
    def is_ready(self) -> bool:
        return self._ready and self._initialized

class MockAsyncAgent:
    """模拟异步智能体"""
    
    def __init__(self):
        self._initialized = False
    
    async def execute_async(self, task: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(0.1)  # 模拟异步执行
        return {
            "status": "success",
            "result": f"异步执行任务: {task.get('task_type', 'unknown')}",
            "execution_time": 0.1
        }
    
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        # 同步执行（向后兼容）
        return asyncio.run(self.execute_async(task))
    
    async def initialize(self) -> bool:
        await asyncio.sleep(0.1)
        self._initialized = True
        return True
    
    async def cleanup(self) -> bool:
        await asyncio.sleep(0.1)
        self._initialized = False
        return True
    
    def get_capabilities(self) -> List[str]:
        return ["async_execution", "sync_execution", "initialization", "cleanup"]

class MockSyncService:
    """模拟同步服务"""
    
    def __init__(self):
        self._initialized = False
    
    def initialize(self) -> bool:
        self._initialized = True
        return True
    
    def is_ready(self) -> bool:
        return self._initialized

async def test_async_dependency_container():
    """测试异步依赖注入容器"""
    print("🧪 测试异步依赖注入容器...")
    
    # 创建容器
    container = DependencyContainer()
    
    # 注册异步服务
    container.register_service(IAsyncService, MockAsyncService, ServiceType.ASYNC)
    container.register_service(IAgent, MockAsyncAgent, ServiceType.HYBRID)
    container.register_service(IConfigManager, MockSyncService, ServiceType.SYNC)
    
    # 测试异步服务获取
    async_service = await container.get_service_async(IAsyncService)
    assert isinstance(async_service, MockAsyncService)
    print("✅ 异步服务获取成功")
    
    # 测试混合服务获取
    agent = await container.get_service_async(IAgent)
    assert isinstance(agent, MockAsyncAgent)
    print("✅ 混合服务异步获取成功")
    
    # 测试同步服务获取
    sync_service = container.get_service(IConfigManager)
    assert isinstance(sync_service, MockSyncService)
    print("✅ 同步服务获取成功")
    
    print("✅ 异步依赖注入容器测试通过")

async def test_async_service_lifecycle():
    """测试异步服务生命周期"""
    print("🧪 测试异步服务生命周期...")
    
    # 获取异步服务
    container = get_dependency_container()
    container.register_service(IAsyncService, MockAsyncService, ServiceType.ASYNC)
    
    async_service = await container.get_service_async(IAsyncService)
    
    # 测试初始化
    result = await async_service.initialize()
    assert result is True
    assert async_service.is_ready() is True
    print("✅ 异步服务初始化成功")
    
    # 测试关闭
    result = await async_service.shutdown()
    assert result is True
    assert async_service.is_ready() is False
    print("✅ 异步服务关闭成功")
    
    print("✅ 异步服务生命周期测试通过")

async def test_async_agent_execution():
    """测试异步智能体执行"""
    print("🧪 测试异步智能体执行...")
    
    # 获取异步智能体
    container = get_dependency_container()
    container.register_service(IAgent, MockAsyncAgent, ServiceType.HYBRID)
    
    agent = await container.get_service_async(IAgent)
    
    # 测试异步执行
    task = {"task_type": "test_task", "query": "测试查询"}
    result = await agent.execute_async(task)
    
    assert result["status"] == "success"
    assert "异步执行任务" in result["result"]
    print("✅ 异步智能体执行成功")
    
    # 测试同步执行（向后兼容）
    sync_result = agent.execute(task)
    assert sync_result["status"] == "success"
    print("✅ 同步智能体执行成功（向后兼容）")
    
    print("✅ 异步智能体执行测试通过")

async def test_async_architecture_integration():
    """测试异步架构集成"""
    print("🧪 测试异步架构集成...")
    
    # 1. 测试容器扩展
    container = DependencyContainer()
    assert hasattr(container, 'get_service_async')
    assert hasattr(container, 'initialize_async_services')
    print("✅ 容器异步扩展成功")
    
    # 2. 测试服务类型管理
    container.register_service(IAsyncService, MockAsyncService, ServiceType.ASYNC)
    service_type = container.get_service_type(IAsyncService)
    assert service_type == ServiceType.ASYNC
    print("✅ 服务类型管理成功")
    
    # 3. 测试异步初始化
    await container.initialize_async_services()
    print("✅ 异步服务初始化成功")
    
    print("✅ 异步架构集成测试通过")

async def main():
    """主测试函数"""
    print("🚀 开始异步架构测试...")
    
    try:
        await test_async_dependency_container()
        await test_async_service_lifecycle()
        await test_async_agent_execution()
        await test_async_architecture_integration()
        
        print("🎉 所有异步架构测试通过！")
        
    except Exception as e:
        print(f"❌ 异步架构测试失败: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
