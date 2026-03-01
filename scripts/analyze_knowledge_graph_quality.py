#!/usr/bin/env python3
"""
分析知识图谱内容质量
检查实体、关系的完整性、准确性和连通性
"""

import sys
import json
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Any, Set

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def analyze_entities(entities: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """分析实体质量"""
    stats = {
        'total': len(entities),
        'by_type': Counter(),
        'with_properties': 0,
        'empty_properties': 0,
        'empty_name': 0,
        'duplicate_names': 0,
        'name_length_stats': {'min': float('inf'), 'max': 0, 'avg': 0},
        'issues': []
    }
    
    name_counts = Counter()
    total_name_length = 0
    
    for entity_id, entity in entities.items():
        # 统计类型
        entity_type = entity.get('type', 'Unknown')
        stats['by_type'][entity_type] += 1
        
        # 检查名称
        name = entity.get('name', '')
        if not name or not name.strip():
            stats['empty_name'] += 1
            stats['issues'].append(f"实体 {entity_id}: 名称为空")
        else:
            name_counts[name] += 1
            name_length = len(name)
            total_name_length += name_length
            stats['name_length_stats']['min'] = min(stats['name_length_stats']['min'], name_length)
            stats['name_length_stats']['max'] = max(stats['name_length_stats']['max'], name_length)
        
        # 检查属性
        properties = entity.get('properties', {})
        if properties:
            stats['with_properties'] += 1
            if not properties or len(properties) == 0:
                stats['empty_properties'] += 1
        else:
            stats['empty_properties'] += 1
    
    # 统计重复名称
    stats['duplicate_names'] = sum(1 for count in name_counts.values() if count > 1)
    
    # 计算平均名称长度
    if stats['total'] > 0:
        stats['name_length_stats']['avg'] = total_name_length / stats['total']
    
    # 处理inf值
    if stats['name_length_stats']['min'] == float('inf'):
        stats['name_length_stats']['min'] = 0
    
    return stats


def analyze_relations(relations: List[Dict[str, Any]], entities: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """分析关系质量"""
    stats = {
        'total': len(relations),
        'by_type': Counter(),
        'confidence_stats': {'min': float('inf'), 'max': 0, 'avg': 0, 'distribution': Counter()},
        'missing_entity1': 0,
        'missing_entity2': 0,
        'self_relations': 0,
        'duplicate_relations': 0,
        'with_properties': 0,
        'empty_properties': 0,
        'issues': []
    }
    
    entity_ids = set(entities.keys())
    relation_set = set()
    total_confidence = 0
    confidence_count = 0
    
    for relation in relations:
        # 统计类型
        relation_type = relation.get('type', 'Unknown')
        stats['by_type'][relation_type] += 1
        
        # 检查实体是否存在
        entity1_id = relation.get('entity1_id', '')
        entity2_id = relation.get('entity2_id', '')
        
        if not entity1_id or entity1_id not in entity_ids:
            stats['missing_entity1'] += 1
            stats['issues'].append(f"关系 {relation.get('id', 'unknown')}: 实体1不存在 ({entity1_id})")
        
        if not entity2_id or entity2_id not in entity_ids:
            stats['missing_entity2'] += 1
            stats['issues'].append(f"关系 {relation.get('id', 'unknown')}: 实体2不存在 ({entity2_id})")
        
        # 检查自环
        if entity1_id == entity2_id:
            stats['self_relations'] += 1
        
        # 检查重复关系
        relation_key = (entity1_id, relation_type, entity2_id)
        if relation_key in relation_set:
            stats['duplicate_relations'] += 1
        else:
            relation_set.add(relation_key)
        
        # 检查属性
        properties = relation.get('properties', {})
        if properties and len(properties) > 0:
            stats['with_properties'] += 1
        else:
            stats['empty_properties'] += 1
        
        # 统计置信度
        confidence = relation.get('confidence', 1.0)
        if confidence is not None:
            total_confidence += confidence
            confidence_count += 1
            stats['confidence_stats']['min'] = min(stats['confidence_stats']['min'], confidence)
            stats['confidence_stats']['max'] = max(stats['confidence_stats']['max'], confidence)
            
            # 置信度分布
            if confidence >= 0.9:
                stats['confidence_stats']['distribution']['high (≥0.9)'] += 1
            elif confidence >= 0.7:
                stats['confidence_stats']['distribution']['medium (0.7-0.9)'] += 1
            elif confidence >= 0.5:
                stats['confidence_stats']['distribution']['low (0.5-0.7)'] += 1
            else:
                stats['confidence_stats']['distribution']['very_low (<0.5)'] += 1
    
    # 计算平均置信度
    if confidence_count > 0:
        stats['confidence_stats']['avg'] = total_confidence / confidence_count
    
    # 处理inf值
    if stats['confidence_stats']['min'] == float('inf'):
        stats['confidence_stats']['min'] = 0
    
    return stats


def analyze_connectivity(entities: Dict[str, Dict[str, Any]], relations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """分析图谱连通性"""
    stats = {
        'connected_entities': 0,
        'isolated_entities': 0,
        'isolated_entity_list': [],
        'max_degree': 0,
        'avg_degree': 0,
        'components': 0,
        'largest_component_size': 0
    }
    
    # 构建邻接表
    entity_degrees = defaultdict(int)
    entity_connections = defaultdict(set)
    
    entity_ids = set(entities.keys())
    
    for relation in relations:
        entity1_id = relation.get('entity1_id', '')
        entity2_id = relation.get('entity2_id', '')
        
        if entity1_id in entity_ids and entity2_id in entity_ids:
            entity_degrees[entity1_id] += 1
            entity_degrees[entity2_id] += 1
            entity_connections[entity1_id].add(entity2_id)
            entity_connections[entity2_id].add(entity1_id)
    
    # 统计连通实体和孤立实体
    for entity_id in entity_ids:
        if entity_id in entity_degrees and entity_degrees[entity_id] > 0:
            stats['connected_entities'] += 1
        else:
            stats['isolated_entities'] += 1
            entity_name = entities[entity_id].get('name', entity_id)
            stats['isolated_entity_list'].append(entity_name)
    
    # 计算度统计
    if entity_degrees:
        stats['max_degree'] = max(entity_degrees.values())
        stats['avg_degree'] = sum(entity_degrees.values()) / len(entity_degrees)
    
    # 计算连通分量（简化版，使用DFS）
    visited = set()
    
    def dfs(entity_id: str, component: Set[str]):
        if entity_id in visited:
            return
        visited.add(entity_id)
        component.add(entity_id)
        for neighbor in entity_connections.get(entity_id, set()):
            if neighbor not in visited:
                dfs(neighbor, component)
    
    components = []
    for entity_id in entity_ids:
        if entity_id not in visited:
            component = set()
            dfs(entity_id, component)
            if component:
                components.append(component)
    
    stats['components'] = len(components)
    if components:
        stats['largest_component_size'] = max(len(c) for c in components)
    
    return stats


def analyze_knowledge_graph_quality():
    """分析知识图谱内容质量"""
    print("=" * 80)
    print("知识图谱内容质量分析")
    print("=" * 80)
    print()
    
    # 文件路径
    entities_file = Path("data/knowledge_management/graph/entities.json")
    relations_file = Path("data/knowledge_management/graph/relations.json")
    
    # 检查文件是否存在
    if not entities_file.exists():
        print(f"❌ 实体文件不存在: {entities_file}")
        print("   💡 提示: 知识图谱可能尚未构建")
        return
    
    if not relations_file.exists():
        print(f"❌ 关系文件不存在: {relations_file}")
        print("   💡 提示: 知识图谱可能尚未构建")
        return
    
    # 加载数据
    try:
        with open(entities_file, 'r', encoding='utf-8') as f:
            entities = json.load(f)
        print(f"✅ 已加载 {len(entities)} 个实体")
    except Exception as e:
        print(f"❌ 加载实体文件失败: {e}")
        return
    
    try:
        with open(relations_file, 'r', encoding='utf-8') as f:
            relations = json.load(f)
        print(f"✅ 已加载 {len(relations)} 条关系")
    except Exception as e:
        print(f"❌ 加载关系文件失败: {e}")
        return
    
    print()
    print("-" * 80)
    print("1. 实体质量分析")
    print("-" * 80)
    
    entity_stats = analyze_entities(entities)
    
    print(f"📊 实体总数: {entity_stats['total']}")
    print()
    
    if entity_stats['total'] > 0:
        print("📋 实体类型分布:")
        for entity_type, count in entity_stats['by_type'].most_common(10):
            percentage = (count / entity_stats['total'] * 100)
            print(f"   - {entity_type}: {count} ({percentage:.1f}%)")
        print()
        
        print("📋 实体属性统计:")
        with_props_pct = entity_stats['with_properties'] / entity_stats['total'] * 100
        empty_props_pct = entity_stats['empty_properties'] / entity_stats['total'] * 100
        print(f"   - 有属性的实体: {entity_stats['with_properties']} ({with_props_pct:.1f}%)")
        print(f"   - 无属性的实体: {entity_stats['empty_properties']} ({empty_props_pct:.1f}%)")
        print()
        
        print("📋 实体名称统计:")
        name_stats = entity_stats['name_length_stats']
        print(f"   - 平均长度: {name_stats['avg']:.1f} 字符")
        print(f"   - 最短: {name_stats['min']} 字符")
        print(f"   - 最长: {name_stats['max']} 字符")
        print(f"   - 空名称: {entity_stats['empty_name']}")
        print(f"   - 重复名称: {entity_stats['duplicate_names']}")
        print()
        
        if entity_stats['issues']:
            print(f"⚠️  发现问题: {len(entity_stats['issues'])} 个")
            for issue in entity_stats['issues'][:10]:  # 只显示前10个
                print(f"   - {issue}")
            if len(entity_stats['issues']) > 10:
                print(f"   ... 还有 {len(entity_stats['issues']) - 10} 个问题未显示")
            print()
    
    print("-" * 80)
    print("2. 关系质量分析")
    print("-" * 80)
    
    relation_stats = analyze_relations(relations, entities)
    
    print(f"📊 关系总数: {relation_stats['total']}")
    print()
    
    if relation_stats['total'] > 0:
        print("📋 关系类型分布:")
        for relation_type, count in relation_stats['by_type'].most_common(10):
            percentage = (count / relation_stats['total'] * 100)
            print(f"   - {relation_type}: {count} ({percentage:.1f}%)")
        print()
        
        print("📋 关系置信度统计:")
        conf_stats = relation_stats['confidence_stats']
        print(f"   - 平均置信度: {conf_stats['avg']:.3f}")
        print(f"   - 最低置信度: {conf_stats['min']:.3f}")
        print(f"   - 最高置信度: {conf_stats['max']:.3f}")
        print()
        print("   - 置信度分布:")
        for level, count in conf_stats['distribution'].items():
            percentage = (count / relation_stats['total'] * 100)
            print(f"     * {level}: {count} ({percentage:.1f}%)")
        print()
        
        print("📋 关系完整性检查:")
        print(f"   - 缺失实体1: {relation_stats['missing_entity1']}")
        print(f"   - 缺失实体2: {relation_stats['missing_entity2']}")
        print(f"   - 自环关系: {relation_stats['self_relations']}")
        print(f"   - 重复关系: {relation_stats['duplicate_relations']}")
        with_props_pct = relation_stats['with_properties'] / relation_stats['total'] * 100
        empty_props_pct = relation_stats['empty_properties'] / relation_stats['total'] * 100
        print(f"   - 有属性的关系: {relation_stats['with_properties']} ({with_props_pct:.1f}%)")
        print(f"   - 无属性的关系: {relation_stats['empty_properties']} ({empty_props_pct:.1f}%)")
        print()
        
        if relation_stats['issues']:
            print(f"⚠️  发现问题: {len(relation_stats['issues'])} 个")
            for issue in relation_stats['issues'][:10]:  # 只显示前10个
                print(f"   - {issue}")
            if len(relation_stats['issues']) > 10:
                print(f"   ... 还有 {len(relation_stats['issues']) - 10} 个问题未显示")
            print()
    
    print("-" * 80)
    print("3. 图谱连通性分析")
    print("-" * 80)
    
    connectivity_stats = analyze_connectivity(entities, relations)
    
    if entity_stats['total'] > 0:
        connected_pct = connectivity_stats['connected_entities'] / entity_stats['total'] * 100
        isolated_pct = connectivity_stats['isolated_entities'] / entity_stats['total'] * 100
        print(f"📊 连通实体: {connectivity_stats['connected_entities']} ({connected_pct:.1f}%)")
        print(f"📊 孤立实体: {connectivity_stats['isolated_entities']} ({isolated_pct:.1f}%)")
    else:
        print(f"📊 连通实体: {connectivity_stats['connected_entities']} (N/A - 无实体)")
        print(f"📊 孤立实体: {connectivity_stats['isolated_entities']} (N/A - 无实体)")
    print()
    
    if connectivity_stats['isolated_entities'] > 0:
        print(f"⚠️  孤立实体列表（前20个）:")
        for entity_name in connectivity_stats['isolated_entity_list'][:20]:
            print(f"   - {entity_name}")
        if len(connectivity_stats['isolated_entity_list']) > 20:
            print(f"   ... 还有 {len(connectivity_stats['isolated_entity_list']) - 20} 个孤立实体")
        print()
    
    print("📋 度统计:")
    print(f"   - 平均度: {connectivity_stats['avg_degree']:.2f}")
    print(f"   - 最大度: {connectivity_stats['max_degree']}")
    print()
    
    print("📋 连通分量:")
    print(f"   - 连通分量数: {connectivity_stats['components']}")
    print(f"   - 最大连通分量大小: {connectivity_stats['largest_component_size']}")
    print()
    
    # 总结
    print("=" * 80)
    print("质量评估总结")
    print("=" * 80)
    
    # 检查知识图谱是否为空
    if entity_stats['total'] == 0 and relation_stats['total'] == 0:
        print("⚠️  知识图谱为空，无法进行质量分析")
        print("   💡 提示: 请先构建知识图谱")
        print()
        print("=" * 80)
        return
    
    total_issues = (
        entity_stats['empty_name'] +
        entity_stats['duplicate_names'] +
        relation_stats['missing_entity1'] +
        relation_stats['missing_entity2'] +
        relation_stats['duplicate_relations'] +
        connectivity_stats['isolated_entities']
    )
    
    if total_issues == 0:
        print("✅ 知识图谱质量良好，未发现明显问题")
    else:
        print(f"⚠️  发现 {total_issues} 个潜在问题:")
        if entity_stats['empty_name'] > 0:
            print(f"   - {entity_stats['empty_name']} 个实体名称为空")
        if entity_stats['duplicate_names'] > 0:
            print(f"   - {entity_stats['duplicate_names']} 个实体名称重复")
        if relation_stats['missing_entity1'] > 0:
            print(f"   - {relation_stats['missing_entity1']} 条关系缺失实体1")
        if relation_stats['missing_entity2'] > 0:
            print(f"   - {relation_stats['missing_entity2']} 条关系缺失实体2")
        if relation_stats['duplicate_relations'] > 0:
            print(f"   - {relation_stats['duplicate_relations']} 条重复关系")
        if connectivity_stats['isolated_entities'] > 0:
            print(f"   - {connectivity_stats['isolated_entities']} 个孤立实体")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    analyze_knowledge_graph_quality()

