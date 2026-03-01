#!/usr/bin/env python3
"""
验证知识库内容质量
检查现有知识库中是否还有HTML标签、引用标记等残留
"""

import sys
from pathlib import Path
import re

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from knowledge_management_system.api.service_interface import get_knowledge_service

def verify_content_quality():
    """验证知识库内容质量"""
    print("=" * 80)
    print("验证知识库内容质量")
    print("=" * 80)
    
    service = get_knowledge_service()
    
    # 查询一些样本
    test_queries = [
        "first lady",
        "president",
        "building",
        "country",
        "year"
    ]
    
    total_checked = 0
    issues_found = {
        'html_tags': 0,
        'reference_markers': 0,
        'json_attrs': 0,
        'total_issues': 0
    }
    
    print("\n检查知识库内容...")
    print("-" * 80)
    
    for query in test_queries:
        print(f"\n查询: {query}")
        try:
            results = service.query_knowledge(
                query=query,
                top_k=5,
                similarity_threshold=0.0  # 获取所有结果
            )
            
            for i, result in enumerate(results, 1):
                content = result.get('content', '')
                if not content:
                    continue
                
                total_checked += 1
                
                # 检查HTML标签
                has_html_tags = '<' in content and '>' in content
                if has_html_tags:
                    issues_found['html_tags'] += 1
                    issues_found['total_issues'] += 1
                    print(f"  ⚠️  结果 {i}: 发现HTML标签残留")
                
                # 检查引用标记
                has_reference_markers = bool(re.search(r'\[\s*\d+\s*\]', content))
                if has_reference_markers:
                    issues_found['reference_markers'] += 1
                    issues_found['total_issues'] += 1
                    print(f"  ⚠️  结果 {i}: 发现引用标记残留")
                
                # 检查JSON属性
                has_json_attrs = bool(re.search(r'["\']?\}\}[^"\']*["\']?', content)) or bool(re.search(r'\s*id=["\'][^"\']*["\']', content))
                if has_json_attrs:
                    issues_found['json_attrs'] += 1
                    issues_found['total_issues'] += 1
                    print(f"  ⚠️  结果 {i}: 发现JSON属性残留")
        
        except Exception as e:
            print(f"  ❌ 查询失败: {e}")
    
    print("\n" + "=" * 80)
    print("验证结果统计")
    print("=" * 80)
    print(f"检查的内容条目数: {total_checked}")
    print(f"发现的问题总数: {issues_found['total_issues']}")
    print(f"  - HTML标签残留: {issues_found['html_tags']}")
    print(f"  - 引用标记残留: {issues_found['reference_markers']}")
    print(f"  - JSON属性残留: {issues_found['json_attrs']}")
    
    if issues_found['total_issues'] == 0:
        print("\n✅ 所有检查的内容都没有发现问题！")
    else:
        issue_rate = (issues_found['total_issues'] / total_checked * 100) if total_checked > 0 else 0
        print(f"\n⚠️  发现问题率: {issue_rate:.1f}%")
        print("建议: 重新导入知识库以应用改进的清理逻辑")
    
    print("=" * 80)

if __name__ == "__main__":
    verify_content_quality()

