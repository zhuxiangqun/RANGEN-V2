#!/usr/bin/env python3
"""
批量linter修复脚本
自动修复常见的linter问题：未使用导入、类型注解、属性访问等

功能特性:
- 自动修复未使用的导入
- 修复类型注解问题
- 修复属性访问问题
- 批量处理文件
- 详细修复报告
"""

import re
import os
from typing import List, Dict, Any


class LinterFixer:
    """linter修复器"""

    def __init__(self):
        self.fixed_files: List[str] = []
        self.errors: List[str] = []

    def fix_unused_imports(self, content: str) -> str:
        """修复未使用的导入"""
        # 常见的未使用导入模式
        unused_imports = [
            r'import json\n',
            r'import os\n',
            r'import time\n',
            r'import time\n',
            r'from datetime import datetime\n',
            r'import typing\n',
            r'from typing import Any\n',
            r'from typing import Dict\n',
            r'from typing import List\n',
            r'from typing import Optional\n',
            r'from typing import Set\n',
            r'from typing import Tuple\n',
            r'from typing import Union\n',
        ]

        for pattern in unused_imports:
            content = re.sub(pattern, '', content)

        # 修复空的typing导入
        content = re.sub(r'from typing import\n', '', content)
        content = re.sub(r'from typing import \n', '', content)

        # 修复重复的导入
        content = re.sub(r'import (\w+)\nimport \1\n', r'import \1\n', content)

        return content

    def fix_type_annotations(self, content: str) -> str:
        """修复类型注解问题"""
        # 修复Dict类型参数
        content = re.sub(r'Dict\[', 'dict[', content)
        content = re.sub(r'List\[', 'list[', content)
        content = re.sub(r'Set\[', 'set[', content)
        content = re.sub(r'Tuple\[', 'tuple[', content)

        # 修复Optional类型
        content = re.sub(r'Optional\[', 'None | ', content)

        # 修复Any类型
        content = re.sub(r': typing\.Any', ': object', content)
        content = re.sub(r'-> Any', '-> object', content)

        # 修复Union类型
        content = re.sub(r'Union\[', 'None | ', content)

        return content

    def fix_attribute_access(self, content: str) -> str:
        """修复属性访问问题"""
        # 添加空值检查（可选，可能过于激进）
        # content = re.sub(
        #     r'(\w+)\.(\w+)',
        #     r'getattr(\1, "\2", None)',
        #     content
        # )
        return content

    def fix_syntax_errors(self, content: str) -> str:
        """修复语法错误"""
        # 修复不完整的语句
        content = re.sub(r'(\w+)\s*=\s*\[([^\]]*)\s*$', r'\1 = [\2]', content)
        content = re.sub(r'(\w+)\s*=\s*\(([^)]*)\s*$', r'\1 = (\2)', content)

        # 修复函数调用
        content = re.sub(r'(\w+)\(([^)]*)\s*$', r'\1(\2)', content)

        # 修复条件语句
        content = re.sub(r'if\s+([^:]+)\s*$', r'if \1:', content)
        content = re.sub(r'elif\s+([^:]+)\s*$', r'elif \1:', content)

        return content

    def fix_indentation(self, content: str) -> str:
        """修复缩进问题"""
        lines = content.split('\n')
        fixed_lines = []
        indent_level = 0

        for line in lines:
            stripped = line.strip()

            # 跳过空行
            if not stripped:
                fixed_lines.append('')
                continue

            # 处理缩进
            if stripped.startswith('class ') or stripped.startswith('def '):
                indent_level = 0
            elif stripped.startswith('if ') or stripped.startswith('elif ') or stripped.startswith('else:'):
                indent_level = 0
            elif stripped.startswith('try:') or stripped.startswith('except ') or stripped.startswith('finally:'):
                indent_level = 0
            elif stripped.startswith('with '):
                indent_level = 0
            elif stripped.startswith('for ') or stripped.startswith('while '):
                indent_level = 0
            elif stripped.startswith('return ') or stripped.startswith('break') or stripped.startswith('continue'):
                indent_level = 4
            elif '=' in stripped and not stripped.startswith('if ') and not stripped.startswith('elif '):
                indent_level = 4
            else:
                indent_level = 4

            fixed_lines.append(' ' * indent_level + stripped)

        return '\n'.join(fixed_lines)

    def fix_file(self, file_path: str) -> Dict[str, Any]:
        """修复单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            fixes_applied = []

            # 应用各种修复
            if content != self.fix_unused_imports(content):
                content = self.fix_unused_imports(content)
                fixes_applied.append("unused_imports")

            if content != self.fix_type_annotations(content):
                content = self.fix_type_annotations(content)
                fixes_applied.append("type_annotations")

            if content != self.fix_syntax_errors(content):
                content = self.fix_syntax_errors(content)
                fixes_applied.append("syntax_errors")

            if content != self.fix_indentation(content):
                content = self.fix_indentation(content)
                fixes_applied.append("indentation")

            # 如果内容有变化，写回文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                self.fixed_files.append(file_path)

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
            error_msg = f"修复文件 {file_path} 时出错: {str(e)}"
            self.errors.append(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "file_path": file_path
            }

    def batch_fix(self, file_list: List[str]) -> Dict[str, Any]:
        """批量修复文件"""
        print(f"开始批量修复 {len(file_list)} 个文件...")

        fixed_count = 0
        error_count = 0

        for i, file_path in enumerate(file_list, 1):
            print(f"进度: {i}/{len(file_list)} - {file_path}")

            result = self.fix_file(file_path)

            if result["success"]:
                if result["fixed"]:
                    fixed_count += 1
                    print(f"  ✅ 已修复 ({', '.join(result['fixes_applied'])})")
                else:
                    print(f"  ⏭️ 无需修复")
            else:
                error_count += 1
                print(f"  ❌ 修复失败: {result['error']}")

        return {
            "total_files": len(file_list),
            "fixed_files": fixed_count,
            "error_files": error_count,
            "fixed_file_list": self.fixed_files,
            "errors": self.errors
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
    print("🔧 批量linter修复工具")
    print("=" * 50)

    # 获取所有Python文件
    python_files = find_python_files()

    if not python_files:
        print("❌ 未找到Python文件")
        return

    print(f"📁 找到 {len(python_files)} 个Python文件")
    print()

    # 创建修复器
    fixer = LinterFixer()

    # 执行批量修复
    results = fixer.batch_fix(python_files)

    # 输出结果
    print("\n" + "=" * 50)
    print("📊 修复结果:")
    print(f"总文件数: {results['total_files']}")
    print(f"修复文件数: {results['fixed_files']}")
    print(f"错误文件数: {results['error_files']}")

    if results['fixed_files'] > 0:
        print(f"\n✅ 已修复的文件:")
        for file_path in results['fixed_file_list']:
            print(f"  - {file_path}")

    if results['errors']:
        print(f"\n❌ 修复错误:")
        for error in results['errors']:
            print(f"  - {error}")

    print(f"\n🎯 修复完成！")


if __name__ == "__main__":
    main()
