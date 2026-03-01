#!/usr/bin/env python3
"""
图谱查询引擎
提供知识图谱的查询功能
"""

from typing import Dict, List, Any, Optional
from .entity_manager import EntityManager
from .relation_manager import RelationManager
from ..utils.logger import get_logger

logger = get_logger()


class GraphQueryEngine:
    """图谱查询引擎"""
    
    def __init__(self):
        self.logger = logger
        self.entity_manager = EntityManager()
        self.relation_manager = RelationManager()
    
    def load_graph(self):
        """加载图谱数据（占位符，当前实现基于内存管理器，无需显式加载）"""
        self.logger.info("图谱查询引擎：图谱数据已就绪")
        
    def query_entity(self, name: str) -> List[Dict[str, Any]]:
        """
        查询实体
        
        Args:
            name: 实体名称
        
        Returns:
            实体列表
        """
        return self.entity_manager.find_entity_by_name(name)
    
    def query_relations(
        self,
        entity_name: Optional[str] = None,
        relation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        查询关系
        
        Args:
            entity_name: 实体名称（可选）
            relation_type: 关系类型（可选）
        
        Returns:
            关系列表（包含实体信息）
        """
        # 如果提供了实体名称，先查找实体ID
        entity_id = None
        if entity_name:
            entities = self.entity_manager.find_entity_by_name(entity_name)
            if entities:
                entity_id = entities[0].get('id')
        
        # 查找关系
        relations = self.relation_manager.find_relations(
            entity_id=entity_id,
            relation_type=relation_type
        )
        
        # 丰富关系信息（添加实体名称）
        enriched_relations = []
        for relation in relations:
            entity1 = self.entity_manager.get_entity(relation.get('entity1_id'))
            entity2 = self.entity_manager.get_entity(relation.get('entity2_id'))
            
            enriched_relations.append({
                **relation,
                'entity1_name': entity1.get('name') if entity1 else 'Unknown',
                'entity2_name': entity2.get('name') if entity2 else 'Unknown'
            })
        
        return enriched_relations
    
    def query_path(
        self,
        entity1_name: str,
        entity2_name: str,
        max_hops: int = 3
    ) -> List[List[Dict[str, Any]]]:
        """
        查询两个实体之间的路径
        
        Args:
            entity1_name: 起始实体名称
            entity2_name: 目标实体名称
            max_hops: 最大跳数
        
        Returns:
            路径列表
        """
        # 查找实体
        entities1 = self.entity_manager.find_entity_by_name(entity1_name)
        entities2 = self.entity_manager.find_entity_by_name(entity2_name)
        
        if not entities1 or not entities2:
            return []
        
        entity1_id = entities1[0].get('id')
        entity2_id = entities2[0].get('id')
        
        # 使用关系管理器查找路径
        paths = self.relation_manager.find_path(
            entity1_id=entity1_id,
            entity2_id=entity2_id,
            max_hops=max_hops
        )
        
        return paths
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        entities = self.entity_manager.list_entities(limit=10000)
        relations = self.relation_manager._relations
        
        # 按类型统计实体
        entity_type_stats = {}
        for entity in entities:
            entity_type = entity.get('type', 'Unknown')
            entity_type_stats[entity_type] = entity_type_stats.get(entity_type, 0) + 1
        
        # 按类型统计关系
        relation_type_stats = {}
        for relation in relations:
            relation_type = relation.get('type', 'Unknown')
            relation_type_stats[relation_type] = relation_type_stats.get(relation_type, 0) + 1
        
        return {
            'total_entities': len(entities),
            'total_relations': len(relations),
            'entity_type_distribution': entity_type_stats,
            'relation_type_distribution': relation_type_stats
        }

