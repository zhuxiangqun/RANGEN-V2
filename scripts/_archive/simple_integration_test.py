#!/usr/bin/env python3
"""
简单集成测试

快速验证核心组件的基本集成功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def test_basic_integration():
    """测试基本集成"""
    print("Testing basic integration...")

    try:
        # 测试通信中间件
        from src.core.agent_communication_middleware import get_communication_middleware
        comm = get_communication_middleware()
        print("✓ Communication middleware initialized")

        # 测试冲突检测
        from src.core.conflict_detection_system import get_conflict_detection_system
        conflict_sys = get_conflict_detection_system()
        print("✓ Conflict detection system initialized")

        # 测试任务分配器
        from src.core.adaptive_task_allocator import get_adaptive_task_allocator
        allocator = get_adaptive_task_allocator()
        print("✓ Task allocator initialized")

        # 测试状态同步器
        from src.core.collaboration_state_synchronizer import get_collaboration_state_synchronizer
        sync = get_collaboration_state_synchronizer()
        print("✓ State synchronizer initialized")

        print("🎉 Basic integration test passed!")
        return True

    except Exception as e:
        print(f"❌ Basic integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    success = await test_basic_integration()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
