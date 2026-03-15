#!/usr/bin/env python3
"""
全面语法修复脚本
修复所有类型的语法错误
"""
import os
import re
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveSyntaxFixer:
    """全面语法修复器"""
    
    def __init__(self, src_dir: str = "src"):
        self.src_dir = Path(src_dir)
    
    def fix_file(self, file_path: Path) -> bool:
        """修复单个文件的语法错误"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            original_lines = lines.copy()
            fixed = False
            
            # 修复空的try语句块
            for i, line in enumerate(lines):
                if line.strip() == 'try:' and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith('#') or next_line == '':
                        lines.insert(i + 1, '        pass\n')
                        fixed = True
            
            # 修复函数定义后缺少缩进
            for i, line in enumerate(lines):
                if line.strip().startswith('def ') and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith('return') and not next_line.startswith('    '):
                        lines[i + 1] = '        ' + next_line + '\n'
                        fixed = True
            
            # 修复缩进不匹配问题
            for i, line in enumerate(lines):
                if line.strip().startswith('# # from') and i > 0:
                    prev_line = lines[i - 1].strip()
                    if prev_line == 'try:' or prev_line == 'pass':
                        # 调整缩进
                        lines[i] = '        ' + line.strip() + '\n'
                        fixed = True
            
            # 修复不匹配的括号
            for i, line in enumerate(lines):
                if line.strip() == ')' and i > 0:
                    prev_line = lines[i - 1].strip()
                    if prev_line.endswith('('):
                        # 删除不匹配的括号
                        lines[i] = ''
                        fixed = True
            
            if fixed:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                logger.info(f"全面修复语法错误: {file_path}")
            
            return fixed
            
        except Exception as e:
            logger.error(f"修复文件失败 {file_path}: {e}")
            return False
    
    def fix_all_files(self):
        """修复所有文件的语法错误"""
        logger.info("🔧 开始全面语法修复...")
        
        fixed_count = 0
        total_count = 0
        
        for py_file in self.src_dir.rglob("*.py"):
            if py_file.name.startswith('__'):
                continue
                
            total_count += 1
            if self.fix_file(py_file):
                fixed_count += 1
        
        logger.info(f"✅ 全面修复完成: {fixed_count}/{total_count} 个文件被修复")
        return fixed_count, total_count

def main():
    """主函数"""
    fixer = ComprehensiveSyntaxFixer()
    fixer.fix_all_files()

if __name__ == "__main__":
    main()
