import re
from pathlib import Path
import os
#!/usr/bin/env python3
"""
终极语法修复脚本
专门处理括号不匹配和缩进问题
"""
def fix_bracket_mismatches(content: str) -> str:
    """修复括号不匹配问题"""
    # 修复常见的括号不匹配错误
    patterns = [
        # 修复函数参数中的括号错误
        (r'(\w+): list\[(\w+)\)\)', r'\1: list[\2])'),
        (r'(\w+): dict\[(\w+)\)\)', r'\1: dict[\2])'),
        (r'(\w+): (\w+)\)\)', r'\1: \2)'),
        # 修复函数调用中的括号错误
        (r'(\w+)\(([^)]*)\)\)', r'\1(\2)'),
        (r'(\w+)\(([^)]*)\[\)', r'\1(\2)'),
        # 修复列表和字典中的括号错误
        (r'\[([^\]*)\)\)', r'[\1]'),
        (r'\{([^}]*)\)\)', r'{\1}'),
        # 修复类型注解中的括号错误
        (r'(\w+): (\w+)\[([^\]*)\)\)', r'\1: \2[\3])'),
        (r'(\w+): (\w+)\[([^\]*)\[\)', r'\1: \2[\3])'),
        # 修复函数返回类型注解
        (r'\) -> (\w+)\)\)', r') -> \1)'),
        (r'\) -> (\w+)\[([^\]*)\)\)', r') -> \1[\2])'),
        # 修复复杂的类型注解
        (r'Union\[([^\]*)\)\)', r'Union[\1])'),
        (r'Optional\[([^\]*)\)\)', r'Optional[\1])'),
        (r'List\[([^\]*)\)\)', r'List[\1])'),
        (r'Dict\[([^\]*)\)\)', r'Dict[\1])'),
        # 修复函数调用中的参数括号
        (r'"([^"]*)"\)\)', r'"\1")'),
        (r"'([^']*)'\)\)", r"'\1')"),
        # 修复列表和字典字面量
        (r'\[([^\]*)\]\)\)', r'[\1])'),
        (r'\{([^}]*)\}\)\)', r'{\1})')
    ]
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    return content
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
                fixed_lines.append(stripped)
            continue
        # 处理变量赋值和其他语句
        if indent_stack:
            indent_level = indent_stack[-1]
            fixed_lines.append(' ' * indent_level + stripped)
        else:
            fixed_lines.append(stripped)
    return '\n'.join(fixed_lines)
def fix_specific_syntax_errors(content: str) -> str:
    """修复特定的语法错误"""
    # 修复常见的语法错误
    patterns = [
        # 修复函数调用中的括号错误
        (r'(\w+)\(([^)]*)\)\)', r'\1(\2)'),
        (r'(\w+)\(([^)]*)\[\)', r'\1(\2)'),
        # 修复列表和字典定义
        (r'\[([^\]*)\]\)\)', r'[\1])'),
        (r'\{([^}]*)\}\)\)', r'{\1})'),
        # 修复类型注解
        (r'(\w+): (\w+)\[([^\]*)\]\)\)', r'\1: \2[\3])'),
        (r'(\w+): (\w+)\[([^\]*)\[\)', r'\1: \2[\3])'),
        # 修复函数返回类型
        (r'\) -> (\w+)\[([^\]*)\]\)\)', r') -> \1[\2])'),
        (r'\) -> (\w+)\[([^\]*)\[\)', r') -> \1[\2])'),
        # 修复复杂的类型注解
        (r'Union\[([^\]*)\]\)\)', r'Union[\1])'),
        (r'Optional\[([^\]*)\]\)\)', r'Optional[\1])'),
        (r'List\[([^\]*)\]\)\)', r'List[\1])'),
        (r'Dict\[([^\]*)\]\)\)', r'Dict[\1])'),
        # 修复字符串字面量
        (r'"([^"]*)"\)\)', r'"\1")'),
        (r"'([^']*)'\)\)", r"'\1')"),
        # 修复变量名
        (r'(\w+)\)\)', r'\1)')
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
        content = fix_bracket_mismatches(content)
        content = fix_indentation_errors(content)
        content = fix_specific_syntax_errors(content)
        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"修复文件 {file_path} 时出错: {str(e)}")
        return False
def main():
    """主函数"""
    print("🔧 终极语法修复工具")
    print("=" * 50)
    # 获取所有Python文件
    with open('all_py_files.txt', 'r') as f:
        file_list = [line.strip() for line in f if line.strip()]
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
    print(f"🎯 终极语法修复完成！")

if __name__ == "__main__":
    main()
