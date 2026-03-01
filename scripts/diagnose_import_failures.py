#!/usr/bin/env python3
"""
诊断Wikipedia导入失败原因
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from knowledge_management_system.scripts.import_wikipedia_from_frames import extract_wikipedia_links_from_item
from knowledge_management_system.utils.wikipedia_fetcher import get_wikipedia_fetcher

def diagnose_failures():
    """诊断导入失败原因"""
    print("=" * 70)
    print("🔍 Wikipedia导入失败原因诊断")
    print("=" * 70)
    
    # 加载进度文件
    progress_file = Path("data/knowledge_management/import_progress.json")
    if not progress_file.exists():
        print("❌ 进度文件不存在")
        return
    
    with open(progress_file, 'r', encoding='utf-8') as f:
        progress = json.load(f)
    
    failed_indices = progress.get('failed_item_indices', [])
    print(f"\n📊 失败统计:")
    print(f"   失败数据项数: {len(failed_indices)}")
    
    if not failed_indices:
        print("   ✅ 没有失败的数据项")
        return
    
    # 加载FRAMES数据
    frames_file = Path("data/frames_dataset.json")
    if not frames_file.exists():
        print(f"❌ FRAMES数据集文件不存在: {frames_file}")
        return
    
    with open(frames_file, 'r', encoding='utf-8') as f:
        frames_data = json.load(f)
    
    # 诊断前10个失败项
    print(f"\n🔍 诊断前10个失败数据项:")
    print("-" * 70)
    
    fetcher = get_wikipedia_fetcher()
    test_count = min(10, len(failed_indices))
    
    for i, item_index in enumerate(failed_indices[:test_count], 1):
        if item_index >= len(frames_data):
            print(f"\n{i}. 数据项 #{item_index}: ❌ 索引超出范围（数据集只有{len(frames_data)}项）")
            continue
        
        item = frames_data[item_index]
        print(f"\n{i}. 数据项 #{item_index}:")
        
        # 1. 检查Wikipedia链接提取
        urls = extract_wikipedia_links_from_item(item)
        if not urls:
            print(f"   ❌ 原因: 没有提取到Wikipedia链接")
            print(f"   💡 可能原因: 数据项格式异常或缺少Wikipedia链接字段")
            continue
        else:
            print(f"   ✅ Wikipedia链接数: {len(urls)}")
        
        # 2. 测试抓取
        print(f"   🔄 测试抓取前2个链接...")
        try:
            test_urls = urls[:2]
            pages = fetcher.fetch_multiple_pages(
                test_urls,
                include_full_text=True,
                deduplicate=True
            )
            
            if not pages:
                print(f"   ❌ 原因: 抓取返回空结果")
                print(f"   💡 可能原因: Wikipedia API限制、网络问题或页面不存在")
            else:
                print(f"   ✅ 抓取成功: {len(pages)} 个页面")
                print(f"   ⚠️  注意: 当前可以抓取，可能是之前的网络问题或超时")
                
        except Exception as e:
            print(f"   ❌ 原因: 抓取异常 - {type(e).__name__}: {str(e)[:150]}")
            print(f"   💡 可能原因: 网络连接问题、API限制或超时")
    
    # 总结
    print(f"\n" + "=" * 70)
    print(f"📋 诊断总结:")
    print(f"   1. 检查数据项是否有Wikipedia链接")
    print(f"   2. 测试实际抓取是否成功")
    print(f"   3. 如果当前可以抓取，可能是之前的临时网络问题")
    print(f"\n💡 建议:")
    print(f"   - 使用 --retry-failed 参数重试失败项")
    print(f"   - 检查网络连接和Wikipedia API访问")
    print(f"   - 如果持续失败，可能需要增加重试次数或延迟")
    print("=" * 70)

if __name__ == "__main__":
    diagnose_failures()
