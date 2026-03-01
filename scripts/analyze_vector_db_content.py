#!/usr/bin/env python3
"""
分析向量数据库内容质量
通过知识管理系统API检查，避免直接解析大JSON文件
"""

import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from knowledge_management_system.api.service_interface import get_knowledge_service
    from knowledge_management_system.storage.metadata_storage import MetadataStorage
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)


def analyze_vector_db_content():
    """分析向量数据库内容"""
    print("=" * 80)
    print("🔍 向量数据库内容质量分析")
    print("=" * 80)
    
    try:
        # 通过API获取服务
        service = get_knowledge_service()
        metadata_storage = MetadataStorage()
        manager = metadata_storage.get_manager()
        
        # 获取所有条目
        entries = manager._metadata.get('entries', {})
        total_entries = len(entries)
        
        print(f"\n📊 1. 数据库统计信息")
        print("-" * 80)
        print(f"   总条目数: {total_entries}")
        
        if total_entries == 0:
            print("\n⚠️  向量数据库为空")
            return
        
        # 检查向量索引
        print(f"\n📊 2. 向量索引检查")
        print("-" * 80)
        
        vector_storage = service.vector_storage
        index_builder = vector_storage.get_index_builder()
        
        if index_builder.index is not None:
            vector_count = index_builder.entry_count
            print(f"   向量索引条目数: {vector_count}")
            
            if vector_count < total_entries:
                missing = total_entries - vector_count
                print(f"   ⚠️  警告: {missing} 个条目未向量化 ({missing/total_entries*100:.1f}%)")
            else:
                print(f"   ✅ 所有条目已向量化")
        else:
            print("   ⚠️  向量索引未初始化")
            vector_count = 0
        
        # 采样检查内容质量
        print(f"\n📊 3. 内容质量检查（采样前100条）")
        print("-" * 80)
        
        sample_size = min(100, total_entries)
        sample_entries = list(entries.items())[:sample_size]
        
        quality_stats = {
            "total": 0,
            "empty_content": 0,
            "short_content": 0,
            "good_content": 0,
            "has_html": 0,
            "has_citations": 0,
            "has_json_artifacts": 0,
            "content_lengths": [],
            "sources": Counter(),
            "sample_entries": []
        }
        
        for entry_id, entry_data in sample_entries:
            quality_stats["total"] += 1
            
            metadata = entry_data.get('metadata', {})
            content = metadata.get('content', '') or metadata.get('content_preview', '')
            
            # 内容长度
            content_len = len(content) if content else 0
            quality_stats["content_lengths"].append(content_len)
            
            if not content or content_len == 0:
                quality_stats["empty_content"] += 1
            elif content_len < 100:
                quality_stats["short_content"] += 1
            elif content_len >= 100:
                quality_stats["good_content"] += 1
            
            # 检查HTML标签
            if "<" in content and ">" in content:
                html_tags = ["<div", "<span", "<p>", "<br", "<a href"]
                if any(tag in content for tag in html_tags):
                    quality_stats["has_html"] += 1
            
            # 检查引用标记
            import re
            if re.search(r'\[\d+\]', content):
                quality_stats["has_citations"] += 1
            
            # 检查JSON残留
            if '}},"i":0}}]}' in content or 'id="mw' in content:
                quality_stats["has_json_artifacts"] += 1
            
            # 来源统计
            source = metadata.get('source', 'unknown')
            quality_stats["sources"][source] += 1
            
            # 收集样本
            if len(quality_stats["sample_entries"]) < 5:
                quality_stats["sample_entries"].append({
                    "id": entry_id,
                    "title": metadata.get('title', 'N/A'),
                    "content_length": content_len,
                    "content_preview": content[:200] + "..." if content_len > 200 else content,
                    "source": source
                })
        
        # 显示统计
        if quality_stats["content_lengths"]:
            avg_length = sum(quality_stats["content_lengths"]) / len(quality_stats["content_lengths"])
            min_length = min(quality_stats["content_lengths"])
            max_length = max(quality_stats["content_lengths"])
            
            print(f"   平均内容长度: {avg_length:.0f} 字符")
            print(f"   最短: {min_length} 字符")
            print(f"   最长: {max_length} 字符")
        
        print(f"\n   内容质量分布:")
        print(f"     空内容: {quality_stats['empty_content']} ({quality_stats['empty_content']/sample_size*100:.1f}%)")
        print(f"     短内容(<100字符): {quality_stats['short_content']} ({quality_stats['short_content']/sample_size*100:.1f}%)")
        print(f"     正常内容(≥100字符): {quality_stats['good_content']} ({quality_stats['good_content']/sample_size*100:.1f}%)")
        
        if quality_stats["has_html"] > 0:
            print(f"\n   ⚠️  包含HTML标签: {quality_stats['has_html']} 条 ({quality_stats['has_html']/sample_size*100:.1f}%)")
        
        if quality_stats["has_citations"] > 0:
            print(f"   ℹ️  包含引用标记: {quality_stats['has_citations']} 条 ({quality_stats['has_citations']/sample_size*100:.1f}%)")
        
        if quality_stats["has_json_artifacts"] > 0:
            print(f"   ⚠️  包含JSON残留: {quality_stats['has_json_artifacts']} 条 ({quality_stats['has_json_artifacts']/sample_size*100:.1f}%)")
        
        # 来源分布
        print(f"\n   内容来源分布:")
        for source, count in quality_stats["sources"].most_common():
            print(f"     - {source}: {count} 条 ({count/sample_size*100:.1f}%)")
        
        # 显示样本
        print(f"\n📊 4. 样本条目（前5个）")
        print("-" * 80)
        
        for i, sample in enumerate(quality_stats["sample_entries"], 1):
            print(f"\n   样本 {i}:")
            print(f"     ID: {sample['id']}")
            print(f"     标题: {sample['title']}")
            print(f"     来源: {sample['source']}")
            print(f"     内容长度: {sample['content_length']} 字符")
            print(f"     内容预览: {sample['content_preview'][:150]}...")
        
        # 总体评估
        print(f"\n📊 5. 总体评估")
        print("-" * 80)
        
        quality_score = 100
        if quality_stats['empty_content'] > 0:
            quality_score -= (quality_stats['empty_content'] / sample_size) * 30
        if quality_stats['has_html'] > 0:
            quality_score -= (quality_stats['has_html'] / sample_size) * 20
        if quality_stats['has_json_artifacts'] > 0:
            quality_score -= (quality_stats['has_json_artifacts'] / sample_size) * 15
        
        vectorization_rate = (vector_count / total_entries * 100) if total_entries > 0 else 0
        
        print(f"   内容质量分数: {quality_score:.1f}/100")
        print(f"   向量化率: {vectorization_rate:.1f}%")
        
        if quality_score >= 90 and vectorization_rate >= 95:
            print(f"   ✅ 向量数据库内容质量优秀")
        elif quality_score >= 70 and vectorization_rate >= 80:
            print(f"   ⚠️  向量数据库内容质量一般，建议优化")
        else:
            print(f"   ❌ 向量数据库内容质量较差，需要修复")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    analyze_vector_db_content()
