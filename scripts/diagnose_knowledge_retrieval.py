#!/usr/bin/env python3
"""
知识检索诊断工具
用于诊断为什么会出现低置信度答案的根本原因
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.enhanced_knowledge_retrieval_agent import EnhancedKnowledgeRetrievalAgent
from src.core.unified_dependency_manager import UnifiedDependencyManager


async def diagnose_query(query: str, top_k: int = 15):
    """诊断单个查询的知识检索过程"""
    print(f"\n{'='*80}")
    print(f"🔍 诊断查询: {query}")
    print(f"{'='*80}\n")
    
    # 初始化知识检索智能体
    agent = EnhancedKnowledgeRetrievalAgent()
    
    # 执行检索
    print("📊 执行知识检索...")
    result = await agent.execute({"query": query, "top_k": top_k})
    
    if not result or not result.data:
        print("❌ 检索失败：没有返回结果")
        return
    
    sources = result.data.get('sources', [])
    print(f"✅ 检索完成：找到 {len(sources)} 条结果\n")
    
    # 分析每条结果
    print("📋 检索结果详情：")
    print("-" * 80)
    for i, source in enumerate(sources[:10], 1):  # 只显示前10条
        content = source.get('content', '')
        similarity = source.get('similarity', 0.0) or source.get('similarity_score', 0.0)
        source_name = source.get('source', 'unknown')
        
        print(f"\n结果 {i}:")
        print(f"  相似度: {similarity:.4f}")
        print(f"  来源: {source_name}")
        print(f"  内容预览: {content[:200]}...")
        
        # 检查内容是否包含查询关键词
        query_lower = query.lower()
        content_lower = content.lower()
        query_words = set(word for word in query_lower.split() if len(word) > 2)
        content_words = set(word for word in content_lower.split() if len(word) > 2)
        overlap = query_words & content_words
        overlap_ratio = len(overlap) / len(query_words) if query_words else 0
        
        print(f"  关键词匹配: {len(overlap)}/{len(query_words)} ({overlap_ratio:.2%})")
        if overlap:
            print(f"  匹配的关键词: {', '.join(list(overlap)[:5])}")
    
    # 分析检索质量
    print("\n" + "-" * 80)
    print("📊 检索质量分析：")
    
    if sources:
        avg_similarity = sum(
            s.get('similarity', 0.0) or s.get('similarity_score', 0.0) 
            for s in sources
        ) / len(sources)
        max_similarity = max(
            s.get('similarity', 0.0) or s.get('similarity_score', 0.0) 
            for s in sources
        )
        
        print(f"  平均相似度: {avg_similarity:.4f}")
        print(f"  最高相似度: {max_similarity:.4f}")
        
        # 检查是否有高相似度结果
        high_similarity_count = sum(
            1 for s in sources 
            if (s.get('similarity', 0.0) or s.get('similarity_score', 0.0)) > 0.5
        )
        print(f"  高相似度结果数 (>0.5): {high_similarity_count}")
        
        # 检查是否有中等相似度结果
        medium_similarity_count = sum(
            1 for s in sources 
            if 0.3 < (s.get('similarity', 0.0) or s.get('similarity_score', 0.0)) <= 0.5
        )
        print(f"  中等相似度结果数 (0.3-0.5): {medium_similarity_count}")
        
        # 检查是否有低相似度结果
        low_similarity_count = sum(
            1 for s in sources 
            if (s.get('similarity', 0.0) or s.get('similarity_score', 0.0)) <= 0.3
        )
        print(f"  低相似度结果数 (<=0.3): {low_similarity_count}")
        
        # 诊断建议
        print("\n💡 诊断建议：")
        if max_similarity < 0.3:
            print("  ⚠️  最高相似度很低，可能原因：")
            print("     1. 知识库中确实没有相关内容")
            print("     2. 查询理解不准确，需要改进查询扩展")
            print("     3. 相似度计算有问题，需要检查embedding模型")
        elif max_similarity < 0.5:
            print("  ⚠️  最高相似度中等，可能原因：")
            print("     1. 知识库中有部分相关内容，但不够精确")
            print("     2. 需要改进检索策略（如使用混合检索）")
            print("     3. 需要改进查询扩展，增加同义词和关联词")
        else:
            print("  ✅ 最高相似度较高，检索质量较好")
            print("     如果答案仍然错误，可能是LLM推理问题")


async def diagnose_frames_sample(sample_id: int = 4):
    """诊断FRAMES样本"""
    # 加载FRAMES数据集
    frames_path = project_root / "data" / "frames_dataset.json"
    if not frames_path.exists():
        print(f"❌ FRAMES数据集不存在: {frames_path}")
        return
    
    with open(frames_path, 'r', encoding='utf-8') as f:
        frames_data = json.load(f)
    
    if sample_id >= len(frames_data):
        print(f"❌ 样本ID超出范围: {sample_id} (总共 {len(frames_data)} 个样本)")
        return
    
    sample = frames_data[sample_id]
    query = sample.get('question', '')
    expected_answer = sample.get('answer', '')
    
    print(f"\n{'='*80}")
    print(f"📋 FRAMES样本 {sample_id} 诊断")
    print(f"{'='*80}")
    print(f"查询: {query}")
    print(f"期望答案: {expected_answer}")
    
    await diagnose_query(query)


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="知识检索诊断工具")
    parser.add_argument("--query", type=str, help="要诊断的查询")
    parser.add_argument("--sample-id", type=int, default=4, help="FRAMES样本ID（默认4，Argentina案例）")
    parser.add_argument("--top-k", type=int, default=15, help="检索结果数量（默认15）")
    
    args = parser.parse_args()
    
    # 初始化依赖管理器
    UnifiedDependencyManager.initialize()
    
    if args.query:
        await diagnose_query(args.query, args.top_k)
    else:
        await diagnose_frames_sample(args.sample_id)


if __name__ == "__main__":
    asyncio.run(main())

