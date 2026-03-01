#!/usr/bin/env python3
"""
诊断属性提取问题
检查知识条目中是否有属性信息，以及LLM是否提取到了属性
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from knowledge_management_system.api.service_interface import get_knowledge_service
from knowledge_management_system.utils.logger import get_logger

logger = get_logger()


def diagnose_property_extraction(sample_size: int = 10):
    """诊断属性提取问题"""
    service = get_knowledge_service()
    
    # 获取一些知识条目
    all_entries = service.knowledge_manager.list_knowledge(limit=sample_size)
    
    if not all_entries:
        print("❌ 没有找到知识条目")
        return
    
    print(f"📊 分析 {len(all_entries)} 个知识条目...")
    print("=" * 80)
    
    total_with_properties = 0
    total_without_properties = 0
    
    for i, entry in enumerate(all_entries, 1):
        entry_id = entry.get('id', 'unknown')
        metadata = entry.get('metadata', {})
        content = metadata.get('content', '')
        
        if not content:
            print(f"\n条目 {i} ({entry_id}): ❌ 没有内容")
            continue
        
        # 只检查内容，不调用LLM（避免卡住）
        print(f"\n条目 {i} ({entry_id}):")
        print(f"  内容长度: {len(content)} 字符")
        print(f"  内容预览: {content[:300]}...")
        
        # 简单检查内容中是否包含可能包含属性的关键词
        property_keywords = ['birth', 'death', 'born', 'died', 'nationality', 'founded', 'date', 'location', 'description']
        found_keywords = [kw for kw in property_keywords if kw.lower() in content.lower()]
        if found_keywords:
            print(f"  ✅ 内容中包含可能的属性关键词: {found_keywords[:5]}")
        else:
            print(f"  ⚠️  内容中未发现明显的属性关键词")
    
    print("\n" + "=" * 80)
    print(f"📊 分析完成")
    print(f"\n💡 问题分析:")
    print(f"  从知识图谱数据来看，所有实体和关系的 properties 字段都是空字典 {{}}")
    print(f"  这说明属性提取逻辑可能存在问题，或者LLM没有提取到属性")
    print(f"\n🔍 可能的原因:")
    print(f"  1. LLM提取时没有返回属性（prompt可能不够强调）")
    print(f"  2. 属性在传递过程中丢失")
    print(f"  3. 属性被过滤掉了（null值、空字符串等）")
    print(f"  4. 知识条目内容本身不包含属性信息")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="诊断属性提取问题")
    parser.add_argument("--sample-size", type=int, default=10, help="分析的条目数量")
    args = parser.parse_args()
    
    diagnose_property_extraction(args.sample_size)

