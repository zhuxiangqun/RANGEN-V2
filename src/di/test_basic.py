#!/usr/bin/env python3
"""
依赖注入系统基础测试
"""

import asyncio
import logging
from typing import Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 定义测试服务
class TestConfigService:
    def __init__(self):
        self.config = {"test": "value"}
    
    def get(self, key: str) -> Any:
        return self.config.get(key)


class TestLoggingService:
    def __init__(self):
        self.messages = []
    
    def info(self, message: str) -> None:
        self.messages.append(("INFO", message))
        print(f"INFO: {message}")
    
    def error(self, message: str) -> None:
        self.messages.append(("ERROR", message))
        print(f"ERROR: {message}")


class TestCoordinator:
    def __init__(self, config_service: TestConfigService, logging_service: TestLoggingService):
        self.config = config_service
        self.logger = logging_service
        self.initialized = True
    
    async def run_task(self, task: str) -> Dict[str, Any]:
        self.logger.info(f"Running task: {task}")
        return {"result": f"Processed: {task}", "config": self.config.get("test")}


async def test_di_basic():
    """测试基础依赖注入功能"""
    print("=" * 60)
    print("测试依赖注入系统 - 基础功能")
    print("=" * 60)
    
    try:
        from src.di.unified_container import UnifiedDIContainer
        from src.di.service_registrar import ServiceRegistrar
        
        # 1. 创建容器
        container = UnifiedDIContainer()
        print("✓ 容器创建成功")
        
        # 2. 注册服务
        container.register_singleton(TestConfigService, TestConfigService)
        container.register_singleton(TestLoggingService, TestLoggingService)
        
        # 3. 注册有依赖的服务
        container.register_singleton(TestCoordinator, TestCoordinator)
        print("✓ 服务注册成功")
        
        # 4. 获取服务
        config_service = container.get_service(TestConfigService)
        logging_service = container.get_service(TestLoggingService)
        coordinator = container.get_service(TestCoordinator)
        print("✓ 服务获取成功")
        
        # 5. 验证依赖注入
        assert coordinator.config is config_service
        assert coordinator.logger is logging_service
        print("✓ 依赖注入验证成功")
        
        # 6. 测试异步获取
        async_coordinator = await container.get_service_async(TestCoordinator)
        assert async_coordinator is coordinator  # 应该是同一个单例实例
        print("✓ 异步服务获取成功")
        
        # 7. 测试服务功能
        result = await coordinator.run_task("测试任务")
        assert "Processed: 测试任务" in result["result"]
        print("✓ 服务功能测试成功")
        
        print("=" * 60)
        print("所有基础测试通过！")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_bootstrap():
    """测试引导程序"""
    print("\n" + "=" * 60)
    print("测试引导程序")
    print("=" * 60)
    
    try:
        from src.di.bootstrap import bootstrap_application_async
        
        # 1. 初始化引导程序
        bootstrap = await bootstrap_application_async()
        print("✓ 引导程序初始化成功")
        
        # 2. 获取容器
        container = bootstrap.get_container()
        print("✓ 容器获取成功")
        
        # 3. 查看已注册的服务
        services = bootstrap.get_registered_services()
        print(f"✓ 已注册服务数量: {len(services)}")
        
        # 4. 列出服务
        print("已注册的服务:")
        for name, lifetime in services.items():
            print(f"  - {name}: {lifetime}")
        
        print("=" * 60)
        print("引导程序测试通过！")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"✗ 引导程序测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_advanced_features():
    """测试高级功能"""
    print("\n" + "=" * 60)
    print("测试高级功能")
    print("=" * 60)
    
    try:
        from src.di.unified_container import UnifiedDIContainer, ServiceLifetime
        
        # 1. 创建新容器
        container = UnifiedDIContainer()
        
        # 2. 测试瞬态服务
        call_count = [0]
        
        def create_transient():
            call_count[0] += 1
            return {"id": call_count[0]}
        
        container.register_factory(dict, create_transient, ServiceLifetime.TRANSIENT)
        
        # 3. 获取瞬态实例（应该每次都是新的）
        instance1 = container.get_service(dict)
        instance2 = container.get_service(dict)
        
        assert instance1["id"] == 1
        assert instance2["id"] == 2
        assert instance1 is not instance2
        print("✓ 瞬态服务测试成功")
        
        # 4. 测试作用域服务
        scope_count = [0]
        
        def create_scoped():
            scope_count[0] += 1
            return {"scope_id": scope_count[0]}
        
        container.register_factory(dict, create_scoped, ServiceLifetime.SCOPED)
        
        # 第一次获取作用域实例
        scope1 = container.get_service(dict)
        assert scope1["scope_id"] == 1
        
        # 清除作用域实例
        container.clear_scoped_instances()
        
        # 再次获取应该创建新实例
        scope2 = container.get_service(dict)
        assert scope2["scope_id"] == 2
        print("✓ 作用域服务测试成功")
        
        # 5. 测试服务检查
        assert container.is_registered(dict) == True
        assert container.is_registered(str) == False
        print("✓ 服务检查测试成功")
        
        print("=" * 60)
        print("高级功能测试通过！")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"✗ 高级功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("开始依赖注入系统测试")
    print("=" * 60)
    
    results = []
    
    # 运行测试
    results.append(await test_di_basic())
    results.append(await test_bootstrap())
    results.append(await test_advanced_features())
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for i, result in enumerate(results):
        test_name = ["基础功能", "引导程序", "高级功能"][i]
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
    
    all_passed = all(results)
    if all_passed:
        print("\n🎉 所有测试通过！依赖注入系统工作正常。")
    else:
        print("\n❌ 部分测试失败，请检查问题。")
    
    return all_passed


if __name__ == "__main__":
    # 运行异步测试
    success = asyncio.run(main())
    exit(0 if success else 1)