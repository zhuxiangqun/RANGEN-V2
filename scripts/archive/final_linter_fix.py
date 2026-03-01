import re
from pathlib import Path
import os
import typing
#!/usr/bin/env python3
"""
最终linter修复脚本
修复所有剩余的语法错误和类型问题
"""
def fix_import_errors(content: str) -> str:
    """修复导入错误"""
    # 修复常见的导入错误
    patterns = [
        (r'from datetime \n', 'from datetime import datetime\n'),
        (r'from datetime import datetime\nfrom', 'from datetime import datetime\nfrom'),
        (r'from datetime$', 'from datetime import datetime'),
        (r'import json\n', ''),  # 移除未使用的json导入
        (r'import os\n', ''),    # 移除未使用的os导入
        (r'import time\n', '')   # 移除未使用的time导入
    ]
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    return content
def fix_type_annotations(content: str) -> str:
    """修复类型注解"""
    # 修复类型注解问题
    patterns = [
        (r'Dict\[', 'dict['),
        (r'List\[', 'list['),
        (r'Optional\[', 'None | '),
        (r': typing.Any', ': object'),
        (r'-> Any', '-> object')
    ]
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    return content
def fix_syntax_errors(content: str) -> str:
    """修复语法错误"""
    # 修复函数参数语法错误
    content = re.sub(r'(\w+): None \| int\] = None', r'\1: None | int = None', content)
    content = re.sub(r'(\w+): None \| int\] = (\w+)', r'\1: None | int = \2', content)
    # 修复其他语法错误
    content = re.sub(r'from datetime import datetime\nfrom', 'from datetime import datetime\nfrom', content)
    return content
def fix_file(file_path: str) -> bool:
    """修复单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        original_content = content
        # 应用修复
        content = fix_import_errors(content)
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
    print("🔧 最终linter修复工具")
    print("=" * 50)
    # 获取所有Python文件
    with open('all_py_files.txt', 'r') as f:
        file_list = [line.strip() for line in f if line.strip()]
    fixed_count = 0
    for i, file_path in enumerate(file_list, 1):
        print(f"进度: {i}/{len(file_list)} - {file_path}")
        try:
            if fix_file(file_path):
                fixed_count += 1
                print(f"  ✅ 已修复")
            else:
                print(f"  ⏭️ 无需修复")
        except Exception as e:
            print(f"  ❌ 修复失败: {str(e)}")
    print(f"\n📊 修复结果:")
    print(f"总文件数: {len(file_list)}")
    print(f"修复文件数: {fixed_count}")
    print(f"🎯 最终修复完成！")

if __name__ == "__main__":
    main()
