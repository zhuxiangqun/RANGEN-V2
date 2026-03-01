#!/usr/bin/env python3
"""
清理100%迁移后不再需要的旧Agent文件
保留8个核心Agent，清理包装器和旧Agent文件
"""

import os
import shutil
from pathlib import Path

def analyze_agents():
    """分析当前Agent文件状态"""
    print("🔍 分析当前Agent文件状态")
    print("=" * 60)

    agents_dir = Path("src/agents")

    # 统计各类文件
    all_files = list(agents_dir.glob("*.py"))
    wrapper_files = [f for f in all_files if "wrapper" in f.name]
    legacy_agent_files = []

    # 识别可能的旧Agent文件（不包含在新架构中的）
    core_agents = {
        'rag_agent.py',  # RAGExpert
        'reasoning_expert.py',  # ReasoningExpert
        'agent_coordinator.py',  # AgentCoordinator
        'quality_controller.py',  # QualityController
        'tool_orchestrator.py',  # ToolOrchestrator
        'memory_manager.py',  # MemoryManager
        'learning_optimizer.py',  # LearningOptimizer
        'chief_agent.py',  # ChiefAgent
    }

    auxiliary_files = {
        '__init__.py',
        'base_agent.py',
        'expert_agent.py',
        'agent_builder.py',
        'agent_communication.py',
        'autonomous_runner.py',
        'execution_coordinator.py',
        'multi_agent_coordinator.py',
        'enhanced_task_executor_registry.py',
        'intelligent_parameter_manager.py',
        'security_guardian.py',
        'semantic_feature_manager.py',
        'tactical_optimizer.py',
        'task_executor_adapter.py',
    }

    for file in all_files:
        if file.name not in core_agents and file.name not in auxiliary_files and "wrapper" not in file.name:
            if "agent" in file.name or "expert" in file.name:
                legacy_agent_files.append(file)

    print(f"📊 文件统计:")
    print(f"   总文件数: {len(all_files)}")
    print(f"   核心Agent: {len(core_agents)}")
    print(f"   辅助文件: {len(auxiliary_files)}")
    print(f"   包装器文件: {len(wrapper_files)}")
    print(f"   旧Agent文件: {len(legacy_agent_files)}")

    print(f"\n🎯 核心Agent (8个，应保留):")
    for agent in sorted(core_agents):
        status = "✅" if (agents_dir / agent).exists() else "❌"
        print(f"   {status} {agent}")

    print(f"\n📦 辅助文件 ({len(auxiliary_files)}个，应保留):")
    for file in sorted(auxiliary_files):
        status = "✅" if (agents_dir / file).exists() else "❌"
        print(f"   {status} {file}")

    print(f"\n🔄 包装器文件 ({len(wrapper_files)}个，100%迁移后可清理):")
    for file in sorted(wrapper_files, key=lambda x: x.name):
        print(f"   🗑️  {file.name}")

    print(f"\n📜 旧Agent文件 ({len(legacy_agent_files)}个，应清理):")
    for file in sorted(legacy_agent_files, key=lambda x: x.name):
        print(f"   🗑️  {file.name}")

    return core_agents, auxiliary_files, wrapper_files, legacy_agent_files

def create_cleanup_plan(wrapper_files, legacy_agent_files):
    """创建清理计划"""
    print("\n🧹 创建清理计划")
    print("-" * 40)

    cleanup_files = wrapper_files + legacy_agent_files

    print(f"📋 计划清理的文件 ({len(cleanup_files)}个):")

    # 按类型分组显示
    wrapper_names = [f.name for f in wrapper_files]
    legacy_names = [f.name for f in legacy_agent_files]

    print(f"\n🔄 包装器文件 ({len(wrapper_files)}个):")
    for name in sorted(wrapper_names):
        print(f"   • {name}")

    print(f"\n📜 旧Agent文件 ({len(legacy_agent_files)}个):")
    for name in sorted(legacy_names):
        print(f"   • {name}")

    print(f"\n⚠️  清理说明:")
    print("   • 包装器文件：在100%迁移后不再需要路由功能")
    print("   • 旧Agent文件：已被新架构完全替代")
    print("   • 清理后系统将只保留8个核心Agent + 必要的辅助文件")

    return cleanup_files

def execute_cleanup(cleanup_files, dry_run=True):
    """执行清理"""
    mode = "预览模式" if dry_run else "执行模式"
    print(f"\n🗑️  执行清理 - {mode}")
    print("-" * 40)

    if dry_run:
        print("🔍 这是一个预览，不会实际删除文件")
        print("如需实际清理，请设置 dry_run=False")
    else:
        print("⚠️  这将永久删除文件，请确保已备份！")
        confirm = input("确认继续清理？(输入 'yes' 确认): ")
        if confirm.lower() != 'yes':
            print("❌ 清理已取消")
            return False

    # 创建备份目录
    if not dry_run:
        backup_dir = Path("backup_legacy_agents")
        backup_dir.mkdir(exist_ok=True)
        print(f"📁 创建备份目录: {backup_dir}")

    cleaned_count = 0

    for file_path in cleanup_files:
        if dry_run:
            print(f"   [预览] 删除: {file_path}")
        else:
            # 备份文件
            backup_path = Path("backup_legacy_agents") / file_path.name
            shutil.copy2(file_path, backup_path)
            print(f"   📋 备份: {file_path} → {backup_path}")

            # 删除原文件
            file_path.unlink()
            print(f"   🗑️  删除: {file_path}")

        cleaned_count += 1

    print(f"\n✅ 清理完成: {cleaned_count} 个文件已{'预览删除' if dry_run else '删除并备份'}")

    if not dry_run:
        print(f"📁 备份文件保存在: backup_legacy_agents/")

    return True

def update_init_file():
    """更新__init__.py文件，只导入核心Agent"""
    print("\n📝 更新__init__.py文件")
    print("-" * 40)

    init_content = '''"""
RANGEN Agent System - 8核心Agent统一架构
"""

from .base_agent import BaseAgent, AgentResult
from .expert_agent import ExpertAgent

# 核心Agent导入 (8个)
from .rag_agent import RAGExpert
from .reasoning_expert import ReasoningExpert
from .agent_coordinator import AgentCoordinator
from .quality_controller import QualityController
from .tool_orchestrator import ToolOrchestrator
from .memory_manager import MemoryManager
from .learning_optimizer import LearningOptimizer
from .chief_agent import ChiefAgent

# 辅助模块导入
from .agent_builder import AgentBuilder
from .agent_communication import AgentCommunication
from .autonomous_runner import AutonomousRunner
from .execution_coordinator import ExecutionCoordinator
from .multi_agent_coordinator import MultiAgentCoordinator

__all__ = [
    # 核心类
    'BaseAgent', 'AgentResult', 'ExpertAgent',

    # 8个核心Agent
    'RAGExpert', 'ReasoningExpert', 'AgentCoordinator',
    'QualityController', 'ToolOrchestrator', 'MemoryManager',
    'LearningOptimizer', 'ChiefAgent',

    # 辅助模块
    'AgentBuilder', 'AgentCommunication', 'AutonomousRunner',
    'ExecutionCoordinator', 'MultiAgentCoordinator'
]

__version__ = "2.0.0"
'''

    init_file = Path("src/agents/__init__.py")
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write(init_content)

    print("✅ __init__.py 已更新为8核心Agent架构")

def main():
    """主函数"""
    print("🧹 Agent系统清理工具 - 100%迁移后清理")
    print("=" * 60)
    print("目标: 保留8个核心Agent，清理不再需要的旧文件")
    print()

    # 分析当前状态
    core_agents, auxiliary_files, wrapper_files, legacy_agent_files = analyze_agents()

    # 创建清理计划
    cleanup_files = create_cleanup_plan(wrapper_files, legacy_agent_files)

    # 执行清理（先预览模式）
    print("\n🚀 第一步: 预览清理")
    execute_cleanup(cleanup_files, dry_run=True)

    # 询问是否执行实际清理
    print("\n❓ 是否执行实际清理？")
    print("这将删除所有包装器和旧Agent文件，并创建备份。")
    choice = input("输入 'yes' 执行清理，输入其他键跳过: ").strip().lower()

    if choice == 'yes':
        print("\n🚨 执行实际清理...")
        success = execute_cleanup(cleanup_files, dry_run=False)

        if success:
            # 更新__init__.py
            update_init_file()

            print("\n🎉 清理完成！")            print("✅ 系统现在只包含8个核心Agent")
            print("✅ 所有旧代码已清理并备份")
            print("✅ __init__.py已更新为新架构")
    else:
        print("\n⏭️  跳过实际清理")
        print("如需稍后清理，请重新运行此脚本")

if __name__ == "__main__":
    main()
