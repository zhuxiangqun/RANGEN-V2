#!/usr/bin/env python3
"""
测试实体名称规范化功能
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from knowledge_management_system.graph.entity_normalizer import normalize_entity_name

def test_normalization():
    """测试规范化功能"""
    print("=" * 80)
    print("测试实体名称规范化功能")
    print("=" * 80)
    print()
    
    test_cases = [
        # (原始名称, 实体类型, 预期结果)
        # 基本清理
        ("  John  Adams  ", "Person", "John Adams"),
        ("john adams", "Person", "John Adams"),
        ("JOHN ADAMS", "Person", "John Adams"),
        
        # 人名测试
        ("john a. smith", "Person", "John A. Smith"),
        ("mary o'brien", "Person", "Mary O'Brien"),
        ("john smith jr.", "Person", "John Smith Junior"),
        ("john smith sr", "Person", "John Smith Senior"),
        
        # 地名测试
        ("new york", "Location", "New York"),
        ("united states", "Location", "United States"),
        ("u.s.", "Location", "United States"),
        ("usa", "Location", "United States"),
        ("united kingdom", "Location", "United Kingdom"),
        ("uk", "Location", "United Kingdom"),
        
        # 组织名测试
        ("microsoft corp.", "Organization", "Microsoft Corporation"),
        ("apple inc", "Organization", "Apple Incorporated"),
        ("google llc", "Organization", "Google Llc"),
        
        # 标点符号清理
        ("John, Adams", "Person", "John Adams"),
        ("John. Adams", "Person", "John Adams"),
        ("John-Adams", "Person", "John-Adams"),  # 保留连字符
        ("O'Brien", "Person", "O'Brien"),  # 保留撇号
        
        # 复杂情况
        ("john  a.  smith  jr.", "Person", "John A. Smith Junior"),
        ("new  york  city", "Location", "New York City"),
        ("united  states  of  america", "Location", "United States of America"),
    ]
    
    print("📋 测试用例:")
    print("-" * 80)
    
    passed = 0
    failed = 0
    
    for original, entity_type, expected in test_cases:
        result = normalize_entity_name(original, entity_type)
        status = "✅" if result == expected else "❌"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} 类型: {entity_type:12} | 原始: {original:30} | 结果: {result:30} | 预期: {expected}")
        if result != expected:
            print(f"   ⚠️  不匹配！")
    
    print()
    print("=" * 80)
    print(f"测试结果: 通过 {passed}/{len(test_cases)}, 失败 {failed}/{len(test_cases)}")
    print("=" * 80)
    
    return failed == 0

if __name__ == "__main__":
    success = test_normalization()
    sys.exit(0 if success else 1)

