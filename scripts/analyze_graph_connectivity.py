#!/usr/bin/env python3
"""
分析知识图谱连通性
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from knowledge_management_system.api.service_interface import get_knowledge_service
from knowledge_management_system.graph.connectivity_optimizer import ConnectivityOptimizer

def analyze_connectivity():
    """分析图谱连通性"""
    print("=" * 80)
    print("知识图谱连通性分析")
    print("=" * 80)
    print()
    
    service = get_knowledge_service()
    
    optimizer = ConnectivityOptimizer(
        service.graph_builder.entity_manager,
        service.graph_builder.relation_manager
    )
    
    # 分析连通性
    connectivity = optimizer.analyze_connectivity()
    
    print("📊 连通性统计:")
    print("-" * 80)
    print(f"  总实体数: {connectivity['total_entities']}")
    print(f"  总关系数: {connectivity['total_relations']}")
    print(f"  连通分量数: {connectivity['connected_components']}")
    print(f"  最大连通分量大小: {connectivity['largest_component_size']}")
    print(f"  孤立实体数: {connectivity['isolated_entities']}")
    print(f"  平均度: {connectivity['average_degree']:.2f}")
    print(f"  最大度: {connectivity['max_degree']}")
    print()
    
    # 连通分量大小分布
    component_sizes = [len(c) for c in connectivity['components']]
    if component_sizes:
        print("📋 连通分量大小分布:")
        print("-" * 80)
        size_distribution = {}
        for size in component_sizes:
            size_distribution[size] = size_distribution.get(size, 0) + 1
        
        for size in sorted(size_distribution.keys())[:10]:
            count = size_distribution[size]
            print(f"  大小 {size:4d}: {count:4d} 个分量")
        print()
    
    # 建议关系
    print("💡 连通性改进建议:")
    print("-" * 80)
    suggestions = optimizer.suggest_relations_for_connectivity(max_suggestions=10)
    if suggestions:
        print(f"  建议添加 {len(suggestions)} 条关系来改善连通性:")
        for i, suggestion in enumerate(suggestions[:5], 1):
            print(f"    {i}. {suggestion['entity1_name']} -> {suggestion['suggested_relation']} -> {suggestion['entity2_name']} (原因: {suggestion['reason']})")
    else:
        print("  暂无改进建议")
    print()
    
    # 评估
    print("📊 连通性评估:")
    print("-" * 80)
    if connectivity['connected_components'] <= 100:
        print("  ✅ 连通性良好（连通分量数 <= 100）")
    elif connectivity['connected_components'] <= 1000:
        print("  ⚠️  连通性一般（连通分量数 100-1000）")
    else:
        print("  ❌ 连通性较差（连通分量数 > 1000）")
    
    if connectivity['average_degree'] >= 2.0:
        print("  ✅ 平均度良好（>= 2.0）")
    elif connectivity['average_degree'] >= 1.5:
        print("  ⚠️  平均度一般（1.5-2.0）")
    else:
        print("  ❌ 平均度较低（< 1.5）")
    
    if connectivity['isolated_entities'] == 0:
        print("  ✅ 无孤立实体")
    else:
        print(f"  ⚠️  有 {connectivity['isolated_entities']} 个孤立实体")
    
    print()

if __name__ == "__main__":
    try:
        analyze_connectivity()
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

