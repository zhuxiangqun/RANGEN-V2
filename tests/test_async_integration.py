"""
异步架构集成测试 - 验证整个异步架构的功能
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.bootstrap.application_bootstrap import (
    bootstrap_application_async, get_service_async
)
from src.interfaces.core_interfaces import IAgent, IConfigManager, IThresholdManager
# from src.services.async_service_manager import get_async_service_manager

async def test_async_architecture_integration():
    """测试异步架构集成"""
    print("🧪 开始异步架构集成测试...")
    
    try:
        # 1. 测试异步应用启动
        print("1️⃣ 测试异步应用启动...")
        success = await bootstrap_application_async()
        assert success, "异步应用启动失败"
        print("✅ 异步应用启动成功")
        
        # 2. 测试异步服务获取
        print("2️⃣ 测试异步服务获取...")
        agent = await get_service_async(IAgent)
        assert agent is not None, "无法获取智能体服务"
        print(f"✅ 异步获取智能体服务成功: {type(agent).__name__}")
        
        # 3. 测试异步服务管理器
        print("3️⃣ 测试异步服务管理器...")
        service_manager = await get_async_service_manager()
        assert service_manager is not None, "无法获取异步服务管理器"
        print(f"✅ 异步服务管理器获取成功: {type(service_manager).__name__}")
        
        # 4. 测试异步服务状态
        print("4️⃣ 测试异步服务状态...")
        status = get_async_services_status()
        assert "error" not in status, f"异步服务状态获取失败: {status}"
        print(f"✅ 异步服务状态获取成功: {status.get('status_summary', {})}")
        
        # 5. 测试异步研究服务
        print("5️⃣ 测试异步研究服务...")
        research_service = await get_async_service("async_research_service")
        assert research_service is not None, "无法获取异步研究服务"
        print(f"✅ 异步研究服务获取成功: {type(research_service).__name__}")
        
        # 6. 测试异步FAISS服务
        print("6️⃣ 测试异步FAISS服务...")
        faiss_service = await get_async_service("async_faiss_service")
        assert faiss_service is not None, "无法获取异步FAISS服务"
        print(f"✅ 异步FAISS服务获取成功: {type(faiss_service).__name__}")
        
        # 7. 测试智能体异步执行 - 使用测试数据工厂
        print("7️⃣ 测试智能体异步执行...")
        from test_data_factory import create_test_task
        task = create_test_task("integration_test", "集成测试查询")
        result = await agent.execute_async(task)
        assert result is not None, "智能体异步执行失败"
        print(f"✅ 智能体异步执行成功: {result}")
        
        print("🎉 所有异步架构集成测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 异步架构集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_async_service_lifecycle():
    """测试异步服务生命周期"""
    print("🧪 开始异步服务生命周期测试...")
    
    try:
        # 1. 获取异步服务管理器
        service_manager = await get_async_service_manager()
        
        # 2. 测试服务状态
        status = service_manager.get_all_services_status()
        print(f"✅ 服务状态: {status.get('status_summary', {})}")
        
        # 3. 测试服务就绪状态
        ready = service_manager.is_ready()
        print(f"✅ 所有服务就绪: {ready}")
        
        print("🎉 异步服务生命周期测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 异步服务生命周期测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("🚀 开始异步架构集成测试套件...")
    
    try:
        # 运行集成测试
        integration_success = await test_async_architecture_integration()
        
        # 运行生命周期测试
        lifecycle_success = await test_async_service_lifecycle()
        
        # 关闭应用
        await shutdown_application_async()
        
        if integration_success and lifecycle_success:
            print("🎉 所有测试通过！异步架构集成成功！")
            return True
        else:
            print("❌ 部分测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试套件执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
