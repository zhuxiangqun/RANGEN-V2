#!/usr/bin/env python3
"""
快速测试脚本 - 只测试核心功能，避免长时间运行
"""
import asyncio
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def quick_test():
    """快速测试"""
    print("🚀 快速测试模式（跳过耗时测试）")
    
    # 只测试工作流构建，不执行实际查询
    from src.core.langgraph_unified_workflow import UnifiedResearchWorkflow
    
    try:
        # 创建简化系统对象
        class MockSystem:
            pass
        
        system = MockSystem()
        
        # 测试工作流构建
        print("📋 测试工作流构建...")
        workflow = UnifiedResearchWorkflow(system=system)
        
        if workflow.workflow is not None:
            print("✅ 工作流构建成功")
            return True
        else:
            print("❌ 工作流构建失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(quick_test())
    sys.exit(0 if result else 1)
