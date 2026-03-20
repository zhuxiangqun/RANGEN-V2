#!/usr/bin/env python3
"""
在非沙箱环境中构建 google/frames-benchmark 向量知识库

由于沙箱环境限制，此脚本需要在外部环境中运行。

使用方法：
1. 复制此脚本到项目目录外
2. 安装依赖：pip install datasets torch sentence-transformers
3. 运行脚本：python build_frames_kb_external.py
4. 将生成的 data/frames_dataset.json 复制回项目目录
"""

import sys
import os
import json
from pathlib import Path
from datasets import load_dataset
import torch
from sentence_transformers import SentenceTransformer

def download_frames_dataset():
    """下载 google/frames-benchmark 数据集"""
    print("=" * 70)
    print("📥 下载 google/frames-benchmark 数据集")
    print("=" * 70)

    try:
        # 下载数据集
        print("📥 正在从 Hugging Face 下载数据集...")
        dataset = load_dataset('google/frames-benchmark')

        # 获取所有分割
        if hasattr(dataset, 'keys'):
            splits = list(dataset.keys())
        else:
            splits = ['default']

        print(f"   发现数据集分割: {', '.join(splits)}")

        # 合并所有分割的数据
        dataset_list = []
        total_items = 0

        for split_name in splits:
            split_data = dataset[split_name]
            split_count = 0

            print(f"   📦 正在处理分割 '{split_name}'...")
            for item in split_data:
                if isinstance(item, dict):
                    dataset_list.append(item)
                    split_count += 1
                else:
                    try:
                        dataset_list.append(dict(item))
                        split_count += 1
                    except (TypeError, ValueError):
                        continue

            total_items += split_count
            print(f"      ✅ 分割 '{split_name}': {split_count} 条数据")

        print(f"   ✅ 合并完成：共 {total_items} 条数据（来自 {len(splits)} 个分割）")

        return dataset_list

    except Exception as e:
        print(f"❌ 下载失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_dataset(data, output_path):
    """保存数据集到文件"""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"💾 保存数据集到: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ 数据集已保存: {len(data)} 条记录")
        return True

    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False

def validate_dataset(data):
    """验证数据集"""
    if not data or not isinstance(data, list):
        print("❌ 数据集格式无效")
        return False

    if len(data) == 0:
        print("❌ 数据集为空")
        return False

    # 检查第一条记录的格式
    first_item = data[0]
    required_fields = ['Prompt', 'Answer']
    missing_fields = [field for field in required_fields if field not in first_item]

    if missing_fields:
        print(f"⚠️  缺少必要字段: {missing_fields}")

    print(f"✅ 数据集验证通过: {len(data)} 条记录")
    print(f"   示例字段: {list(first_item.keys())[:5]}...")

    return True

def main():
    print("🚀 google/frames-benchmark 数据集下载工具")
    print("   此脚本需要在非沙箱环境中运行")
    print()

    # 设置输出路径
    output_path = Path("frames_dataset.json")

    # 检查是否已存在
    if output_path.exists():
        response = input(f"⚠️  文件已存在: {output_path}，是否覆盖？(y/N): ")
        if response.lower() != 'y':
            print("❌ 操作取消")
            return

    # 下载数据集
    dataset = download_frames_dataset()
    if not dataset:
        print("❌ 数据集下载失败")
        sys.exit(1)

    # 验证数据集
    if not validate_dataset(dataset):
        print("❌ 数据集验证失败")
        sys.exit(1)

    # 保存数据集
    if not save_dataset(dataset, output_path):
        print("❌ 数据集保存失败")
        sys.exit(1)

    print()
    print("🎉 数据集下载完成！")
    print(f"   文件位置: {output_path.absolute()}")
    print(f"   数据条数: {len(dataset)}")
    print()
    print("📋 下一步操作：")
    print("   1. 将此文件复制到项目目录的 data/ 文件夹")
    print("   2. 重命名或移动为 data/frames_dataset.json")
    print("   3. 在项目中运行向量知识库构建脚本")

if __name__ == "__main__":
    main()
