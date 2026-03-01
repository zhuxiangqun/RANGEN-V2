from pathlib import Path
import os
import re
import subprocess
#!/usr/bin/env python3
"""
递归括号与缩进修复脚本
自动多轮修复所有括号配对、缩进、冒号、import等语法错误，直到py_compile全部通过。
"""
# 括号配对表
BRACKETS = {'(': ')', '[': ']', '{': '}'}
REVERSE_BRACKETS = {v: k for k, v in BRACKETS.items()}
# 递归修复括号配对
def fix_brackets(line: str) -> str:
    stack = []
    new_line = ''
    for c in line:
        if c in BRACKETS:
            stack.append(c)
            new_line += c
        elif c in REVERSE_BRACKETS:
            if stack and stack[-1] == REVERSE_BRACKETS[c]:
                stack.pop()
                new_line += c
            else:
                # 不匹配，跳过或补全
                if stack:
                    new_line += BRACKETS[stack.pop()]
                    new_line += c
                else:
                    new_line += c
        else:
            new_line += c
    # 补全未闭合括号
    while stack:
        new_line += BRACKETS[stack.pop()]
    return new_line

# 修复类型注解、参数、字典/列表/元组/集合、print、f-string等所有括号
BRACKET_PATTERN = re.compile(r'([\[\](){}])')

def fix_line_brackets(line: str) -> str:
    # 只修复代码部分，不修复注释
    if '#' in line:
        code, comment = line.split('#', 1)
        return fix_brackets(code) + '#' + comment
    else:
        return fix_brackets(line)

# 修复 import 语句、冒号、缩进
def fix_import_and_colon(lines):
    fixed = []
    for line in lines:
        l = line.lstrip()
        # 修复 import 语句前的缩进
        if l.startswith('import ') or l.startswith('from '):
            fixed.append(l)
            continue
        # 自动补全 if/for/with/try/except/def/class 等语句块的冒号
        if re.match(r'^(if|for|with|try|except|elif|else|def|class)\b.*[^:]:?$', l) and not l.rstrip().endswith(':'):
            fixed.append(line.rstrip() + ':')
            continue
        fixed.append(line)
    return fixed

# 修复缩进（简单左对齐）
def fix_indentation(lines):
    fixed = []
    for line in lines:
        fixed.append(line.lstrip())
    return fixed

# 递归修复单个文件
def fix_file(file_path: str) -> bool:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        original = lines[:]
        # 逐行修复括号
        lines = [fix_line_brackets(line) for line in lines]
        # 修复 import、冒号
        lines = fix_import_and_colon(lines)
        # 修复缩进
        lines = fix_indentation(lines)
        # 写回
        if lines != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            return True
        return False
    except Exception as e:
        print(f"修复文件 {file_path} 时出错: {str(e)}")
        return False

def get_py_files():
    with open('all_py_files.txt', 'r') as f:
        return [line.strip() for line in f if line.strip()]

def check_py_compile():
    result = subprocess.run(
        'cat all_py_files.txt | xargs -I {} python3 -m py_compile {} 2>&1',
        shell=True,
        capture_output=True,
        text=True
    )
    return result.stdout

def main():
    print('🔁 递归括号与缩进修复工具')
    print('='*50)
    py_files = get_py_files()
    max_rounds = get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit"))
    for round in range(max_rounds):
        print(f'第{round+1}轮修复...')
        changed = False
        for i, file_path in enumerate(py_files, 1):
            if fix_file(file_path):
                print(f'  {file_path} ✅ 已修复')
                changed = True
        # 检查 py_compile
        errors = check_py_compile()
        if not errors.strip():
            print('🎉 全部通过 py_compile，无语法报错！')
            return
        print(f'本轮后仍有报错：\n{errors[:1000]}')
        if not changed:
            print('未检测到进一步可自动修复的内容。')
            break
    print('递归修复结束。请人工检查剩余报错。')

if __name__ == '__main__':
    main()
