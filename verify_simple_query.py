#!/usr/bin/env python3
"""
验证简单查询检测逻辑
"""

def test_simple_query_logic():
    """测试简单查询检测逻辑"""

    def is_ultra_simple_query(query: str, query_type: str) -> bool:
        """检查是否是极简单的查询，可以直接回答"""
        query_lower = query.lower().strip()

        # 简单的定义查询
        simple_definition_patterns = [
            '什么是', 'what is', 'define', '定义',
            '解释', 'explain', 'describe', '描述',
            '介绍', 'introduce', '简介'
        ]

        # 检查查询长度（太长的查询不简单）
        if len(query) > 50:
            return False

        # 检查是否包含简单定义关键词
        for pattern in simple_definition_patterns:
            if pattern in query_lower:
                # 确保不是复杂查询（不包含比较、分析等词）
                complex_indicators = ['比较', '对比', '分析', '如何', '为什么', '怎样', 'compare', 'analyze', 'how', 'why']
                if not any(indicator in query_lower for indicator in complex_indicators):
                    return True

        return False

    # 测试用例
    test_cases = [
        ("什么是RAG？", True),
        ("什么是人工智能？", True),
        ("解释一下机器学习", True),
        ("RAG的优势是什么？", False),  # 包含"是什么"但也包含复杂词
        ("如何使用RAG？", False),  # 包含复杂词"如何"
        ("比较RAG和传统方法", False),  # 包含复杂词"比较"
        ("这是一个很长的查询用来测试长度限制是否工作正常", False),  # 太长
    ]

    print("🧪 简单查询检测测试:")
    for query, expected in test_cases:
        result = is_ultra_simple_query(query, "definition")
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{query}' -> {result} (期望: {expected})")

    # 特别测试超时问题中的查询
    print("\n🎯 测试超时问题中的查询:")
    problematic_queries = [
        "什么是RAG？",
        "RAG的优势是什么？"
    ]

    for query in problematic_queries:
        result = is_ultra_simple_query(query, "definition")
        print(f"  '{query}' -> {'✅ 会被简化处理' if result else '❌ 会走复杂推理'}")

if __name__ == "__main__":
    test_simple_query_logic()
