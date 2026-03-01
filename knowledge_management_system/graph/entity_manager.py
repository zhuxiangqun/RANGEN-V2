#!/usr/bin/env python3
"""
实体管理器
管理知识图谱中的实体（Entity）
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from ..utils.logger import get_logger
from .entity_normalizer import normalize_entity_name

logger = get_logger()


class EntityManager:
    """实体管理器"""
    
    def __init__(self, entities_path: str = "data/knowledge_management/graph/entities.json"):
        self.logger = logger
        self.entities_path = entities_path
        self._entities: Dict[str, Dict[str, Any]] = {}
        self._load_entities()
    
    def _load_entities(self):
        """加载实体数据"""
        try:
            import json
            from pathlib import Path
            
            path = Path(self.entities_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    self._entities = json.load(f)
                self.logger.info(f"已加载 {len(self._entities)} 个实体")
            else:
                self._entities = {}
                self._save_entities()
        except Exception as e:
            self.logger.error(f"加载实体失败: {e}")
            self._entities = {}
    
    def _save_entities(self):
        """保存实体数据"""
        try:
            import json
            from pathlib import Path
            
            path = Path(self.entities_path)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self._entities, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存实体失败: {e}")
    
    def find_entity_by_name(self, name: str, entity_type: Optional[str] = None, context: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        根据名称查找实体（🚀 P0修复：改进实体消歧，避免"Frances"匹配到"France"）
        
        Args:
            name: 实体名称（会自动规范化）
            entity_type: 可选的实体类型过滤（Person、Location等）
            context: 可选的上下文信息（用于消歧）
        
        Returns:
            匹配的实体列表（按匹配度排序）
        """
        # 🚀 优化：规范化查询名称
        normalized_name = normalize_entity_name(name)
        if not normalized_name:
            return []
        
        results = []
        normalized_name_lower = normalized_name.lower()
        normalized_name_words = normalized_name_lower.split()
        
        # 🚀 P0修复：先尝试精确匹配，然后按匹配度排序
        for entity in self._entities.values():
            entity_name = entity.get('name', '')
            entity_type_in_db = entity.get('type', 'Person')
            
            # 🚀 P0修复：实体类型过滤
            if entity_type and entity_type_in_db != entity_type:
                continue
            
            # 使用规范化后的名称进行匹配
            entity_name_normalized = normalize_entity_name(entity_name)
            entity_name_normalized_lower = entity_name_normalized.lower()
            entity_name_words = entity_name_normalized_lower.split()
            
            match_score = 0.0
            match_type = None
            
            # 1. 精确匹配（最高优先级）
            if entity_name_normalized_lower == normalized_name_lower:
                match_score = 1.0
                match_type = 'exact'
            # 2. 单词完全匹配（如"Frances Cleveland"匹配"Frances Cleveland"）
            elif normalized_name_words == entity_name_words:
                match_score = 0.95
                match_type = 'word_exact'
            # 3. 所有单词都匹配（顺序可能不同）
            elif set(normalized_name_words) == set(entity_name_words):
                match_score = 0.9
                match_type = 'word_set'
            # 4. 查询名称是实体名称的前缀（如"Frances"匹配"Frances Cleveland"）
            elif normalized_name_lower == entity_name_normalized_lower[:len(normalized_name_lower)] and len(normalized_name) >= 3:
                match_score = 0.8
                match_type = 'prefix'
            # 5. 实体名称是查询名称的前缀（如"Frances Cleveland"匹配"Frances"）
            elif entity_name_normalized_lower == normalized_name_lower[:len(entity_name_normalized_lower)] and len(entity_name_normalized) >= 3:
                match_score = 0.7
                match_type = 'entity_prefix'
            # 6. 🚀 P0修复：避免部分匹配导致混淆（如"Frances"不应匹配"France"）
            # 只有当查询名称是完整单词时才允许部分匹配
            elif len(normalized_name_words) == 1 and normalized_name_lower in entity_name_normalized_lower:
                # 检查是否是完整单词匹配（不是子串匹配）
                # 例如："frances"应该匹配"frances cleveland"，但不应该匹配"france"
                if normalized_name_lower in entity_name_words:
                    match_score = 0.6
                    match_type = 'word_contained'
                # 如果查询名称是实体名称的子串，但长度差异很大，可能是误匹配
                # 例如："frances"（7字符）不应匹配"france"（6字符），因为差异太小
                elif len(normalized_name) >= 5 and len(entity_name_normalized) >= 5:
                    # 计算相似度，如果相似度太低，拒绝匹配
                    similarity = len(normalized_name) / max(len(entity_name_normalized), len(normalized_name))
                    if similarity >= 0.8:  # 相似度阈值
                        match_score = 0.5
                        match_type = 'substring'
            
            # 🚀 P0修复：上下文消歧（如果提供上下文）
            if match_score > 0 and context:
                context_lower = context.lower()
                # 如果上下文包含实体名称，提高匹配分数
                if entity_name_normalized_lower in context_lower:
                    match_score += 0.1
                # 如果上下文包含实体类型相关的关键词，提高匹配分数
                if entity_type_in_db == 'Person' and any(word in context_lower for word in ['person', 'people', 'name', 'first', 'last', 'maiden']):
                    match_score += 0.05
                elif entity_type_in_db == 'Location' and any(word in context_lower for word in ['location', 'place', 'country', 'city', 'state']):
                    match_score += 0.05
            
            if match_score > 0:
                # 添加匹配信息到结果
                entity_with_score = entity.copy()
                entity_with_score['_match_score'] = match_score
                entity_with_score['_match_type'] = match_type
                results.append(entity_with_score)
        
        # 🚀 P0修复：按匹配分数排序，返回最佳匹配
        results.sort(key=lambda x: x.get('_match_score', 0.0), reverse=True)
        
        # 🚀 P0修复：如果最高分匹配是精确匹配，只返回精确匹配
        if results and results[0].get('_match_score', 0.0) >= 1.0:
            return [r for r in results if r.get('_match_score', 0.0) >= 1.0]
        
        return results
    
    def update_entity(
        self,
        entity_id: str,
        properties: Optional[Dict[str, Any]] = None,
        entity_type: Optional[str] = None
    ) -> bool:
        """
        更新实体属性（🚀 优化：支持属性合并）
        
        Args:
            entity_id: 实体ID
            properties: 要更新的属性（会合并到现有属性）
            entity_type: 实体类型（如果提供，会更新类型）
        
        Returns:
            是否更新成功
        """
        if entity_id not in self._entities:
            return False
        
        entity = self._entities[entity_id]
        
        # 合并属性
        if properties:
            existing_properties = entity.get('properties', {})
            # 新属性覆盖旧属性
            merged_properties = {**existing_properties, **properties}
            entity['properties'] = merged_properties
        
        # 更新类型（如果提供）
        if entity_type:
            entity['type'] = entity_type
        
        # 更新时间戳
        entity['updated_at'] = datetime.now().isoformat()
        
        # 保存
        self._save_entities()
        return True
    
    def create_entity(
        self,
        name: str,
        entity_type: str = "Person",
        properties: Optional[Dict[str, Any]] = None,
        skip_duplicate: bool = True,
        merge_properties: bool = True,  # 🚀 优化：新增参数，支持属性合并
        validate_quality: bool = True  # 🚀 新增：是否进行质量验证
    ) -> str:
        """
        创建实体（🆕 支持查重，🚀 优化：支持属性合并，🚀 新增：质量验证）
        
        Args:
            name: 实体名称
            entity_type: 实体类型（Person、Event、Location等）
            properties: 实体属性
            skip_duplicate: 如果发现重复实体，是否返回已存在的ID
            merge_properties: 如果实体已存在，是否合并属性（默认True）
            validate_quality: 是否进行质量验证（默认True）
        
        Returns:
            实体ID（如果重复且skip_duplicate=True，返回已存在的ID）
        """
        try:
            # 🚀 新增：质量验证
            if validate_quality:
                quality_result = self._validate_entity_quality(name, entity_type, properties)
                if not quality_result['is_valid']:
                    self.logger.warning(
                        f"跳过低质量实体，不创建: {quality_result.get('reason', '质量检查失败')} | "
                        f"名称: {name}, 类型: {entity_type}"
                    )
                    return ""
            
            # 🚀 优化：规范化实体名称
            normalized_name = normalize_entity_name(name, entity_type)
            if not normalized_name:
                self.logger.warning(f"实体名称规范化后为空，跳过: {name}")
                return ""
            
            # 🆕 查重处理（使用规范化后的名称）
            if skip_duplicate:
                existing_entities = self.find_entity_by_name(normalized_name)
                if existing_entities:
                    # 优先匹配相同类型的实体
                    for entity in existing_entities:
                        if entity.get('type') == entity_type:
                            entity_id = entity['id']
                            
                            # 🚀 优化：如果启用属性合并，更新实体
                            if merge_properties and properties:
                                self.update_entity(entity_id, properties=properties)
                                self.logger.debug(f"更新实体属性: {normalized_name} ({entity_type})，ID: {entity_id}")
                            
                            # 🚀 优化：如果名称被规范化，更新实体名称
                            if normalized_name != name:
                                self.update_entity(entity_id, properties=None, entity_type=None)
                                # 更新名称
                                entity = self._entities.get(entity_id)
                                if entity:
                                    entity['name'] = normalized_name
                                    self._save_entities()
                                    self.logger.debug(f"实体名称已规范化: {name} -> {normalized_name}")
                            
                            self.logger.debug(f"使用已存在的实体: {normalized_name} ({entity_type})，ID: {entity_id}")
                            return entity_id
                    
                    # 如果没有相同类型的，返回第一个
                    if existing_entities:
                        entity_id = existing_entities[0]['id']
                        
                        # 🚀 优化：如果启用属性合并，更新实体
                        if merge_properties and properties:
                            self.update_entity(entity_id, properties=properties, entity_type=entity_type)
                            self.logger.debug(f"更新实体属性和类型: {normalized_name}，ID: {entity_id}")
                        
                        # 🚀 优化：如果名称被规范化，更新实体名称
                        if normalized_name != name:
                            entity = self._entities.get(entity_id)
                            if entity:
                                entity['name'] = normalized_name
                                self._save_entities()
                                self.logger.debug(f"实体名称已规范化: {name} -> {normalized_name}")
                        
                        self.logger.debug(f"使用已存在的实体: {normalized_name}，ID: {entity_id}")
                        return entity_id
            
            entity_id = str(uuid.uuid4())
            
            self._entities[entity_id] = {
                'id': entity_id,
                'name': normalized_name,  # 🚀 优化：使用规范化后的名称
                'type': entity_type,
                'properties': properties or {},
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self._save_entities()
            if normalized_name != name:
                self.logger.info(f"创建实体: {normalized_name} ({entity_type}) [规范化自: {name}]")
            else:
                self.logger.info(f"创建实体: {normalized_name} ({entity_type})")
            return entity_id
            
        except Exception as e:
            self.logger.error(f"创建实体失败: {e}")
            return ""
    
    def _validate_entity_quality(
        self,
        name: str,
        entity_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """🚀 新增：验证实体质量
        
        Args:
            name: 实体名称
            entity_type: 实体类型
            properties: 实体属性
        
        Returns:
            验证结果字典，包含is_valid、reason、quality_score等字段
        """
        try:
            quality_score = 100
            issues = []
            
            # 1. 名称验证
            if not name or not isinstance(name, str):
                return {
                    'is_valid': False,
                    'reason': '实体名称为空或不是字符串',
                    'quality_score': 0
                }
            
            name_stripped = name.strip()
            if not name_stripped:
                return {
                    'is_valid': False,
                    'reason': '实体名称为空（只包含空白字符）',
                    'quality_score': 0
                }
            
            # 名称长度检查
            if len(name_stripped) < 1:
                return {
                    'is_valid': False,
                    'reason': '实体名称过短',
                    'quality_score': 0
                }
            
            if len(name_stripped) > 200:
                issues.append("实体名称过长（>200字符）")
                quality_score -= 20
            
            # 检查名称是否包含特殊字符（可能是错误）
            import re
            if re.search(r'[<>{}[\]\\|`~]', name_stripped):
                issues.append("实体名称包含特殊字符")
                quality_score -= 15
            
            # 检查名称是否主要是数字或符号
            if re.match(r'^[\d\s\-_\.]+$', name_stripped):
                issues.append("实体名称主要是数字或符号")
                quality_score -= 30
            
            # 2. 实体类型验证
            valid_types = ['Person', 'Event', 'Location', 'Organization', 'Concept', 'Entity']
            if entity_type not in valid_types:
                issues.append(f"实体类型不在标准类型列表中: {entity_type}")
                quality_score -= 10
            
            # 3. 属性验证
            if properties:
                # 检查属性值是否有效
                for key, value in properties.items():
                    if value is None or value == '' or value == 'null':
                        issues.append(f"属性 '{key}' 值为空")
                        quality_score -= 5
                    
                    # 检查属性值类型
                    if isinstance(value, str) and len(value) > 1000:
                        issues.append(f"属性 '{key}' 值过长（>1000字符）")
                        quality_score -= 5
            
            # 质量分数阈值：至少70分才通过
            is_valid = quality_score >= 70
            
            return {
                'is_valid': is_valid,
                'reason': '; '.join(issues) if issues else '质量检查通过',
                'quality_score': max(0, quality_score),
                'issues': issues
            }
            
        except Exception as e:
            self.logger.warning(f"实体质量验证失败: {e}")
            # 验证失败时，默认通过（避免误过滤）
            return {
                'is_valid': True,
                'reason': f'验证过程出错: {str(e)}',
                'quality_score': 50
            }
    
    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """获取实体"""
        return self._entities.get(entity_id)
    
    def list_entities(
        self, 
        entity_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """列出实体"""
        results = []
        for entity in self._entities.values():
            if entity_type is None or entity.get('type') == entity_type:
                results.append(entity)
                if len(results) >= limit:
                    break
        return results

