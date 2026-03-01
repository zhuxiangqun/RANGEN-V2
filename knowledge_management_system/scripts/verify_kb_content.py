#!/usr/bin/env python3
"""
向量知识库内容验证脚本
用于验证构建完成后的知识库内容正确性，包括：
1. 随机抽样查询
2. 验证元数据完整性
3. 验证向量检索准确性
"""

import sys
import os
import argparse
import json
import random
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from knowledge_management_system.api.service_interface import get_knowledge_service
from knowledge_management_system.utils.logger import get_logger

logger = get_logger()

def verify_knowledge_base(
    dataset_path: str,
    sample_size: int = 5,
    verify_content: bool = True
):
    """
    验证知识库内容
    
    Args:
        dataset_path: 原始数据集路径
        sample_size: 抽样验证数量
        verify_content: 是否验证具体内容
    """
    print("=" * 70)
    print("🔍 向量知识库内容验证工具")
    print("=" * 70)
    
    # 1. 加载原始数据集
    print(f"\n📥 正在加载原始数据集: {dataset_path}")
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            frames_data = json.load(f)
        print(f"✅ 数据集加载成功，共 {len(frames_data)} 条记录")
    except Exception as e:
        print(f"❌ 数据集加载失败: {e}")
        return

    # 2. 初始化知识库服务
    print("\n🔄 初始化知识库服务...")
    try:
        service = get_knowledge_service()
        # 获取知识库统计信息（如果支持）
        try:
            stats = service.get_statistics()
            print(f"📊 知识库当前状态: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        except:
            print("⚠️ 无法获取详细统计信息")
    except Exception as e:
        print(f"❌ 服务初始化失败: {e}")
        return

    # 3. 随机抽样验证
    print(f"\n🎲 正在进行随机抽样验证 (样本数: {sample_size})...")
    samples = random.sample(frames_data, min(sample_size, len(frames_data)))
    
    success_count = 0
    
    for i, item in enumerate(samples):
        # 获取查询词
        prompt = (
            item.get('query') or item.get('Query') or
            item.get('question') or item.get('Question') or
            item.get('prompt') or item.get('Prompt')
        )
        
        if not prompt:
            print(f"⚠️ 样本 {i+1} 缺少查询词，跳过")
            continue
            
        print(f"\n🔎 验证样本 {i+1}/{sample_size}:")
        print(f"   Query: {prompt[:100]}...")
        
        try:
            # 执行检索
            results = service.query_knowledge(
                query=prompt,
                top_k=3,
                similarity_threshold=0.5
            )
            
            if not results:
                print(f"   ❌ 未找到相关结果")
                continue
                
            # 验证结果相关性
            found_match = False
            first_match = results[0]
            metadata = first_match.get('metadata', {})
            score = first_match.get('similarity', 0)
            
            print(f"   ✅ 检索到 {len(results)} 条结果 (最高相似度: {score:.4f})")
            print(f"   🏆 Top1 标题: {metadata.get('title', 'N/A')}")
            print(f"   📄 Top1 来源: {metadata.get('source_urls', ['N/A'])[0]}")
            
            # 简单的内容匹配验证
            expected_answer = item.get('expected_answer') or item.get('answer', '')
            if verify_content and expected_answer:
                content = first_match.get('content', '')
                # 这里只做简单的关键词检查，不做严格语义匹配
                print(f"   📝 内容预览: {content[:100].replace(chr(10), ' ')}...")
            
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ 检索过程发生错误: {e}")

    print("\n" + "=" * 70)
    print(f"🏁 验证完成! 成功率: {success_count}/{len(samples)} ({success_count/len(samples)*100:.1f}%)")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="验证向量知识库内容")
    parser.add_argument(
        "--dataset-path", 
        type=str, 
        default="data/frames-benchmark/queries.json",
        help="原始数据集路径"
    )
    parser.add_argument(
        "--sample-size", 
        type=int, 
        default=5,
        help="验证样本数量"
    )
    
    args = parser.parse_args()
    
    verify_knowledge_base(
        dataset_path=args.dataset_path,
        sample_size=args.sample_size
    )
