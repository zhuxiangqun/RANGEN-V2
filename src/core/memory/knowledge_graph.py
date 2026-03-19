#!/usr/bin/env python3
"""
知识图谱 - 用于记忆系统的实体关系建模

功能:
- 实体管理
- 关系建模
- 语义查询
- 用户偏好提取
"""

import time
import uuid
from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class EntityType(str, Enum):
    """实体类型"""
    USER = "user"
    AGENT = "agent"
    SKILL = "skill"
    TASK = "task"
    CONCEPT = "concept"
    TOOL = "tool"
    MEMORY = "memory"
    PREFERENCE = "preference"


class RelationType(str, Enum):
    """关系类型"""
    KNOWS = "knows"
    USES = "uses"
    PREFERS = "prefers"
    BELONGS_TO = "belongs_to"
    RELATED_TO = "related_to"
    EXECUTED_BY = "executed_by"
    DEPENDS_ON = "depends_on"
    SIMILAR_TO = "similar_to"


@dataclass
class Entity:
    """实体"""
    entity_id: str
    name: str
    entity_type: EntityType
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "type": self.entity_type.value,
            "properties": self.properties,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        }


@dataclass
class Relation:
    """关系"""
    relation_id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "source": self.source_id,
            "target": self.target_id,
            "type": self.relation_type.value,
            "weight": self.weight,
            "properties": self.properties,
            "created_at": self.created_at
        }


class KnowledgeGraph:
    """
    知识图谱
    
    支持实体和关系的存储、查询、推理
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or "./data/knowledge_graph.json"
        self._entities: Dict[str, Entity] = {}
        self._relations: Dict[str, Relation] = {}
        self._index_by_type: Dict[EntityType, Set[str]] = {}
        self._index_by_name: Dict[str, str] = {}
        self._relation_index: Dict[Tuple[str, str], List[str]] = {}
        self._load()
    
    def add_entity(self, name: str, entity_type: EntityType, 
                   properties: Optional[Dict[str, Any]] = None) -> Entity:
        """添加实体"""
        entity_id = f"{entity_type.value}_{uuid.uuid4().hex[:8]}"
        
        entity = Entity(
            entity_id=entity_id,
            name=name,
            entity_type=entity_type,
            properties=properties or {}
        )
        
        self._entities[entity_id] = entity
        self._index_by_name[name.lower()] = entity_id
        
        if entity_type not in self._index_by_type:
            self._index_by_type[entity_type] = set()
        self._index_by_type[entity_type].add(entity_id)
        
        self._save()
        return entity
    
    def add_relation(self, source_id: str, target_id: str,
                    relation_type: RelationType,
                    weight: float = 1.0,
                    properties: Optional[Dict[str, Any]] = None) -> Relation:
        """添加关系"""
        if source_id not in self._entities or target_id not in self._entities:
            raise ValueError("Source or target entity not found")
        
        relation_id = f"rel_{uuid.uuid4().hex[:8]}"
        
        relation = Relation(
            relation_id=relation_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            weight=weight,
            properties=properties or {}
        )
        
        self._relations[relation_id] = relation
        
        key = (source_id, target_id)
        if key not in self._relation_index:
            self._relation_index[key] = []
        self._relation_index[key].append(relation_id)
        
        self._save()
        return relation
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """获取实体"""
        return self._entities.get(entity_id)
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """获取指定类型的所有实体"""
        entity_ids = self._index_by_type.get(entity_type, set())
        return [self._entities[eid] for eid in entity_ids if eid in self._entities]
    
    def find_entity_by_name(self, name: str) -> Optional[Entity]:
        """根据名称查找实体"""
        entity_id = self._index_by_name.get(name.lower())
        return self._entities.get(entity_id) if entity_id else None
    
    def get_relations(self, entity_id: str, 
                     direction: str = "out") -> List[Tuple[Relation, Entity]]:
        """
        获取实体的关系
        
        Args:
            entity_id: 实体ID
            direction: "out"(出), "in"(入), "both"(双向)
            
        Returns:
            [(relation, related_entity), ...]
        """
        results = []
        
        if direction in ("out", "both"):
            for relation in self._relations.values():
                if relation.source_id == entity_id:
                    target = self._entities.get(relation.target_id)
                    if target:
                        results.append((relation, target))
        
        if direction in ("in", "both"):
            for relation in self._relations.values():
                if relation.target_id == entity_id:
                    source = self._entities.get(relation.source_id)
                    if source:
                        results.append((relation, source))
        
        return results
    
    def get_preferences(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户偏好"""
        preferences = []
        
        for relation in self._relations.values():
            if relation.source_id == user_id and relation.relation_type == RelationType.PREFERS:
                target = self._entities.get(relation.target_id)
                if target:
                    preferences.append({
                        "preference": target.name,
                        "weight": relation.weight,
                        "properties": relation.properties,
                        "entity": target.to_dict()
                    })
        
        return sorted(preferences, key=lambda x: x["weight"], reverse=True)
    
    def learn_preference(self, user_id: str, preference: str, weight: float = 1.0):
        """
        学习用户偏好
        
        Args:
            user_id: 用户ID
            preference: 偏好内容
            weight: 偏好权重
        """
        entity_type = EntityType.PREFERENCE
        
        pref_entity = self.add_entity(
            name=preference,
            entity_type=entity_type,
            properties={"learned_from": user_id}
        )
        
        self.add_relation(
            source_id=user_id,
            target_id=pref_entity.entity_id,
            relation_type=RelationType.PREFERS,
            weight=weight
        )
    
    def find_similar_entities(self, entity_id: str, limit: int = 5) -> List[Tuple[Entity, float]]:
        """
        查找相似实体
        
        Args:
            entity_id: 实体ID
            limit: 返回数量
            
        Returns:
            [(entity, similarity_score), ...]
        """
        entity = self._entities.get(entity_id)
        if not entity:
            return []
        
        scores = []
        target_types = {RelationType.SIMILAR_TO, RelationType.RELATED_TO}
        
        for relation in self._relations.values():
            if relation.relation_type in target_types:
                if relation.source_id == entity_id:
                    target = self._entities.get(relation.target_id)
                    if target:
                        scores.append((target, relation.weight))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:limit]
    
    def query_path(self, source_id: str, target_id: str, 
                   max_depth: int = 3) -> List[List[str]]:
        """
        查询两个实体之间的路径
        
        Args:
            source_id: 起始实体
            target_id: 目标实体
            max_depth: 最大深度
            
        Returns:
            [[entity_id, ...], ...] 路径列表
        """
        paths = []
        
        def dfs(current: str, target: str, path: List[str], depth: int):
            if depth > max_depth:
                return
            if current == target:
                paths.append(path.copy())
                return
            
            for relation, next_entity in self.get_relations(current, "out"):
                if next_entity.entity_id not in path:
                    path.append(next_entity.entity_id)
                    dfs(next_entity.entity_id, target, path, depth + 1)
                    path.pop()
        
        dfs(source_id, target_id, [source_id], 0)
        return paths
    
    def _save(self):
        """保存到文件"""
        try:
            import os
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                data = {
                    "entities": {k: v.to_dict() for k, v in self._entities.items()},
                    "relations": {k: v.to_dict() for k, v in self._relations.items()}
                }
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _load(self):
        """从文件加载"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                for eid, edata in data.get("entities", {}).items():
                    entity = Entity(
                        entity_id=edata["entity_id"],
                        name=edata["name"],
                        entity_type=EntityType(edata["type"]),
                        properties=edata.get("properties", {}),
                        created_at=edata.get("created_at", time.time()),
                        updated_at=edata.get("updated_at", time.time()),
                        metadata=edata.get("metadata", {})
                    )
                    self._entities[eid] = entity
                    self._index_by_name[entity.name.lower()] = eid
                    
                    if entity.entity_type not in self._index_by_type:
                        self._index_by_type[entity.entity_type] = set()
                    self._index_by_type[entity.entity_type].add(eid)
                
                for rid, rdata in data.get("relations", {}).items():
                    relation = Relation(
                        relation_id=rdata["relation_id"],
                        source_id=rdata["source"],
                        target_id=rdata["target"],
                        relation_type=RelationType(rdata["type"]),
                        weight=rdata.get("weight", 1.0),
                        properties=rdata.get("properties", {}),
                        created_at=rdata.get("created_at", time.time())
                    )
                    self._relations[rid] = relation
                    
                    key = (relation.source_id, relation.target_id)
                    if key not in self._relation_index:
                        self._relation_index[key] = []
                    self._relation_index[key].append(rid)
        except Exception:
            pass
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_entities": len(self._entities),
            "total_relations": len(self._relations),
            "entity_types": {t.value: len(ids) for t, ids in self._index_by_type.items()},
            "relation_types": self._get_relation_type_counts()
        }
    
    def _get_relation_type_counts(self) -> Dict[str, int]:
        counts = {}
        for relation in self._relations.values():
            rtype = relation.relation_type.value
            counts[rtype] = counts.get(rtype, 0) + 1
        return counts


_kg_instance: Optional[KnowledgeGraph] = None

def get_knowledge_graph() -> KnowledgeGraph:
    """获取知识图谱实例"""
    global _kg_instance
    if _kg_instance is None:
        _kg_instance = KnowledgeGraph()
    return _kg_instance
