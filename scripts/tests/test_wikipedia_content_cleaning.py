#!/usr/bin/env python3
"""
测试Wikipedia内容清理功能
验证改进后的HTML清理逻辑是否正常工作
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from knowledge_management_system.utils.wikipedia_fetcher import WikipediaFetcher
import re

def test_html_cleaning():
    """测试HTML清理功能"""
    print("=" * 80)
    print("测试Wikipedia内容清理功能")
    print("=" * 80)
    
    fetcher = WikipediaFetcher()
    
    # 测试用例1: 包含HTML标签和引用标记的内容
    test_html_1 = """
    <html>
    <body>
    <p>Jacqueline "Jackie" Kennedy <sup id="mwBXM">[1]</sup> (aged 64)"}},"i":0}}]}' id="mwBXM">July 28, 1929 – May 19, 1994 (aged 64)  [ 82 ]  [ 83 ]  January 20, 1961 – November 22, 1963</p>
    <script>alert('test');</script>
    <style>.test { color: red; }</style>
    </body>
    </html>
    """
    
    print("\n【测试用例1】包含HTML标签和引用标记的内容")
    print("-" * 80)
    print("原始内容（前200字符）:")
    print(test_html_1[:200])
    print()
    
    cleaned_1 = fetcher._extract_text_from_html(test_html_1)
    print("清理后内容:")
    print(cleaned_1)
    print()
    
    # 验证清理效果
    has_html_tags = '<' in cleaned_1 and '>' in cleaned_1
    has_reference_markers = bool(re.search(r'\[\s*\d+\s*\]', cleaned_1))
    has_script = 'script' in cleaned_1.lower()
    has_style = 'style' in cleaned_1.lower()
    has_json_attrs = 'mwBXM' in cleaned_1 or '"}},"i":0}}]}' in cleaned_1
    
    print("验证结果:")
    print(f"  - 是否还有HTML标签: {'❌ 是' if has_html_tags else '✅ 否'}")
    print(f"  - 是否还有引用标记: {'❌ 是' if has_reference_markers else '✅ 否'}")
    print(f"  - 是否还有script标签: {'❌ 是' if has_script else '✅ 否'}")
    print(f"  - 是否还有style标签: {'❌ 是' if has_style else '✅ 否'}")
    print(f"  - 是否还有JSON属性: {'❌ 是' if has_json_attrs else '✅ 否'}")
    
    if not (has_html_tags or has_reference_markers or has_script or has_style or has_json_attrs):
        print("\n✅ 测试用例1通过：所有HTML标签、引用标记和JSON属性都已清理")
    else:
        print("\n❌ 测试用例1失败：仍有未清理的内容")
    
    # 测试用例2: 包含引用标记的文本
    test_html_2 = """
    <p>This is a test paragraph with references [ 82 ]  [ 83 ] and more text.</p>
    <p>Another paragraph with [ 1 ] reference.</p>
    """
    
    print("\n【测试用例2】包含引用标记的文本")
    print("-" * 80)
    print("原始内容:")
    print(test_html_2)
    print()
    
    cleaned_2 = fetcher._extract_text_from_html(test_html_2)
    print("清理后内容:")
    print(cleaned_2)
    print()
    
    has_reference_markers_2 = bool(re.search(r'\[\s*\d+\s*\]', cleaned_2))
    print(f"验证结果: 是否还有引用标记: {'❌ 是' if has_reference_markers_2 else '✅ 否'}")
    
    if not has_reference_markers_2:
        print("\n✅ 测试用例2通过：引用标记已清理")
    else:
        print("\n❌ 测试用例2失败：仍有引用标记")
    
    # 测试用例3: 长文本截断
    long_text = "A" * 150000  # 150000字符
    test_html_3 = f"<p>{long_text}</p>"
    
    print("\n【测试用例3】长文本截断测试")
    print("-" * 80)
    print(f"原始内容长度: {len(long_text)} 字符")
    
    cleaned_3 = fetcher._extract_text_from_html(test_html_3)
    print(f"清理后内容长度: {len(cleaned_3)} 字符")
    
    if len(cleaned_3) <= 100000:
        print("\n✅ 测试用例3通过：长文本已正确截断")
    else:
        print(f"\n❌ 测试用例3失败：文本长度 {len(cleaned_3)} 超过限制 100000")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

if __name__ == "__main__":
    test_html_cleaning()

