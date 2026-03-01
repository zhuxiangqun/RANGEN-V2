#!/usr/bin/env python3
"""
测试智能领域关键词生成功能
"""

from src.utils.domain_manager import get_domain_manager

def test_smart_domain_generation():
    """测试智能领域生成"""
    print("🔬 测试智能领域关键词生成功能")
    print("=" * 50)
    
    # 获取领域管理器
    manager = get_domain_manager()
    
    # 测试查询
    test_queries = [
        "What is machine learning and how does it work?",
        "Tell me about the history of artificial intelligence",
        "How do chemical reactions work in the laboratory?",
        "Who won the Nobel Prize in Physics this year?",
        "What are the rules of professional basketball?",
        "How to compose music using modern techniques?",
        "What is the best algorithm for data compression?",
        "How does climate change affect global weather patterns?",
        "What are the principles of quantum physics?",
        "How to start a successful business venture?"
    ]
    
    print(f"📊 测试查询数量: {len(test_queries)}")
    print("📝 示例查询:")
    for i, query in enumerate(test_queries[:3], 1):
        print(f"   {i}. {query}")
    print("   ...")
    
    # 智能生成领域关键词
    print("\\n🤖 正在智能生成领域关键词...")
    smart_domains = manager.generate_domain_keywords_from_queries(test_queries)
    
    print(f"✅ 智能生成了 {len(smart_domains)} 个领域:")
    
    for domain_name, domain_config in smart_domains.items():
        core_count = len(domain_config.get('core_keywords', []))
        extended_count = len(domain_config.get('extended_keywords', []))
        total_count = core_count + extended_count
        
        print(f"\\n📚 领域: {domain_name}")
        print(f"   核心关键词 ({core_count}): {domain_config.get('core_keywords', [])[:3]}")
        print(f"   扩展关键词 ({extended_count}): {domain_config.get('extended_keywords', [])[:3]}")
        print(f"   总计关键词: {total_count}")
        print(f"   生成方式: {domain_config.get('generated_by', 'unknown')}")
        print(f"   置信度: {domain_config.get('confidence', 0):.2f}")
    
    # 合并到现有系统
    print("\\n🔄 合并智能领域到现有系统...")
    new_count = manager.merge_smart_domains(smart_domains)
    print(f"✅ 新增领域数量: {new_count}")
    
    # 显示领域统计
    print("\\n📊 领域统计信息:")
    stats = manager.get_domain_statistics()
    print(f"   总领域数: {stats['total_domains']}")
    print(f"   总关键词数: {stats['total_keywords']}")
    
    if stats.get('keyword_distribution'):
        dist = stats['keyword_distribution']
        print(f"   关键词分布: 平均 {dist['average']:.1f}, 最大 {dist['max']}, 最小 {dist['min']}")

if __name__ == "__main__":
    test_smart_domain_generation()
