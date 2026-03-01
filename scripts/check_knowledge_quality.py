#!/usr/bin/env python3
"""
综合知识质量检查工具
检查向量知识库和知识图谱的内容质量
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import Counter
import re

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_vector_kb_quality() -> Dict[str, Any]:
    """检查向量知识库内容质量"""
    print("\n" + "=" * 80)
    print("🔍 向量知识库内容质量检查")
    print("=" * 80)
    
    try:
        # 🚀 修复：使用知识库管理系统的向量索引构建器
        from knowledge_management_system.core.vector_index_builder import VectorIndexBuilder
        
        # 使用正确的路径
        vector_index_path = "data/knowledge_management/vector_index.bin"
        vector_index_builder = VectorIndexBuilder(vector_index_path)
        
        # 确保索引已加载
        if not vector_index_builder.ensure_index_ready():
            print("   ⚠️  向量索引未就绪或无法加载")
            return {"status": "not_ready", "size": 0}
        
        # 获取向量数量
        kb_size = vector_index_builder.entry_count if hasattr(vector_index_builder, 'entry_count') else 0
        
        # 如果索引存在，尝试从索引获取数量
        if vector_index_builder.index is not None:
            try:
                kb_size = vector_index_builder.index.ntotal
            except:
                pass
        
        print(f"\n📊 向量知识库统计:")
        print(f"   向量索引路径: {vector_index_path}")
        print(f"   总条目数: {kb_size}")
        
        if kb_size == 0:
            print("   ⚠️  向量知识库为空")
            return {"status": "empty", "size": 0}
        
        # 检查元数据文件
        metadata_file = Path("data/knowledge_management/metadata.json")
        if not metadata_file.exists():
            print("   ⚠️  元数据文件不存在")
            return {"status": "no_metadata", "size": kb_size}
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata_data = json.load(f)
        
        entries_dict = metadata_data.get('entries', {})
        total_entries = len(entries_dict)
        
        print(f"   元数据条目数: {total_entries}")
        
        # 内容质量统计
        quality_stats = {
            "total": 0,
            "empty": 0,
            "short": 0,
            "good": 0,
            "issues": Counter(),
            "quality_scores": []
        }
        
        # 检查前100个条目
        check_count = min(100, total_entries)
        print(f"\n   检查前 {check_count} 个条目...")
        
        for i, (entry_id, entry_data) in enumerate(list(entries_dict.items())[:check_count]):
            metadata = entry_data.get('metadata', {})
            content = metadata.get('content', '') or metadata.get('content_preview', '')
            
            quality = _check_content_quality(content)
            quality_stats["total"] += 1
            quality_stats["quality_scores"].append(quality["quality_score"])
            
            if not content:
                quality_stats["empty"] += 1
            elif quality["length"] < 100:
                quality_stats["short"] += 1
            elif quality["quality_score"] >= 80:
                quality_stats["good"] += 1
            
            for issue in quality["issues"]:
                quality_stats["issues"][issue] += 1
        
        # 显示统计
        avg_score = sum(quality_stats["quality_scores"]) / len(quality_stats["quality_scores"]) if quality_stats["quality_scores"] else 0
        print(f"\n   平均质量分数: {avg_score:.1f}/100")
        print(f"   空内容: {quality_stats['empty']} 条")
        print(f"   短内容(<100字符): {quality_stats['short']} 条")
        print(f"   高质量内容(≥80分): {quality_stats['good']} 条")
        
        if quality_stats["issues"]:
            print(f"\n   主要问题:")
            for issue, count in quality_stats["issues"].most_common(5):
                print(f"     - {issue}: {count} 条")
        
        return {
            "status": "success",
            "size": kb_size,
            "total_entries": total_entries,
            "avg_quality_score": avg_score,
            "quality_stats": dict(quality_stats)
        }
        
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}


def check_knowledge_graph_quality() -> Dict[str, Any]:
    """检查知识图谱内容质量"""
    print("\n" + "=" * 80)
    print("🔍 知识图谱内容质量检查")
    print("=" * 80)
    
    try:
        # 导入知识图谱管理器
        from knowledge_management_system.graph.entity_manager import EntityManager
        from knowledge_management_system.graph.relation_manager import RelationManager
        
        entity_manager = EntityManager()
        relation_manager = RelationManager()
        
        # 获取所有实体（使用list_entities，设置较大的limit）
        all_entities = entity_manager.list_entities(limit=10000)
        entity_count = len(all_entities)
        
        # 获取所有关系（直接访问_relations）
        all_relations = relation_manager._relations
        relation_count = len(all_relations)
        
        print(f"\n📊 知识图谱统计:")
        print(f"   实体总数: {entity_count}")
        print(f"   关系总数: {relation_count}")
        
        if entity_count == 0:
            print("   ⚠️  知识图谱为空")
            return {"status": "empty", "entity_count": 0, "relation_count": 0}
        
        # 实体质量检查
        entity_quality_stats = {
            "total": 0,
            "empty_name": 0,
            "duplicate_names": Counter(),
            "entity_types": Counter(),
            "low_confidence": 0
        }
        
        entity_names = []
        for entity in all_entities:
            entity_quality_stats["total"] += 1
            name = entity.get('name', '')
            entity_type = entity.get('type', 'Unknown')
            confidence = entity.get('confidence', 1.0)
            
            if not name or not name.strip():
                entity_quality_stats["empty_name"] += 1
            else:
                entity_names.append(name)
                entity_quality_stats["duplicate_names"][name] += 1
            
            entity_quality_stats["entity_types"][entity_type] += 1
            
            if confidence < 0.5:
                entity_quality_stats["low_confidence"] += 1
        
        # 关系质量检查
        relation_quality_stats = {
            "total": 0,
            "invalid_entity": 0,
            "self_loop": 0,
            "duplicate_relations": Counter(),
            "relation_types": Counter(),
            "low_confidence": 0
        }
        
        relation_keys = []
        for relation in all_relations:
            relation_quality_stats["total"] += 1
            entity1_id = relation.get('entity1_id')
            entity2_id = relation.get('entity2_id')
            relation_type = relation.get('type', relation.get('relation_type', 'Unknown'))  # 兼容两种字段名
            confidence = relation.get('confidence', 1.0)
            
            # 检查自环
            if entity1_id == entity2_id:
                relation_quality_stats["self_loop"] += 1
            
            # 检查实体是否存在
            entity1 = entity_manager.get_entity(entity1_id)
            entity2 = entity_manager.get_entity(entity2_id)
            if not entity1 or not entity2:
                relation_quality_stats["invalid_entity"] += 1
            
            # 检查重复关系
            relation_key = f"{entity1_id}-{relation_type}-{entity2_id}"
            relation_keys.append(relation_key)
            relation_quality_stats["duplicate_relations"][relation_key] += 1
            
            relation_quality_stats["relation_types"][relation_type] += 1
            
            if confidence < 0.5:
                relation_quality_stats["low_confidence"] += 1
        
        # 显示实体质量统计
        print(f"\n📊 实体质量统计:")
        print(f"   总实体数: {entity_quality_stats['total']}")
        print(f"   空名称: {entity_quality_stats['empty_name']} 个")
        print(f"   低置信度(<0.5): {entity_quality_stats['low_confidence']} 个")
        
        duplicate_entities = sum(1 for count in entity_quality_stats["duplicate_names"].values() if count > 1)
        if duplicate_entities > 0:
            print(f"   ⚠️  重复实体名称: {duplicate_entities} 个")
            print(f"      最常见的重复:")
            for name, count in entity_quality_stats["duplicate_names"].most_common(5):
                if count > 1:
                    print(f"         - '{name}': {count} 次")
        
        print(f"\n   实体类型分布:")
        for entity_type, count in entity_quality_stats["entity_types"].most_common(10):
            print(f"     - {entity_type}: {count} 个")
        
        # 显示关系质量统计
        print(f"\n📊 关系质量统计:")
        print(f"   总关系数: {relation_quality_stats['total']}")
        print(f"   自环关系: {relation_quality_stats['self_loop']} 个")
        print(f"   无效实体关系: {relation_quality_stats['invalid_entity']} 个")
        print(f"   低置信度(<0.5): {relation_quality_stats['low_confidence']} 个")
        
        duplicate_relations = sum(1 for count in relation_quality_stats["duplicate_relations"].values() if count > 1)
        if duplicate_relations > 0:
            print(f"   ⚠️  重复关系: {duplicate_relations} 个")
        
        print(f"\n   关系类型分布:")
        for relation_type, count in relation_quality_stats["relation_types"].most_common(10):
            print(f"     - {relation_type}: {count} 个")
        
        # 计算质量分数
        entity_quality_score = 100
        if entity_quality_stats['empty_name'] > 0:
            entity_quality_score -= (entity_quality_stats['empty_name'] / entity_quality_stats['total']) * 30
        if duplicate_entities > 0:
            entity_quality_score -= (duplicate_entities / entity_quality_stats['total']) * 20
        if entity_quality_stats['low_confidence'] > 0:
            entity_quality_score -= (entity_quality_stats['low_confidence'] / entity_quality_stats['total']) * 10
        
        relation_quality_score = 100
        if relation_quality_stats['self_loop'] > 0:
            relation_quality_score -= (relation_quality_stats['self_loop'] / relation_quality_stats['total']) * 30
        if relation_quality_stats['invalid_entity'] > 0:
            relation_quality_score -= (relation_quality_stats['invalid_entity'] / relation_quality_stats['total']) * 40
        if duplicate_relations > 0:
            relation_quality_score -= (duplicate_relations / relation_quality_stats['total']) * 20
        if relation_quality_stats['low_confidence'] > 0:
            relation_quality_score -= (relation_quality_stats['low_confidence'] / relation_quality_stats['total']) * 10
        
        overall_score = (entity_quality_score + relation_quality_score) / 2
        
        print(f"\n📊 质量评估:")
        print(f"   实体质量分数: {entity_quality_score:.1f}/100")
        print(f"   关系质量分数: {relation_quality_score:.1f}/100")
        print(f"   总体质量分数: {overall_score:.1f}/100")
        
        if overall_score >= 90:
            print(f"   ✅ 知识图谱质量优秀")
        elif overall_score >= 80:
            print(f"   ✅ 知识图谱质量良好")
        elif overall_score >= 70:
            print(f"   ⚠️  知识图谱质量一般，建议检查并修复问题")
        else:
            print(f"   ❌ 知识图谱质量较差，需要重新构建或修复")
        
        return {
            "status": "success",
            "entity_count": entity_count,
            "relation_count": relation_count,
            "entity_quality_score": entity_quality_score,
            "relation_quality_score": relation_quality_score,
            "overall_score": overall_score,
            "entity_quality_stats": {
                "empty_name": entity_quality_stats['empty_name'],
                "duplicate_entities": duplicate_entities,
                "low_confidence": entity_quality_stats['low_confidence']
            },
            "relation_quality_stats": {
                "self_loop": relation_quality_stats['self_loop'],
                "invalid_entity": relation_quality_stats['invalid_entity'],
                "duplicate_relations": duplicate_relations,
                "low_confidence": relation_quality_stats['low_confidence']
            }
        }
        
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}


def _check_content_quality(content: str) -> Dict[str, Any]:
    """检查单个内容的质量"""
    issues = []
    quality_score = 100
    
    if not content:
        issues.append("内容为空")
        quality_score = 0
        return {"issues": issues, "quality_score": quality_score, "length": 0}
    
    content_length = len(content)
    
    # 检查内容长度
    if content_length < 50:
        issues.append(f"内容过短（{content_length}字符）")
        quality_score -= 30
    elif content_length < 100:
        issues.append(f"内容较短（{content_length}字符）")
        quality_score -= 10
    
    # 检查是否包含HTML标签（未清理）
    if "<" in content and ">" in content:
        html_tags = ["<div", "<span", "<p>", "<br", "<a href"]
        if any(tag in content for tag in html_tags):
            issues.append("包含未清理的HTML标签")
            quality_score -= 20
    
    # 检查是否包含引用标记（应该被清理）
    citation_pattern = r'\[\d+\]'
    if re.search(citation_pattern, content):
        issues.append("包含引用标记（如[1]、[2]等）")
        quality_score -= 10
    
    # 检查是否包含特殊字符（可能是JSON残留）
    if '}},"i":0}}]}' in content or 'id="mw' in content:
        issues.append("包含JSON残留或HTML属性")
        quality_score -= 15
    
    # 检查内容是否主要是空白字符
    if len(content.strip()) < content_length * 0.5:
        issues.append("包含过多空白字符")
        quality_score -= 10
    
    # 检查是否包含有效文本（至少有一些字母）
    if not re.search(r'[a-zA-Z\u4e00-\u9fff]', content):
        issues.append("不包含有效文本（无字母或中文）")
        quality_score -= 50
    
    return {
        "issues": issues,
        "quality_score": max(0, quality_score),
        "length": content_length
    }


def main():
    """主函数"""
    print("=" * 80)
    print("🔍 综合知识质量检查工具")
    print("=" * 80)
    
    # 检查向量知识库
    vector_kb_result = check_vector_kb_quality()
    
    # 检查知识图谱
    graph_result = check_knowledge_graph_quality()
    
    # 总结
    print("\n" + "=" * 80)
    print("📊 总结")
    print("=" * 80)
    
    if vector_kb_result.get("status") == "success":
        print(f"\n✅ 向量知识库: {vector_kb_result.get('size', 0)} 条, 平均质量: {vector_kb_result.get('avg_quality_score', 0):.1f}/100")
    else:
        print(f"\n⚠️  向量知识库: {vector_kb_result.get('status', 'unknown')}")
    
    if graph_result.get("status") == "success":
        print(f"✅ 知识图谱: {graph_result.get('entity_count', 0)} 实体, {graph_result.get('relation_count', 0)} 关系, 总体质量: {graph_result.get('overall_score', 0):.1f}/100")
    else:
        print(f"⚠️  知识图谱: {graph_result.get('status', 'unknown')}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()

