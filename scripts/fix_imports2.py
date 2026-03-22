#!/usr/bin/env python3
"""
批量修复 src/ 目录中的导入路径问题 (第二轮)

修复模式：
1. src.api → src.access.api (在 src/access/api/ 内)
2. src.services.tool_registry → src.agents.execution_tools.tool_registry
3. src.services.multimodal_service → 正确路径
4. src.services.answer_generation_service → 正确路径
5. src.services.knowledge_retrieval_service → 正确路径
"""

import os
from pathlib import Path

# 导入路径映射
IMPORT_MAPPINGS = {
    # API 路由内的相对导入
    'from src.api.': 'from .',
    # services 模块路径
    'from src.services.tool_registry': 'from src.agents.execution_tools.tool_registry',
}

def fix_imports_in_file(filepath):
    """修复单个文件中的导入"""
    # 跳过 server.py，因为它需要特殊处理
    if filepath.name == 'server.py':
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # 跳过已经是相对导入的情况
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            # 如果是在 src/access/api/ 目录下，将 from src.api.X 改为 from .X
            if 'from src.access.api.' in line:
                line = line.replace('from src.access.api.', 'from .')
            # 跳过非 api 路由的 src.api 导入
            elif 'from src.api.' in line and 'src.access.api' not in line:
                # 可能是其他 src.api.xxx，保持不变
                pass
            new_lines.append(line)
        content = '\n'.join(new_lines)
        
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
