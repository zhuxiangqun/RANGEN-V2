#!/usr/bin/env python3
"""
沙箱环境友好的向量知识库构建脚本
使用本地数据文件，避免网络访问

使用方法：
1. 先运行 build_frames_kb_external.py 下载数据集到本地
2. 然后运行此脚本构建向量库

python build_kb_sandbox_friendly.py --input-file frames_dataset.json --batch-size 10
"""

import sys
import os
import json
import argparse
import numpy as np
from pathlib import Path

def load_local_dataset(input_file):
    """加载本地数据集"""
    print("=" * 70)
    print("📂 加载本地数据集")
    print("=" * 70)

    try:
        input_path = Path(input_file)
        if not input_path.exists():
            print(f"❌ 文件不存在: {input_file}")
            return None

        print(f"📖 读取文件: {input_file}")
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"✅ 数据集加载成功: {len(data)} 条记录")

        # 验证数据格式
        if data and isinstance(data[0], dict):
            sample_keys = list(data[0].keys())[:3]
            print(f"📋 示例字段: {sample_keys}")

        return data

    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return None

def build_simple_embeddings(data, embedding_dim=384):
    """构建简单的向量嵌入（用于演示）"""
    print("=" * 70)
    print("🧮 构建向量嵌入（简化版本）")
    print("=" * 70)

    try:
        # 准备文本数据
        texts = []
        for item in data:
            prompt = item.get('Prompt', '')
            answer = item.get('Answer', '')
            combined_text = f"Question: {prompt}\nAnswer: {answer}"
            texts.append(combined_text)

        print(f"📝 准备文本数据: {len(texts)} 条")

        # 使用TF-IDF风格的简单嵌入（演示用）
        print("🔄 生成简化向量嵌入...")

        embeddings = []
        for i, text in enumerate(texts):
            # 创建一个基于文本长度的简单向量（仅用于演示）
            # 在实际应用中，应该使用真正的嵌入模型
            text_length = len(text)
            word_count = len(text.split())

            # 创建固定维度的向量
            vector = np.zeros(embedding_dim)
            vector[0] = text_length / 1000.0  # 归一化文本长度
            vector[1] = word_count / 100.0   # 归一化词数
            vector[2] = len(prompt) / 500.0  # 问题长度
            vector[3] = len(answer) / 500.0  # 答案长度

            # 添加一些随机噪声使向量不同
            np.random.seed(i)  # 确保可重现
            noise = np.random.normal(0, 0.1, embedding_dim)
            vector += noise

            # L2归一化
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm

            embeddings.append(vector)

            # 进度显示
            if (i + 1) % 100 == 0:
                progress = (i + 1) / len(texts) * 100
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
            "dataset": "google/frames-benchmark (本地)",
            "total_items": len(data),
            "embedding_type": "simple_tf_idf_style",
            "embedding_dim": embeddings.shape[1],
            "created_at": str(np.datetime64('now')),
            "note": "此为简化版本，用于沙箱环境演示。在生产环境中应使用真实的嵌入模型"
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
    parser = argparse.ArgumentParser(description="沙箱环境友好的向量知识库构建")
    parser.add_argument("--input-file", type=str, required=True, help="输入数据集文件")
    parser.add_argument("--output-dir", type=str, default="data/knowledge_management", help="输出目录")
    parser.add_argument("--embedding-dim", type=int, default=384, help="向量维度")

    args = parser.parse_args()

    print("🚀 沙箱环境友好的向量知识库构建工具")
    print("   使用本地数据文件，避免网络访问")
    print()

    # 加载数据集
    print("第一步: 加载数据集")
    data = load_local_dataset(args.input_file)
    if not data:
        print("❌ 数据集加载失败")
        sys.exit(1)

    # 构建向量嵌入
    print("\n第二步: 构建向量嵌入")
    embeddings, texts = build_simple_embeddings(data, args.embedding_dim)
    if embeddings is None:
        print("❌ 向量嵌入失败")
        sys.exit(1)

    # 保存知识库
    print("\n第三步: 保存知识库")
    if not save_knowledge_base(data, embeddings, texts, args.output_dir):
        print("❌ 知识库保存失败")
        sys.exit(1)

    print("\n🎉 向量知识库构建完成！")
    print(f"📊 数据集大小: {len(data)} 条记录")
    print(f"🧮 向量维度: {embeddings.shape[1]}")
    print(f"📁 输出目录: {args.output_dir}")
    print("\n⚠️  注意：此版本使用简化嵌入算法，仅用于演示")
    print("   在生产环境中，请使用真实的嵌入模型如 SentenceTransformer")

if __name__ == "__main__":
    main()
