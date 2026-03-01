#!/usr/bin/env python3
"""
图谱连通性优化器
通过更深入的关系提取策略，提高图谱的连通性
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict
from ..utils.logger import get_logger

logger = get_logger()


class ConnectivityOptimizer:
    """图谱连通性优化器"""
    
    def __init__(self, entity_manager, relation_manager):
        """
        初始化连通性优化器
        
        Args:
            entity_manager: 实体管理器
            relation_manager: 关系管理器
        """
        self.entity_manager = entity_manager
        self.relation_manager = relation_manager
        self.logger = logger
    
    def analyze_connectivity(self) -> Dict[str, Any]:
        """
        分析图谱连通性
        
        Returns:
            连通性分析结果
        """
        entities = self.entity_manager._entities
        relations = self.relation_manager._relations
        
        # 构建邻接表
        adjacency = defaultdict(set)
        entity_ids = set(entities.keys())
        
        for relation in relations:
            entity1_id = relation.get('entity1_id')
            entity2_id = relation.get('entity2_id')
            if entity1_id and entity2_id and entity1_id in entity_ids and entity2_id in entity_ids:
                adjacency[entity1_id].add(entity2_id)
                adjacency[entity2_id].add(entity1_id)
        
        # 计算连通分量
        visited = set()
        components = []
        
        def dfs(node: str, component: Set[str]):
            """深度优先搜索"""
            visited.add(node)
            component.add(node)
            for neighbor in adjacency.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor, component)
        
        for entity_id in entity_ids:
            if entity_id not in visited:
                component = set()
                dfs(entity_id, component)
                if component:
                    components.append(component)
        
        # 计算度统计
        degrees = {}
        for entity_id in entity_ids:
            degrees[entity_id] = len(adjacency.get(entity_id, set()))
        
        # 统计孤立实体
        isolated_entities = [eid for eid, degree in degrees.items() if degree == 0]
        
        return {
            'total_entities': len(entity_ids),
            'total_relations': len(relations),
            'connected_components': len(components),
            'largest_component_size': max([len(c) for c in components]) if components else 0,
            'isolated_entities': len(isolated_entities),
            'average_degree': sum(degrees.values()) / len(degrees) if degrees else 0,
            'max_degree': max(degrees.values()) if degrees else 0,
            'components': components,
            'isolated_entity_ids': isolated_entities
        }
    
    def suggest_relations_for_connectivity(
        self,
        max_suggestions: int = 100
    ) -> List[Dict[str, Any]]:
        """
        基于连通性分析，建议可能的关系来改善连通性
        
        Args:
            max_suggestions: 最大建议数量
        
        Returns:
            建议的关系列表
        """
        connectivity = self.analyze_connectivity()
        suggestions = []
        
        # 策略1: 连接孤立实体到最近的连通分量
        isolated_ids = connectivity.get('isolated_entity_ids', [])
        components = connectivity.get('components', [])
        
        if isolated_ids and components:
            # 为每个孤立实体找到最近的连通分量
            for isolated_id in isolated_ids[:max_suggestions // 2]:
                isolated_entity = self.entity_manager.get_entity(isolated_id)
                if not isolated_entity:
                    continue
                
                isolated_name = isolated_entity.get('name', '')
                isolated_type = isolated_entity.get('type', '')
                
                # 找到最近的连通分量（通过实体类型匹配）
                for component in components:
                    for entity_id in component:
                        entity = self.entity_manager.get_entity(entity_id)
                        if entity and entity.get('type') == isolated_type:
                            suggestions.append({
                                'entity1_id': isolated_id,
                                'entity2_id': entity_id,
                                'entity1_name': isolated_name,
                                'entity2_name': entity.get('name', ''),
                                'suggested_relation': 'related_to',
                                'reason': 'connect_isolated_entity',
                                'confidence': 0.3
                            })
                            break
                    if suggestions and len(suggestions) >= max_suggestions:
                        break
                if len(suggestions) >= max_suggestions:
                    break
        
        # 策略2: 连接小的连通分量
        small_components = [c for c in components if len(c) < 5]
        if len(small_components) > 1:
            # 尝试连接小的连通分量
            for i, comp1 in enumerate(small_components[:max_suggestions // 4]):
                for comp2 in small_components[i+1:max_suggestions // 4]:
                    # 找到两个分量中的实体，尝试建立连接
                    entity1_id = list(comp1)[0]
                    entity2_id = list(comp2)[0]
                    
                    entity1 = self.entity_manager.get_entity(entity1_id)
                    entity2 = self.entity_manager.get_entity(entity2_id)
                    
                    if entity1 and entity2:
                        suggestions.append({
                            'entity1_id': entity1_id,
                            'entity2_id': entity2_id,
                            'entity1_name': entity1.get('name', ''),
                            'entity2_name': entity2.get('name', ''),
                            'suggested_relation': 'related_to',
                            'reason': 'connect_small_components',
                            'confidence': 0.2
                        })
                    
                    if len(suggestions) >= max_suggestions:
                        break
                if len(suggestions) >= max_suggestions:
                    break
        
        return suggestions[:max_suggestions]
    
    def extract_implicit_relations(
        self,
        text: str,
        entities_in_text: List[str]
    ) -> List[Dict[str, Any]]:
        """
        从文本中提取隐式关系（基于上下文推理）
        
        Args:
            text: 文本内容
            entities_in_text: 文本中出现的实体列表
        
        Returns:
            提取的隐式关系列表
        """
        implicit_relations = []
        
        if len(entities_in_text) < 2:
            return implicit_relations
        
        # 策略1: 基于共现的关系
        # 如果两个实体在同一段落或句子中出现，可能有关联
        sentences = text.split('.')
        for sentence in sentences:
            sentence_lower = sentence.lower()
            entities_in_sentence = [
                e for e in entities_in_text
                if e.lower() in sentence_lower
            ]
            
            if len(entities_in_sentence) >= 2:
                # 为每对实体创建隐式关系
                for i, entity1 in enumerate(entities_in_sentence):
                    for entity2 in entities_in_sentence[i+1:]:
                        implicit_relations.append({
                            'entity1': entity1,
                            'entity2': entity2,
                            'relation': 'co_occurrence',
                            'confidence': 0.4,
                            'context': sentence.strip()[:100]
                        })
        
        # 策略2: 基于实体类型的常见关系
        # 例如：Person - Person 可能是 related_to, worked_with
        # Person - Location 可能是 born_in, died_in, lived_in
        # Person - Organization 可能是 worked_at, founded, president_of
        
        return implicit_relations
    
    def improve_relation_extraction_prompt(self) -> str:
        """
        改进关系提取的prompt，要求提取更多关系类型
        
        Returns:
            改进后的prompt模板
        """
        return """
Extract entities and relations from the following knowledge entry content.

**IMPORTANT**: Extract ALL possible relations between entities, not just the most obvious ones.
Consider the following relation types:
- Direct relations: mother_of, father_of, son_of, daughter_of, wife_of, husband_of
- Professional relations: worked_at, founded, president_of, member_of, graduated_from
- Location relations: born_in, died_in, lived_in, located_in
- Temporal relations: created_at, happened_at, occurred_in
- Causal relations: caused_by, resulted_in, influenced_by
- General relations: related_to, associated_with, connected_to

For each relation, extract:
- entity1: source entity name
- entity2: target entity name
- relation: relation type (be specific, avoid generic "related_to" when possible)
- properties: {
    "date": date if mentioned,
    "location": location if mentioned,
    "description": brief context
}

Extract as many relations as possible to improve graph connectivity.
"""

