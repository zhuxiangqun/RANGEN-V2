#!/usr/bin/env python3
"""
高级语法修复脚本
专门处理缩进错误和括号不匹配问题

功能特性:
- 自动修复缩进错误
- 修复括号不匹配问题
- 修复语法错误
- 批量处理文件
- 详细修复报告
"""

import re
import os
from typing import List, Dict, Any


def fix_indentation_errors(content: str) -> str:
    """修复缩进错误"""
    lines = content.split('\n')
    fixed_lines = []
    indent_stack = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # 跳过空行
        if not stripped:
            fixed_lines.append(line)
            continue

        # 处理类定义
        if stripped.startswith('class '):
            # 确保类定义没有缩进
            fixed_lines.append(stripped)
            indent_stack.append(0)
            continue

        # 处理函数定义
        if stripped.startswith('def ') or stripped.startswith('async def '):
            # 确保函数定义没有缩进
            fixed_lines.append(stripped)
            indent_stack.append(0)
            continue

        # 处理控制流语句
        if stripped.startswith('if ') or stripped.startswith('elif ') or stripped.startswith('else:'):
            # 确保控制流语句缩进正确
            if indent_stack:
                indent_level = indent_stack[-1] + 4
                fixed_lines.append(' ' * indent_level + stripped)
            else:
                fixed_lines.append(stripped)
            continue

        # 处理with语句
        if stripped.startswith('with '):
            if indent_stack:
                indent_level = indent_stack[-1] + 4
                fixed_lines.append(' ' * indent_level + stripped)
            else:
                fixed_lines.append(stripped)
            continue

        # 处理try/except语句
        if stripped.startswith('try:') or stripped.startswith('except ') or stripped.startswith('finally:'):
            if indent_stack:
                indent_level = indent_stack[-1] + 4
                fixed_lines.append(' ' * indent_level + stripped)
            else:
                fixed_lines.append(stripped)
            continue

        # 处理其他语句
        if stripped.startswith('return ') or stripped.startswith('break') or stripped.startswith('continue'):
            if indent_stack:
                indent_level = indent_stack[-1] + 4
                fixed_lines.append(' ' * indent_level + stripped)
            else:
                fixed_lines.append(stripped)
            continue

        # 处理变量赋值
        if '=' in stripped and not stripped.startswith('if ') and not stripped.startswith('elif '):
            if indent_stack:
                indent_level = indent_stack[-1] + 4
                fixed_lines.append(' ' * indent_level + stripped)
            else:
                fixed_lines.append(stripped)
            continue

        # 处理其他情况
        if indent_stack:
            indent_level = indent_stack[-1] + 4
            fixed_lines.append(' ' * indent_level + stripped)
        else:
            fixed_lines.append(stripped)

    return '\n'.join(fixed_lines)


def fix_bracket_errors(content: str) -> str:
    """修复括号不匹配错误"""
    # 修复常见的括号错误
    patterns = [
        # 修复未闭合的方括号
        (r'\[([^\]]*)$', r'[\1]'),
        (r'\(([^)]*)$', r'(\1)'),
        # 修复括号不匹配
        (r'\(\s*\)\s*\]', '()'),
        (r'\[\s*\)', '()'),
        (r'\(\s*\]', '()'),
        # 修复列表推导式
        (r'\[([^\]]*)\s*$', r'[\1]'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    return content


def fix_syntax_errors(content: str) -> str:
    """修复其他语法错误"""
    # 修复常见的语法错误
    patterns = [
        # 修复不完整的语句
        (r'(\w+)\s*=\s*\[([^\]]*)\s*$', r'\1 = [\2]'),
        (r'(\w+)\s*=\s*\(([^)]*)\s*$', r'\1 = (\2)'),
        # 修复函数调用
        (r'(\w+)\(([^)]*)\s*$', r'\1(\2)'),
        # 修复条件语句
        (r'if\s+([^:]+)\s*$', r'if \1:'),
        (r'elif\s+([^:]+)\s*$', r'elif \1:'),
        # 修复循环语句
        (r'for\s+([^:]+)\s*$', r'for \1:'),
        (r'while\s+([^:]+)\s*$', r'while \1:'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    return content


def fix_import_errors(content: str) -> str:
    """修复导入错误"""
    # 修复常见的导入错误
    patterns = [
        # 修复不完整的导入
        (r'import\s+([^,\s]+)\s*$', r'import \1'),
        (r'from\s+([^\s]+)\s+import\s+([^,\s]+)\s*$', r'from \1 import \2'),
        # 修复类型导入
        (r'import\s+([A-Z][a-zA-Z]*)\s*$', r'from typing import \1'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    return content


def fix_type_annotations(content: str) -> str:
    """修复类型注解错误"""
    # 修复常见的类型注解错误
    patterns = [
        # 修复不完整的类型注解
        (r':\s*([A-Z][a-zA-Z]*)\s*$', r': \1'),
        (r':\s*([A-Z][a-zA-Z]*)\s*\[([^\]]*)\s*$', r': \1[\2]'),
        # 修复类型参数
        (r'([A-Z][a-zA-Z]*)\s*\[([^\]]*)\s*$', r'\1[\2]'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    return content


def fix_file(file_path: str) -> Dict[str, Any]:
    """修复单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        fixes_applied = []

        # 应用各种修复
        if content != fix_indentation_errors(content):
            content = fix_indentation_errors(content)
            fixes_applied.append("indentation")

        if content != fix_bracket_errors(content):
            content = fix_bracket_errors(content)
            fixes_applied.append("brackets")

        if content != fix_syntax_errors(content):
            content = fix_syntax_errors(content)
            fixes_applied.append("syntax")

        if content != fix_import_errors(content):
            content = fix_import_errors(content)
            fixes_applied.append("imports")

        if content != fix_type_annotations(content):
            content = fix_type_annotations(content)
            fixes_applied.append("type_annotations")

        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                "success": True,
                "fixed": True,
                "fixes_applied": fixes_applied,
                "file_path": file_path
            }
        else:
            return {
                "success": True,
                "fixed": False,
                "fixes_applied": [],
                "file_path": file_path
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path
        }


def find_python_files(directory: str = ".") -> List[str]:
    """查找所有Python文件"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # 跳过venv和.git目录
        dirs[:] = [d for d in dirs if d not in ['venv', '.git', '__pycache__']]

        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    return python_files


def main():
    """主函数"""
    print("🔧 高级语法修复工具")
    print("=" * 50)

    # 获取所有Python文件
    python_files = find_python_files()

    if not python_files:
        print("❌ 未找到Python文件")
        return

    print(f"📁 找到 {len(python_files)} 个Python文件")
    print()

    fixed_count = 0
    error_count = 0
    total_fixes = 0

    for i, file_path in enumerate(python_files, 1):
        print(f"进度: {i}/{len(python_files)} - {file_path}")

        result = fix_file(file_path)

        if result["success"]:
            if result["fixed"]:
                fixed_count += 1
                total_fixes += len(result["fixes_applied"])
                print(f"  ✅ 已修复 ({', '.join(result['fixes_applied'])})")
            else:
                print(f"  ⏭️ 无需修复")
        else:
            error_count += 1
            print(f"  ❌ 修复失败: {result['error']}")

    print(f"\n📊 修复结果:")
    print(f"总文件数: {len(python_files)}")
    print(f"修复文件数: {fixed_count}")
    print(f"错误文件数: {error_count}")
    print(f"总修复次数: {total_fixes}")
    print(f"🎯 高级语法修复完成！")


if __name__ == "__main__":
    main()
