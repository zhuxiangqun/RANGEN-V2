#!/usr/bin/env python3
"""
完整构建 google/frames-benchmark 向量知识库脚本
需要在非沙箱环境中运行以获得完整功能

此脚本会：
1. 从 Hugging Face 下载 google/frames-benchmark 数据集
2. 构建向量知识库
3. 可选构建知识图谱

使用方法：
python build_frames_kb_full.py --batch-size 10 --resume
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datasets import load_dataset
from sentence_transformers import SentenceTransformer
import torch
import numpy as np

def download_frames_dataset():
    """下载完整的 google/frames-benchmark 数据集"""
    print("=" * 70)
    print("📥 下载 google/frames-benchmark 数据集")
    print("=" * 70)

    try:
        print("📦 从 Hugging Face 下载数据集...")
        dataset = load_dataset('google/frames-benchmark')

        # 合并所有分割的数据
        all_data = []
        total_items = 0

        splits = list(dataset.keys())
        print(f"发现数据集分割: {', '.join(splits)}")

        for split_name in splits:
            split_data = dataset[split_name]
            split_count = 0

            print(f"📊 处理分割 '{split_name}'...")

            for item in split_data:
                if isinstance(item, dict):
                    all_data.append(item)
                    split_count += 1
                else:
                    try:
                        all_data.append(dict(item))
                        split_count += 1
                    except (TypeError, ValueError):
                        continue

            total_items += split_count
            print(f"   ✅ 分割 '{split_name}': {split_count} 条数据")

        print(f"📈 数据集总条数: {total_items}")
        return all_data

    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return None

def build_vector_embeddings(data, model_name='all-MiniLM-L6-v2', batch_size=10):
    """构建向量嵌入"""
    print("=" * 70)
    print("🧮 构建向量嵌入")
    print("=" * 70)

    try:
        print(f"🤖 加载模型: {model_name}")
        model = SentenceTransformer(model_name)

        # 准备文本数据
        texts = []
        for item in data:
            # 组合 Prompt 和 Answer 作为输入文本
            prompt = item.get('Prompt', '')
            answer = item.get('Answer', '')
            combined_text = f"Question: {prompt}\nAnswer: {answer}"
            texts.append(combined_text)

        print(f"📝 准备文本数据: {len(texts)} 条")

        # 分批处理
        embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size

        print(f"🔄 开始分批编码 (批大小: {batch_size})...")

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = model.encode(batch_texts, convert_to_numpy=True)

            embeddings.extend(batch_embeddings)

            # 进度显示
            current_batch = (i // batch_size) + 1
            progress = current_batch / total_batches * 100
            print(".1f"
        embeddings = np.array(embeddings)
        print(f"✅ 向量嵌入完成: 形状 {embeddings.shape}")

        return embeddings, texts

    except Exception as e:
        print(f"❌ 向量嵌入失败: {e}")
        return None, None

def save_knowledge_base(data, embeddings, texts, output_dir="data/knowledge_management"):
    """保存知识库"""
    print("=" * 70)
    print("💾 保存知识库")
    print("=" * 70)

    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 保存原始数据
        data_file = output_path / "frames_dataset.json"
        print(f"💾 保存数据集到: {data_file}")
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 保存向量嵌入
        embeddings_file = output_path / "frames_embeddings.npy"
        print(f"💾 保存向量嵌入到: {embeddings_file}")
        np.save(embeddings_file, embeddings)

        # 保存文本数据
        texts_file = output_path / "frames_texts.json"
        print(f"💾 保存文本数据到: {texts_file}")
        with open(texts_file, 'w', encoding='utf-8') as f:
            json.dump(texts, f, ensure_ascii=False, indent=2)

        # 保存元数据
        metadata = {
            "dataset": "google/frames-benchmark",
            "total_items": len(data),
            "embedding_model": "all-MiniLM-L6-v2",
            "embedding_dim": embeddings.shape[1] if embeddings is not None else None,
            "created_at": str(np.datetime64('now'))
        }

        metadata_file = output_path / "metadata.json"
        print(f"💾 保存元数据到: {metadata_file}")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print("✅ 知识库保存完成！")
        return True

    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="构建 google/frames-benchmark 向量知识库")
    parser.add_argument("--batch-size", type=int, default=10, help="批处理大小")
    parser.add_argument("--model", type=str, default="all-MiniLM-L6-v2", help="SentenceTransformer模型")
    parser.add_argument("--output-dir", type=str, default="data/knowledge_management", help="输出目录")

    args = parser.parse_args()

    print("🚀 google/frames-benchmark 完整向量知识库构建工具")
    print("   此脚本需要在非沙箱环境中运行")
    print()

    # 下载数据集
    print("第一步: 下载数据集")
    data = download_frames_dataset()
    if not data:
        print("❌ 数据集下载失败")
        sys.exit(1)

    # 构建向量嵌入
    print("\n第二步: 构建向量嵌入")
    embeddings, texts = build_vector_embeddings(data, args.model, args.batch_size)
    if embeddings is None:
        print("❌ 向量嵌入失败")
        sys.exit(1)

    # 保存知识库
    print("\n第三步: 保存知识库")
    if not save_knowledge_base(data, embeddings, texts, args.output_dir):
        print("❌ 知识库保存失败")
        sys.exit(1)

    print("\n🎉 完整向量知识库构建完成！")
    print(f"📊 数据集大小: {len(data)} 条记录")
    print(f"🧮 向量维度: {embeddings.shape[1]}")
    print(f"📁 输出目录: {args.output_dir}")

if __name__ == "__main__":
    main()
