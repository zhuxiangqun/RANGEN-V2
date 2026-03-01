#!/usr/bin/env python3
"""
测试工作流初始化
验证系统启动时工作流是否能正确初始化
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 加载环境变量
try:
    from dotenv import load_dotenv
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=False)
        print(f"✅ 已加载环境变量: {env_path}")
except ImportError:
    print("⚠️ python-dotenv 未安装，无法加载 .env 文件")

print("=" * 60)
print("工作流初始化测试")
print("=" * 60)
print()

async def test_workflow_initialization():
    """测试工作流初始化"""
    try:
        from src.unified_research_system import UnifiedResearchSystem
        
        print("1. 创建 UnifiedResearchSystem 实例...")
        system = UnifiedResearchSystem()
        print("   ✅ 实例创建成功")
        print()
        
        print("2. 初始化系统...")
        await system.initialize()
        print("   ✅ 系统初始化完成")
        print()
        
        print("3. 检查工作流状态...")
        if hasattr(system, '_unified_workflow'):
            if system._unified_workflow is not None:
                print("   ✅ _unified_workflow 已初始化")
                if hasattr(system._unified_workflow, 'workflow'):
                    if system._unified_workflow.workflow is not None:
                        print("   ✅ workflow 对象存在")
                        print(f"   ✅ 工作流类型: {type(system._unified_workflow.workflow).__name__}")
                    else:
                        print("   ❌ workflow 对象为 None")
                else:
                    print("   ❌ _unified_workflow 没有 workflow 属性")
            else:
                print("   ❌ _unified_workflow 为 None")
                print("   💡 检查初始化日志，查看失败原因")
        else:
            print("   ❌ _unified_workflow 属性不存在")
        print()
        
        print("4. 检查可视化服务器...")
        if hasattr(system, '_visualization_server'):
            if system._visualization_server is not None:
                print("   ✅ 可视化服务器已初始化")
                if hasattr(system._visualization_server, 'workflow'):
                    if system._visualization_server.workflow is not None:
                        print("   ✅ 可视化服务器的工作流已设置")
                    else:
                        print("   ⚠️  可视化服务器的工作流为 None")
                        print("   💡 可视化服务器会尝试从系统动态获取工作流")
                else:
                    print("   ⚠️  可视化服务器没有 workflow 属性")
            else:
                print("   ⚠️  可视化服务器未初始化（可能已禁用）")
        else:
            print("   ⚠️  可视化服务器属性不存在")
        print()
        
        print("=" * 60)
        print("✅ 测试完成！")
        print("=" * 60)
        print()
        
        # 总结
        if system._unified_workflow and hasattr(system._unified_workflow, 'workflow') and system._unified_workflow.workflow:
            print("✅ 工作流初始化成功！系统应该可以正常使用工作流。")
        else:
            print("❌ 工作流初始化失败。请检查：")
            print("   1. LangGraph 已安装: pip install langgraph")
            print("   2. 环境变量 ENABLE_UNIFIED_WORKFLOW=true")
            print("   3. 查看系统初始化日志")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_workflow_initialization())

