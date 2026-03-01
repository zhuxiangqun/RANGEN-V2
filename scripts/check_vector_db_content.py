#!/usr/bin/env python3
"""
检查向量数据库中的内容质量
评估内容是否符合要求，影响核心系统准确率
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_content_quality(content: str) -> Dict[str, Any]:
    """检查单个内容的质量"""
    issues = []
    quality_score = 100
    
    if not content:
        issues.append("内容为空")
        quality_score = 0
        return {"issues": issues, "quality_score": quality_score, "length": 0}
    
    content_length = len(content)
    
    # 检查内容长度
    if content_length < 50:
        issues.append(f"内容过短（{content_length}字符）")
        quality_score -= 30
    elif content_length < 100:
        issues.append(f"内容较短（{content_length}字符）")
        quality_score -= 10
    
    # 检查是否包含HTML标签（未清理）
    if "<" in content and ">" in content:
        html_tags = ["<div", "<span", "<p>", "<br", "<a href"]
        if any(tag in content for tag in html_tags):
            issues.append("包含未清理的HTML标签")
            quality_score -= 20
    
    # 检查是否包含引用标记（应该被清理）
    import re
    citation_pattern = r'\[\d+\]'
    if re.search(citation_pattern, content):
        issues.append("包含引用标记（如[1]、[2]等）")
        quality_score -= 10
    
    # 检查是否包含特殊字符（可能是JSON残留）
    if '}},"i":0}}]}' in content or 'id="mw' in content:
        issues.append("包含JSON残留或HTML属性")
        quality_score -= 15
    
    # 检查内容是否主要是空白字符
    if len(content.strip()) < content_length * 0.5:
        issues.append("包含过多空白字符")
        quality_score -= 10
    
    # 检查是否包含有效文本（至少有一些字母）
    if not re.search(r'[a-zA-Z\u4e00-\u9fff]', content):
        issues.append("不包含有效文本（无字母或中文）")
        quality_score -= 50
    
    return {
        "issues": issues,
        "quality_score": max(0, quality_score),
        "length": content_length
    }


def check_metadata_quality(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """检查元数据质量"""
    issues = []
    quality_score = 100
    
    # 检查必要字段
    required_fields = ['title', 'source']
    for field in required_fields:
        if field not in metadata or not metadata[field]:
            issues.append(f"缺少必要字段: {field}")
            quality_score -= 20
    
    # 检查Wikipedia相关字段
    if metadata.get('source') == 'wikipedia':
        if 'source_urls' not in metadata or not metadata.get('source_urls'):
            issues.append("Wikipedia条目缺少source_urls")
            quality_score -= 15
        
        if 'wikipedia_titles' not in metadata or not metadata.get('wikipedia_titles'):
            issues.append("Wikipedia条目缺少wikipedia_titles")
            quality_score -= 10
    
    # 检查item_index（用于FRAMES数据集）
    if 'item_index' not in metadata:
        issues.append("缺少item_index（可能不是FRAMES数据集条目）")
        quality_score -= 5
    
    return {
        "issues": issues,
        "quality_score": max(0, quality_score)
    }


def check_vector_db_content():
    """检查向量数据库内容"""
    print("=" * 80)
    print("🔍 向量数据库内容质量检查")
    print("=" * 80)
    
    try:
        # 直接读取元数据文件
        metadata_file = Path("data/knowledge_management/metadata.json")
        if not metadata_file.exists():
            print("\n⚠️  元数据文件不存在: data/knowledge_management/metadata.json")
            return
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata_data = json.load(f)
        
        # 1. 获取统计信息
        print("\n📊 1. 数据库统计信息")
        print("-" * 80)
        
        # 获取所有知识条目
        entries_dict = metadata_data.get('entries', {})
        total_entries = len(entries_dict)
        
        # 转换为列表格式
        all_entries = []
        for entry_id, entry_data in entries_dict.items():
            entry_data['id'] = entry_id
            all_entries.append(entry_data)
        
        print(f"   总条目数: {total_entries}")
        
        if total_entries == 0:
            print("\n⚠️  向量数据库为空，无法进行检查")
            return
        
        # 2. 检查向量索引
        print("\n📊 2. 向量索引检查")
        print("-" * 80)
        
        mapping_file = Path("data/knowledge_management/vector_index.mapping.json")
        if mapping_file.exists():
            with open(mapping_file, 'r') as f:
                vector_mapping = json.load(f)
            vector_count = len(vector_mapping) if isinstance(vector_mapping, dict) else 0
            print(f"   向量索引条目数: {vector_count}")
            
            if vector_count < total_entries:
                missing = total_entries - vector_count
                print(f"   ⚠️  警告: {missing} 个条目未向量化")
        else:
            print("   ⚠️  向量索引映射文件不存在")
            vector_count = 0
        
        # 3. 内容质量检查
        print("\n📊 3. 内容质量检查")
        print("-" * 80)
        
        content_quality_stats = {
            "total": 0,
            "empty": 0,
            "short": 0,
            "good": 0,
            "issues": Counter(),
            "quality_scores": []
        }
        
        metadata_quality_stats = {
            "total": 0,
            "missing_fields": Counter(),
            "quality_scores": []
        }
        
        sample_entries = []
        problematic_entries = []
        
        # 检查前100个条目（或全部，如果少于100）
        check_count = min(100, total_entries)
        print(f"   检查前 {check_count} 个条目...")
        
        for i, entry in enumerate(all_entries[:check_count]):
            entry_id = entry.get('id', f'entry_{i}')
            metadata = entry.get('metadata', {})
            content = metadata.get('content', '') or metadata.get('content_preview', '')
            
            # 检查内容质量
            content_quality = check_content_quality(content)
            content_quality_stats["total"] += 1
            content_quality_stats["quality_scores"].append(content_quality["quality_score"])
            
            if not content:
                content_quality_stats["empty"] += 1
            elif content_quality["length"] < 100:
                content_quality_stats["short"] += 1
            elif content_quality["quality_score"] >= 80:
                content_quality_stats["good"] += 1
            
            for issue in content_quality["issues"]:
                content_quality_stats["issues"][issue] += 1
            
            # 检查元数据质量
            metadata_quality = check_metadata_quality(metadata)
            metadata_quality_stats["total"] += 1
            metadata_quality_stats["quality_scores"].append(metadata_quality["quality_score"])
            
            for issue in metadata_quality["issues"]:
                metadata_quality_stats["missing_fields"][issue] += 1
            
            # 收集样本和问题条目
            if i < 5:
                sample_entries.append({
                    "id": entry_id,
                    "title": metadata.get('title', 'N/A'),
                    "content_length": len(content),
                    "content_preview": content[:200] + "..." if len(content) > 200 else content,
                    "content_quality": content_quality,
                    "metadata_quality": metadata_quality
                })
            
            if content_quality["issues"] or metadata_quality["issues"]:
                problematic_entries.append({
                    "id": entry_id,
                    "title": metadata.get('title', 'N/A'),
                    "content_issues": content_quality["issues"],
                    "metadata_issues": metadata_quality["issues"]
                })
        
        # 显示内容质量统计
        avg_content_score = sum(content_quality_stats["quality_scores"]) / len(content_quality_stats["quality_scores"]) if content_quality_stats["quality_scores"] else 0
        print(f"   平均内容质量分数: {avg_content_score:.1f}/100")
        print(f"   空内容: {content_quality_stats['empty']} 条")
        print(f"   短内容(<100字符): {content_quality_stats['short']} 条")
        print(f"   高质量内容(≥80分): {content_quality_stats['good']} 条")
        
        if content_quality_stats["issues"]:
            print(f"\n   内容问题统计:")
            for issue, count in content_quality_stats["issues"].most_common(5):
                print(f"     - {issue}: {count} 条")
        
        # 显示元数据质量统计
        avg_metadata_score = sum(metadata_quality_stats["quality_scores"]) / len(metadata_quality_stats["quality_scores"]) if metadata_quality_stats["quality_scores"] else 0
        print(f"\n   平均元数据质量分数: {avg_metadata_score:.1f}/100")
        
        if metadata_quality_stats["missing_fields"]:
            print(f"   元数据问题统计:")
            for issue, count in metadata_quality_stats["missing_fields"].most_common(5):
                print(f"     - {issue}: {count} 条")
        
        # 4. 显示样本条目
        print("\n📊 4. 样本条目（前5个）")
        print("-" * 80)
        
        for i, sample in enumerate(sample_entries, 1):
            print(f"\n   样本 {i}:")
            print(f"     ID: {sample['id']}")
            print(f"     标题: {sample['title']}")
            print(f"     内容长度: {sample['content_length']} 字符")
            print(f"     内容预览: {sample['content_preview']}")
            print(f"     内容质量: {sample['content_quality']['quality_score']}/100")
            if sample['content_quality']['issues']:
                print(f"     内容问题: {', '.join(sample['content_quality']['issues'])}")
            print(f"     元数据质量: {sample['metadata_quality']['quality_score']}/100")
            if sample['metadata_quality']['issues']:
                print(f"     元数据问题: {', '.join(sample['metadata_quality']['issues'])}")
        
        # 5. 问题条目
        if problematic_entries:
            print(f"\n📊 5. 问题条目（前10个）")
            print("-" * 80)
            
            for i, entry in enumerate(problematic_entries[:10], 1):
                print(f"\n   问题条目 {i}:")
                print(f"     ID: {entry['id']}")
                print(f"     标题: {entry['title']}")
                if entry['content_issues']:
                    print(f"     内容问题: {', '.join(entry['content_issues'])}")
                if entry['metadata_issues']:
                    print(f"     元数据问题: {', '.join(entry['metadata_issues'])}")
        
        # 6. 总体评估
        print("\n📊 6. 总体评估")
        print("-" * 80)
        
        overall_score = (avg_content_score + avg_metadata_score) / 2
        
        if overall_score >= 90:
            status = "✅ 优秀"
            recommendation = "内容质量优秀，符合要求"
        elif overall_score >= 80:
            status = "✅ 良好"
            recommendation = "内容质量良好，基本符合要求"
        elif overall_score >= 70:
            status = "⚠️  一般"
            recommendation = "内容质量一般，建议检查并修复问题条目"
        else:
            status = "❌ 较差"
            recommendation = "内容质量较差，需要重新导入或修复"
        
        print(f"   总体质量分数: {overall_score:.1f}/100")
        print(f"   状态: {status}")
        print(f"   建议: {recommendation}")
        
        # 7. 检查未向量化的条目
        print("\n📊 7. 未向量化条目检查")
        print("-" * 80)
        
        if vector_count < total_entries:
            unvectorized_count = total_entries - vector_count
            print(f"   未向量化条目数: {unvectorized_count}")
            
            # 找出未向量化的条目
            unvectorized_entries = []
            for entry in all_entries:
                entry_id = entry.get('id', '')
                if entry_id not in vector_mapping:
                    metadata = entry.get('metadata', {})
                    content = metadata.get('content', '') or metadata.get('content_preview', '')
                    unvectorized_entries.append({
                        'id': entry_id,
                        'title': metadata.get('title', 'N/A'),
                        'content_length': len(content),
                        'has_content': bool(content)
                    })
            
            if unvectorized_entries:
                print(f"\n   未向量化条目详情（前10个）:")
                for i, entry in enumerate(unvectorized_entries[:10], 1):
                    print(f"     {i}. ID: {entry['id']}")
                    print(f"        标题: {entry['title']}")
                    print(f"        内容长度: {entry['content_length']} 字符")
                    print(f"        是否有内容: {'是' if entry['has_content'] else '否'}")
        
        # 8. 关键指标
        print("\n📊 8. 关键指标")
        print("-" * 80)
        
        vectorization_rate = (vector_count / total_entries * 100) if total_entries > 0 else 0
        print(f"   向量化率: {vectorization_rate:.1f}% ({vector_count}/{total_entries})")
        
        if vectorization_rate < 100:
            print(f"   ⚠️  警告: 有 {total_entries - vector_count} 个条目未向量化，可能影响检索效果")
            print(f"   💡 建议: 运行自动向量化脚本处理未向量化的条目")
        
        empty_rate = (content_quality_stats['empty'] / check_count * 100) if check_count > 0 else 0
        print(f"   空内容率: {empty_rate:.1f}% ({content_quality_stats['empty']}/{check_count})")
        
        if empty_rate > 10:
            print(f"   ⚠️  警告: 空内容率较高，可能影响检索准确性")
        
        # 9. 内容来源分析
        print("\n📊 9. 内容来源分析")
        print("-" * 80)
        
        source_counter = Counter()
        for entry in all_entries[:check_count]:
            metadata = entry.get('metadata', {})
            source = metadata.get('source', 'unknown')
            source_counter[source] += 1
        
        print(f"   内容来源分布（前{check_count}个条目）:")
        for source, count in source_counter.most_common():
            print(f"     - {source}: {count} 条")
        
        # 10. Title质量检查
        print("\n📊 10. Title质量检查")
        print("-" * 80)
        
        title_stats = {
            "total": 0,
            "empty": 0,
            "item_0": 0,  # 检查是否有"Item 0"这样的默认值
            "too_long": 0,  # 标题过长（>200字符）
            "too_short": 0,  # 标题过短（<5字符）
            "has_wikipedia_title": 0,  # 包含Wikipedia标题（优化后的结果）
            "has_prompt_only": 0,  # 只有prompt作为title（未优化）
            "duplicate_titles": Counter(),
            "title_lengths": [],
            "sample_titles": []
        }
        
        # 检查所有条目的title
        for entry in all_entries:
            metadata = entry.get('metadata', {})
            title = metadata.get('title', '')
            prompt = metadata.get('prompt', '')
            wikipedia_titles = metadata.get('wikipedia_titles', [])
            
            title_stats["total"] += 1
            
            if not title or title.strip() == '':
                title_stats["empty"] += 1
            else:
                title_length = len(title)
                title_stats["title_lengths"].append(title_length)
                
                # 检查是否是"Item 0"或类似的默认值
                if title.startswith("Item ") and title.replace("Item ", "").strip().isdigit():
                    item_num = int(title.replace("Item ", "").strip())
                    if item_num == 0:
                        title_stats["item_0"] += 1
                
                # 检查标题长度
                if title_length > 200:
                    title_stats["too_long"] += 1
                elif title_length < 5:
                    title_stats["too_short"] += 1
                
                # 检查是否包含Wikipedia标题（优化后的结果）
                if wikipedia_titles and any(wiki_title in title for wiki_title in wikipedia_titles):
                    title_stats["has_wikipedia_title"] += 1
                
                # 检查是否只有prompt作为title（未优化的情况）
                if prompt and title == prompt:
                    title_stats["has_prompt_only"] += 1
                
                # 收集重复的title
                title_stats["duplicate_titles"][title] += 1
                
                # 收集样本title（前10个）
                if len(title_stats["sample_titles"]) < 10:
                    title_stats["sample_titles"].append({
                        "title": title,
                        "length": title_length,
                        "has_wikipedia": bool(wikipedia_titles and any(wiki_title in title for wiki_title in wikipedia_titles)),
                        "is_prompt": title == prompt if prompt else False
                    })
        
        # 显示title统计
        print(f"   总条目数: {title_stats['total']}")
        print(f"   空title: {title_stats['empty']} 条 ({title_stats['empty']/title_stats['total']*100:.1f}%)")
        
        if title_stats['item_0'] > 0:
            print(f"   ⚠️  'Item 0'标题: {title_stats['item_0']} 条 ({title_stats['item_0']/title_stats['total']*100:.1f}%)")
            print(f"      💡 这是未优化的标题，应该使用Wikipedia标题")
        
        if title_stats['too_long'] > 0:
            print(f"   ⚠️  标题过长(>200字符): {title_stats['too_long']} 条")
        
        if title_stats['too_short'] > 0:
            print(f"   ⚠️  标题过短(<5字符): {title_stats['too_short']} 条")
        
        if title_stats['title_lengths']:
            avg_length = sum(title_stats['title_lengths']) / len(title_stats['title_lengths'])
            max_length = max(title_stats['title_lengths'])
            min_length = min(title_stats['title_lengths'])
            print(f"\n   标题长度统计:")
            print(f"     平均长度: {avg_length:.1f} 字符")
            print(f"     最短: {min_length} 字符")
            print(f"     最长: {max_length} 字符")
        
        print(f"\n   标题优化情况:")
        print(f"     包含Wikipedia标题: {title_stats['has_wikipedia_title']} 条 ({title_stats['has_wikipedia_title']/title_stats['total']*100:.1f}%) ✅")
        print(f"     只有prompt作为title: {title_stats['has_prompt_only']} 条 ({title_stats['has_prompt_only']/title_stats['total']*100:.1f}%) ⚠️")
        
        # 检查重复的title（区分正常和不正常）
        # 正常：同一个item_index的多个分块有相同标题（分块导致）
        # 不正常：不同item_index有相同标题（可能是数据问题）
        normal_duplicates = {}  # title -> set of item_indices
        abnormal_duplicates = {}  # title -> list of (item_index, count)
        
        for entry in all_entries:
            metadata = entry.get('metadata', {})
            title = metadata.get('title', '')
            item_index = metadata.get('item_index')
            
            if title and title in title_stats['duplicate_titles'] and title_stats['duplicate_titles'][title] > 1:
                if title not in normal_duplicates:
                    normal_duplicates[title] = set()
                if item_index is not None:
                    normal_duplicates[title].add(item_index)
        
        # 检查是否有不正常的重复（不同item_index有相同标题）
        for title, item_indices in normal_duplicates.items():
            if len(item_indices) > 1:
                # 不同item_index有相同标题，这是不正常的
                count = title_stats['duplicate_titles'][title]
                abnormal_duplicates[title] = {
                    'item_indices': list(item_indices),
                    'count': count
                }
        
        # 只显示不正常的重复标题警告
        if abnormal_duplicates:
            print(f"\n   ⚠️  异常重复标题: {len(abnormal_duplicates)} 个标题在不同FRAMES数据项中重复出现")
            print(f"      这可能表示数据问题，建议检查:")
            for i, (title, info) in enumerate(list(abnormal_duplicates.items())[:5], 1):
                item_indices_str = ', '.join(map(str, sorted(info['item_indices'])[:5]))
                if len(info['item_indices']) > 5:
                    item_indices_str += f" 等({len(info['item_indices'])}个)"
                print(f"       {i}. '{title[:60]}...' ({info['count']} 次, 涉及item_index: {item_indices_str})" 
                      if len(title) > 60 else 
                      f"       {i}. '{title}' ({info['count']} 次, 涉及item_index: {item_indices_str})")
        
        # 统计正常重复（分块导致的）
        normal_duplicate_count = sum(1 for title, item_indices in normal_duplicates.items() 
                                     if len(item_indices) == 1 and title_stats['duplicate_titles'][title] > 1)
        if normal_duplicate_count > 0:
            print(f"\n   ℹ️  正常重复标题: {normal_duplicate_count} 个标题因内容分块而重复（这是正常的）")
        
        # 显示样本title
        if title_stats['sample_titles']:
            print(f"\n   样本标题（前10个）:")
            for i, sample in enumerate(title_stats['sample_titles'], 1):
                status = "✅" if sample['has_wikipedia'] else ("⚠️" if sample['is_prompt'] else "ℹ️")
                print(f"     {i}. {status} [{sample['length']}字符] {sample['title'][:80]}{'...' if len(sample['title']) > 80 else ''}")
                if sample['is_prompt']:
                    print(f"        ⚠️  这是prompt，应该使用Wikipedia标题")
        
        # Title质量评估
        # 🚀 修复：只对真正的问题扣分，正常重复（分块导致）不扣分
        title_quality_score = 100
        if title_stats['empty'] > 0:
            title_quality_score -= (title_stats['empty'] / title_stats['total']) * 30
        if title_stats['item_0'] > 0:
            title_quality_score -= (title_stats['item_0'] / title_stats['total']) * 40
        if title_stats['has_prompt_only'] > 0:
            title_quality_score -= (title_stats['has_prompt_only'] / title_stats['total']) * 30
        # 异常重复标题也扣分
        if abnormal_duplicates:
            abnormal_count = sum(info['count'] for info in abnormal_duplicates.values())
            title_quality_score -= (abnormal_count / title_stats['total']) * 20
        
        print(f"\n   Title质量分数: {title_quality_score:.1f}/100")
        if title_quality_score >= 90:
            print(f"   ✅ Title质量优秀")
        elif title_quality_score >= 70:
            print(f"   ⚠️  Title质量一般，建议检查并优化")
        else:
            print(f"   ❌ Title质量较差，需要重新导入或修复")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n❌ 检查向量数据库内容失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_vector_db_content()

