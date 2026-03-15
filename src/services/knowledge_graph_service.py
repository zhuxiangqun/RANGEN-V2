"""
知识图谱服务 - 智能关联发现与实体关系管理
Intelligent Knowledge Graph Service with Association Discovery

核心功能：
1. 实体管理：实体的创建、查询、更新、删除
2. 关系管理：关系类型化、权重计算、路径发现
3. 智能关联发现：基于语义、时序、协同的隐含关系挖掘
4. 图谱查询：实体查询、关系查询、多跳查询
5. RAG+图谱结合：结构化知识与非结构化知识联合检索

技术特性：
- 动态关联图构建
- 语义相似度计算
- 协同过滤推荐
- 图神经网络启发式算法
"""

import asyncio
import logging
import time
import hashlib
import json
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import re

logger = logging.getLogger(__name__)


class EntityType(str, Enum):
    """实体类型"""
    CONCEPT = "concept"           # 概念
    TOOL = "tool"               # 工具
    SKILL = "skill"             # 技能
    AGENT = "agent"             # Agent
    TEAM = "team"               # 团队
    PERSON = "person"           # 人物
    ORGANIZATION = "organization"  # 组织
    PRODUCT = "product"         # 产品
    PROCESS = "process"         # 流程
    KNOWLEDGE = "knowledge"     # 知识


class RelationType(str, Enum):
    """关系类型"""
    USES = "uses"               # 使用关系
    DEPENDS_ON = "depends_on"   # 依赖关系
    COMPOSED_OF = "composed_of" # 组合关系
    EVOLVED_FROM = "evolved_from"  # 演化关系
    SIMILAR_TO = "similar_to"   # 相似关系
    PART_OF = "part_of"         # 属于
    LEADS_TO = "leads_to"       # 导致
    RELATED_TO = "related_to"   # 相关关系
    COLLABORATES_WITH = "collaborates_with"  # 协作关系
    DERIVED_FROM = "derived_from"  # 派生关系


@dataclass
class Entity:
    """实体"""
    id: str
    name: str
    entity_type: EntityType
    description: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'type': self.entity_type.value,
            'description': self.description,
            'properties': self.properties,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


@dataclass
class Relation:
    """关系"""
    id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'type': self.relation_type.value,
            'weight': self.weight,
            'properties': self.properties,
            'metadata': self.metadata,
            'created_at': self.created_at
        }


@dataclass
class AssociationDiscoveryResult:
    """关联发现结果"""
    source_entity: Entity
    discovered_associations: List[Dict[str, Any]]
    confidence_scores: List[float]
    reasoning: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source_entity': self.source_entity.to_dict(),
            'discovered_associations': self.discovered_associations,
            'confidence_scores': self.confidence_scores,
            'reasoning': self.reasoning
        }


class KnowledgeGraphService:
    """知识图谱服务 - 智能关联发现与实体关系管理"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 图谱存储
        self._entities: Dict[str, Entity] = {}
        self._relations: Dict[str, Relation] = {}
        
        # 索引结构
        self._entity_name_index: Dict[str, Set[str]] = defaultdict(set)  # 名称 -> 实体ID
        self._entity_type_index: Dict[EntityType, Set[str]] = defaultdict(set)  # 类型 -> 实体ID
        self._relation_type_index: Dict[RelationType, Set[str]] = defaultdict(set)  # 关系类型 -> 关系ID
        self._source_target_index: Dict[str, Set[str]] = defaultdict(set)  # 源ID -> 目标ID集合
        
        # 关联网络
        self._adjacency_list: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
        self._reverse_adjacency: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
        
        # 统计信息
        self._stats = {
            'total_entities': 0,
            'total_relations': 0,
            'entity_type_counts': defaultdict(int),
            'relation_type_counts': defaultdict(int),
            'discovery_operations': 0
        }
        
        # 配置参数
        self._semantic_similarity_threshold = self.config.get('semantic_similarity_threshold', 0.7)
        self._min_association_weight = self.config.get('min_association_weight', 0.3)
        self._max_hop_depth = self.config.get('max_hop_depth', 3)
        self._enable_auto_discovery = self.config.get('enable_auto_discovery', True)
        
        # 嵌入服务（可选）
        self._embedding_service = None
        
        logger.info("知识图谱服务初始化完成")
    
    def _set_embedding_service(self, embedding_service):
        """设置嵌入服务"""
        self._embedding_service = embedding_service
    
    # ==================== 实体管理 ====================
    
    def create_entity(
        self,
        name: str,
        entity_type: EntityType,
        description: str = "",
        properties: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Entity:
        """创建实体"""
        entity_id = self._generate_entity_id(name, entity_type)
        
        # 检查是否已存在
        if entity_id in self._entities:
            logger.warning(f"实体已存在: {name} ({entity_type.value})")
            return self._entities[entity_id]
        
        entity = Entity(
            id=entity_id,
            name=name,
            entity_type=entity_type,
            description=description,
            properties=properties or {},
            metadata=metadata or {}
        )
        
        # 存储实体
        self._entities[entity_id] = entity
        
        # 更新索引
        self._entity_name_index[name.lower()].add(entity_id)
        self._entity_type_index[entity_type].add(entity_id)
        
        # 更新统计
        self._stats['total_entities'] += 1
        self._stats['entity_type_counts'][entity_type.value] += 1
        
        logger.info(f"创建实体: {name} ({entity_type.value})")
        return entity
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """获取实体"""
        return self._entities.get(entity_id)
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """根据类型获取实体"""
        entity_ids = self._entity_type_index.get(entity_type, set())
        return [self._entities[eid] for eid in entity_ids if eid in self._entities]
    
    def get_entities_by_name(self, name: str) -> List[Entity]:
        """根据名称获取实体"""
        entity_ids = self._entity_name_index.get(name.lower(), set())
        return [self._entities[eid] for eid in entity_ids if eid in self._entities]
    
    def update_entity(
        self,
        entity_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Entity]:
        """更新实体"""
        entity = self._entities.get(entity_id)
        if not entity:
            return None
        
        if name is not None:
            # 更新名称索引
            self._entity_name_index[entity.name.lower()].discard(entity_id)
            entity.name = name
            self._entity_name_index[name.lower()].add(entity_id)
        
        if description is not None:
            entity.description = description
        
        if properties is not None:
            entity.properties.update(properties)
        
        if metadata is not None:
            entity.metadata.update(metadata)
        
        entity.updated_at = time.time()
        
        logger.info(f"更新实体: {entity_id}")
        return entity
    
    def delete_entity(self, entity_id: str) -> bool:
        """删除实体及其关联"""
        if entity_id not in self._entities:
            return False
        
        entity = self._entities[entity_id]
        
        # 删除相关的所有关系
        relations_to_delete = [
            rid for rid, rel in self._relations.items()
            if rel.source_id == entity_id or rel.target_id == entity_id
        ]
        
        for rid in relations_to_delete:
            self._delete_relation(rid)
        
        # 删除实体
        del self._entities[entity_id]
        
        # 更新索引
        self._entity_name_index[entity.name.lower()].discard(entity_id)
        self._entity_type_index[entity.entity_type].discard(entity_id)
        
        # 更新统计
        self._stats['total_entities'] -= 1
        self._stats['entity_type_counts'][entity.entity_type.value] -= 1
        
        logger.info(f"删除实体: {entity_id}")
        return True
    
    # ==================== 关系管理 ====================
    
    def create_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        weight: float = 1.0,
        properties: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Relation]:
        """创建关系"""
        # 验证实体存在
        if source_id not in self._entities or target_id not in self._entities:
            logger.warning(f"关系创建失败: 实体不存在")
            return None
        
        # 生成关系ID
        relation_id = self._generate_relation_id(source_id, target_id, relation_type)
        
        # 检查是否已存在
        if relation_id in self._relations:
            logger.warning(f"关系已存在: {relation_id}")
            return self._relations[relation_id]
        
        relation = Relation(
            id=relation_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            weight=weight,
            properties=properties or {},
            metadata=metadata or {}
        )
        
        # 存储关系
        self._relations[relation_id] = relation
        
        # 更新索引
        self._relation_type_index[relation_type].add(relation_id)
        self._source_target_index[source_id].add(relation_id)
        
        # 更新邻接表
        self._adjacency_list[source_id][relation_type.value].add(target_id)
        self._reverse_adjacency[target_id][relation_type.value].add(source_id)
        
        # 更新统计
        self._stats['total_relations'] += 1
        self._stats['relation_type_counts'][relation_type.value] += 1
        
        logger.info(f"创建关系: {source_id} --[{relation_type.value}]--> {target_id}")
        return relation
    
    def _delete_relation(self, relation_id: str) -> bool:
        """删除关系"""
        if relation_id not in self._relations:
            return False
        
        relation = self._relations[relation_id]
        
        # 从索引中移除
        self._relation_type_index[relation.relation_type].discard(relation_id)
        self._source_target_index[relation.source_id].discard(relation_id)
        
        # 从邻接表移除
        self._adjacency_list[relation.source_id][relation.relation_type.value].discard(relation.target_id)
        self._reverse_adjacency[relation.target_id][relation.relation_type.value].discard(relation.source_id)
        
        # 删除关系
        del self._relations[relation_id]
        
        # 更新统计
        self._stats['total_relations'] -= 1
        self._stats['relation_type_counts'][relation.relation_type.value] -= 1
        
        return True
    
    def get_relations(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relation_type: Optional[RelationType] = None
    ) -> List[Relation]:
        """查询关系"""
        results = []
        
        for relation in self._relations.values():
            if source_id and relation.source_id != source_id:
                continue
            if target_id and relation.target_id != target_id:
                continue
            if relation_type and relation.relation_type != relation_type:
                continue
            results.append(relation)
        
        return results
    
    def get_neighbors(
        self,
        entity_id: str,
        relation_types: Optional[List[RelationType]] = None,
        max_depth: int = 1
    ) -> Dict[str, List[Entity]]:
        """获取邻居实体"""
        if entity_id not in self._entities:
            return {}
        
        neighbors = defaultdict(list)
        visited = {entity_id}
        
        def _dfs(current_id: str, depth: int):
            if depth > max_depth:
                return
            
            # 获取所有出边
            for rel_type, target_ids in self._adjacency_list[current_id].items():
                if relation_types and RelationType(rel_type) not in relation_types:
                    continue
                
                for target_id in target_ids:
                    if target_id not in visited:
                        visited.add(target_id)
                        if target_id in self._entities:
                            neighbors[rel_type].append(self._entities[target_id])
                            _dfs(target_id, depth + 1)
        
        _dfs(entity_id, 0)
        
        return dict(neighbors)
    
    # ==================== 图谱查询 ====================
    
    def query_entity(self, query: str, limit: int = 10) -> List[Entity]:
        """实体查询 - 支持名称匹配和属性查询"""
        results = []
        query_lower = query.lower()
        
        # 名称匹配
        for entity in self._entities.values():
            if query_lower in entity.name.lower():
                results.append(entity)
                continue
            
            # 描述匹配
            if query_lower in entity.description.lower():
                results.append(entity)
                continue
        
        # 属性匹配
        for entity in self._entities.values():
            for key, value in entity.properties.items():
                if isinstance(value, str) and query_lower in value.lower():
                    if entity not in results:
                        results.append(entity)
                    break
        
        return results[:limit]
    
    def query_relation(
        self,
        source_name: Optional[str] = None,
        target_name: Optional[str] = None,
        relation_type: Optional[RelationType] = None
    ) -> List[Dict[str, Any]]:
        """关系查询"""
        results = []
        
        # 解析实体名称
        source_ids = None
        target_ids = None
        
        if source_name:
            source_entities = self.get_entities_by_name(source_name)
            source_ids = {e.id for e in source_entities}
        
        if target_name:
            target_entities = self.get_entities_by_name(target_name)
            target_ids = {e.id for e in target_entities}
        
        # 查询关系
        for relation in self.get_relations(relation_type=relation_type):
            if source_ids and relation.source_id not in source_ids:
                continue
            if target_ids and relation.target_id not in target_ids:
                continue
            
            source_entity = self._entities.get(relation.source_id)
            target_entity = self._entities.get(relation.target_id)
            
            if source_entity and target_entity:
                results.append({
                    'source': source_entity.to_dict(),
                    'target': target_entity.to_dict(),
                    'relation': relation.to_dict()
                })
        
        return results
    
    def multi_hop_query(
        self,
        start_entity: str,
        end_pattern: str,
        max_hops: int = 3
    ) -> List[List[Dict[str, Any]]]:
        """多跳查询 - 查找从起始实体到目标模式的路径"""
        paths = []
        
        # BFS查找路径
        queue = [(start_entity, [], 0)]
        visited = {start_entity}
        
        end_pattern_lower = end_pattern.lower()
        
        while queue:
            current_id, current_path, depth = queue.pop(0)
            
            if depth >= max_hops:
                continue
            
            # 探索所有出边
            for rel_type, target_ids in self._adjacency_list[current_id].items():
                for target_id in target_ids:
                    if target_id in visited:
                        continue
                    
                    visited.add(target_id)
                    
                    # 检查是否匹配目标模式
                    target_entity = self._entities.get(target_id)
                    if target_entity:
                        # 添加到当前路径
                        new_path = current_path + [{
                            'from': current_id,
                            'to': target_id,
                            'relation': rel_type,
                            'entity': target_entity.to_dict()
                        }]
                        
                        # 检查是否匹配目标
                        if (end_pattern_lower in target_entity.name.lower() or 
                            end_pattern_lower in target_entity.description.lower()):
                            paths.append(new_path)
                        
                        # 继续探索
                        queue.append((target_id, new_path, depth + 1))
        
        return paths
    
    # ==================== 智能关联发现 ====================
    
    async def discover_associations(
        self,
        source_entity_id: str,
        discovery_modes: Optional[List[str]] = None
    ) -> AssociationDiscoveryResult:
        """智能关联发现 - 核心功能"""
        
        if discovery_modes is None:
            discovery_modes = ['semantic', 'temporal', 'collaborative']
        
        source_entity = self._entities.get(source_entity_id)
        if not source_entity:
            raise ValueError(f"实体不存在: {source_entity_id}")
        
        self._stats['discovery_operations'] += 1
        
        discovered = []
        confidences = []
        reasoning = []
        
        # 1. 语义关联发现
        if 'semantic' in discovery_modes:
            semantic_associations = await self._discover_semantic_associations(source_entity)
            discovered.extend(semantic_associations['associations'])
            confidences.extend(semantic_associations['confidences'])
            reasoning.extend(semantic_associations['reasoning'])
        
        # 2. 时序关联发现
        if 'temporal' in discovery_modes:
            temporal_associations = self._discover_temporal_associations(source_entity)
            discovered.extend(temporal_associations['associations'])
            confidences.extend(temporal_associations['confidences'])
            reasoning.extend(temporal_associations['reasoning'])
        
        # 3. 协同过滤关联
        if 'collaborative' in discovery_modes:
            collaborative_associations = self._discover_collaborative_associations(source_entity)
            discovered.extend(collaborative_associations['associations'])
            confidences.extend(collaborative_associations['confidences'])
            reasoning.extend(collaborative_associations['reasoning'])
        
        # 4. 结构化关联
        structural_associations = self._discover_structural_associations(source_entity)
        discovered.extend(structural_associations['associations'])
        confidences.extend(structural_associations['confidences'])
        reasoning.extend(structural_associations['reasoning'])
        
        # 按置信度排序
        sorted_indices = sorted(range(len(confidences)), key=lambda i: confidences[i], reverse=True)
        discovered = [discovered[i] for i in sorted_indices]
        confidences = [confidences[i] for i in sorted_indices]
        reasoning = [reasoning[i] for i in sorted_indices]
        
        return AssociationDiscoveryResult(
            source_entity=source_entity,
            discovered_associations=discovered[:10],  # 返回前10个
            confidence_scores=confidences[:10],
            reasoning=reasoning[:10]
        )
    
    async def _discover_semantic_associations(
        self,
        source_entity: Entity
    ) -> Dict[str, Any]:
        """语义关联发现 - 基于描述相似性"""
        associations = []
        confidences = []
        reasoning = []
        
        source_text = f"{source_entity.name} {source_entity.description}".lower()
        source_words = set(re.findall(r'\b\w+\b', source_text))
        
        for entity_id, entity in self._entities.items():
            if entity_id == source_entity.id:
                continue
            
            # 计算文本相似度
            entity_text = f"{entity.name} {entity.description}".lower()
            entity_words = set(re.findall(r'\b\w+\b', entity_text))
            
            # Jaccard相似度
            if source_words and entity_words:
                intersection = len(source_words & entity_words)
                union = len(source_words | entity_words)
                similarity = intersection / union if union > 0 else 0
                
                if similarity > self._semantic_similarity_threshold:
                    associations.append({
                        'target_entity': entity.to_dict(),
                        'association_type': 'semantic_similarity',
                        'score': similarity
                    })
                    confidences.append(similarity)
                    reasoning.append(
                        f"语义相似度: '{source_entity.name}' 与 '{entity.name}' 共享 {intersection} 个关键词"
                    )
        
        return {
            'associations': associations,
            'confidences': confidences,
            'reasoning': reasoning
        }
    
    def _discover_temporal_associations(
        self,
        source_entity: Entity
    ) -> Dict[str, Any]:
        """时序关联发现 - 基于创建时间的相近性"""
        associations = []
        confidences = []
        reasoning = []
        
        source_time = source_entity.created_at
        
        for entity_id, entity in self._entities.items():
            if entity_id == source_entity.id:
                continue
            
            # 时间差（秒）
            time_diff = abs(entity.created_at - source_time)
            
            # 30天内创建的实体认为是时序相关
            if time_diff < 30 * 24 * 3600:
                confidence = 1.0 - (time_diff / (30 * 24 * 3600))
                
                associations.append({
                    'target_entity': entity.to_dict(),
                    'association_type': 'temporal_proximity',
                    'score': confidence,
                    'time_diff_days': time_diff / (24 * 3600)
                })
                confidences.append(confidence)
                reasoning.append(
                    f"时序接近: '{entity.name}' 在 {time_diff / (24 * 3600):.1f} 天内创建"
                )
        
        return {
            'associations': associations,
            'confidences': confidences,
            'reasoning': reasoning
        }
    
    def _discover_collaborative_associations(
        self,
        source_entity: Entity
    ) -> Dict[str, Any]:
        """协同过滤关联 - 基于共同交互模式"""
        associations = []
        confidences = []
        reasoning = []
        
        # 找出与源实体有相同关系的实体
        source_relations = self._source_target_index.get(source_entity.id, set())
        
        # 统计共同关系
        co_occurrence: Dict[str, int] = defaultdict(int)
        
        for rel_id in source_relations:
            relation = self._relations.get(rel_id)
            if not relation:
                continue
            
            # 找出其他与相同实体有关系的实体
            other_relations = self._source_target_index.get(relation.target_id, set())
            for other_rel_id in other_relations:
                other_relation = self._relations.get(other_rel_id)
                if other_relation and other_relation.target_id != source_entity.id:
                    co_occurrence[other_relation.target_id] += 1
        
        # 计算协同过滤得分
        for entity_id, count in co_occurrence.items():
            if entity_id not in self._entities:
                continue
            
            entity = self._entities[entity_id]
            
            # 归一化置信度
            max_count = max(co_occurrence.values()) if co_occurrence else 1
            confidence = count / max_count
            
            if confidence > 0.2:
                associations.append({
                    'target_entity': entity.to_dict(),
                    'association_type': 'collaborative_filtering',
                    'score': confidence,
                    'co_occurrence_count': count
                })
                confidences.append(confidence)
                reasoning.append(
                    f"协同过滤: '{entity.name}' 与 '{source_entity.name}' 有 {count} 个共同关联"
                )
        
        return {
            'associations': associations,
            'confidences': confidences,
            'reasoning': reasoning
        }
    
    def _discover_structural_associations(
        self,
        source_entity: Entity
    ) -> Dict[str, Any]:
        """结构化关联 - 基于图结构特征"""
        associations = []
        confidences = []
        reasoning = []
        
        # 1. 查找二度关联（朋友的朋友）
        first_degree = self._adjacency_list[source_entity.id]
        for rel_type, targets in first_degree.items():
            for target_id in targets:
                if target_id not in self._entities:
                    continue
                
                second_degree = self._adjacency_list.get(target_id, {})
                for second_rel_type, second_targets in second_degree.items():
                    for second_target_id in second_targets:
                        if second_target_id == source_entity.id:
                            continue
                        if second_target_id in first_degree.get(rel_type, set()):
                            continue  # 已是一度关联
                        
                        if second_target_id not in self._entities:
                            continue
                        
                        target_entity = self._entities[second_target_id]
                        
                        # 检查是否已存在
                        if not any(a['target_entity']['id'] == target_entity.id for a in associations):
                            confidence = 0.6
                            
                            associations.append({
                                'target_entity': target_entity.to_dict(),
                                'association_type': 'structural_bridge',
                                'score': confidence,
                                'bridge_entity': self._entities[target_id].to_dict() if target_id in self._entities else None
                            })
                            confidences.append(confidence)
                            reasoning.append(
                                f"结构桥接: '{target_entity.name}' 通过 '{self._entities[target_id].name}' 连接到 '{source_entity.name}'"
                            )
        
        # 2. 查找高连接度中心节点
        for entity_id, entity in self._entities.items():
            if entity_id == source_entity.id:
                continue
            
            # 计算连接度
            connections = len(self._adjacency_list.get(entity_id, {}).get(RelationType.RELATED_TO.value, set()))
            connections += len(self._reverse_adjacency.get(entity_id, {}).get(RelationType.RELATED_TO.value, set()))
            
            if connections >= 5:  # 高连接度阈值
                confidence = min(0.5, connections / 20)
                
                if not any(a['target_entity']['id'] == entity_id for a in associations):
                    associations.append({
                        'target_entity': entity.to_dict(),
                        'association_type': 'hub_discovery',
                        'score': confidence,
                        'connection_count': connections
                    })
                    confidences.append(confidence)
                    reasoning.append(
                        f"中心节点: '{entity.name}' 是高连接度节点({connections}个连接)"
                    )
        
        return {
            'associations': associations,
            'confidences': confidences,
            'reasoning': reasoning
        }
    
    # ==================== RAG+图谱结合 ====================
    
    async def rag_kg_joint_query(
        self,
        query: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """RAG+图谱联合查询"""
        
        # 1. 从查询中提取实体
        query_entities = self.query_entity(query, limit=3)
        
        # 2. 基于实体进行图谱检索
        kg_results = []
        for entity in query_entities:
            neighbors = self.get_neighbors(entity.id, max_depth=2)
            for rel_type, neighbors_list in neighbors.items():
                for neighbor in neighbors_list[:3]:
                    kg_results.append({
                        'entity': neighbor.to_dict(),
                        'relation': rel_type,
                        'source': entity.name
                    })
        
        # 3. 合并并排序结果
        # 优先返回有图谱关联的结果
        ranked_results = kg_results[:top_k]
        
        return {
            'query': query,
            'extracted_entities': [e.to_dict() for e in query_entities],
            'kg_results': ranked_results,
            'total_kg_results': len(kg_results),
            'joint_retrieval': len(kg_results) > 0
        }
    
    # ==================== 批量操作 ====================
    
    def batch_import_entities(self, entities: List[Dict[str, Any]]) -> int:
        """批量导入实体"""
        count = 0
        for entity_data in entities:
            entity = self.create_entity(
                name=entity_data['name'],
                entity_type=EntityType(entity_data.get('type', 'concept')),
                description=entity_data.get('description', ''),
                properties=entity_data.get('properties', {}),
                metadata=entity_data.get('metadata', {})
            )
            if entity:
                count += 1
        return count
    
    def batch_import_relations(self, relations: List[Dict[str, Any]]) -> int:
        """批量导入关系"""
        count = 0
        for rel_data in relations:
            # 通过名称查找实体ID
            source_entities = self.get_entities_by_name(rel_data['source'])
            target_entities = self.get_entities_by_name(rel_data['target'])
            
            if not source_entities or not target_entities:
                continue
            
            relation = self.create_relation(
                source_id=source_entities[0].id,
                target_id=target_entities[0].id,
                relation_type=RelationType(rel_data.get('type', 'related_to')),
                weight=rel_data.get('weight', 1.0)
            )
            if relation:
                count += 1
        return count
    
    # ==================== 工具方法 ====================
    
    def _generate_entity_id(self, name: str, entity_type: EntityType) -> str:
        """生成实体ID"""
        raw = f"{name}:{entity_type.value}"
        return f"ent_{hashlib.md5(raw.encode()).hexdigest()[:16]}"
    
    def _generate_relation_id(self, source_id: str, target_id: str, relation_type: RelationType) -> str:
        """生成关系ID"""
        raw = f"{source_id}:{target_id}:{relation_type.value}"
        return f"rel_{hashlib.md5(raw.encode()).hexdigest()[:16]}"
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            'entity_type_counts': dict(self._stats['entity_type_counts']),
            'relation_type_counts': dict(self._stats['relation_type_counts'])
        }
    
    def export_graph(self) -> Dict[str, Any]:
        """导出图谱"""
        return {
            'entities': [e.to_dict() for e in self._entities.values()],
            'relations': [r.to_dict() for r in self._relations.values()],
            'stats': self.get_stats()
        }
    
    def import_graph(self, data: Dict[str, Any]) -> bool:
        """导入图谱"""
        try:
            # 导入实体
            for entity_data in data.get('entities', []):
                self.create_entity(
                    name=entity_data['name'],
                    entity_type=EntityType(entity_data['type']),
                    description=entity_data.get('description', ''),
                    properties=entity_data.get('properties', {}),
                    metadata=entity_data.get('metadata', {})
                )
            
            # 导入关系
            for rel_data in data.get('relations', []):
                source = self.get_entities_by_name(rel_data['source_id'])
                target = self.get_entities_by_name(rel_data['target_id'])
                
                if source and target:
                    self.create_relation(
                        source_id=source[0].id,
                        target_id=target[0].id,
                        relation_type=RelationType(rel_data['type']),
                        weight=rel_data.get('weight', 1.0)
                    )
            
            return True
        except Exception as e:
            logger.error(f"图谱导入失败: {e}")
            return False


# 全局实例
_knowledge_graph_service: Optional[KnowledgeGraphService] = None


def get_knowledge_graph_service(config: Optional[Dict[str, Any]] = None) -> KnowledgeGraphService:
    """获取知识图谱服务实例"""
    global _knowledge_graph_service
    if _knowledge_graph_service is None:
        _knowledge_graph_service = KnowledgeGraphService(config)
    return _knowledge_graph_service


def create_knowledge_graph_service(config: Optional[Dict[str, Any]] = None) -> KnowledgeGraphService:
    """创建知识图谱服务实例（工厂函数）"""
    return KnowledgeGraphService(config)
