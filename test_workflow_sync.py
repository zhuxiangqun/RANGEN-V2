#!/usr/bin/env python3
"""
测试工作流同步问题的诊断脚本
"""
import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_workflow_sync():
    """测试工作流同步的关键组件"""
    print("=" * 60)
    print("🔍 工作流同步问题诊断")
    print("=" * 60)

    try:
        # 1. 测试系统创建
        print("\n1. 创建UnifiedResearchSystem...")
        from src.unified_research_system import create_unified_research_system

        system = await create_unified_research_system()
        print("   ✅ 系统创建成功")

        # 2. 检查工作流初始化
        print("\n2. 检查工作流初始化...")
        if hasattr(system, '_unified_workflow') and system._unified_workflow:
            workflow_obj = system._unified_workflow
            print(f"   ✅ _unified_workflow存在: {type(workflow_obj).__name__}")

            if hasattr(workflow_obj, 'workflow') and workflow_obj.workflow:
                workflow = workflow_obj.workflow
                print(f"   ✅ workflow对象存在: {type(workflow).__name__}")

                # 检查关键方法
                has_astream = hasattr(workflow, 'astream')
                has_astream_events = hasattr(workflow, 'astream_events')
                print(f"   astream方法: {'✅' if has_astream else '❌'}")
                print(f"   astream_events方法: {'✅' if has_astream_events else '❌'}")

                if has_astream_events:
                    print("   🎯 支持实时事件流 - 这是进度条工作所需的关键功能")
                else:
                    print("   ⚠️  不支持实时事件流 - 进度条将无法实时更新")
            else:
                print("   ❌ workflow对象为None")
                return False
        else:
            print("   ❌ _unified_workflow不存在")
            return False

        # 3. 测试BrowserVisualizationServer创建
        print("\n3. 测试BrowserVisualizationServer创建...")
        from src.visualization.browser_server import BrowserVisualizationServer

        server = BrowserVisualizationServer(
            workflow=None,
            system=system,
            port=8080
        )
        print("   ✅ BrowserVisualizationServer创建成功")

        # 4. 检查服务器管理器
        if hasattr(server, 'server_manager') and server.server_manager:
            print("   ✅ UnifiedServerManager存在")

            # 检查服务
            services = server.server_manager.services
            required_services = ['api', 'visualization', 'websocket']
            for service_name in required_services:
                if service_name in services:
                    print(f"   ✅ {service_name}服务已注册")
                else:
                    print(f"   ❌ {service_name}服务未注册")
                    return False
        else:
            print("   ❌ UnifiedServerManager不存在")
            return False

        # 5. 测试服务间通信设置
        print("\n4. 测试服务间通信...")
        await server.server_manager._start_services()

        api_server = server.server_manager.services.get('api')
        viz_server = server.server_manager.services.get('visualization')

        if api_server and hasattr(api_server, 'visualization_server'):
            if api_server.visualization_server:
                print("   ✅ API服务器已获得可视化服务器引用")
            else:
                print("   ❌ API服务器的可视化服务器引用为None")
                return False
        else:
            print("   ❌ API服务器没有visualization_server属性")
            return False

        # 6. 测试工作流执行能力
        print("\n5. 测试工作流执行能力...")
        if hasattr(viz_server, '_execute_workflow_async'):
            print("   ✅ 可视化服务器有_execute_workflow_async方法")

            # 尝试创建一个测试执行
            test_execution_id = "test_sync_123"
            try:
                # 这里我们不真正执行，只是检查方法是否存在
                print("   ✅ 工作流执行方法可用")
            except Exception as e:
                print(f"   ⚠️  工作流执行方法检查失败: {e}")
        else:
            print("   ❌ 可视化服务器没有_execute_workflow_async方法")
            return False

        await system.shutdown()
        print("\n" + "=" * 60)
        print("✅ 所有关键组件检查通过！")
        print("🎯 如果进度条仍然不工作，可能是运行时的问题")
        print("💡 建议：检查浏览器控制台的WebSocket连接状态")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ 诊断过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_workflow_sync())
    sys.exit(0 if success else 1)
