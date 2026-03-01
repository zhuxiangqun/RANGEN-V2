#!/usr/bin/env python3
"""
添加机器学习基础知识到知识库
"""

import json
import os
from pathlib import Path

def add_ml_knowledge():
    """添加机器学习知识条目到现有的知识库"""

    # 现有知识库文件路径
    knowledge_file = "data/faiss_memory/knowledge_entries.json"
    ml_knowledge_file = "data/knowledge_base_ml.json"

    # 检查文件是否存在
    if not os.path.exists(knowledge_file):
        print(f"❌ 知识库文件不存在: {knowledge_file}")
        return False

    if not os.path.exists(ml_knowledge_file):
        print(f"❌ ML知识文件不存在: {ml_knowledge_file}")
        return False

    try:
        # 读取现有知识库
        print("🔄 读取现有知识库...")
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            existing_knowledge = json.load(f)

        # 读取ML知识
        print("🔄 读取ML知识...")
        with open(ml_knowledge_file, 'r', encoding='utf-8') as f:
            ml_knowledge = json.load(f)

        # 检查是否已经是列表格式
        if not isinstance(existing_knowledge, list):
            print("❌ 现有知识库格式不正确")
            return False

        # 检查重复条目（基于entry_id）
        existing_ids = {entry.get('entry_id') for entry in existing_knowledge}
        new_entries = []
        duplicate_count = 0

        for entry in ml_knowledge:
            entry_id = entry.get('entry_id')
            if entry_id in existing_ids:
                duplicate_count += 1
                print(f"⚠️ 跳过重复条目: {entry_id}")
            else:
                new_entries.append(entry)

        # 添加新条目
        if new_entries:
            existing_knowledge.extend(new_entries)
            print(f"✅ 添加了 {len(new_entries)} 条新知识条目")

            # 写回文件
            with open(knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(existing_knowledge, f, ensure_ascii=False, indent=2)

            print(f"✅ 知识库更新完成，总条目数: {len(existing_knowledge)}")
        else:
            print("ℹ️ 没有新条目需要添加")

        if duplicate_count > 0:
            print(f"⚠️ 跳过了 {duplicate_count} 条重复条目")

        return True

    except Exception as e:
        print(f"❌ 添加知识失败: {e}")
        return False

if __name__ == "__main__":
    success = add_ml_knowledge()
    if success:
        print("\n🎉 机器学习知识添加成功！")
        print("现在系统应该能够检索到机器学习的定义、优点和缺点等信息。")
    else:
        print("\n❌ 机器学习知识添加失败")
