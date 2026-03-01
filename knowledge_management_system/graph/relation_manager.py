#!/usr/bin/env python3
"""
关系管理器
管理知识图谱中的关系（Relation）
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from ..utils.logger import get_logger

logger = get_logger()


class RelationManager:
    """关系管理器"""
    
    def __init__(self, relations_path: str = "data/knowledge_management/graph/relations.json"):
        self.logger = logger
        self.relations_path = relations_path
        self._relations: List[Dict[str, Any]] = []
        self._load_relations()
    
    def _load_relations(self):
        """加载关系数据"""
        try:
            import json
            from pathlib import Path
            
            path = Path(self.relations_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    self._relations = json.load(f)
                self.logger.info(f"已加载 {len(self._relations)} 条关系")
            else:
                self._relations = []
                self._save_relations()
        except Exception as e:
            self.logger.error(f"加载关系失败: {e}")
            self._relations = []
    
    def _save_relations(self):
        """保存关系数据"""
        try:
            import json
            from pathlib import Path
            
            path = Path(self.relations_path)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self._relations, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存关系失败: {e}")
    
    def update_relation(
        self,
        relation_id: str,
        properties: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None
    ) -> bool:
        """
        更新关系属性（🚀 优化：支持属性合并和置信度更新）
        
        Args:
            relation_id: 关系ID
            properties: 要更新的属性（会合并到现有属性）
            confidence: 置信度（如果提供且更高，会更新）
        
        Returns:
            是否更新成功
        """
        relation = None
        for r in self._relations:
            if r.get('id') == relation_id:
                relation = r
                break
        
        if not relation:
            return False
        
        # 合并属性
        if properties:
            existing_properties = relation.get('properties', {})
            merged_properties = {**existing_properties, **properties}
            relation['properties'] = merged_properties
        
        # 更新置信度（只更新为更高值）
        if confidence is not None:
            existing_confidence = relation.get('confidence', 0.0)
            if confidence > existing_confidence:
                relation['confidence'] = confidence
        
        # 保存
        self._save_relations()
        return True
    
    def create_relation(
        self,
        entity1_id: str,
        entity2_id: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
        skip_duplicate: bool = True,
        merge_properties: bool = True,  # 🚀 优化：新增参数，支持属性合并
        validate_quality: bool = True,  # 🚀 新增：是否进行质量验证
        entity_manager=None  # 🚀 新增：实体管理器（用于验证实体是否存在）
    ) -> str:
        """
        创建关系（🆕 支持查重，🚀 优化：支持属性合并，🚀 新增：质量验证）
        
        Args:
            entity1_id: 实体1的ID
            entity2_id: 实体2的ID
            relation_type: 关系类型（mother_of、president_of等）
            properties: 关系属性
            confidence: 置信度
            skip_duplicate: 如果发现重复关系，是否返回已存在的ID
            merge_properties: 如果关系已存在，是否合并属性（默认True）
            validate_quality: 是否进行质量验证（默认True）
            entity_manager: 实体管理器（用于验证实体是否存在）
        
        Returns:
            关系ID（如果重复且skip_duplicate=True，返回已存在的ID）
        """
        try:
            # 🚀 新增：质量验证
            if validate_quality:
                quality_result = self._validate_relation_quality(
                    entity1_id, entity2_id, relation_type, confidence, entity_manager
                )
                if not quality_result['is_valid']:
                    self.logger.warning(
                        f"跳过低质量关系，不创建: {quality_result.get('reason', '质量检查失败')} | "
                        f"{entity1_id} --[{relation_type}]--> {entity2_id}"
                    )
                    return ""
            
            # 🆕 查重处理
            if skip_duplicate:
                existing_relations = self.find_relations(
                    entity_id=entity1_id,
                    relation_type=relation_type
                )
                for relation in existing_relations:
                    if relation.get('entity2_id') == entity2_id:
                        relation_id = relation['id']
                        
                        # 🚀 优化：如果启用属性合并，更新关系
                        if merge_properties and properties:
                            # 🎯 关键修复：确保属性不为空时才更新
                            filtered_properties = {
                                k: v for k, v in properties.items()
                                if v is not None and v != '' and v != 'null'
                            }
                            if filtered_properties:
                                self.update_relation(
                                    relation_id,
                                    properties=filtered_properties,
                                    confidence=confidence
                                )
                                self.logger.info(f"✅ 更新关系属性: {entity1_id} --[{relation_type}]--> {entity2_id}，ID: {relation_id}，属性: {filtered_properties}")
                        
                        self.logger.debug(f"使用已存在的关系: {entity1_id} --[{relation_type}]--> {entity2_id}，ID: {relation_id}")
                        return relation_id
            
            relation_id = str(uuid.uuid4())
            
            # 🎯 关键修复：确保属性不为空时才保存
            filtered_properties = {}
            if properties:
                filtered_properties = {
                    k: v for k, v in properties.items()
                    if v is not None and v != '' and v != 'null'
                }
            
            relation = {
                'id': relation_id,
                'entity1_id': entity1_id,
                'entity2_id': entity2_id,
                'type': relation_type,
                'properties': filtered_properties,  # 🎯 关键修复：使用过滤后的属性
                'confidence': confidence,
                'created_at': datetime.now().isoformat()
            }
            
            self._relations.append(relation)
            self._save_relations()
            if filtered_properties:
                self.logger.info(f"✅ 创建关系: {entity1_id} --[{relation_type}]--> {entity2_id}，属性: {filtered_properties}")
            else:
                self.logger.info(f"创建关系: {entity1_id} --[{relation_type}]--> {entity2_id}")
            return relation_id
            
        except Exception as e:
            self.logger.error(f"创建关系失败: {e}")
            return ""
    
    def _validate_relation_quality(
        self,
        entity1_id: str,
        entity2_id: str,
        relation_type: str,
        confidence: float,
        entity_manager=None
    ) -> Dict[str, Any]:
        """🚀 新增：验证关系质量
        
        Args:
            entity1_id: 实体1的ID
            entity2_id: 实体2的ID
            relation_type: 关系类型
            confidence: 置信度
            entity_manager: 实体管理器（用于验证实体是否存在）
        
        Returns:
            验证结果字典，包含is_valid、reason、quality_score等字段
        """
        try:
            quality_score = 100
            issues = []
            
            # 1. 基本验证
            if not entity1_id or not entity2_id:
                return {
                    'is_valid': False,
                    'reason': '实体ID为空',
                    'quality_score': 0
                }
            
            # 2. 自环检查（实体指向自己）
            if entity1_id == entity2_id:
                return {
                    'is_valid': False,
                    'reason': '自环关系（实体指向自己）',
                    'quality_score': 0
                }
            
            # 3. 实体存在性验证
            if entity_manager:
                entity1 = entity_manager.get_entity(entity1_id)
                entity2 = entity_manager.get_entity(entity2_id)
                
                if not entity1:
                    return {
                        'is_valid': False,
                        'reason': f'实体1不存在: {entity1_id}',
                        'quality_score': 0
                    }
                
                if not entity2:
                    return {
                        'is_valid': False,
                        'reason': f'实体2不存在: {entity2_id}',
                        'quality_score': 0
                    }
            
            # 4. 关系类型验证
            if not relation_type or not isinstance(relation_type, str):
                return {
                    'is_valid': False,
                    'reason': '关系类型为空或不是字符串',
                    'quality_score': 0
                }
            
            relation_type_stripped = relation_type.strip()
            if not relation_type_stripped:
                return {
                    'is_valid': False,
                    'reason': '关系类型为空（只包含空白字符）',
                    'quality_score': 0
                }
            
            # 关系类型长度检查
            if len(relation_type_stripped) > 100:
                issues.append("关系类型过长（>100字符）")
                quality_score -= 15
            
            # 检查关系类型是否包含特殊字符
            import re
            if re.search(r'[<>{}[\]\\|`~]', relation_type_stripped):
                issues.append("关系类型包含特殊字符")
                quality_score -= 10
            
            # 5. 置信度验证
            if confidence < 0.0 or confidence > 1.0:
                return {
                    'is_valid': False,
                    'reason': f'置信度超出范围: {confidence}（应在0.0-1.0之间）',
                    'quality_score': 0
                }
            
            if confidence < 0.3:
                issues.append(f"置信度过低: {confidence}")
                quality_score -= 30
            
            if confidence < 0.5:
                issues.append(f"置信度较低: {confidence}")
                quality_score -= 15
            
            # 质量分数阈值：至少70分才通过
            is_valid = quality_score >= 70
            
            return {
                'is_valid': is_valid,
                'reason': '; '.join(issues) if issues else '质量检查通过',
                'quality_score': max(0, quality_score),
                'issues': issues
            }
            
        except Exception as e:
            self.logger.warning(f"关系质量验证失败: {e}")
            # 验证失败时，默认通过（避免误过滤）
            return {
                'is_valid': True,
                'reason': f'验证过程出错: {str(e)}',
                'quality_score': 50
            }
    
    def find_relations(
        self,
        entity_id: Optional[str] = None,
        relation_type: Optional[str] = None,
        direction: str = "both"  # "both"|"out"|"in"
    ) -> List[Dict[str, Any]]:
        """
        查找关系
        
        Args:
            entity_id: 实体ID（可选）
            relation_type: 关系类型（可选）
            direction: 方向（both=双向, out=出边, in=入边）
        
        Returns:
            关系列表
        """
        results = []
        
        for relation in self._relations:
            match = True
            
            if entity_id:
                if direction == "out":
                    match = relation.get('entity1_id') == entity_id
                elif direction == "in":
                    match = relation.get('entity2_id') == entity_id
                else:  # both
                    match = (relation.get('entity1_id') == entity_id or 
                            relation.get('entity2_id') == entity_id)
            
            if match and relation_type:
                match = relation.get('type') == relation_type
            
            if match:
                results.append(relation)
        
        return results
    
    def find_path(
        self,
        entity1_id: str,
        entity2_id: str,
        max_hops: int = 3
    ) -> List[List[Dict[str, Any]]]:
        """
        查找两个实体之间的路径（多跳推理）
        
        Args:
            entity1_id: 起始实体ID
            entity2_id: 目标实体ID
            max_hops: 最大跳数
        
        Returns:
            路径列表（每条路径是关系列表）
        """
        # TODO: 实现路径查找算法（BFS或DFS）
        self.logger.warning("路径查找功能待实现")
        return []

