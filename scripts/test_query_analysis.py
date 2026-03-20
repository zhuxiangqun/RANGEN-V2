#!/usr/bin/env python3
"""
分析Groundhog Day查询的特征
"""

def analyze_groundhog_query():
    """分析Groundhog Day查询的特征"""

    query = "How many years earlier would Punxsutawney Phil have to be canonically alive to have made a Groundhog Day prediction in the same state as the US capitol?"

    print("🔍 Groundhog Day查询特征分析")
    print("=" * 80)
    print(f"查询: {query}")
    print()

    # 长度检查
    length = len(query)
    print(f"📏 长度: {length} 字符")

    # 简单查询检测逻辑
    query_lower = query.lower().strip()

    # 简单的定义查询模式
    simple_definition_patterns = [
        '什么是', 'what is', 'define', '定义',
        '解释', 'explain', 'describe', '描述',
        '介绍', 'introduce', '简介'
    ]

    # 检查查询长度（太长的查询不简单）
    is_too_long = length > 50
    print(f"📏 长度检查: {'>50字符' if is_too_long else '<=50字符'} -> {'不简单' if is_too_long else '可能简单'}")

    # 检查是否包含简单定义关键词
    has_definition_pattern = any(pattern in query_lower for pattern in simple_definition_patterns)
    print(f"🔤 包含定义关键词: {has_definition_pattern}")

    # 检查是否包含复杂指标
    complex_indicators = ['比较', '对比', '分析', '如何', '为什么', '怎样', 'compare', 'analyze', 'how', 'why']
    has_complex_indicators = any(indicator in query_lower for indicator in complex_indicators)
    print(f"🔍 包含复杂指标: {has_complex_indicators}")

    # 最终判断
    is_simple_query = False

    if length <= 50:
        if has_definition_pattern:
            if not has_complex_indicators:
                is_simple_query = True

    print(f"\n🎯 最终判断: {'✅ 简单查询' if is_simple_query else '❌ 复杂查询'}")

    if not is_simple_query:
        print("\n📚 这个查询应该走RAG流程，需要从知识库检索：")
        print("   - Punxsutawney Phil的历史和位置")
        print("   - Groundhog Day传统的起源")
        print("   - 美国首都（Washington D.C.）的位置")
        print("   - 宾夕法尼亚州的历史")
        print("   - 年份计算和推理")

    return not is_simple_query

if __name__ == "__main__":
    analyze_groundhog_query()
