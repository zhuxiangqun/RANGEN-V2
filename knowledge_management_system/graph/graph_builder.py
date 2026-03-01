#!/usr/bin/env python3
"""
图谱构建器
从各种数据源构建知识图谱
"""

from typing import Dict, List, Any, Optional
from .entity_manager import EntityManager
from .relation_manager import RelationManager
from ..utils.logger import get_logger
# 🚀 统一使用Jina服务（可选，用于rerank）
from ..utils.jina_service import get_jina_service
# 🆕 使用TextProcessor进行向量化（支持本地模型fallback）
from ..modalities.text_processor import TextProcessor

logger = get_logger()


class GraphBuilder:
    """图谱构建器"""
    
    def __init__(self, text_processor: Optional[TextProcessor] = None):
        self.logger = logger
        self.entity_manager = EntityManager()
        self.relation_manager = RelationManager()
        # 🆕 优先使用TextProcessor（支持本地模型fallback）
        self.text_processor = text_processor or TextProcessor()
        # 🚀 Jina服务（可选，用于rerank，如果API key可用）
        self.jina_service = get_jina_service()
    
    def build_from_text(
        self,
        text: str,
        use_ner: bool = True,
        use_re: bool = True
    ) -> Dict[str, Any]:
        """
        从文本构建知识图谱（🚀 使用Jina Embedding和Rerank）
        
        Args:
            text: 文本内容
            use_ner: 是否使用命名实体识别（通过embedding进行语义理解）
            use_re: 是否使用关系提取（通过embedding进行语义理解）
        
        Returns:
            构建结果（实体数、关系数等）
        """
        entities_created = 0
        relations_created = 0
        
        try:
            # 🆕 优先使用TextProcessor（支持本地模型fallback）
            text_embedding = self.text_processor.encode(text)
            if text_embedding is None:
                self.logger.warning("文本向量化失败，无法进行智能提取")
                return {
                    'entities_created': 0,
                    'relations_created': 0,
                    'status': 'embedding_failed'
                }
            
            # 🚀 方法1: 使用embedding进行实体识别（简单的语义匹配）
            if use_ner:
                entities = self._extract_entities_with_embedding(text, text_embedding)
                for entity in entities:
                    entity_id = self.entity_manager.create_entity(
                        name=entity['name'],
                        entity_type=entity.get('type', 'Entity'),
                        skip_duplicate=True,
                        validate_quality=True  # 🚀 新增：启用质量验证
                    )
                    if entity_id:
                        # 检查是否是新创建的
                        existing = self.entity_manager.find_entity_by_name(entity['name'])
                        if existing and existing[0].get('id') == entity_id:
                            entities_created += 1
            
            # 🚀 方法2: 使用embedding进行关系提取
            if use_re:
                relations = self._extract_relations_with_embedding(text, text_embedding)
                for relation in relations:
                    # 查找实体ID
                    entity1_list = self.entity_manager.find_entity_by_name(relation['entity1'])
                    entity2_list = self.entity_manager.find_entity_by_name(relation['entity2'])
                    
                    if entity1_list and entity2_list:
                        entity1_id = entity1_list[0].get('id')
                        entity2_id = entity2_list[0].get('id')
                        
                        # 🚀 优化：跳过自环关系（实体指向自己）
                        if entity1_id == entity2_id:
                            self.logger.debug(f"跳过自环关系: {relation['entity1']} -> {relation['entity2']} ({relation.get('relation', 'unknown')})")
                            continue
                        
                        relation_id = self.relation_manager.create_relation(
                            entity1_id=entity1_id,
                            entity2_id=entity2_id,
                            relation_type=relation['relation'],
                            confidence=relation.get('confidence', 0.7),
                            skip_duplicate=True,
                            validate_quality=True,  # 🚀 新增：启用质量验证
                            entity_manager=self.entity_manager  # 🚀 新增：传递实体管理器用于验证
                        )
                        if relation_id:
                            # 检查是否是新创建的关系
                            existing_relations = self.relation_manager.find_relations(
                                entity_id=entity1_id,
                                relation_type=relation['relation']
                            )
                            is_new = not any(
                                r.get('entity2_id') == entity2_id 
                                for r in existing_relations
                                if r.get('id') != relation_id
                            )
                            if is_new:
                                relations_created += 1
            
            self.logger.info(f"从文本构建图谱: {entities_created}个实体, {relations_created}条关系")
            
            return {
                'entities_created': entities_created,
                'relations_created': relations_created,
                'status': 'success'
            }
            
        except Exception as e:
            self.logger.error(f"从文本构建图谱失败: {e}")
            return {
                'entities_created': entities_created,
                'relations_created': relations_created,
                'status': 'error',
                'error': str(e)
            }
    
    def _extract_entities_with_embedding(
        self,
        text: str,
        text_embedding: Any
    ) -> List[Dict[str, Any]]:
        """
        使用Jina Embedding进行实体识别（🚀 改进：智能类型识别）
        
        Args:
            text: 文本内容
            text_embedding: 文本的embedding向量
        
        Returns:
            实体列表
        """
        entities = []
        
        try:
            # 🚀 改进：使用多种模式提取实体并智能识别类型
            import re
            
            # 模式1: 人名（首字母大写，包含空格）
            person_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
            names = re.findall(person_pattern, text)
            
            # 模式2: 地名（城市、国家等，通常以特定后缀结尾或出现在特定上下文）
            location_patterns = [
                r'\b[A-Z][a-z]+(?:ia|land|stan|city|burg|ton|ville|polis|burgh)\b',  # 地名后缀
                r'\b(?:New|Old|North|South|East|West|Upper|Lower)\s+[A-Z][a-z]+\b',  # 复合地名
            ]
            locations = []
            for pattern in location_patterns:
                locations.extend(re.findall(pattern, text, re.IGNORECASE))
            
            # 模式3: 组织/机构（通常包含 Organization, Company, University 等词）
            org_keywords = ['University', 'College', 'Company', 'Corporation', 'Organization', 
                          'Foundation', 'Institute', 'Society', 'Club', 'Team']
            organizations = []
            for keyword in org_keywords:
                org_pattern = r'\b[A-Z][a-z]+\s+{}(?:\s+of\s+[A-Z][a-z]+)?\b'.format(keyword)
                organizations.extend(re.findall(org_pattern, text))
            
            # 模式4: 事件（包含时间或事件关键词）
            event_keywords = ['War', 'Battle', 'Revolution', 'Convention', 'Conference', 
                            'Festival', 'Award', 'Prize', 'Championship', 'Olympics']
            events = []
            for keyword in event_keywords:
                event_pattern = r'\b(?:the\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+{}\b'.format(keyword)
                events.extend(re.findall(event_pattern, text))
            
            # 🆕 改进：使用TextProcessor进行语义类型分类（支持本地模型fallback）
            # 优先使用TextProcessor，如果不可用则尝试Jina服务
            text_processor = self.text_processor
            jina_service = self.jina_service if (self.jina_service and self.jina_service.api_key) else None
            if text_processor or jina_service:
                # 构建类型分类提示词
                type_keywords = {
                    'Person': ['person', 'human', 'individual', 'people', 'man', 'woman', 'president', 'author', 'artist'],
                    'Location': ['place', 'location', 'city', 'country', 'region', 'state', 'area', 'geography'],
                    'Organization': ['organization', 'company', 'institution', 'university', 'corporation', 'group'],
                    'Event': ['event', 'happening', 'occurrence', 'war', 'battle', 'conference', 'festival'],
                    'Date': ['date', 'time', 'year', 'month', 'day', 'period', 'era', 'century'],
                    'Work': ['book', 'novel', 'movie', 'film', 'song', 'album', 'artwork', 'literature']
                }
                
                # 🚀 优化：批量向量化实体名称，提升性能
                import numpy as np
                
                # 收集所有需要分类的实体
                entities_to_classify = []
                entity_indices = {}  # 映射：实体名称 -> 在entities_to_classify中的索引
                
                # 处理提取的人名
                common_words = ['The', 'This', 'That', 'What', 'Who', 'When', 'Where', 'How']
                for name in names:
                    if name.split()[0] not in common_words and len(name.split()) >= 2:
                        entities_to_classify.append((name, text))
                        entity_indices[name] = len(entities_to_classify) - 1
                
                # 批量向量化实体名称
                if entities_to_classify:
                    entity_texts = [f"{name} {context[:100]}" for name, context in entities_to_classify]
                    # 🆕 优先使用TextProcessor（支持本地模型fallback）
                    if text_processor:
                        entity_embeddings = text_processor.encode(entity_texts)
                    elif jina_service:
                        entity_embeddings = jina_service.get_embeddings(entity_texts)
                    else:
                        entity_embeddings = None
                    
                    # 预加载所有类型关键词的embeddings（只加载一次）
                    all_keyword_embeddings = {}
                    for entity_type, keywords in type_keywords.items():
                        # 🆕 优先使用TextProcessor
                        if text_processor:
                            keyword_embs = text_processor.encode(keywords)
                        elif jina_service:
                            keyword_embs = jina_service.get_embeddings(keywords)
                        else:
                            keyword_embs = None
                        if keyword_embs:
                            all_keyword_embeddings[entity_type] = keyword_embs
                else:
                    entity_embeddings = None
                    all_keyword_embeddings = {}
                
                def classify_entity(entity_name: str, context_text: str, entity_emb: Any = None) -> str:
                    """使用语义相似度分类实体类型（支持批量处理）"""
                    try:
                        # 如果提供了预计算的embedding，直接使用
                        if entity_emb is None:
                            # 回退到单独向量化
                            # 🆕 优先使用TextProcessor（支持本地模型fallback）
                            entity_text = f"{entity_name} {context_text[:100]}"
                            if text_processor:
                                entity_emb = text_processor.encode(entity_text)
                            elif jina_service:
                                entity_emb = jina_service.get_embedding(entity_text)
                            else:
                                return self._simple_classify(entity_name)
                            if entity_emb is None:
                                return self._simple_classify(entity_name)
                        
                        max_similarity = 0.0
                        best_type = 'Person'  # 默认类型
                        
                        # 使用预加载的关键词embeddings
                        for entity_type, keyword_embs in all_keyword_embeddings.items():
                            # 计算与所有关键词的平均相似度
                            similarities = []
                            for kw_emb in keyword_embs:
                                if kw_emb is not None:
                                    similarity = np.dot(entity_emb, kw_emb) / (
                                        np.linalg.norm(entity_emb) * np.linalg.norm(kw_emb) + 1e-8
                                    )
                                    similarities.append(similarity)
                            
                            if similarities:
                                avg_similarity = np.mean(similarities)
                                if avg_similarity > max_similarity:
                                    max_similarity = avg_similarity
                                    best_type = entity_type
                        
                        # 如果相似度太低，使用简单分类
                        if max_similarity < 0.3:
                            return self._simple_classify(entity_name)
                        
                        return best_type
                    except Exception:
                        return self._simple_classify(entity_name)
                
                # 批量分类实体
                if entity_embeddings and len(entity_embeddings) == len(entities_to_classify):
                    for idx, (name, context) in enumerate(entities_to_classify):
                        if idx < len(entity_embeddings) and entity_embeddings[idx] is not None:
                            entity_type = classify_entity(name, context, entity_embeddings[idx])
                            entities.append({
                                'name': name,
                                'type': entity_type,
                                'confidence': 0.7 if entity_type == 'Person' else 0.6
                            })
                        else:
                            # 回退到简单分类
                            entity_type = self._simple_classify(name)
                            entities.append({
                                'name': name,
                                'type': entity_type,
                                'confidence': 0.6
                            })
                else:
                    # 如果批量向量化失败，回退到逐个处理
                    for name, context in entities_to_classify:
                        entity_type = classify_entity(name, context)
                        entities.append({
                            'name': name,
                            'type': entity_type,
                            'confidence': 0.7 if entity_type == 'Person' else 0.6
                        })
                
                
            else:
                # 如果没有Jina服务，使用简单分类
                def classify_entity(entity_name: str, context_text: str) -> str:
                    return self._simple_classify(entity_name)
            
            # 处理提取的人名（已在批量处理中完成，这里跳过）
            
            # 处理提取的地点、组织、事件（使用简单分类，因为批量处理主要针对人名）
            for location in set(locations):
                if jina_service and jina_service.api_key:
                    entity_type = classify_entity(location, text)
                else:
                    entity_type = self._simple_classify(location)
                entities.append({
                    'name': location,
                    'type': entity_type,
                    'confidence': 0.7
                })
            
            # 处理提取的组织
            for org in set(organizations):
                if jina_service and jina_service.api_key:
                    entity_type = classify_entity(org, text)
                else:
                    entity_type = self._simple_classify(org)
                entities.append({
                    'name': org,
                    'type': entity_type,
                    'confidence': 0.75
                })
            
            # 处理提取的事件
            for event in set(events):
                if jina_service and jina_service.api_key:
                    entity_type = classify_entity(event, text)
                else:
                    entity_type = self._simple_classify(event)
                entities.append({
                    'name': event,
                    'type': entity_type,
                    'confidence': 0.7
                })
        
        except Exception as e:
            self.logger.debug(f"实体提取失败: {e}")
        
        return entities
    
    def _simple_classify(self, entity_name: str) -> str:
        """简单的实体类型分类（基于命名模式）"""
        import re
        
        # 地点模式
        if re.search(r'(?:ia|land|stan|city|burg|ton|ville|polis|burgh|York|Angeles|States)$', entity_name, re.IGNORECASE):
            return 'Location'
        
        # 组织模式
        if re.search(r'(?:University|College|Company|Corporation|Organization|Foundation|Institute|Society|Club|Team)$', entity_name):
            return 'Organization'
        
        # 事件模式
        if re.search(r'(?:War|Battle|Revolution|Convention|Conference|Festival|Award|Prize|Championship|Olympics)$', entity_name):
            return 'Event'
        
        # 日期模式（数字年份）
        if re.search(r'^\d{4}$|^(?:January|February|March|April|May|June|July|August|September|October|November|December)', entity_name, re.IGNORECASE):
            return 'Date'
        
        # 默认：人名
        return 'Person'
    
    def _extract_relations_with_embedding(
        self,
        text: str,
        text_embedding: Any
    ) -> List[Dict[str, Any]]:
        """
        使用Jina Embedding进行关系提取
        
        Args:
            text: 文本内容
            text_embedding: 文本的embedding向量
        
        Returns:
            关系列表
        """
        relations = []
        
        try:
            # 🚀 使用embedding计算文本与关系关键词的相似度
            relation_keywords = [
                "mother of", "father of", "president of", "born in",
                "married to", "related to", "worked with", "founded"
            ]
            
            # 🆕 使用TextProcessor计算关系关键词的相似度（支持本地模型fallback）
            if self.text_processor:
                keyword_embeddings = self.text_processor.encode(relation_keywords)
            elif self.jina_service and self.jina_service.api_key:
                keyword_embeddings = self.jina_service.get_embeddings(relation_keywords)
            else:
                keyword_embeddings = None
            if keyword_embeddings:
                import numpy as np
                similarities = []
                for kw_emb in keyword_embeddings:
                    if kw_emb is not None:
                        similarity = np.dot(text_embedding, kw_emb) / (
                            np.linalg.norm(text_embedding) * np.linalg.norm(kw_emb)
                        )
                        similarities.append(similarity)
                    else:
                        similarities.append(0.0)
                
                # 找到相似度最高的关系关键词
                max_sim_idx = np.argmax(similarities) if similarities else -1
                if max_sim_idx >= 0 and similarities[max_sim_idx] > 0.5:
                    relation_type = relation_keywords[max_sim_idx].replace(" ", "_")
                    
                    # 提取实体名称
                    import re
                    names = re.findall(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b', text)
                    if len(names) >= 2:
                        relations.append({
                            'entity1': names[0],
                            'entity2': names[1],
                            'relation': relation_type,
                            'confidence': float(similarities[max_sim_idx])
                        })
        
        except Exception as e:
            self.logger.debug(f"关系提取失败: {e}")
        
        return relations
    
    def build_from_structured_data(
        self,
        data: List[Dict[str, Any]],
        merge_properties: bool = True  # 🚀 优化：新增参数，支持属性合并
    ) -> Dict[str, Any]:
        """
        从结构化数据构建知识图谱（🚀 优化：支持属性合并）
        
        Args:
            data: 结构化数据列表，格式：
                [
                    {
                        "entity1": "Jane Ballou",
                        "entity2": "James A. Garfield",
                        "relation": "mother_of",
                        "entity1_type": "Person",
                        "entity2_type": "Person",
                        "entity1_properties": {...},
                        "entity2_properties": {...},
                        "relation_properties": {...},
                        "confidence": 0.9
                    },
                    ...
                ]
            merge_properties: 是否合并已有实体和关系的属性（默认True）
        
        Returns:
            构建结果
        """
        entities_created = 0
        relations_created = 0
        
        entity_name_to_id: Dict[str, str] = {}
        
        try:
            for item in data:
                entity1_name = item.get('entity1')
                entity2_name = item.get('entity2')
                relation_type = item.get('relation')
                
                if not all([entity1_name, entity2_name, relation_type]):
                    continue
                
                # 🆕 创建或获取实体1（支持查重和属性合并）
                # 🎯 关键修复：使用规范化后的名称作为 key，避免名称规范化导致的属性丢失
                from .entity_normalizer import normalize_entity_name
                entity1_type = item.get('entity1_type', 'Person')
                normalized_entity1_name = normalize_entity_name(entity1_name, entity1_type)
                
                if normalized_entity1_name not in entity_name_to_id:
                    # 检查是否已存在
                    existing_entities = self.entity_manager.find_entity_by_name(entity1_name)
                    is_new_entity1 = len(existing_entities) == 0
                    
                    entity1_properties = item.get('entity1_properties') or {}
                    # 🐛 调试：记录属性传递
                    if entity1_properties:
                        self.logger.info(f"创建实体1 {entity1_name}（规范化: {normalized_entity1_name}），属性: {entity1_properties}")
                    
                    entity1_id = self.entity_manager.create_entity(
                        name=entity1_name,
                        entity_type=entity1_type,
                        properties=entity1_properties,
                        skip_duplicate=True,  # 🆕 启用查重
                        merge_properties=merge_properties  # 🚀 优化：传递合并参数
                    )
                    if entity1_id:
                        entity_name_to_id[normalized_entity1_name] = entity1_id
                        if is_new_entity1:
                            entities_created += 1
                else:
                    entity1_id = entity_name_to_id[normalized_entity1_name]
                    # 🎯 关键修复：如果实体已存在，也要更新属性（支持属性合并）
                    if merge_properties:
                        entity1_properties = item.get('entity1_properties') or {}
                        if entity1_properties:
                            self.entity_manager.update_entity(entity1_id, properties=entity1_properties)
                            self.logger.info(f"✅ 更新已存在实体1 {normalized_entity1_name} 的属性: {entity1_properties}")
                
                # 🆕 创建或获取实体2（支持查重和属性合并）
                # 🎯 关键修复：使用规范化后的名称作为 key，避免名称规范化导致的属性丢失
                entity2_type = item.get('entity2_type', 'Person')
                normalized_entity2_name = normalize_entity_name(entity2_name, entity2_type)
                
                if normalized_entity2_name not in entity_name_to_id:
                    # 检查是否已存在
                    existing_entities = self.entity_manager.find_entity_by_name(entity2_name)
                    is_new_entity2 = len(existing_entities) == 0
                    
                    entity2_properties = item.get('entity2_properties') or {}
                    # 🐛 调试：记录属性传递
                    if entity2_properties:
                        self.logger.info(f"创建实体2 {entity2_name}（规范化: {normalized_entity2_name}），属性: {entity2_properties}")
                    
                    entity2_id = self.entity_manager.create_entity(
                        name=entity2_name,
                        entity_type=entity2_type,
                        properties=entity2_properties,
                        skip_duplicate=True,  # 🆕 启用查重
                        merge_properties=merge_properties  # 🚀 优化：传递合并参数
                    )
                    if entity2_id:
                        entity_name_to_id[normalized_entity2_name] = entity2_id
                        if is_new_entity2:
                            entities_created += 1
                else:
                    entity2_id = entity_name_to_id[normalized_entity2_name]
                    # 🎯 关键修复：如果实体已存在，也要更新属性（支持属性合并）
                    if merge_properties:
                        entity2_properties = item.get('entity2_properties') or {}
                        if entity2_properties:
                            self.entity_manager.update_entity(entity2_id, properties=entity2_properties)
                            self.logger.info(f"✅ 更新已存在实体2 {normalized_entity2_name} 的属性: {entity2_properties}")
                
                # 🆕 创建关系（支持查重和属性合并）
                if entity1_id and entity2_id:
                    # 🚀 优化：跳过自环关系（实体指向自己）
                    if entity1_id == entity2_id:
                        self.logger.debug(f"跳过自环关系: {entity1_name} -> {entity2_name} ({relation_type})")
                        continue
                    
                    # 检查关系是否已存在
                    existing_relations = self.relation_manager.find_relations(
                        entity_id=entity1_id,
                        relation_type=relation_type
                    )
                    is_new_relation = not any(
                        r.get('entity2_id') == entity2_id 
                        for r in existing_relations
                    )
                    
                    relation_properties = item.get('relation_properties') or {}
                    # 🎯 关键修复：确保关系属性被正确传递和保存
                    # 过滤掉空值，但保留非空属性
                    if relation_properties:
                        # 再次过滤，确保没有空值
                        relation_properties = {
                            k: v for k, v in relation_properties.items()
                            if v is not None and v != '' and v != 'null'
                        }
                        if relation_properties:
                            self.logger.info(f"✅ 创建关系 {entity1_name} -> {relation_type} -> {entity2_name}，属性: {relation_properties}")
                    
                    relation_id = self.relation_manager.create_relation(
                        entity1_id=entity1_id,
                        entity2_id=entity2_id,
                        relation_type=relation_type,
                        properties=relation_properties if relation_properties else None,  # 🎯 关键修复：如果属性为空，传递None而不是空字典
                        confidence=item.get('confidence', 1.0),
                        skip_duplicate=True,  # 🆕 启用查重
                        merge_properties=merge_properties  # 🚀 优化：传递合并参数
                    )
                    if relation_id and is_new_relation:
                        relations_created += 1
            
            self.logger.info(f"从结构化数据构建图谱: {entities_created}个实体, {relations_created}条关系")
            
            return {
                'entities_created': entities_created,
                'relations_created': relations_created,
                'status': 'success'
            }
            
        except Exception as e:
            self.logger.error(f"从结构化数据构建图谱失败: {e}")
            return {
                'entities_created': entities_created,
                'relations_created': relations_created,
                'status': 'error',
                'error': str(e)
            }

