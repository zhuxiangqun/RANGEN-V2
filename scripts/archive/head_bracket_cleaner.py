import re
#!/usr/bin/env python3
"""
自动清理所有py文件头部多余括号和空行，只保留有效代码和注释。
"""
def clean_head_brackets(file_path: str) -> bool:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        original = lines[:]
        # 跳过文件头部的 ) ] } 和空行（允许任意数量、空格、Tab）
        i = 0
        pattern = re.compile(r'^[\s\)\]\}]*$')
        while i < len(lines):
            l = lines[i]
            if pattern.match(l):
                i += 1
            else:
                break
        # 保留剩余内容
        new_lines = lines[i:]
        if new_lines != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            return True
        return False
    except Exception as e:
        print(f"清理文件 {file_path} 时出错: {str(e)}")
        return False
def main():
    print('🧹 自动清理所有py文件头部多余括号...')
    with open('all_py_files.txt', 'r') as f:
        py_files = [line.strip() for line in f if line.strip()]
    cleaned = 0
    for file_path in py_files:
        if clean_head_brackets(file_path):
            print(f'  {file_path} ✅ 已清理')
            cleaned += 1
    print(f'共清理 {cleaned} 个文件。')

if __name__ == '__main__':
    main()
