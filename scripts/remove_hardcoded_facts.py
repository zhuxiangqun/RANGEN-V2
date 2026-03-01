#!/usr/bin/env python3
"""
删除硬编码的历史事实
这些事实是针对特定问题的，违反了项目原则
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from knowledge_management_system.api.service_interface import get_knowledge_service
import json

def remove_hardcoded_facts():
    """删除硬编码的历史事实"""
    print("=" * 80)
    print("删除硬编码的历史事实")
    print("=" * 80)
    
    # 初始化知识服务
    print("\n1. 初始化知识服务...")
    try:
        service = get_knowledge_service()
        print("✅ 知识服务初始化成功")
    except Exception as e:
        print(f"❌ 知识服务初始化失败: {e}")
        return
    
    # 硬编码事实的ID（从之前的添加结果中获取）
    hardcoded_ids = [
        "720aec7b-fa82-4652-8773-6d78054f7e7d",
        "39e9135b-0fa3-45cc-8ec8-ba09a91d849c",
        "d59d8759-d342-44ac-8b77-4919149de20f",
        "e8cc7370-5081-46f9-8c26-a176c62110a3",
        "04293969-b092-422d-b16b-c20efa9fa37f"
    ]
    
    # 硬编码事实的关键词（用于查找）
    hardcoded_keywords = [
        "Harriet Lane was the niece of President James Buchanan and served as First Lady",
        "Harriet Lane's mother was Jane Ann Lane (née Buchanan)",
        "Jane Ann Lane was the mother of Harriet Lane, the 15th First Lady",
        "The second assassinated U.S. President was James A. Garfield",
        "James A. Garfield's mother was Eliza Ballou Garfield",
        "Ballou is the maiden name of Eliza Ballou Garfield",
        "Eliza Ballou was the mother of James A. Garfield",
        "James Buchanan was the 15th President of the United States, serving from 1857 to 1861"
    ]
    
    print(f"\n2. 查找硬编码的历史事实...")
    
    # 通过metadata查找
    metadata_storage = service.metadata_storage
    all_entries = metadata_storage._metadata.get('entries', {})
    
    found_ids = []
    for knowledge_id, entry in all_entries.items():
        content = entry.get('content', '')
        metadata = entry.get('metadata', {})
        
        # 检查是否是硬编码的事实
        is_hardcoded = False
        
        # 检查metadata中的标记
        if metadata.get('type') in ['historical_fact', 'family_relation']:
            if metadata.get('category') == 'US_history':
                # 检查是否包含硬编码关键词
                for keyword in hardcoded_keywords:
                    if keyword.lower() in content.lower():
                        is_hardcoded = True
                        break
        
        # 检查内容是否匹配硬编码模式
        if not is_hardcoded:
            for keyword in hardcoded_keywords:
                if keyword.lower() in content.lower():
                    is_hardcoded = True
                    break
        
        if is_hardcoded:
            found_ids.append(knowledge_id)
            print(f"  找到硬编码事实: {knowledge_id}")
            print(f"    内容: {content[:100]}...")
    
    # 也检查已知的ID
    for knowledge_id in hardcoded_ids:
        if knowledge_id in all_entries:
            if knowledge_id not in found_ids:
                found_ids.append(knowledge_id)
                print(f"  找到已知ID的硬编码事实: {knowledge_id}")
    
    if not found_ids:
        print("  ✅ 未找到硬编码的历史事实（可能已经被删除）")
        return
    
    print(f"\n3. 删除 {len(found_ids)} 条硬编码事实...")
    
    deleted_count = 0
    failed_count = 0
    
    for knowledge_id in found_ids:
        try:
            # 使用knowledge_manager删除
            if hasattr(service, 'knowledge_manager'):
                success = service.knowledge_manager.delete_knowledge(knowledge_id)
                if success:
                    print(f"  ✅ 删除成功: {knowledge_id}")
                    deleted_count += 1
                else:
                    print(f"  ❌ 删除失败: {knowledge_id}")
                    failed_count += 1
            else:
                # 直接操作metadata_storage
                if knowledge_id in all_entries:
                    del all_entries[knowledge_id]
                    metadata_storage._save_metadata()
                    print(f"  ✅ 删除成功: {knowledge_id}")
                    deleted_count += 1
                else:
                    print(f"  ⚠️  条目不存在: {knowledge_id}")
        except Exception as e:
            print(f"  ❌ 删除失败: {knowledge_id} - {e}")
            failed_count += 1
    
    # 总结
    print("\n" + "=" * 80)
    print("删除完成")
    print("=" * 80)
    print(f"成功删除: {deleted_count}/{len(found_ids)}")
    print(f"失败: {failed_count}/{len(found_ids)}")
    
    if deleted_count > 0:
        print("\n✅ 硬编码的历史事实已删除")
        print("💡 系统现在应该依赖动态检索，而不是硬编码的事实")

if __name__ == "__main__":
    remove_hardcoded_facts()

