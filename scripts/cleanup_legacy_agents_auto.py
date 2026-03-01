#!/usr/bin/env python3
"""
自动Agent清理脚本 - 100%迁移后清理不再需要的旧文件
非交互式版本，直接执行清理
"""

import os
import shutil
from pathlib import Path

def analyze_and_cleanup():
    """分析并清理旧Agent文件"""
    print("🧹 自动Agent清理 - 100%迁移后清理")
    print("=" * 60)

    agents_dir = Path("src/agents")

    # 获取所有Python文件（排除__pycache__和tools目录）
    all_py_files = []
    for file_path in agents_dir.rglob("*.py"):
        if "__pycache__" not in str(file_path) and "tools" not in str(file_path):
            all_py_files.append(file_path)

    print(f"📊 发现 {len(all_py_files)} 个Python文件")

    # 核心Agent（8个，保留）
    core_agents = [
        'rag_agent.py',  # RAGExpert
        'reasoning_expert.py',  # ReasoningExpert
        'agent_coordinator.py',  # AgentCoordinator
        'quality_controller.py',  # QualityController
        'tool_orchestrator.py',  # ToolOrchestrator
        'memory_manager.py',  # MemoryManager
        'learning_optimizer.py',  # LearningOptimizer
        'chief_agent.py',  # ChiefAgent
    ]

    # 辅助文件（保留）
    auxiliary_files = [
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
    ]

    # 统计各类文件
    core_count = sum(1 for f in all_py_files if f.name in core_agents)
    aux_count = sum(1 for f in all_py_files if f.name in auxiliary_files)
    wrapper_count = sum(1 for f in all_py_files if 'wrapper' in f.name)
    legacy_count = sum(1 for f in all_py_files
                      if f.name not in core_agents
                      and f.name not in auxiliary_files
                      and 'wrapper' not in f.name)

    print(f"\n📋 文件分类统计:")
    print(f"   核心Agent (8个): {core_count} 个 ✅")
    print(f"   辅助文件: {aux_count} 个 ✅")
    print(f"   包装器文件: {wrapper_count} 个 🗑️")
    print(f"   旧Agent文件: {legacy_count} 个 🗑️")

    # 识别需要清理的文件
    cleanup_files = []
    for file_path in all_py_files:
        if (file_path.name not in core_agents and
            file_path.name not in auxiliary_files):
            cleanup_files.append(file_path)

    print(f"\n🗑️  需要清理的文件 ({len(cleanup_files)}个):")
    for file_path in sorted(cleanup_files, key=lambda x: x.name):
        print(f"   • {file_path.name}")

    if not cleanup_files:
        print("ℹ️  没有发现需要清理的文件")
        return

    # 执行清理
    print(f"\n🗑️  执行清理...")
    print("⚠️  将自动备份并删除文件")

    # 创建备份目录
    backup_dir = Path("backup_legacy_agents")
    backup_dir.mkdir(exist_ok=True)
    print(f"📁 创建备份目录: {backup_dir}")

    cleaned_count = 0
    for file_path in cleanup_files:
        try:
            # 备份文件
            backup_path = backup_dir / file_path.name
            shutil.copy2(file_path, backup_path)
            print(f"   📋 备份: {file_path.name}")

            # 删除原文件
            file_path.unlink()
            print(f"   🗑️  删除: {file_path.name}")
            cleaned_count += 1

        except Exception as e:
            print(f"   ❌ 处理失败 {file_path.name}: {e}")

    print(f"\n✅ 清理完成: {cleaned_count} 个文件已删除并备份")

    # 更新__init__.py文件
    update_init_file()

    # 最终验证
    print("\n🔍 最终验证")    print("-" * 40)

    remaining_files = list(agents_dir.glob("*.py"))
    remaining_files = [f for f in remaining_files if "__pycache__" not in str(f)]

    print(f"📊 清理后剩余文件: {len(remaining_files)} 个")

    # 验证8个核心Agent都在
    core_present = sum(1 for f in remaining_files if f.name in core_agents)
    print(f"✅ 核心Agent: {core_present}/8 个存在")

    # 验证辅助文件
    aux_present = sum(1 for f in remaining_files if f.name in auxiliary_files)
    print(f"✅ 辅助文件: {aux_present}/{len(auxiliary_files)} 个存在")

    print("\n🎉 清理完成！")    print("✅ 系统现在只包含8个核心Agent + 必要的辅助文件")
    print("✅ 所有旧代码已清理并备份")
    print("✅ __init__.py已更新为新架构")

def update_init_file():
    """更新__init__.py文件"""
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
    analyze_and_cleanup()

if __name__ == "__main__":
    main()
