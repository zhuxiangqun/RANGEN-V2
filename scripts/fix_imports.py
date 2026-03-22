#!/usr/bin/env python3
"""
批量修复 src/ 目录中的导入路径问题

修复模式：
1. src.agents.base_agent → src.agents.core.base_agent
2. src.agents.react_agent → src.agents.core.react_agent
3. src.agents.reasoning_agent → src.agents.core.reasoning_agent
4. src.agents.retrieval_agent → src.agents.core.retrieval_agent
5. src.agents.tools.xxx → src.agents.execution_tools.xxx
"""

import os
from pathlib import Path

# 导入路径映射
IMPORT_MAPPINGS = {
    # Agent 核心模块
    'from src.agents.base_agent': 'from src.agents.core.base_agent',
    'from src.agents.react_agent': 'from src.agents.core.react_agent',
    'from src.agents.reasoning_agent': 'from src.agents.core.reasoning_agent',
    'from src.agents.retrieval_agent': 'from src.agents.core.retrieval_agent',
    # Tools 模块
    'from src.agents.tools.': 'from src.agents.execution_tools.',
    # 废弃的 intelligent_tool_selector
    'from src.agents.intelligent_tool_selector': 'from src.agents.execution.intelligent_tool_selector',
}

def fix_imports_in_file(filepath):
    """修复单个文件中的导入"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        for old, new in IMPORT_MAPPINGS.items():
            content = content.replace(old, new)
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    src_dir = Path(__file__).parent.parent / 'src'
    fixed_count = 0
    
    for py_file in src_dir.rglob('*.py'):
        if py_file.name == __name__:
            continue
        if fix_imports_in_file(py_file):
            print(f"✅ Fixed: {py_file.relative_to(src_dir.parent)}")
            fixed_count += 1
    
    print(f"\nTotal fixed: {fixed_count} files")

if __name__ == '__main__':
    main()
