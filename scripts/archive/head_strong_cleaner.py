from pathlib import Path
import ast
import os
import re
#!/usr/bin/env python3
"""
强力头部清理脚本：
对所有有语法错误的Python文件，移除头部无效内容，直到遇到第一个有效import/def/class/注释/字符串等代码行。
"""
def is_valid_code_line(line: str) -> bool:
    # 判断是否为有效代码行
    line_strip = line.strip()
    if not line_strip:
        return False
    if line_strip.startswith(('import ', 'from ', 'def ', 'class ', '#', '"', "'")):
        return True
    # 多行字符串起始
    if line_strip.startswith(('"""', "'''")):
        return True
    return False
def clean_head(file_path: Path) -> bool:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    # 找到第一个有效代码行
    first_code_idx = None
    for idx, line in enumerate(lines):
        if is_valid_code_line(line):
            first_code_idx = idx
            break
    if first_code_idx is None:
        return False
    # 保留第一个有效代码行及其后内容
    new_lines = lines[first_code_idx:]
    # 再次尝试解析AST
    try:
        ast.parse(''.join(new_lines))
        # 如果能解析，说明修复有效
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"[CLEANED] {file_path}")
        return True
    except Exception:
        return False
def main():
    error_files = []
    # 扫描所有py文件
    for root, dirs, files in os.walk('.'):
        if any(skip in root for skip in ['venv', '__pycache__', '.git', 'node_modules']):
            continue
        for file in files:
            if file.endswith('.py'):
                path = Path(root) / file
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    ast.parse(content)
                except Exception:
                    error_files.append(path)
    print(f"检测到语法错误文件 {len(error_files)} 个")
    cleaned = 0
    for file_path in error_files:
        if clean_head(file_path):
            cleaned += 1
    print(f"已清理 {cleaned} 个文件头部")

if __name__ == '__main__':
    main()
