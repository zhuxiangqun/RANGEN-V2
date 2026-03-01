import re
from pathlib import Path
import os
import typing
#!/usr/bin/env python3
"""
全面语法修复脚本
专门修复函数参数类型注解和其他语法错误
"""
def fix_function_parameter_syntax(content: str) -> str:
    """修复函数参数类型注解语法错误"""
    # 修复常见的函数参数类型注解错误
    patterns = [
        # 修复 None | Type] = default 语法
        (r'(\w+): None \| (\w+)\] = (\w+)', r'\1: None | \2 = \3'),
        (r'(\w+): None \| (\w+)\] = None', r'\1: None | \2 = None'),
        # 修复其他类型注解错误
        (r'(\w+): (\w+)\] = (\w+)', r'\1: \2 = \3'),
        (r'(\w+): (\w+)\] = None', r'\1: \2 = None'),
        # 修复 Union 类型注解
        (r'(\w+): Union\[([^\]+)\] = (\w+)', r'\1: typing.Union[\2] = \3'),
        (r'(\w+): Union\[([^\]+)\] = None', r'\1: typing.Union[\2] = None'),
        # 修复复杂的类型注解
        (r'(\w+): dict\[([^\]+)\] = (\w+)', r'\1: dict[\2] = \3'),
        (r'(\w+): list\[([^\]+)\] = (\w+)', r'\1: list[\2] = \3'),
        # 修复返回类型注解
        (r'\) -> (\w+)\]', r') -> \1')
    ]
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    return content

def fix_indentation_errors(content: str) -> str:
    """修复缩进错误"""
    lines = content.split('\n')
    fixed_lines = []
    for i, line in enumerate(lines):
        # 检查是否有意外的缩进
        if (line.strip() and not line.startswith(' ') and
            (line.strip().startswith('def ') or line.strip().startswith('class '))):
            # 确保类和函数定义没有意外缩进
            fixed_lines.append(line)
        elif (line.strip() and line.startswith(' ') and
              (line.strip().startswith('def ') or line.strip().startswith('class '))):
            # 修复意外缩进的函数或类定义
            fixed_lines.append(line.lstrip())
        else:
            fixed_lines.append(line)
    return '\n'.join(fixed_lines)
def fix_import_statements(content: str) -> str:
    """修复导入语句"""
    # 修复不完整的导入语句
    patterns = [
        (r'from datetime \n', 'from datetime import datetime\n'),
        (r'from datetime$', 'from datetime import datetime'),
        (r'import (\w+)\n\s*import (\w+)', r'import \1\nimport \2')
    ]
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    return content
def fix_type_annotations(content: str) -> str:
    """修复类型注解"""
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
        (r'Optional\[(\w+)\]', r'None | \1')
    ]
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    return content
def fix_syntax_errors(content: str) -> str:
    """修复其他语法错误"""
    # 修复常见的语法错误
    patterns = [
        # 修复括号不匹配
        (r'\(\s*\)\s*\]', '()'),
        (r'\[\s*\)', '()'),
        # 修复函数定义语法
        (r'async def (\w+)\(([^)]*)\):\s*$', r'async def \1(\2):'),
        (r'def (\w+)\(([^)]*)\):\s*$', r'def \1(\2):'),
        # 修复变量定义
        (r'(\w+): (\w+) = (\w+)\s*$', r'\1: \2 = \3')
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
        content = fix_function_parameter_syntax(content)
        content = fix_indentation_errors(content)
        content = fix_import_statements(content)
        content = fix_type_annotations(content)
        content = fix_syntax_errors(content)
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
    print("🔧 全面语法修复工具")
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
    print(f"🎯 全面语法修复完成！")

if __name__ == "__main__":
    main()
