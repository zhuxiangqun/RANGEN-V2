import re
from pathlib import Path
import os
#!/usr/bin/env python3
"""
缩进修复脚本
专门处理try/except、if/else、for循环等语句的缩进问题
"""
def fix_indentation_errors(content: str) -> str:
    """修复缩进错误"""
    lines = content.split('\n')
    fixed_lines = []
    indent_level = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        # 跳过空行
        if not stripped:
            fixed_lines.append(line)
            continue
        # 处理控制流语句
        if stripped.startswith('try:') or stripped.startswith('except ') or stripped.startswith('finally:'):
            # try/except/finally 语句
            fixed_lines.append(' ' * (indent_level * 4) + stripped)
            indent_level += 1
            continue
        if stripped.startswith('if ') or stripped.startswith('elif ') or stripped.startswith('else:'):
            # if/elif/else 语句
            fixed_lines.append(' ' * (indent_level * 4) + stripped)
            if not stripped.endswith(':'):
                # 如果if语句没有冒号，添加冒号
                fixed_lines[-1] = fixed_lines[-1] + ':'
                indent_level += 1
            continue
        if stripped.startswith('for ') or stripped.startswith('while '):
            # for/while 循环语句
            fixed_lines.append(' ' * (indent_level * 4) + stripped)
            if not stripped.endswith(':'):
                # 如果for语句没有冒号，添加冒号
                fixed_lines[-1] = fixed_lines[-1] + ':'
                indent_level += 1
        elif stripped.startswith('with '):
            # with 语句
            fixed_lines.append(' ' * (indent_level * 4) + stripped)
            if not stripped.endswith(':'):
                # 如果with语句没有冒号，添加冒号
                fixed_lines[-1] = fixed_lines[-1] + ':'
                indent_level += 1
        elif stripped.startswith('def ') or stripped.startswith('async def '):
            # 函数定义
            indent_level = 0
            fixed_lines.append(stripped)
            indent_level += 1
        elif stripped.startswith('class '):
            # 类定义
            indent_level = 0
            fixed_lines.append(stripped)
            indent_level += 1
        elif stripped.startswith('return ') or stripped.startswith('break') or stripped.startswith('continue'):
            # 控制流语句
            fixed_lines.append(' ' * (indent_level * 4) + stripped)
        elif '=' in stripped and not stripped.startswith('if ') and not stripped.startswith('elif '):
            # 变量赋值
            fixed_lines.append(' ' * (indent_level * 4) + stripped)
        else:
            # 处理其他情况
            fixed_lines.append(' ' * (indent_level * 4) + stripped)
    return '\n'.join(fixed_lines)
def fix_bracket_errors(content: str) -> str:
    """修复括号错误"""
    # 修复常见的括号错误
    patterns = [
        # 修复未闭合的括号
        (r'\(\s*\)\s*\)', '()'),
        (r'\[\s*\)', '()'),
        (r'\(\s*\]', '()'),
        # 修复函数调用
        (r'(\w+)\(([^)]*)\s*$', r'\1(\2)'),
        # 修复列表定义
        (r'(\w+)\s*=\s*\[([^\]*)\s*$', r'\1 = [\2]')
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
        content = fix_indentation_errors(content)
        content = fix_bracket_errors(content)
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
    print("🔧 缩进修复工具")
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
    print(f"🎯 缩进修复完成！")

if __name__ == "__main__":
    main()
