#!/usr/bin/env python3
"""
最终语法修复脚本
专门处理剩余的特定语法错误
"""

import os
import re
from typing import List, Tuple


def fix_specific_syntax_errors(content: str) -> str:
    """修复特定的语法错误"""
    # 修复函数调用中的括号错误
    patterns = [
        # 修复 asyncio.run(check_faiss_data()] 这样的错误
        (r'asyncio\.run\(([^)]+)\]', r'asyncio.run(\1)'),
        (r'\(([^)]+)\]', r'(\1)'),

        # 修复函数调用中缺少的括号
        (r'(\w+)\(([^)]*)\s*$', r'\1(\2)'),

        # 修复列表定义中的括号错误
        (r'\[([^\]]*)\s*$', r'[\1]'),

        # 修复字典定义中的括号错误
        (r'\{([^}]*)\s*$', r'{\1}'),

        # 修复函数参数中的语法错误
        (r'(\w+): (\w+)\] = (\w+)', r'\1: \2 = \3'),
        (r'(\w+): (\w+)\] = None', r'\1: \2 = None'),

        # 修复返回类型注解
        (r'\) -> (\w+)\]', r') -> \1'),

        # 修复复杂的类型注解
        (r'Union\[([^\]]+)\]', r'Union[\1]'),
        (r'Optional\[([^\]]+)\]', r'Optional[\1]'),
        (r'List\[([^\]]+)\]', r'List[\1]'),
        (r'Dict\[([^\]]+)\]', r'Dict[\1]'),

        # 修复函数调用中的逗号问题
        (r'(\w+)\(([^)]*)\s*$', r'\1(\2)'),

        # 修复列表推导式
        (r'\[([^\]]*)\s*$', r'[\1]'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    return content


def fix_indentation_blocks(content: str) -> str:
    """修复缩进块问题"""
    lines = content.split('\n')
    fixed_lines = []
    indent_stack = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # 跳过空行
        if not stripped:
            fixed_lines.append(line)
            continue

        # 处理控制流语句
        if stripped.startswith('try:') or stripped.startswith('except ') or stripped.startswith('finally:'):
            # 确保有正确的缩进
            if indent_stack:
                indent_level = indent_stack[-1] + 4
            else:
                indent_level = 0
            fixed_lines.append(' ' * indent_level + stripped)
            indent_stack.append(indent_level)
            continue

        if stripped.startswith('if ') or stripped.startswith('elif ') or stripped.startswith('else:'):
            # 确保有正确的缩进
            if indent_stack:
                indent_level = indent_stack[-1] + 4
            else:
                indent_level = 0
            fixed_lines.append(' ' * indent_level + stripped)
            if not stripped.endswith(':'):
                fixed_lines[-1] = fixed_lines[-1] + ':'
            indent_stack.append(indent_level)
            continue

        if stripped.startswith('for ') or stripped.startswith('while '):
            # 确保有正确的缩进
            if indent_stack:
                indent_level = indent_stack[-1] + 4
            else:
                indent_level = 0
            fixed_lines.append(' ' * indent_level + stripped)
            if not stripped.endswith(':'):
                fixed_lines[-1] = fixed_lines[-1] + ':'
            indent_stack.append(indent_level)
            continue

        if stripped.startswith('with '):
            # 确保有正确的缩进
            if indent_stack:
                indent_level = indent_stack[-1] + 4
            else:
                indent_level = 0
            fixed_lines.append(' ' * indent_level + stripped)
            if not stripped.endswith(':'):
                fixed_lines[-1] = fixed_lines[-1] + ':'
            indent_stack.append(indent_level)
            continue

        # 处理函数和类定义
        if stripped.startswith('def ') or stripped.startswith('async def '):
            indent_stack = [0]
            fixed_lines.append(stripped)
            indent_stack.append(4)
            continue

        if stripped.startswith('class '):
            indent_stack = [0]
            fixed_lines.append(stripped)
            indent_stack.append(4)
            continue

        # 处理其他语句
        if stripped.startswith('return ') or stripped.startswith('break') or stripped.startswith('continue'):
            if indent_stack:
                indent_level = indent_stack[-1]
                fixed_lines.append(' ' * indent_level + stripped)
            else:
                fixed_lines.append(stripped)
            continue

        # 处理变量赋值和其他语句
        if indent_stack:
            indent_level = indent_stack[-1]
            fixed_lines.append(' ' * indent_level + stripped)
        else:
            fixed_lines.append(stripped)

    return '\n'.join(fixed_lines)


def fix_import_errors(content: str) -> str:
    """修复导入错误"""
    # 修复不完整的导入语句
    patterns = [
        (r'from datetime \n', 'from datetime import datetime\n'),
        (r'from datetime$', 'from datetime import datetime'),
        (r'import (\w+)\n\s*import (\w+)', r'import \1\nimport \2'),
        (r'from (\w+) import (\w+)\n\s*from (\w+) import (\w+)', r'from \1 import \2\nfrom \3 import \4'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    return content


def fix_type_annotations(content: str) -> str:
    """修复类型注解错误"""
    # 修复复杂的类型注解
    patterns = [
        # 简化复杂的类型注解
        (r'dict\[str, Union\[str, float, list\[dict\[str, Union\[str, float\]\]\]\]\]', 'dict'),
        (r'list\[dict\[str, Union\[str, float\]\]\]', 'list'),
        (r'Union\[str, float, list\[dict\[str, Union\[str, float\]\]\]\]', 'object'),
        (r'Union\[str, float\]', 'object'),

        # 修复其他复杂类型
        (r'Dict\[str, Any\]', 'dict'),
        (r'List\[Dict\[str, Any\]\]', 'list'),
        (r'Optional\[(\w+)\]', r'None | \1'),

        # 修复函数参数类型注解
        (r'(\w+): None \| (\w+)\] = (\w+)', r'\1: None | \2 = \3'),
        (r'(\w+): None \| (\w+)\] = None', r'\1: None | \2 = None'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    return content


def fix_bracket_errors(content: str) -> str:
    """修复括号错误"""
    # 修复未匹配的括号
    patterns = [
        # 移除多余的右括号
        (r'\)+$', ''),
        (r'^\s*\)+\s*$', ''),

        # 移除多余的右方括号
        (r'\]+\s*$', ''),
        (r'^\s*\]+\s*$', ''),

        # 移除多余的大括号
        (r'\}+\s*$', ''),
        (r'^\s*\}+\s*$', ''),

        # 修复多余的逗号
        (r',\s*\)', ')'),
        (r',\s*\]', ']'),
        (r',\s*}', '}'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    return content


def fix_variable_errors(content: str) -> str:
    """修复变量相关错误"""
    # 修复未定义的变量引用
    patterns = [
        # 修复常见的变量名错误
        (r'\b(\w+)\s*=\s*(\w+)\s*if\s*(\w+)\s*else\s*(\w+)\s*$', r'\1 = \2 if \3 else \4'),

        # 修复赋值语句
        (r'(\w+)\s*=\s*(\w+)\s*$', r'\1 = \2'),

        # 修复函数调用
        (r'(\w+)\(\)\s*$', r'\1()'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    return content


def fix_file(file_path: str) -> bool:
    """修复单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 应用修复
        content = fix_specific_syntax_errors(content)
        content = fix_indentation_blocks(content)
        content = fix_import_errors(content)
        content = fix_type_annotations(content)
        content = fix_bracket_errors(content)
        content = fix_variable_errors(content)

        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False

    except Exception as e:
        print(f"修复文件 {file_path} 时出错: {str(e)}")
        return False


def find_python_files(directory: str = ".") -> List[str]:
    """查找所有Python文件"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # 跳过虚拟环境和缓存目录
        if any(skip in root for skip in ['venv', '__pycache__', '.git', 'node_modules']):
            continue
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files


def main():
    """主函数"""
    print("🔧 最终语法修复工具")
    print("=" * 50)

    # 获取所有Python文件
    try:
        with open('all_py_files.txt', 'r') as f:
            file_list = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        # 如果文件不存在，自动查找Python文件
        file_list = find_python_files()
        print(f"自动找到 {len(file_list)} 个Python文件")

    fixed_count = 0
    error_count = 0

    for i, file_path in enumerate(file_list, 1):
        print(f"进度: {i}/{len(file_list)} - {file_path}")
        try:
            if fix_file(file_path):
                fixed_count += 1
                print(f"  ✅ 已修复")
            else:
                print(f"  ⏭️ 无需修复")
        except Exception as e:
            error_count += 1
            print(f"  ❌ 修复失败: {str(e)}")

    print(f"\n📊 修复结果:")
    print(f"总文件数: {len(file_list)}")
    print(f"修复文件数: {fixed_count}")
    print(f"错误文件数: {error_count}")
    print(f"🎯 最终语法修复完成！")


if __name__ == "__main__":
    main()
