#!/usr/bin/env python3
"""
Phase 7 迁移脚本
整理 src/core/ 根目录文件到对应子目录
"""

import os
import re
import sys
from pathlib import Path

# 迁移映射: {原文件: 新目录}
MIGRATION_MAP = {
    # langgraph_nodes/ - LangGraph 工作流节点
    "langgraph_unified_workflow.py": "langgraph_nodes/",
    "langgraph_agent_nodes.py": "langgraph_nodes/",
    "langgraph_capability_nodes.py": "langgraph_nodes/",
    "langgraph_config_nodes.py": "langgraph_nodes/",
    "langgraph_core_nodes.py": "langgraph_nodes/",
    "langgraph_detailed_processing_nodes.py": "langgraph_nodes/",
    "langgraph_error_handler.py": "langgraph_nodes/",
    "langgraph_learning_nodes.py": "langgraph_nodes/",
    "langgraph_reasoning_nodes.py": "langgraph_nodes/",
    
    # validators/ - 验证和审查
    "validation_system.py": "validators/",
    "verification_loop.py": "validators/",
    "verdict.py": "validators/",
    "judgment_evaluation.py": "validators/",
    "review_pipeline.py": "validators/",
    "review_integration.py": "validators/",
    "agent_reviewer.py": "validators/",
    
    # config/ - 配置系统
    "dynamic_config_system.py": "config/",
    "declarative_config.py": "config/",
    "config_loader.py": "config/",
    "lite_configurator.py": "config/",
    
    # agents/ - Agent 相关 (core 级别的)
    "capability_orchestration_engine.py": "agents/",
    "skill_registry.py": "agents/",
    "agent_linter.py": "agents/",
    "agent_observability_client.py": "agents/",
}

def get_import_pattern(old_module, new_module):
    """生成导入替换模式"""
    return [
        (f"from src.core.{old_module} import", f"from src.core.{new_module}.{old_module} import"),
        (f"from src.core import {old_module}", f"from src.core.{new_module} import {old_module}"),
        (f"import src.core.{old_module}", f"import src.core.{new_module}.{old_module}"),
    ]

def update_file_imports(filepath, old_module, new_module):
    """更新单个文件的导入"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # 替换模式
    replacements = get_import_pattern(old_module, new_module)
    for old, new in replacements:
        content = content.replace(old, new)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    project_root = Path(__file__).parent.parent
    core_dir = project_root / "src" / "core"
    
    updated_files = []
    
    for filename, target_dir in MIGRATION_MAP.items():
        old_path = core_dir / filename
        new_dir = core_dir / target_dir
        new_path = new_dir / filename
        
        if not old_path.exists():
            print(f"⚠ 跳过 (不存在): {filename}")
            continue
        
        old_module = filename.replace(".py", "")
        print(f"处理: {filename} → {target_dir}")
        
        # 1. 创建目标目录
        new_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. 移动文件
        old_path.rename(new_path)
        print(f"  ✓ 移动: {old_path} → {new_path}")
        
        # 3. 更新所有导入
        src_dir = project_root / "src"
        for pyfile in src_dir.rglob("*.py"):
            if pyfile == new_path:  # 跳过自己
                continue
            if update_file_imports(pyfile, old_module, target_dir.rstrip("/")):
                updated_files.append(str(pyfile))
                print(f"  ✓ 更新导入: {pyfile}")
    
    print(f"\n完成! 更新了 {len(updated_files)} 个文件的导入")

if __name__ == "__main__":
    main()
