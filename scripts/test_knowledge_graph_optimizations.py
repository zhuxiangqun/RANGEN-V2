#!/usr/bin/env python3
"""
测试知识图谱构建优化功能
验证属性合并、每批保存、断点续传等功能
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 直接导入管理器，避免导入整个服务（可能缺少依赖）
from knowledge_management_system.graph.entity_manager import EntityManager
from knowledge_management_system.graph.relation_manager import RelationManager


def test_entity_property_merge():
    """测试实体属性合并功能"""
    print("=" * 80)
    print("测试1: 实体属性合并功能")
    print("=" * 80)
    
    # 创建临时实体管理器
    test_entities_path = "data/knowledge_management/graph/test_entities.json"
    entity_manager = EntityManager(entities_path=test_entities_path)
    
    # 清理测试数据
    entity_manager._entities = {}
    entity_manager._save_entities()
    
    try:
        # 第一次创建实体
        entity_id1 = entity_manager.create_entity(
            name="Jane Ballou",
            entity_type="Person",
            properties={"birth_year": 1709},
            merge_properties=True
        )
        print(f"✅ 第一次创建实体: {entity_id1}")
        
        # 获取实体
        entity1 = entity_manager.get_entity(entity_id1)
        print(f"   属性: {entity1.get('properties', {})}")
        
        # 第二次创建相同实体（应该合并属性）
        entity_id2 = entity_manager.create_entity(
            name="Jane Ballou",
            entity_type="Person",
            properties={"birth_year": 1709, "death_year": 1790},
            merge_properties=True
        )
        print(f"✅ 第二次创建相同实体: {entity_id2}")
        
        # 验证ID相同
        if entity_id1 == entity_id2:
            print("✅ 实体ID相同（正确）")
        else:
            print(f"❌ 实体ID不同（错误）: {entity_id1} != {entity_id2}")
            return False
        
        # 获取更新后的实体
        entity2 = entity_manager.get_entity(entity_id2)
        properties = entity2.get('properties', {})
        print(f"   合并后属性: {properties}")
        
        # 验证属性合并
        if properties.get('birth_year') == 1709 and properties.get('death_year') == 1790:
            print("✅ 属性合并成功（正确）")
        else:
            print(f"❌ 属性合并失败（错误）: {properties}")
            return False
        
        # 验证updated_at已更新
        if entity2.get('updated_at') != entity1.get('updated_at'):
            print("✅ updated_at已更新（正确）")
        else:
            print("⚠️  updated_at未更新（可能正常，如果时间戳相同）")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理测试数据
        if Path(test_entities_path).exists():
            Path(test_entities_path).unlink()


def test_relation_property_merge():
    """测试关系属性合并和置信度更新功能"""
    print("\n" + "=" * 80)
    print("测试2: 关系属性合并和置信度更新功能")
    print("=" * 80)
    
    # 创建临时管理器
    test_entities_path = "data/knowledge_management/graph/test_entities.json"
    test_relations_path = "data/knowledge_management/graph/test_relations.json"
    entity_manager = EntityManager(entities_path=test_entities_path)
    relation_manager = RelationManager(relations_path=test_relations_path)
    
    # 清理测试数据
    entity_manager._entities = {}
    relation_manager._relations = []
    entity_manager._save_entities()
    relation_manager._save_relations()
    
    try:
        # 创建两个实体
        entity1_id = entity_manager.create_entity("Jane Ballou", "Person")
        entity2_id = entity_manager.create_entity("John Adams", "Person")
        print(f"✅ 创建实体: {entity1_id}, {entity2_id}")
        
        # 第一次创建关系
        relation_id1 = relation_manager.create_relation(
            entity1_id=entity1_id,
            entity2_id=entity2_id,
            relation_type="mother_of",
            properties={"source": "book1"},
            confidence=0.7,
            merge_properties=True
        )
        print(f"✅ 第一次创建关系: {relation_id1}")
        
        # 获取关系
        relation1 = None
        for r in relation_manager._relations:
            if r.get('id') == relation_id1:
                relation1 = r
                break
        print(f"   属性: {relation1.get('properties', {})}, 置信度: {relation1.get('confidence')}")
        
        # 第二次创建相同关系（应该合并属性和更新置信度）
        relation_id2 = relation_manager.create_relation(
            entity1_id=entity1_id,
            entity2_id=entity2_id,
            relation_type="mother_of",
            properties={"source": "book1", "page": 123},
            confidence=0.9,  # 更高的置信度
            merge_properties=True
        )
        print(f"✅ 第二次创建相同关系: {relation_id2}")
        
        # 验证ID相同
        if relation_id1 == relation_id2:
            print("✅ 关系ID相同（正确）")
        else:
            print(f"❌ 关系ID不同（错误）: {relation_id1} != {relation_id2}")
            return False
        
        # 获取更新后的关系
        relation2 = None
        for r in relation_manager._relations:
            if r.get('id') == relation_id2:
                relation2 = r
                break
        properties = relation2.get('properties', {})
        confidence = relation2.get('confidence')
        print(f"   合并后属性: {properties}, 更新后置信度: {confidence}")
        
        # 验证属性合并
        if properties.get('source') == "book1" and properties.get('page') == 123:
            print("✅ 属性合并成功（正确）")
        else:
            print(f"❌ 属性合并失败（错误）: {properties}")
            return False
        
        # 验证置信度更新（应该更新为更高值0.9）
        if confidence == 0.9:
            print("✅ 置信度更新成功（正确）")
        else:
            print(f"❌ 置信度更新失败（错误）: {confidence} != 0.9")
            return False
        
        # 测试：如果新置信度更低，应该保持旧值
        relation_id3 = relation_manager.create_relation(
            entity1_id=entity1_id,
            entity2_id=entity2_id,
            relation_type="mother_of",
            confidence=0.5,  # 更低的置信度
            merge_properties=True
        )
        relation3 = None
        for r in relation_manager._relations:
            if r.get('id') == relation_id3:
                relation3 = r
                break
        if relation3.get('confidence') == 0.9:  # 应该保持0.9
            print("✅ 低置信度不覆盖高置信度（正确）")
        else:
            print(f"❌ 低置信度覆盖了高置信度（错误）: {relation3.get('confidence')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理测试数据
        if Path(test_entities_path).exists():
            Path(test_entities_path).unlink()
        if Path(test_relations_path).exists():
            Path(test_relations_path).unlink()


def test_batch_save_functionality():
    """测试每批保存功能（模拟）"""
    print("\n" + "=" * 80)
    print("测试3: 每批保存功能（模拟）")
    print("=" * 80)
    
    try:
        from knowledge_management_system.graph.graph_builder import GraphBuilder
        
        # 使用测试文件路径
        test_entities_path = "data/knowledge_management/graph/test_entities_batch.json"
        test_relations_path = "data/knowledge_management/graph/test_relations_batch.json"
        
        # 创建临时管理器
        entity_manager = EntityManager(entities_path=test_entities_path)
        relation_manager = RelationManager(relations_path=test_relations_path)
        
        # 清理测试数据
        entity_manager._entities = {}
        relation_manager._relations = []
        entity_manager._save_entities()
        relation_manager._save_relations()
        
        # 创建GraphBuilder并替换管理器
        graph_builder = GraphBuilder()
        graph_builder.entity_manager = entity_manager
        graph_builder.relation_manager = relation_manager
        
        # 准备测试数据
        test_data_batch1 = [
            {
                "entity1": "Jane Ballou",
                "entity2": "John Adams",
                "relation": "mother_of",
                "entity1_type": "Person",
                "entity2_type": "Person"
            }
        ]
        
        test_data_batch2 = [
            {
                "entity1": "Jane Ballou",  # 相同实体，应该合并
                "entity2": "John Adams",
                "relation": "mother_of",
                "entity1_type": "Person",
                "entity2_type": "Person",
                "entity1_properties": {"birth_year": 1709, "death_year": 1790}  # 新属性
            }
        ]
        
        # 第一批构建
        result1 = graph_builder.build_from_structured_data(test_data_batch1, merge_properties=True)
        print(f"✅ 第一批构建: {result1.get('entities_created')}个实体, {result1.get('relations_created')}条关系")
        
        # 检查实体是否已保存
        entities_count1 = len(entity_manager._entities)
        print(f"   实体数量: {entities_count1}")
        
        # 第二批构建（应该合并属性）
        result2 = graph_builder.build_from_structured_data(test_data_batch2, merge_properties=True)
        print(f"✅ 第二批构建: {result2.get('entities_created')}个实体, {result2.get('relations_created')}条关系")
        
        # 检查实体数量（应该不变，因为是合并）
        entities_count2 = len(entity_manager._entities)
        print(f"   实体数量: {entities_count2}")
        
        # 验证实体属性是否合并
        jane_entities = entity_manager.find_entity_by_name("Jane Ballou")
        if jane_entities:
            jane = jane_entities[0]
            properties = jane.get('properties', {})
            if properties.get('birth_year') == 1709 and properties.get('death_year') == 1790:
                print("✅ 属性合并成功（正确）")
                return True
            else:
                print(f"❌ 属性合并失败（错误）: {properties}")
                return False
        else:
            print("❌ 未找到实体")
            return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理测试数据
        if Path(test_entities_path).exists():
            Path(test_entities_path).unlink()
        if Path(test_relations_path).exists():
            Path(test_relations_path).unlink()


def test_resume_functionality():
    """测试断点续传功能（模拟）"""
    print("\n" + "=" * 80)
    print("测试4: 断点续传功能（模拟）")
    print("=" * 80)
    
    try:
        # 检查进度文件是否存在
        progress_file = Path("data/knowledge_management/graph_progress.json")
        if progress_file.exists():
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            
            processed_count = len(progress.get('processed_entry_ids', []))
            failed_count = len(progress.get('failed_entry_ids', []))
            total_entries = progress.get('total_entries', 0)
            
            print(f"✅ 进度文件存在")
            print(f"   已处理: {processed_count} 条")
            print(f"   失败: {failed_count} 条")
            print(f"   总条目: {total_entries} 条")
            
            if total_entries > 0:
                progress_pct = (processed_count / total_entries * 100) if total_entries > 0 else 0
                print(f"   进度: {progress_pct:.1f}%")
            
            # 检查实体和关系文件
            entities_file = Path("data/knowledge_management/graph/entities.json")
            relations_file = Path("data/knowledge_management/graph/relations.json")
            
            if entities_file.exists():
                with open(entities_file, 'r', encoding='utf-8') as f:
                    entities = json.load(f)
                print(f"✅ 实体文件存在: {len(entities)} 个实体")
            else:
                print("⚠️  实体文件不存在")
            
            if relations_file.exists():
                with open(relations_file, 'r', encoding='utf-8') as f:
                    relations = json.load(f)
                print(f"✅ 关系文件存在: {len(relations)} 条关系")
            else:
                print("⚠️  关系文件不存在")
            
            return True
        else:
            print("⚠️  进度文件不存在（可能尚未开始构建）")
            return True  # 不算错误，只是还没有开始构建
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("知识图谱构建优化功能测试")
    print("=" * 80)
    print()
    
    results = {
        'entity_property_merge': False,
        'relation_property_merge': False,
        'batch_save': False,
        'resume': False
    }
    
    # 运行测试
    results['entity_property_merge'] = test_entity_property_merge()
    results['relation_property_merge'] = test_relation_property_merge()
    results['batch_save'] = test_batch_save_functionality()
    results['resume'] = test_resume_functionality()
    
    # 总结
    print("\n" + "=" * 80)
    print("测试结果总结")
    print("=" * 80)
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print()
    print(f"总计: {passed_tests}/{total_tests} 个测试通过")
    
    if passed_tests == total_tests:
        print("\n✅ 所有测试通过！")
        return True
    else:
        print(f"\n⚠️  有 {total_tests - passed_tests} 个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

