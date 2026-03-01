#!/usr/bin/env python3
"""
测试实体和关系属性提取功能
验证修复后的属性提取是否正常工作
"""

import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from knowledge_management_system.api.service_interface import get_knowledge_service
from knowledge_management_system.utils.logger import get_logger

logger = get_logger()

def test_properties_extraction():
    """测试属性提取功能"""
    print("=" * 80)
    print("测试实体和关系属性提取功能")
    print("=" * 80)
    print()
    
    service = get_knowledge_service()
    
    # 测试文本：包含明确的属性信息
    test_texts = [
        {
            "text": """
            John Adams was born on October 30, 1735, in Braintree, Massachusetts. 
            He was the second President of the United States, serving from 1797 to 1801.
            His mother was Jane Ballou, who was born in 1709.
            """,
            "expected_entities": ["John Adams", "Jane Ballou", "Braintree", "Massachusetts", "United States"],
            "expected_properties": {
                "John Adams": ["birth_date", "description"],
                "Jane Ballou": ["birth_date"]
            }
        },
        {
            "text": """
            Harvard University was founded in 1636 in Cambridge, Massachusetts.
            It is one of the oldest universities in the United States.
            """,
            "expected_entities": ["Harvard University", "Cambridge", "Massachusetts", "United States"],
            "expected_properties": {
                "Harvard University": ["founded_date", "location", "description"]
            }
        }
    ]
    
    print("📝 测试文本1: 人物信息")
    print("-" * 80)
    test_text = test_texts[0]["text"]
    print(test_text.strip())
    print()
    
    # 提取实体和关系
    print("🔍 提取实体和关系...")
    extracted_data = service._extract_entities_and_relations(test_text, None)
    
    if not extracted_data:
        print("❌ 未提取到任何数据")
        return False
    
    print(f"✅ 提取到 {len(extracted_data)} 条关系数据")
    print()
    
    # 检查属性
    print("📊 检查属性提取情况:")
    print("-" * 80)
    
    # 先打印完整的数据结构以便调试
    print("🔍 完整提取数据结构:")
    print(json.dumps(extracted_data[0] if extracted_data else {}, indent=2, ensure_ascii=False))
    print()
    
    has_properties = False
    entity_properties_found = {}
    
    for item in extracted_data:
        entity1 = item.get('entity1', '')
        entity2 = item.get('entity2', '')
        relation = item.get('relation', '')
        entity1_props = item.get('entity1_properties', {})
        entity2_props = item.get('entity2_properties', {})
        relation_props = item.get('relation_properties', {})
        
        print(f"  关系: {entity1} -> {relation} -> {entity2}")
        print(f"    实体1属性字段存在: {'entity1_properties' in item}")
        print(f"    实体2属性字段存在: {'entity2_properties' in item}")
        print(f"    关系属性字段存在: {'relation_properties' in item}")
        print(f"    实体1属性值: {entity1_props}")
        print(f"    实体2属性值: {entity2_props}")
        print(f"    关系属性值: {relation_props}")
        print()
        
        if entity1_props:
            has_properties = True
            if entity1 not in entity_properties_found:
                entity_properties_found[entity1] = entity1_props
            print(f"  ✅ 实体1 '{entity1}' 有属性: {entity1_props}")
        
        if entity2_props:
            has_properties = True
            if entity2 not in entity_properties_found:
                entity_properties_found[entity2] = entity2_props
            print(f"  ✅ 实体2 '{entity2}' 有属性: {entity2_props}")
        
        if relation_props:
            has_properties = True
            print(f"  ✅ 关系 '{entity1} -> {relation} -> {entity2}' 有属性: {relation_props}")
        
        if not entity1_props and not entity2_props and not relation_props:
            print(f"  ⚠️  关系 '{entity1} -> {relation} -> {entity2}' 无属性")
    
    print()
    
    if has_properties:
        print("✅ 测试通过：成功提取到属性")
        print()
        print("📋 提取到的实体属性:")
        for entity, props in entity_properties_found.items():
            print(f"  - {entity}: {props}")
        return True
    else:
        print("❌ 测试失败：未提取到任何属性")
        print()
        print("🔍 调试信息:")
        print(f"  提取的数据数量: {len(extracted_data)}")
        if extracted_data:
            print(f"  第一条数据示例: {json.dumps(extracted_data[0], indent=2, ensure_ascii=False)}")
        return False


def test_existing_graph_properties():
    """检查现有知识图谱中的属性情况"""
    print()
    print("=" * 80)
    print("检查现有知识图谱中的属性情况")
    print("=" * 80)
    print()
    
    service = get_knowledge_service()
    
    # 获取实体和关系
    entities = service.graph_builder.entity_manager.list_entities(limit=100)
    # 获取所有关系（通过实体管理器）
    all_relations = []
    for entity_id in list(service.graph_builder.entity_manager._entities.keys())[:100]:
        relations_for_entity = service.graph_builder.relation_manager.find_relations(entity_id=entity_id)
        all_relations.extend(relations_for_entity)
        if len(all_relations) >= 100:
            break
    relations = all_relations[:100]
    
    print(f"📊 检查前100个实体和前100条关系")
    print("-" * 80)
    
    # 统计实体属性
    entities_with_props = 0
    entities_without_props = 0
    sample_entities_with_props = []
    
    for entity in entities:
        props = entity.get('properties', {})
        if props and len(props) > 0:
            entities_with_props += 1
            if len(sample_entities_with_props) < 5:
                sample_entities_with_props.append({
                    'name': entity.get('name', ''),
                    'type': entity.get('type', ''),
                    'properties': props
                })
        else:
            entities_without_props += 1
    
    # 统计关系属性
    relations_with_props = 0
    relations_without_props = 0
    sample_relations_with_props = []
    
    for relation in relations:
        props = relation.get('properties', {})
        if props and len(props) > 0:
            relations_with_props += 1
            if len(sample_relations_with_props) < 5:
                sample_relations_with_props.append(relation)
        else:
            relations_without_props += 1
    
    print(f"📋 实体属性统计:")
    print(f"  有属性的实体: {entities_with_props} ({entities_with_props/(entities_with_props+entities_without_props)*100:.1f}%)")
    print(f"  无属性的实体: {entities_without_props} ({entities_without_props/(entities_with_props+entities_without_props)*100:.1f}%)")
    
    if sample_entities_with_props:
        print()
        print("  ✅ 示例实体（有属性）:")
        for entity in sample_entities_with_props:
            print(f"    - {entity['name']} ({entity['type']}): {entity['properties']}")
    
    print()
    print(f"📋 关系属性统计:")
    print(f"  有属性的关系: {relations_with_props} ({relations_with_props/(relations_with_props+relations_without_props)*100:.1f}%)")
    print(f"  无属性的关系: {relations_without_props} ({relations_without_props/(relations_with_props+relations_without_props)*100:.1f}%)")
    
    if sample_relations_with_props:
        print()
        print("  ✅ 示例关系（有属性）:")
        for relation in sample_relations_with_props:
            entity1_id = relation.get('entity1_id', '')
            entity2_id = relation.get('entity2_id', '')
            entity1 = service.graph_builder.entity_manager.get_entity(entity1_id)
            entity2 = service.graph_builder.entity_manager.get_entity(entity2_id)
            entity1_name = entity1.get('name', 'Unknown') if entity1 else 'Unknown'
            entity2_name = entity2.get('name', 'Unknown') if entity2 else 'Unknown'
            print(f"    - {entity1_name} -> {relation.get('type', '')} -> {entity2_name}: {relation.get('properties', {})}")
    
    print()
    
    if entities_with_props > 0 or relations_with_props > 0:
        print("✅ 现有知识图谱中包含属性")
        return True
    else:
        print("⚠️  现有知识图谱中无属性（需要重新构建）")
        return False


if __name__ == "__main__":
    try:
        # 测试1: 测试属性提取功能
        test1_result = test_properties_extraction()
        
        # 测试2: 检查现有知识图谱
        test2_result = test_existing_graph_properties()
        
        print()
        print("=" * 80)
        print("测试总结")
        print("=" * 80)
        print(f"属性提取功能测试: {'✅ 通过' if test1_result else '❌ 失败'}")
        print(f"现有知识图谱检查: {'✅ 有属性' if test2_result else '⚠️  无属性（需要重新构建）'}")
        print()
        
        if not test1_result:
            print("💡 建议:")
            print("  1. 检查LLM API是否正常工作")
            print("  2. 检查日志中的调试信息")
            print("  3. 确认prompt是否正确传递")
        
        if not test2_result:
            print("💡 建议:")
            print("  1. 重新构建知识图谱以应用修复")
            print("  2. 运行: ./build_knowledge_graph.sh")
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        print(f"❌ 测试失败: {e}")
        sys.exit(1)

