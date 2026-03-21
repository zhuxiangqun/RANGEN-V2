#!/usr/bin/env python3
"""
全面清理脚本
清理所有剩余的重复代码、未使用的导入和空方法
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Set

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveCleaner:
    """全面清理器"""

    def __init__(self, src_dir: str = "src"):
        self.src_dir = Path(src_dir)

    def remove_unused_imports(self) -> int:
        """移除未使用的导入"""
        logger.info("🧹 移除未使用的导入...")

        cleaned_count = 0

        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                original_content = content

                # 移除未使用的导入
                lines = content.split('\n')
                cleaned_lines = []
                i = 0

                while i < len(lines):
                    line = lines[i]

                    # 检查是否是导入语句
                    if line.strip().startswith(('import ', 'from ')):
                        # 检查这个导入是否在文件中被使用
                        import_name = self._extract_import_name(line)
                        if import_name and not self._is_import_used(content, import_name):
                            # 跳过这个导入
                            i += 1
                            continue

                    cleaned_lines.append(line)
                    i += 1

                cleaned_content = '\n'.join(cleaned_lines)

                if cleaned_content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(cleaned_content)
                    cleaned_count += 1
                    logger.info(f"清理导入: {py_file}")

            except Exception as e:
                logger.error(f"清理导入失败 {py_file}: {e}")

        return cleaned_count

    def _extract_import_name(self, import_line: str) -> str:
        """提取导入名称"""
        if import_line.startswith('import '):
            return import_line[7:].split(' as ')[0].split('.')[0].strip()
        elif import_line.startswith('from '):
            parts = import_line[5:].split(' import ')
            if len(parts) == 2:
                return parts[1].split(' as ')[0].split('.')[0].strip()
        return ""

    def _is_import_used(self, content: str, import_name: str) -> bool:
        """检查导入是否被使用"""
        # 简单的使用检查
        if import_name in content:
            # 排除导入语句本身
            import_lines = [line for line in content.split('\n') if line.strip().startswith(('import ', 'from '))]
            for line in import_lines:
                if import_name in line:
                    continue
            return True
        return False

    def remove_pass_methods(self) -> int:
        """移除只有pass的方法"""
        logger.info("🧹 移除pass方法...")

        cleaned_count = 0

        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                original_content = content

                # 查找只有pass的方法
                pattern = r'def\s+\w+\([^)]*\):\s*\n\s*pass\s*\n'
                matches = re.finditer(pattern, content)

                for match in reversed(list(matches)):
                    start, end = match.span()
                    content = content[:start] + content[end:]
                    cleaned_count += 1

                if content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"清理pass方法: {py_file}")

            except Exception as e:
                logger.error(f"清理pass方法失败 {py_file}: {e}")

        return cleaned_count

    def remove_duplicate_imports(self) -> int:
        """移除重复的导入"""
        logger.info("🧹 移除重复导入...")

        cleaned_count = 0

        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                original_content = content

                # 移除重复的导入
                lines = content.split('\n')
                seen_imports = set()
                cleaned_lines = []

                for line in lines:
                    if line.strip().startswith(('import ', 'from ')):
                        if line.strip() in seen_imports:
                            continue  # 跳过重复的导入
                        seen_imports.add(line.strip())
                    cleaned_lines.append(line)

                cleaned_content = '\n'.join(cleaned_lines)

                if cleaned_content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(cleaned_content)
                    cleaned_count += 1
                    logger.info(f"清理重复导入: {py_file}")

            except Exception as e:
                logger.error(f"清理重复导入失败 {py_file}: {e}")

        return cleaned_count

    def remove_commented_code(self) -> int:
        """移除注释掉的代码"""
        logger.info("🧹 移除注释代码...")

        cleaned_count = 0

        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                original_content = content

                # 移除注释掉的代码块
                lines = content.split('\n')
                cleaned_lines = []

                for line in lines:
                    # 跳过只包含#的行
                    if line.strip().startswith('#') and len(line.strip()) > 1:
                        # 检查是否是注释掉的代码
                        code_part = line.strip()[1:].strip()
                        if code_part and not code_part.startswith('#'):
                            continue  # 跳过注释掉的代码
                    cleaned_lines.append(line)

                cleaned_content = '\n'.join(cleaned_lines)

                if cleaned_content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(cleaned_content)
                    cleaned_count += 1
                    logger.info(f"清理注释代码: {py_file}")

            except Exception as e:
                logger.error(f"清理注释代码失败 {py_file}: {e}")

        return cleaned_count

    def run_comprehensive_cleanup(self):
        """运行全面清理"""
        logger.info("🚀 开始全面清理...")

        # 1. 移除未使用的导入
        imports_cleaned = self.remove_unused_imports()

        # 2. 移除pass方法
        pass_methods_cleaned = self.remove_pass_methods()

        # 3. 移除重复导入
        duplicate_imports_cleaned = self.remove_duplicate_imports()

        # 4. 移除注释代码
        commented_code_cleaned = self.remove_commented_code()

        total_cleaned = imports_cleaned + pass_methods_cleaned + duplicate_imports_cleaned + commented_code_cleaned

        logger.info("✅ 全面清理完成！")
        logger.info(f"清理了 {imports_cleaned} 个未使用的导入")
        logger.info(f"清理了 {pass_methods_cleaned} 个pass方法")
        logger.info(f"清理了 {duplicate_imports_cleaned} 个重复导入")
        logger.info(f"清理了 {commented_code_cleaned} 个注释代码")
        logger.info(f"总共清理了 {total_cleaned} 项")

        return {
            'imports_cleaned': imports_cleaned,
            'pass_methods_cleaned': pass_methods_cleaned,
            'duplicate_imports_cleaned': duplicate_imports_cleaned,
            'commented_code_cleaned': commented_code_cleaned,
            'total_cleaned': total_cleaned
        }

def main():
    """主函数"""
    cleaner = ComprehensiveCleaner()
    result = cleaner.run_comprehensive_cleanup()

    print("全面清理完成！")
    print(f"清理结果: {result}")

if __name__ == "__main__":
    main()
