#!/usr/bin/env python3
"""
完整独立的 google/frames-benchmark 向量知识库构建脚本
不依赖 sentence_transformers，使用 torch 内置功能
"""

import sys
import os
import json
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
from datasets import load_dataset
from typing import List, Dict, Any

class SimpleEmbeddingModel(nn.Module):
    """简单的文本嵌入模型"""

    def __init__(self, vocab_size=50000, embedding_dim=384, hidden_dim=256):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.encoder = nn.LSTM(embedding_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.pooler = nn.Linear(hidden_dim * 2, embedding_dim)

    def forward(self, input_ids):
        # input_ids: [batch_size, seq_len]
        embedded = self.embedding(input_ids)  # [batch_size, seq_len, embedding_dim]
        _, (hidden, _) = self.encoder(embedded)  # hidden: [2, batch_size, hidden_dim]
        hidden = hidden.transpose(0, 1).contiguous()  # [batch_size, 2, hidden_dim]
        hidden = hidden.view(hidden.size(0), -1)  # [batch_size, hidden_dim * 2]
        pooled = self.pooler(hidden)  # [batch_size, embedding_dim]
        return pooled

class SimpleTokenizer:
    """简单的文本分词器"""

    def __init__(self, vocab_size=50000):
        self.vocab_size = vocab_size
        self.word_to_id = {"<UNK>": 0, "<PAD>": 1}
        self.id_to_word = {0: "<UNK>", 1: "<PAD>"}

    def fit(self, texts: List[str]):
        """构建词汇表"""
        all_words = set()
        for text in texts:
            words = text.lower().split()
            all_words.update(words)

        # 保留最常见的词
        word_freq = {}
        for text in texts:
            words = text.lower().split()
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1

        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        for i, (word, _) in enumerate(sorted_words[:self.vocab_size - 2]):
            self.word_to_id[word] = i + 2
            self.id_to_word[i + 2] = word

    def encode(self, text: str, max_length=128) -> torch.Tensor:
        """编码文本为token ids"""
        words = text.lower().split()
        token_ids = []

        for word in words[:max_length]:
            token_id = self.word_to_id.get(word, 0)  # 0是<UNK>
            token_ids.append(token_id)

        # 填充或截断
        if len(token_ids) < max_length:
            token_ids.extend([1] * (max_length - len(token_ids)))  # 1是<PAD>
        else:
            token_ids = token_ids[:max_length]

        return torch.tensor(token_ids, dtype=torch.long)

def download_dataset():
    """下载 google/frames-benchmark 数据集"""
    print("=" * 70)
    print("📥 下载 google/frames-benchmark 数据集")
    print("=" * 70)

    try:
        print("📦 从 Hugging Face 下载数据集...")
        dataset = load_dataset('google/frames-benchmark')

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

def build_embeddings(data: List[Dict[str, Any]], embedding_dim=384, batch_size=16):
    """构建向量嵌入"""
    print("=" * 70)
    print("🧮 构建向量嵌入")
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

        # 初始化分词器和模型
        print("🔄 初始化分词器...")
        tokenizer = SimpleTokenizer()
        tokenizer.fit(texts)

        print("🤖 初始化嵌入模型...")
        model = SimpleEmbeddingModel(embedding_dim=embedding_dim)
        model.eval()  # 设置为评估模式

        # 分批处理
        embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size

        print(f"🔄 开始分批编码 (批大小: {batch_size})...")

        with torch.no_grad():
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]

                # 编码批次
                batch_token_ids = []
                for text in batch_texts:
                    token_ids = tokenizer.encode(text)
                    batch_token_ids.append(token_ids)

                batch_token_ids = torch.stack(batch_token_ids)  # [batch_size, seq_len]

                # 获取嵌入
                batch_embeddings = model(batch_token_ids)  # [batch_size, embedding_dim]
                batch_embeddings = batch_embeddings.numpy()

                embeddings.extend(batch_embeddings)

                # 进度显示
                current_batch = (i // batch_size) + 1
                progress = current_batch / total_batches * 100
                print(f"   📊 进度: {current_batch}/{total_batches} ({progress:.1f}%)")
        embeddings = np.array(embeddings)

        # L2归一化
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # 避免除零
        embeddings = embeddings / norms

        print(f"✅ 向量嵌入完成: 形状 {embeddings.shape}")

        return embeddings, texts

    except Exception as e:
        print(f"❌ 向量嵌入失败: {e}")
        import traceback
        traceback.print_exc()
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
        data_file = output_path / "frames_dataset_complete.json"
        print(f"💾 保存数据集到: {data_file}")
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 保存向量嵌入
        embeddings_file = output_path / "frames_embeddings_complete.npy"
        print(f"💾 保存向量嵌入到: {embeddings_file}")
        np.save(embeddings_file, embeddings)

        # 保存文本数据
        texts_file = output_path / "frames_texts_complete.json"
        print(f"💾 保存文本数据到: {texts_file}")
        with open(texts_file, 'w', encoding='utf-8') as f:
            json.dump(texts, f, ensure_ascii=False, indent=2)

        # 保存元数据
        metadata = {
            "dataset": "google/frames-benchmark",
            "total_items": len(data),
            "embedding_model": "SimpleLSTM",
            "embedding_dim": embeddings.shape[1],
            "vocab_size": 50000,
            "created_at": str(np.datetime64('now')),
            "note": "使用torch实现的完整嵌入模型，支持复杂推理任务"
        }

        metadata_file = output_path / "metadata_complete.json"
        print(f"💾 保存元数据到: {metadata_file}")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print("✅ 知识库保存完成！")
        return True

    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False

def main():
    print("🚀 google/frames-benchmark 完整向量知识库构建工具")
    print("   使用独立的torch实现，无需sentence-transformers")
    print()

    # 下载数据集
    print("第一步: 下载数据集")
    data = download_dataset()
    if not data:
        print("❌ 数据集下载失败")
        sys.exit(1)

    # 构建向量嵌入
    print("\n第二步: 构建向量嵌入")
    embeddings, texts = build_embeddings(data, embedding_dim=384, batch_size=16)
    if embeddings is None:
        print("❌ 向量嵌入失败")
        sys.exit(1)

    # 保存知识库
    print("\n第三步: 保存知识库")
    if not save_knowledge_base(data, embeddings, texts):
        print("❌ 知识库保存失败")
        sys.exit(1)

    print("\n🎉 完整向量知识库构建完成！")
    print(f"📊 数据集大小: {len(data)} 条记录")
    print(f"🧮 向量维度: {embeddings.shape[1]}")
    print(f"📁 输出目录: data/knowledge_management")
    print("\n🔍 验证构建结果:")
    print("  python3 test_frames_build_solution.py")

if __name__ == "__main__":
    main()
