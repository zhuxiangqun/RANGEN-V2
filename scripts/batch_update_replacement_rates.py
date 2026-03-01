#!/usr/bin/env python3
"""
批量更新Agent包装器的替换率
根据智能优化结果，将所有Agent的初始替换率调整到3.5%
"""

import os
import re
from pathlib import Path

def update_replacement_rate_in_file(filepath: str):
    """更新单个文件中的替换率"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找并替换初始替换率
        pattern = r'(initial_replacement_rate.*=.*)0\.01'
        replacement = r'\g<1>0.035'

        if re.search(pattern, content):
            new_content = re.sub(pattern, replacement, content)

            # 同时更新注释
            new_content = re.sub(
                r'(初始替换比例.*默认)1%\)',
                r'\g<1>3.5%)',
                new_content
            )

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)

            print(f"✅ 更新 {filepath}")
            return True
        else:
            print(f"ℹ️ 无需更新 {filepath}")
            return False

    except Exception as e:
        print(f"❌ 更新失败 {filepath}: {e}")
        return False

def main():
    """主函数"""
    print("🔧 开始批量更新Agent包装器替换率...")

    # 需要更新的包装器文件列表
    wrapper_files = [
        'src/agents/chief_agent_wrapper.py',
        'src/agents/answer_generation_agent_wrapper.py',
        'src/agents/learning_system_wrapper.py',
        'src/agents/strategic_chief_agent_wrapper.py',
        'src/agents/prompt_engineering_agent_wrapper.py',
        'src/agents/context_engineering_agent_wrapper.py',
        'src/agents/optimized_knowledge_retrieval_agent_wrapper.py'
    ]

    updated_count = 0
    total_count = len(wrapper_files)

    for filepath in wrapper_files:
        if os.path.exists(filepath):
            if update_replacement_rate_in_file(filepath):
                updated_count += 1
        else:
            print(f"⚠️ 文件不存在: {filepath}")

    print("\n📊 更新完成统计")
    print(f"  总文件数: {total_count}")
    print(f"  已更新: {updated_count}")
    print(f"  跳过: {total_count - updated_count}")

    if updated_count > 0:
        print("\n✅ 替换率批量更新完成！")
        print("所有Agent包装器的初始替换率已调整为3.5%")

if __name__ == "__main__":
    main()
