#!/usr/bin/env python3
"""
Phase 2 迁移脚本
将 core/ 根目录文件移动到子目录并更新导入路径
"""

import os
import re
import sys
from pathlib import Path

# 迁移映射: {原文件: 新目录}
MIGRATION_MAP = {
    # executor/ - 工作流执行
    "execution_coordinator.py": "executor/",
    "production_workflow.py": "executor/",
    "team_executor.py": "executor/",
    "review_coordinator.py": "executor/",
    "cli_executor.py": "executor/",
    "executor_ecosystem.py": "executor/",
    "unified_tool_executor.py": "executor/",
    "langgraph_workflow_utils.py": "executor/",
    
    # routing/ - 路由
    "configurable_router.py": "routing/",
    "context_manager.py": "routing/",
    "entry_router.py": "routing/",
    "intelligent_router.py": "routing/",
    "langgraph_configurable_router.py": "routing/",
    
    # core_services/ - 核心服务
    "cache_system.py": "core_services/",
    "llm_integration.py": "core_services/",
}

# 旧导入 → 新导入 的替换模式
IMPORT_REPLACEMENTS = []

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
