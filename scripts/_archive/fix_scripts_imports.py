#!/usr/bin/env python3
"""
批量修复 scripts/ 目录中的旧路径引用

需要修复的路径映射：
- src.access.api.server → src.access.api.server
- src.core.* → 新路径或注释
"""

import os
import re
from pathlib import Path

# 路径映射表
PATH_MAPPINGS = {
    'src.access.api.server': 'src.access.api.server',
    'src/core/llm_integration': 'src/orchestration/core_services/llm_integration',
}

# 需要注释掉的 src.core 导入（文件已移除）
COMMENT_OUT_PATTERNS = [
    'src/core/reflection.py',
    'src/core/learning_orchestrator.py',
    'src/core/agent_role_registry.py',
    'src/core/progressive_tool_loader.py',
    'src/core/cli_tools.py',
    'src/core/tool_loader_integration.py',
    'src/core/agent_linter.py',
    'src/core/agent_reviewer.py',
    'src/core/agent_observability_client.py',
    'src/core/harness_entropy_manager.py',
]

def fix_file(filepath):
    """修复单个文件中的路径引用"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # 替换 src.access.api.server
    content = content.replace('from src.access.api.server', 'from src.access.api.server')
    content = content.replace('src.access.api.server', 'src.access.api.server')
    content = content.replace('src.access.api.server', 'src.access.api.server')
    
    # 替换 src.core.llm_integration
    content = content.replace('from src.orchestration.core_services.llm_integration', 'from src.orchestration.core_services.llm_integration')
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    scripts_dir = Path(__file__).parent.parent / 'scripts'
    fixed_count = 0
    
    # 遍历所有 Python 文件
    for py_file in scripts_dir.rglob('*.py'):
        if py_file.name == __name__:
            continue
        if fix_file(py_file):
            print(f"✅ Fixed: {py_file.relative_to(scripts_dir.parent)}")
            fixed_count += 1
    
    print(f"\nTotal fixed: {fixed_count} files")

if __name__ == '__main__':
    main()
