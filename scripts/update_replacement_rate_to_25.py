#!/usr/bin/env python3
"""
将所有Agent包装器的替换率更新为25%
"""

import os
import re
from pathlib import Path

def update_replacement_rate(file_path, target_rate=0.25):
    """更新单个文件的替换率"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找并替换替换率
        pattern = r'initial_replacement_rate:\s*float\s*=\s*0\.\d+'
        replacement = f'initial_replacement_rate: float = {target_rate}'

        if re.search(pattern, content):
            new_content = re.sub(pattern, replacement, content)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            print(f"✅ 更新 {file_path.name}: 替换率 → {target_rate}")
            return True
        else:
            print(f"ℹ️ 跳过 {file_path.name}: 未找到替换率设置")
            return False

    except Exception as e:
        print(f"❌ 更新失败 {file_path.name}: {e}")
        return False

def main():
    """主函数"""
    project_root = Path(__file__).parent.parent
    agents_dir = project_root / "src" / "agents"

    print("🔧 开始更新Agent包装器替换率到25%...")
    print("=" * 60)

    # 需要更新的包装器文件
    wrapper_files = [
        "answer_generation_agent_wrapper.py",
        "learning_system_wrapper.py",
        "strategic_chief_agent_wrapper.py",
        "prompt_engineering_agent_wrapper.py",
        "context_engineering_agent_wrapper.py",
        "optimized_knowledge_retrieval_agent_wrapper.py",
        "chief_agent_wrapper.py"
    ]

    updated_count = 0
    total_count = len(wrapper_files)

    for filename in wrapper_files:
        file_path = agents_dir / filename
        if file_path.exists():
            if update_replacement_rate(file_path, 0.25):
                updated_count += 1
        else:
            print(f"⚠️ 文件不存在: {filename}")

    print("\n" + "=" * 60)
    print(f"📊 更新完成: {updated_count}/{total_count} 个文件已更新")

    if updated_count > 0:
        print("\n🧪 运行稳定性检查验证更新...")
        os.system("cd /Users/syu/workdata/person/zy/RANGEN-main\\(syu-python\\) && python3 scripts/simple_stability_check.py")

if __name__ == "__main__":
    main()
