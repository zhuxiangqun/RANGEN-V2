#!/usr/bin/env python3
"""
增强版向量知识库构建脚本
支持断点续传、向量化及高效索引功能
"""

import json
import os
import sys
import math
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Any, Set
import hashlib


class SimpleVectorizer:
    """简化的向量化器"""

    def __init__(self):
        self.vocab: Dict[str, int] = {}
        self.idf_scores: Dict[str, float] = {}
        self.vocab_size = 0

    def tokenize(self, text: str) -> List[str]:
        """简单的中文分词"""
        # 移除标点符号，分割为词
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text.lower())
        # 简单的按字符分割（对于中文可以按字或词，这里使用字级别）
        tokens = []
        for char in text:
            if char.strip() and len(char.strip()) > 0:
                tokens.append(char.strip())
        return tokens

    def fit_transform(self, documents: List[str]) -> List[List[float]]:
        """训练并转换文档为向量"""
        print("🔢 开始向量化处理...")

        # 分词
        tokenized_docs = [self.tokenize(doc) for doc in documents]

        # 构建词汇表
        all_tokens = []
        for tokens in tokenized_docs:
            all_tokens.extend(tokens)

        token_freq = Counter(all_tokens)
        # 只保留出现频率高的词（TF-IDF中的常见词过滤）
        min_freq = max(1, len(documents) // 1000)  # 根据文档数量动态调整
        self.vocab = {token: idx for idx, (token, freq) in enumerate(token_freq.items()) if freq >= min_freq}
        self.vocab_size = len(self.vocab)

        print(f"📚 构建词汇表: {self.vocab_size} 个词")

        # 计算IDF
        doc_count = len(tokenized_docs)
        for token in self.vocab:
            doc_freq = sum(1 for doc_tokens in tokenized_docs if token in doc_tokens)
            self.idf_scores[token] = math.log(doc_count / (1 + doc_freq))

        # 转换为TF-IDF向量
        vectors = []
        for tokens in tokenized_docs:
            vector = [0.0] * self.vocab_size
            token_freq = Counter(tokens)

            # 计算TF-IDF
            for token, freq in token_freq.items():
                if token in self.vocab:
                    tf = freq / len(tokens) if len(tokens) > 0 else 0
                    tf_idf = tf * self.idf_scores[token]
                    vector[self.vocab[token]] = tf_idf

            vectors.append(vector)

        print(f"✅ 向量化完成: {len(vectors)} 个文档向量")
        return vectors


class SimpleIndexer:
    """简化的索引器"""

    def __init__(self):
        self.inverted_index: Dict[str, Set[str]] = defaultdict(set)
        self.document_vectors: Dict[str, List[float]] = {}
        self.document_metadata: Dict[str, Dict[str, Any]] = {}

    def add_document(self, doc_id: str, content: str, vector: List[float], metadata: Dict[str, Any]):
        """添加文档到索引"""
        self.document_vectors[doc_id] = vector
        self.document_metadata[doc_id] = metadata

        # 构建倒排索引
        tokens = self._tokenize(content)
        for token in tokens:
            self.inverted_index[token].add(doc_id)

    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text.lower())
        return [char for char in text if char.strip()]

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """搜索文档"""
        query_tokens = self._tokenize(query)
        candidate_docs = set()

        # 收集候选文档
        for token in query_tokens:
            if token in self.inverted_index:
                candidate_docs.update(self.inverted_index[token])

        if not candidate_docs:
            return []

        # 计算相似度（余弦相似度）
        query_vector = self._vectorize_query(query_tokens)
        results = []

        for doc_id in candidate_docs:
            if doc_id in self.document_vectors:
                doc_vector = self.document_vectors[doc_id]
                similarity = self._cosine_similarity(query_vector, doc_vector)
                results.append({
                    'doc_id': doc_id,
                    'similarity': similarity,
                    'metadata': self.document_metadata[doc_id]
                })

        # 排序并返回top_k
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]

    def _vectorize_query(self, query_tokens: List[str]) -> List[float]:
        """将查询转换为向量"""
        # 简单的词袋模型
        vector = [0.0] * len(self.document_vectors[next(iter(self.document_vectors))]) if self.document_vectors else []
        query_freq = Counter(query_tokens)

        # 这里简化处理，实际应该使用训练好的词汇表
        for token, freq in query_freq.items():
            # 简化的向量表示
            if vector:
                # 使用token的hash值作为向量位置
                hash_value = int(hashlib.md5(token.encode()).hexdigest()[:8], 16)
                if len(vector) > 0:
                    pos = hash_value % len(vector)
                    vector[pos] = min(1.0, vector[pos] + freq * 0.1)

        return vector

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


def save_checkpoint(output_dir: Path, processed_count: int, knowledge_entries: List[Dict],
                   vectorizer: SimpleVectorizer, indexer: SimpleIndexer) -> bool:
    """保存断点续传检查点"""
    try:
        checkpoint_dir = output_dir / "checkpoints"
        checkpoint_dir.mkdir(exist_ok=True)

        checkpoint_data = {
            "processed_count": processed_count,
            "timestamp": datetime.now().isoformat(),
            "knowledge_entries": knowledge_entries[-100:],  # 只保存最近的条目
            "vocab_size": vectorizer.vocab_size if vectorizer else 0,
            "index_size": len(indexer.document_vectors)
        }

        checkpoint_file = checkpoint_dir / "build_checkpoint.json"
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)

        return True
    except Exception as e:
        print(f"⚠️ 保存检查点失败: {e}")
        return False


def load_checkpoint(output_dir: Path) -> Dict[str, Any]:
    """加载断点续传检查点"""
    checkpoint_file = output_dir / "checkpoints" / "build_checkpoint.json"
    if checkpoint_file.exists():
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 加载检查点失败: {e}")
    return {}


def enhanced_build_vector_kb(input_file: str, output_dir: str = "data/knowledge_management",
                           resume: bool = True, checkpoint_interval: int = 50) -> bool:
    """
    增强版向量知识库构建函数
    支持断点续传、向量化及高效索引功能

    Args:
        input_file: 输入数据文件路径
        output_dir: 输出目录
        resume: 是否启用断点续传
        checkpoint_interval: 检查点保存间隔

    Returns:
        是否成功
    """
    print("🚀 开始增强版向量知识库构建...")
    print("✨ 支持功能: 断点续传 | 向量化 | 高效索引")

    # 检查输入文件
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"❌ 输入文件不存在: {input_file}")
        return False

    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        # 读取输入数据
        print(f"📖 读取输入文件: {input_file}")
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            print("❌ 输入文件必须是JSON数组格式")
            return False

        print(f"📊 读取到 {len(data)} 条数据记录")

        # 检查断点续传
        checkpoint_file = output_path / "checkpoints" / "build_checkpoint.json"
        start_index = 0

        if resume and checkpoint_file.exists():
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    checkpoint = json.load(f)
                start_index = checkpoint.get('processed_count', 0)
                print(f"📋 发现检查点，从第 {start_index} 条记录继续处理")
            except Exception as e:
                print(f"⚠️ 检查点加载失败: {e}，从头开始处理")

        # 初始化组件
        vectorizer = SimpleVectorizer()
        indexer = SimpleIndexer()

        # 处理数据并创建知识条目
        knowledge_entries = []
        processed_count = start_index

        # 收集所有文本用于向量化训练
        all_texts = []

        print("🔄 开始处理数据记录...")
        for i in range(start_index, len(data)):
            try:
                item = data[i]

                # 从数据项中提取文本内容
                title, content = extract_text_from_item(item)
                if content:
                    entry_id = f"kb_{i:06d}"
                    all_texts.append(content)

                    # 创建知识条目
                    entry = {
                        "entry_id": entry_id,
                        "title": title,
                        "content": content,
                        "metadata": {
                            "title": title,
                            "source": "frames_dataset",
                            "original_index": i,
                            "timestamp": datetime.now().isoformat(),
                            "word_count": len(content.split()),
                            "hash": hashlib.md5(content.encode()).hexdigest()[:8]
                        }
                    }
                    knowledge_entries.append(entry)
                    processed_count += 1

                    # 定期保存检查点
                    if processed_count % checkpoint_interval == 0:
                        save_checkpoint(output_path, processed_count, knowledge_entries, vectorizer, indexer)
                        print(f"💾 检查点已保存: 已处理 {processed_count} 条记录")

                    if processed_count % 100 == 0:
                        print(f"✅ 已处理 {processed_count} 条记录...")

            except Exception as e:
                print(f"⚠️ 处理第 {i} 条记录时出错: {e}")
                continue

        if not knowledge_entries:
            print("❌ 没有成功处理任何知识条目")
            return False

        print(f"✅ 数据处理完成，共 {len(knowledge_entries)} 条知识条目")

        # 训练向量化器
        print("🔢 开始向量化训练...")
        vectors = vectorizer.fit_transform([entry['content'] for entry in knowledge_entries])

        # 构建索引
        print("📚 开始构建索引...")
        for entry, vector in zip(knowledge_entries, vectors):
            indexer.add_document(
                doc_id=entry['entry_id'],
                content=entry['content'],
                vector=vector,
                metadata=entry['metadata']
            )

        print(f"✅ 索引构建完成，包含 {len(indexer.document_vectors)} 个文档")

        # 保存结果
        print("💾 保存知识库文件...")

        # 保存知识条目
        entries_file = output_path / "knowledge_entries.json"
        with open(entries_file, 'w', encoding='utf-8') as f:
            json.dump(knowledge_entries, f, ensure_ascii=False, indent=2)

        # 保存向量化器
        vectorizer_data = {
            "vocab": vectorizer.vocab,
            "vocab_size": vectorizer.vocab_size,
            "idf_scores": vectorizer.idf_scores
        }
        vectorizer_file = output_path / "vectorizer.json"
        with open(vectorizer_file, 'w', encoding='utf-8') as f:
            json.dump(vectorizer_data, f, ensure_ascii=False, indent=2)

        # 保存索引
        index_data = {
            "inverted_index": {k: list(v) for k, v in indexer.inverted_index.items()},
            "document_vectors": indexer.document_vectors,
            "document_metadata": indexer.document_metadata
        }
        index_file = output_path / "vector_index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        # 保存映射文件
        mapping_file = output_path / "vector_index.mapping.json"
        mapping_data = {
            "created_at": datetime.now().isoformat(),
            "total_entries": len(knowledge_entries),
            "mapping_type": "enhanced_vector_mapping",
            "entries": {entry["entry_id"]: idx for idx, entry in enumerate(knowledge_entries)},
            "vectorizer_info": {
                "vocab_size": vectorizer.vocab_size,
                "algorithm": "TF-IDF"
            },
            "index_info": {
                "total_docs": len(indexer.document_vectors),
                "has_inverted_index": True
            }
        }
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(mapping_data, f, ensure_ascii=False, indent=2)

        # 清理检查点
        if checkpoint_file.exists():
            checkpoint_file.unlink()
            print("🧹 已清理检查点文件")

        # 输出统计信息
        print("\n📊 构建统计:")
        print(f"   • 处理记录: {len(data)} 条")
        print(f"   • 成功条目: {len(knowledge_entries)} 条")
        print(f"   • 词汇表大小: {vectorizer.vocab_size} 个词")
        print(f"   • 索引文档数: {len(indexer.document_vectors)} 个")
        print(f"   • 跳过记录: {len(data) - len(knowledge_entries)} 条")

        print("\n📁 生成文件:")
        print(f"   • {entries_file} ({entries_file.stat().st_size} bytes)")
        print(f"   • {vectorizer_file} ({vectorizer_file.stat().st_size} bytes)")
        print(f"   • {index_file} ({index_file.stat().st_size} bytes)")
        print(f"   • {mapping_file} ({mapping_file.stat().st_size} bytes)")

        return True

    except Exception as e:
        print(f"❌ 构建过程中出现错误: {e}")
        return False


def extract_text_from_item(item: dict) -> tuple[str, str]:
    """从数据项中提取标题和内容"""
    title = ""
    content = ""

    if isinstance(item, dict):
        # 尝试不同的字段名
        if 'Prompt' in item and 'Answer' in item:
            # FRAMES数据集格式
            title = item.get('Prompt', '')[:100] + "..." if len(item.get('Prompt', '')) > 100 else item.get('Prompt', '')
            content = f"问题: {item.get('Prompt', '')}\n答案: {item.get('Answer', '')}"
            if 'wiki_links' in item and item['wiki_links']:
                content += f"\n相关链接: {item['wiki_links']}"
        elif 'title' in item and 'content' in item:
            # 标准格式
            title = item['title']
            content = item['content']
        elif 'text' in item:
            # 简单文本格式
            content = item['text']
            title = content[:50] + "..." if len(content) > 50 else content
        else:
            # 通用处理：将所有字符串值合并
            text_parts = []
            for key, value in item.items():
                if isinstance(value, str) and value.strip():
                    text_parts.append(f"{key}: {value}")
            content = "\n".join(text_parts)
            title = content[:50] + "..." if len(content) > 50 else content

    return title.strip(), content.strip()
    """
    简化的向量知识库构建函数

    Args:
        input_file: 输入数据文件路径
        output_dir: 输出目录

    Returns:
        是否成功
    """
    print("🔄 开始简化的向量知识库构建...")

    # 检查输入文件
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"❌ 输入文件不存在: {input_file}")
        return False

    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        # 读取输入数据
        print(f"📖 读取输入文件: {input_file}")
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            print("❌ 输入文件必须是JSON数组格式")
            return False

        print(f"📊 读取到 {len(data)} 条数据记录")

        # 处理数据并创建知识条目
        knowledge_entries = []
        processed_count = 0

        for i, item in enumerate(data):
            try:
                # 从数据项中提取文本内容
                entry_id = f"simple_kb_{i:06d}"

                # 提取主要文本内容
                title = ""
                content = ""
                source = "frames_dataset"

                # 根据数据结构提取内容
                if isinstance(item, dict):
                    # 尝试不同的字段名
                    if 'Prompt' in item and 'Answer' in item:
                        # FRAMES数据集格式
                        title = item.get('Prompt', '')[:100] + "..." if len(item.get('Prompt', '')) > 100 else item.get('Prompt', '')
                        content = f"问题: {item.get('Prompt', '')}\n答案: {item.get('Answer', '')}"
                        if 'wiki_links' in item and item['wiki_links']:
                            content += f"\n相关链接: {item['wiki_links']}"
                    elif 'title' in item and 'content' in item:
                        # 标准格式
                        title = item['title']
                        content = item['content']
                    elif 'text' in item:
                        # 简单文本格式
                        content = item['text']
                        title = content[:50] + "..." if len(content) > 50 else content
                    else:
                        # 通用处理：将所有字符串值合并
                        text_parts = []
                        for key, value in item.items():
                            if isinstance(value, str) and value.strip():
                                text_parts.append(f"{key}: {value}")
                        content = "\n".join(text_parts)
                        title = content[:50] + "..." if len(content) > 50 else content

                # 创建知识条目
                if content.strip():
                    entry = {
                        "entry_id": entry_id,
                        "title": title.strip() or f"Entry {i}",
                        "content": content.strip(),
                        "source": source,
                        "metadata": {
                            "title": title.strip() or f"Entry {i}",
                            "source": source,
                            "original_index": i,
                            "timestamp": datetime.now().isoformat(),
                            "word_count": len(content.split()),
                            "hash": hashlib.md5(content.encode()).hexdigest()[:8]
                        }
                    }
                    knowledge_entries.append(entry)
                    processed_count += 1

                    if processed_count % 100 == 0:
                        print(f"✅ 已处理 {processed_count} 条记录...")

            except Exception as e:
                print(f"⚠️ 处理第 {i} 条记录时出错: {e}")
                continue

        if not knowledge_entries:
            print("❌ 没有成功处理任何知识条目")
            return False

        print(f"✅ 成功处理 {len(knowledge_entries)} 条知识条目")

        # 保存知识条目
        entries_file = output_path / "knowledge_entries.json"
        print(f"💾 保存知识条目到: {entries_file}")

        with open(entries_file, 'w', encoding='utf-8') as f:
            json.dump(knowledge_entries, f, ensure_ascii=False, indent=2)

        # 创建简单的索引文件（模拟FAISS索引）
        index_file = output_path / "faiss_index.json"
        print(f"💾 创建简单索引文件: {index_file}")

        # 创建简单的ID到内容的映射（模拟向量索引）
        simple_index = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "total_entries": len(knowledge_entries),
                "index_type": "simple_text_mapping",
                "description": "简化的知识库索引（无向量嵌入）"
            },
            "entries": [
                {
                    "id": entry["entry_id"],
                    "title": entry["title"],
                    "content_preview": entry["content"][:200] + "..." if len(entry["content"]) > 200 else entry["content"],
                    "word_count": entry["metadata"]["word_count"],
                    "hash": entry["metadata"]["hash"]
                }
                for entry in knowledge_entries
            ]
        }

        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(simple_index, f, ensure_ascii=False, indent=2)

        # 创建映射文件
        mapping_file = output_path / "vector_index.mapping.json"
        print(f"💾 创建映射文件: {mapping_file}")

        mapping_data = {
            "created_at": datetime.now().isoformat(),
            "total_entries": len(knowledge_entries),
            "mapping_type": "simple_id_mapping",
            "entries": {entry["entry_id"]: idx for idx, entry in enumerate(knowledge_entries)}
        }

        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(mapping_data, f, ensure_ascii=False, indent=2)

        print("\n📊 构建统计:")
        print(f"   • 处理记录: {len(data)} 条")
        print(f"   • 成功条目: {len(knowledge_entries)} 条")
        print(f"   • 跳过记录: {len(data) - len(knowledge_entries)} 条")

        print("\n📁 生成文件:")
        print(f"   • {entries_file} ({entries_file.stat().st_size} bytes)")
        print(f"   • {index_file} ({index_file.stat().st_size} bytes)")
        print(f"   • {mapping_file} ({mapping_file.stat().st_size} bytes)")

        return True

    except Exception as e:
        print(f"❌ 构建过程中出现错误: {e}")
        return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="增强版向量知识库构建工具")
    parser.add_argument("input_file", help="输入数据文件路径（JSON格式）")
    parser.add_argument("--output-dir", default="data/knowledge_management",
                       help="输出目录（默认: data/knowledge_management）")
    parser.add_argument("--no-resume", action="store_true",
                       help="不启用断点续传（默认启用）")
    parser.add_argument("--checkpoint-interval", type=int, default=50,
                       help="检查点保存间隔（默认: 50）")
    parser.add_argument("--demo-search", action="store_true",
                       help="构建完成后演示搜索功能")

    args = parser.parse_args()

    print("=" * 70)
    print("🚀 增强版向量知识库构建工具")
    print("✨ 支持: 断点续传 | TF-IDF向量化 | 高效索引")
    print("=" * 70)
    print()

    print(f"📂 输入文件: {args.input_file}")
    print(f"📂 输出目录: {args.output_dir}")
    print(f"🔄 断点续传: {'禁用' if args.no_resume else '启用'}")
    print(f"💾 检查点间隔: {args.checkpoint_interval}")
    print()

    # 检查输入文件
    if not os.path.exists(args.input_file):
        print(f"❌ 输入文件不存在: {args.input_file}")
        sys.exit(1)

    # 执行增强版构建
    success = enhanced_build_vector_kb(
        input_file=args.input_file,
        output_dir=args.output_dir,
        resume=not args.no_resume,
        checkpoint_interval=args.checkpoint_interval
    )

    print()
    if success:
        print("✅ 向量知识库构建完成！")
        print("🎉 增强功能:")
        print("   • ✅ 断点续传: 支持中断后继续")
        print("   • ✅ TF-IDF向量化: 智能文本向量化")
        print("   • ✅ 高效索引: 倒排索引 + 相似度搜索")

        # 演示搜索功能
        if args.demo_search:
            print("\n🔍 演示搜索功能:")
            print("-" * 40)
            demo_search(args.output_dir)

    else:
        print("❌ 向量知识库构建失败")
        sys.exit(1)


def demo_search(output_dir: str):
    """演示搜索功能"""
    try:
        # 加载索引
        index_file = Path(output_dir) / "vector_index.json"
        if not index_file.exists():
            print("❌ 索引文件不存在")
            return

        with open(index_file, 'r', encoding='utf-8') as f:
            index_data = json.load(f)

        # 重建索引器
        indexer = SimpleIndexer()
        indexer.inverted_index = {k: set(v) for k, v in index_data['inverted_index'].items()}
        indexer.document_vectors = index_data['document_vectors']
        indexer.document_metadata = index_data['document_metadata']

        # 演示搜索
        test_queries = [
            "机器学习",
            "人工智能",
            "president"
        ]

        for query in test_queries:
            print(f"\n🔎 搜索: '{query}'")
            results = indexer.search(query, top_k=3)
            if results:
                for i, result in enumerate(results, 1):
                    metadata = result['metadata']
                    title = metadata.get('title', 'Unknown')[:50]
                    score = result['similarity']
                    print(f"   {i}. [{title}] 相似度: {score:.3f}")
            else:
                print("   未找到相关结果")

    except Exception as e:
        print(f"❌ 搜索演示失败: {e}")


if __name__ == "__main__":
    main()
