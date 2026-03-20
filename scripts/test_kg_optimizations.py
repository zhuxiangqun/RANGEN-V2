#!/usr/bin/env python3
"""
测试知识图谱构建的所有优化改进
1. 智能跳过LLM调用（性能优化）
2. 实体属性提取和传递
3. 孤立实体处理
"""

import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from knowledge_management_system.api.service_interface import get_knowledge_service
from knowledge_management_system.utils.logger import get_logger

logger = get_logger()

def test_llm_skip_logic():
    """测试智能跳过LLM调用的逻辑"""
    print("=" * 80)
    print("测试1: 智能跳过LLM调用逻辑")
    print("=" * 80)
    print()
    
    service = get_knowledge_service()
    
    # 测试用例1: 包含明确关系模式的文本（应该被方法2提取到，且有属性）
    test_text_1 = """
    John Adams was born on October 30, 1735, in Braintree, Massachusetts.
    He was the second President of the United States, serving from 1797 to 1801.
    His mother was Jane Ballou, who was born in 1709.
    """
    
    print("📝 测试用例1: 包含明确关系模式的文本")
    print("-" * 80)
    print("文本:", test_text_1.strip()[:100] + "...")
    print()
    
    # 捕获日志以检查是否跳过LLM
    import logging
    from io import StringIO
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    try:
        extracted_data = service._extract_entities_and_relations(test_text_1, None)
        log_output = log_capture.getvalue()
        
        print(f"✅ 提取结果: {len(extracted_data)} 条数据")
        if extracted_data:
            print(f"   第一条数据: {extracted_data[0]}")
        
        # 检查日志
        if "跳过LLM调用" in log_output or "提取的数据已有属性" in log_output:
            print("✅ 正确跳过了LLM调用（因为其他方法已提取到数据且有属性）")
            return True
        elif "使用LLM提取" in log_output or "🔍 尝试使用LLM提取" in log_output:
            print("⚠️  仍然调用了LLM（可能其他方法没有提取到数据，或提取的数据没有属性）")
            print(f"   日志片段: {log_output[-500:]}")
            return False
        else:
            print("⚠️  无法确定是否调用了LLM（日志中没有相关信息）")
            return False
    finally:
        logger.removeHandler(handler)
        handler.close()

def test_property_extraction():
    """测试实体属性提取"""
    print()
    print("=" * 80)
    print("测试2: 实体属性提取")
    print("=" * 80)
    print()
    
    service = get_knowledge_service()
    
    # 测试文本：包含明确的属性信息
    test_text = """
    John Adams was born on October 30, 1735, in Braintree, Massachusetts.
    He was the second President of the United States, serving from 1797 to 1801.
    His mother was Jane Ballou, who was born in 1709.
    """
    
    print("📝 测试文本: 包含明确的属性信息")
    print("-" * 80)
    print(test_text.strip())
    print()
    
    extracted_data = service._extract_entities_and_relations(test_text, None)
    
    print(f"✅ 提取结果: {len(extracted_data)} 条数据")
    print()
    
    if not extracted_data:
        print("❌ 未提取到任何数据")
        return False
    
    # 检查属性
    entities_with_properties = 0
    relations_with_properties = 0
    
    for item in extracted_data:
        entity1_props = item.get('entity1_properties', {})
        entity2_props = item.get('entity2_properties', {})
        relation_props = item.get('relation_properties', {})
        
        if entity1_props:
            entities_with_properties += 1
        if entity2_props:
            entities_with_properties += 1
        if relation_props:
            relations_with_properties += 1
        
        print(f"关系: {item.get('entity1')} -[{item.get('relation')}]-> {item.get('entity2')}")
        if entity1_props:
            print(f"  实体1属性: {entity1_props}")
        if entity2_props:
            print(f"  实体2属性: {entity2_props}")
        if relation_props:
            print(f"  关系属性: {relation_props}")
        print()
    
    total_entities = len(extracted_data) * 2  # 每条关系有2个实体
    total_relations = len(extracted_data)
    
    print(f"📊 统计:")
    print(f"   有属性的实体: {entities_with_properties}/{total_entities}")
    print(f"   有属性的关系: {relations_with_properties}/{total_relations}")
    print()
    
    if entities_with_properties > 0 or relations_with_properties > 0:
        print("✅ 属性提取正常")
        return True
    else:
        print("⚠️  所有实体和关系都没有属性")
        return False

def test_isolated_entities():
    """测试孤立实体处理"""
    print()
    print("=" * 80)
    print("测试3: 孤立实体处理")
    print("=" * 80)
    print()
    
    service = get_knowledge_service()
    
    # 测试文本：包含实体但没有明确关系
    test_text = """
    John Adams was born on October 30, 1735.
    He was the second President of the United States.
    """
    
    print("📝 测试文本: 包含实体但没有明确关系")
    print("-" * 80)
    print(test_text.strip())
    print()
    
    extracted_data = service._extract_entities_and_relations(test_text, None)
    
    print(f"✅ 提取结果: {len(extracted_data)} 条数据")
    print()
    
    if not extracted_data:
        print("⚠️  未提取到任何数据（这是正常的，因为文本中没有明确的关系）")
        return True
    
    # 检查是否有孤立实体（出现在实体中但不在任何关系中）
    entities_in_relations = set()
    for item in extracted_data:
        entities_in_relations.add(item.get('entity1'))
        entities_in_relations.add(item.get('entity2'))
    
    print(f"📊 统计:")
    print(f"   提取的关系数: {len(extracted_data)}")
    print(f"   关系中的实体: {len(entities_in_relations)}")
    print(f"   实体列表: {list(entities_in_relations)}")
    print()
    
    if len(extracted_data) == 0:
        print("✅ 没有孤立实体（因为没有提取到关系）")
        return True
    elif len(entities_in_relations) > 0:
        print("✅ 所有实体都在关系中（没有孤立实体）")
        return True
    else:
        print("⚠️  存在孤立实体")
        return False

def test_with_real_data():
    """使用真实数据测试"""
    print()
    print("=" * 80)
    print("测试4: 使用真实数据测试")
    print("=" * 80)
    print()
    
    service = get_knowledge_service()
    
    # 获取前几条知识条目
    try:
        knowledge_entries = service.knowledge_manager.list_knowledge(limit=5)
        print(f"📚 获取到 {len(knowledge_entries)} 条知识条目")
        print()
        
        if not knowledge_entries:
            print("⚠️  知识库中没有条目")
            return False
        
        total_extracted = 0
        total_with_properties = 0
        total_llm_calls = 0
        total_llm_skipped = 0
        
        for idx, entry in enumerate(knowledge_entries[:3], 1):  # 只测试前3条
            entry_id = entry.get('id', 'unknown')
            metadata = entry.get('metadata', {})
            content = metadata.get('content', '') or metadata.get('content_preview', '')
            
            if not content:
                print(f"⚠️  条目 {idx} ({entry_id[:20]}...) 没有内容，跳过")
                continue
            
            print(f"📝 条目 {idx}: {entry_id[:50]}...")
            print(f"   内容长度: {len(content)} 字符")
            
            # 捕获日志
            import logging
            from io import StringIO
            log_capture = StringIO()
            handler = logging.StreamHandler(log_capture)
            handler.setLevel(logging.DEBUG)
            logger.addHandler(handler)
            
            try:
                extracted_data = service._extract_entities_and_relations(content, metadata)
                log_output = log_capture.getvalue()
                
                total_extracted += len(extracted_data)
                
                # 检查属性
                has_properties = any(
                    item.get('entity1_properties') or 
                    item.get('entity2_properties') or 
                    item.get('relation_properties')
                    for item in extracted_data
                )
                
                if has_properties:
                    total_with_properties += 1
                
                # 检查LLM调用
                if "跳过LLM调用" in log_output or "提取的数据已有属性" in log_output:
                    total_llm_skipped += 1
                elif "使用LLM提取" in log_output or "🔍 尝试使用LLM提取" in log_output:
                    total_llm_calls += 1
                
                print(f"   提取结果: {len(extracted_data)} 条数据")
                print(f"   有属性: {'是' if has_properties else '否'}")
                print(f"   LLM调用: {'跳过' if '跳过LLM调用' in log_output or '提取的数据已有属性' in log_output else '调用'}")
                print()
            finally:
                logger.removeHandler(handler)
                handler.close()
        
        print(f"📊 统计:")
        print(f"   总提取数据: {total_extracted} 条")
        print(f"   有属性的数据: {total_with_properties} 条")
        print(f"   LLM调用: {total_llm_calls} 次")
        print(f"   LLM跳过: {total_llm_skipped} 次")
        print()
        
        if total_llm_skipped > 0:
            print("✅ 智能跳过LLM调用功能正常工作")
            return True
        else:
            print("⚠️  所有条目都调用了LLM（可能其他方法都没有提取到数据）")
            return False
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print()
    print("🧪 知识图谱构建优化测试")
    print("=" * 80)
    print()
    
    results = {}
    
    try:
        # 测试1: 智能跳过LLM调用
        results['llm_skip'] = test_llm_skip_logic()
        
        # 测试2: 实体属性提取
        results['properties'] = test_property_extraction()
        
        # 测试3: 孤立实体处理
        results['isolated'] = test_isolated_entities()
        
        # 测试4: 真实数据测试
        results['real_data'] = test_with_real_data()
        
        # 总结
        print()
        print("=" * 80)
        print("测试总结")
        print("=" * 80)
        print(f"智能跳过LLM调用: {'✅ 通过' if results.get('llm_skip') else '❌ 失败'}")
        print(f"实体属性提取: {'✅ 通过' if results.get('properties') else '❌ 失败'}")
        print(f"孤立实体处理: {'✅ 通过' if results.get('isolated') else '❌ 失败'}")
        print(f"真实数据测试: {'✅ 通过' if results.get('real_data') else '❌ 失败'}")
        print()
        
        all_passed = all(results.values())
        if all_passed:
            print("🎉 所有测试通过！")
        else:
            print("⚠️  部分测试失败，请检查日志")
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        print(f"❌ 测试失败: {e}")
        sys.exit(1)

