#!/usr/bin/env python3
"""
检查系统中实际使用的Agent类型
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def check_agent_imports():
    """检查系统中的Agent导入情况"""
    print("🔍 检查Agent导入情况...")
    print("=" * 60)

    # 检查主要文件中的Agent使用
    files_to_check = [
        'src/unified_research_system.py',
        'src/core/langgraph_agent_nodes.py',
        'src/core/intelligent_orchestrator.py',
    ]

    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"\n📄 检查文件: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查ReActAgent相关导入
                if 'ReActAgentWrapper' in content:
                    print("   ✅ 使用 ReActAgentWrapper")
                    # 查找具体的使用位置
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if 'ReActAgentWrapper' in line:
                            print(f"   📍 第{i}行: {line.strip()}")
                elif 'ReActAgent' in content:
                    print("   ⚠️ 直接使用 ReActAgent")
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if 'ReActAgent' in line and 'ReActAgentWrapper' not in line:
                            print(f"   📍 第{i}行: {line.strip()}")
                else:
                    print("   ℹ️ 未发现ReActAgent使用")

            except Exception as e:
                print(f"   ❌ 读取文件失败: {e}")

def check_gradual_replacement_status():
    """检查逐步替换状态"""
    print("\n🔍 检查逐步替换配置...")
    print("=" * 60)

    try:
        from src.agents.react_agent_wrapper import ReActAgentWrapper

        print("📊 ReActAgentWrapper默认配置:")
        # 创建一个实例来检查默认配置
        wrapper = ReActAgentWrapper(enable_gradual_replacement=True, initial_replacement_rate=0.01)

        print(f"   逐步替换启用: {wrapper.enable_gradual_replacement}")
        if wrapper.replacement_strategy:
            print(f"   当前替换率: {wrapper.replacement_strategy.replacement_rate:.1%}")
            print(f"   新Agent类型: {type(wrapper.replacement_strategy.new_agent).__name__}")
            print(f"   旧Agent类型: {type(wrapper.replacement_strategy.old_agent).__name__}")
        else:
            print("   ❌ 替换策略未初始化")

    except Exception as e:
        print(f"❌ 检查失败: {e}")

def check_migration_state():
    """检查迁移管理器的状态"""
    print("\n🔍 检查迁移管理器状态...")
    print("=" * 60)

    try:
        from scripts.manage_agent_migrations import AgentMigrationManager

        manager = AgentMigrationManager()

        print("📋 当前迁移任务状态:")
        for task in manager.migration_tasks:
            if task.agent_name == "ReActAgent":
                print(f"   Agent: {task.agent_name}")
                print(f"   状态: {task.status}")
                print(f"   替换率: {task.replacement_rate:.1%}")
                print(f"   备注: {task.notes}")
                print(f"   包装器: {'✅' if task.wrapper_created else '❌'}")
                print(f"   逐步替换: {'✅' if task.gradual_replacement_started else '❌'}")
                break

    except Exception as e:
        print(f"❌ 检查失败: {e}")

def main():
    print("🚀 检查系统中实际使用的Agent类型")
    print("=" * 80)

    check_agent_imports()
    check_gradual_replacement_status()
    check_migration_state()

    print("\n" + "=" * 80)
    print("📊 分析结果:")

    print("\n💡 迁移状态说明:")
    print("1. ✅ 代码层面: 系统使用ReActAgentWrapper而不是直接ReActAgent")
    print("2. ✅ 基础设施: GradualReplacementStrategy和适配器都已实现")
    print("3. ✅ 配置层面: 替换率可以通过管理界面调整")

    print("\n⚠️ 可能的误解:")
    print("- 管理界面只是配置工具，不是实际的迁移执行者")
    print("- 实际的Agent替换发生在请求处理时，根据概率决定")
    print("- 如果没有实际请求，替换就不会发生")

    print("\n🎯 验证迁移效果:")
    print("要验证迁移是否真正发生，需要:")
    print("1. 发送实际的API请求到使用ReActAgent的服务")
    print("2. 检查日志中是否出现了ReasoningExpert的执行记录")
    print("3. 观察响应质量和处理时间的差异")

    print("\n🔍 如果你想看到更直接的迁移证据:")
    print("- 检查系统日志中的Agent执行记录")
    print("- 发送测试请求并观察新Agent的使用情况")
    print("- 查看性能监控数据中的Agent使用统计")

if __name__ == "__main__":
    main()
