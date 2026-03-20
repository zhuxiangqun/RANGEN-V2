#!/usr/bin/env python3
"""
检查知识库内容
"""

import json
import sys
from pathlib import Path

def check_knowledge_content():
    """检查知识库中的内容"""
    project_root = Path(__file__).parent
    metadata_file = project_root / "data" / "knowledge_management" / "metadata.json"

    if not metadata_file.exists():
        print(f"❌ 元数据文件不存在: {metadata_file}")
        return

    try:
        print(f"✅ 正在读取元数据文件: {metadata_file}")

        # 读取文件大小
        file_size = metadata_file.stat().st_size
        print(".1f"        # 尝试读取文件
        with open(metadata_file, 'r', encoding='utf-8') as f:
            # 只读取前几行来了解结构
            lines = []
            for i, line in enumerate(f):
                lines.append(line)
                if i >= 10:  # 只读取前10行
                    break

            # 解析JSON
            content = ''.join(lines)
            try:
                data = json.loads(content)
                print("✅ JSON格式正确")
                print(f"数据类型: {type(data)}")

                if isinstance(data, dict):
                    print(f"键数量: {len(data)}")
                    print(f"前5个键: {list(data.keys())[:5]}")

                    # 检查是否有RAG相关的内容
                    rag_related = {}
                    for key, value in list(data.items())[:100]:  # 只检查前100个
                        if isinstance(value, dict) and 'content' in value:
                            content = value['content'].lower()
                            if 'rag' in content or '检索增强生成' in content:
                                rag_related[key] = content[:200]

                    if rag_related:
                        print(f"✅ 找到 {len(rag_related)} 条RAG相关内容")
                        for key, content in list(rag_related.items())[:3]:
                            print(f"  ID: {key}")
                            print(f"  内容: {content}...")
                    else:
                        print("❌ 未找到RAG相关内容")

                elif isinstance(data, list):
                    print(f"列表长度: {len(data)}")
                    if len(data) > 0:
                        print(f"第一个元素类型: {type(data[0])}")
                        if isinstance(data[0], dict):
                            print(f"第一个元素的键: {list(data[0].keys())}")

            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
                print(f"内容预览: {content[:200]}")

    except Exception as e:
        print(f"❌ 读取文件失败: {e}")

if __name__ == "__main__":
    check_knowledge_content()
