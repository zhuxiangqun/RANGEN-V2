#!/usr/bin/env python3
"""
测试迁移状态持久化功能
"""

import sys
import os
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_persistence():
    """测试状态持久化"""
    print("🧪 测试迁移状态持久化功能")
    print("=" * 50)

    try:
        from scripts.manage_agent_migrations import AgentMigrationManager

        print("\n1️⃣ 创建管理器并检查初始状态")
        manager = AgentMigrationManager()

        # 找到ReActAgent任务
        react_task = None
        for task in manager.migration_tasks:
            if task.agent_name == "ReActAgent":
                react_task = task
                break

        if not react_task:
            print("❌ 未找到ReActAgent任务")
            return

        print(f"   初始替换率: {react_task.replacement_rate:.1%}")
        print(f"   初始备注: {react_task.notes}")

        print("\n2️⃣ 修改ReActAgent的替换率")
        old_rate = react_task.replacement_rate
        manager.adjust_replacement_rate("ReActAgent", 0.75)

        # 重新获取任务状态
        react_task_updated = None
        for task in manager.migration_tasks:
            if task.agent_name == "ReActAgent":
                react_task_updated = task
                break

        print(f"   修改后替换率: {react_task_updated.replacement_rate:.1%}")
        print(f"   修改后备注: {react_task_updated.notes}")

        print("\n3️⃣ 检查状态文件是否创建")
        state_file = Path("data/migration_state.json")
        if state_file.exists():
            print(f"   ✅ 状态文件已创建: {state_file}")

            # 读取文件内容验证
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            react_data = None
            for task_data in data.get('tasks', []):
                if task_data['agent_name'] == 'ReActAgent':
                    react_data = task_data
                    break

            if react_data:
                print(f"   文件中替换率: {react_data['replacement_rate']:.1%}")
                print(f"   文件中备注: {react_data['notes']}")
            else:
                print("   ❌ 文件中未找到ReActAgent数据")
        else:
            print(f"   ❌ 状态文件未创建: {state_file}")

        print("\n4️⃣ 创建新管理器实例验证加载")
        manager2 = AgentMigrationManager()

        react_task_loaded = None
        for task in manager2.migration_tasks:
            if task.agent_name == "ReActAgent":
                react_task_loaded = task
                break

        if react_task_loaded:
            print(f"   加载后替换率: {react_task_loaded.replacement_rate:.1%}")
            print(f"   加载后备注: {react_task_loaded.notes}")

            if abs(react_task_loaded.replacement_rate - 0.75) < 0.001:
                print("   ✅ 状态持久化成功！")
            else:
                print("   ❌ 状态持久化失败，替换率没有正确保存")
        else:
            print("   ❌ 加载后未找到ReActAgent任务")

        print("\n" + "=" * 50)
        print("🎉 持久化测试完成")

        # 显示状态文件内容摘要
        if state_file.exists():
            print(f"\n📄 状态文件位置: {state_file}")
            print("💡 现在你可以重启管理器，状态应该会保持")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_persistence()
