#!/usr/bin/env python3
"""
实体关系辅助工具
🚀 重构：完全依赖知识库和知识图谱动态查询，移除硬编码配置
通用工具，适用于任何领域的实体和关系查询
"""

from typing import Dict, List, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)


class HistoricalKnowledgeHelper:
    """实体关系辅助工具 - 🚀 重构：完全依赖知识库和知识图谱，移除硬编码
    
    这个工具现在是一个通用的实体关系查询辅助工具，不针对特定领域。
    所有信息都从知识库管理系统和知识图谱动态查询。
    """
    
    def __init__(self, unified_config_center=None, kms_service=None):
        """初始化实体关系辅助工具
        
        Args:
            unified_config_center: 统一配置中心实例（可选）
            kms_service: 知识库管理系统服务实例（必需，用于查询知识）
        """
        self.logger = logger
        self.unified_config_center = unified_config_center
        self.kms_service = kms_service
        
        # 🚀 重构：不再加载硬编码配置，完全依赖知识库查询
        self.graph_query_engine = None
        if kms_service:
            try:
                # 尝试获取知识图谱查询引擎
                if hasattr(kms_service, 'graph_service'):
                    graph_service = kms_service.graph_service
                    if hasattr(graph_service, 'graph_query_engine'):
                        self.graph_query_engine = graph_service.graph_query_engine
                elif hasattr(kms_service, 'graph_query_engine'):
                    self.graph_query_engine = kms_service.graph_query_engine
            except Exception as e:
                self.logger.debug(f"无法获取知识图谱查询引擎: {e}，将仅使用向量知识库查询")
    
    def _query_knowledge_base(self, query: str, top_k: int = 3, similarity_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """从知识库管理系统查询知识（🚀 重构：通用查询，不限于历史知识）
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            similarity_threshold: 相似度阈值（默认0.5，降低阈值以获取更多结果）
            
        Returns:
            查询结果列表
        """
        if not self.kms_service:
            return []
        
        try:
            # 🚀 P0修复：强制启用知识图谱，降低相似度阈值，提高检索成功率
            results = self.kms_service.query_knowledge(
                query=query,
                modality="text",
                top_k=top_k * 2,  # 获取更多结果，然后过滤
                similarity_threshold=similarity_threshold,  # 降低阈值
                use_rerank=True,
                use_graph=True,  # 🚀 强制启用知识图谱
                use_llamaindex=True  # 启用LlamaIndex增强检索
            )
            
            return results or []
        except Exception as e:
            self.logger.debug(f"从知识库查询失败: {e}")
        
        return []
    
    def _query_entity_from_graph(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """从知识图谱查询实体
        
        Args:
            entity_name: 实体名称
            
        Returns:
            实体信息，如果不存在返回None
        """
        if not self.graph_query_engine:
            return None
        
        try:
            entities = self.graph_query_engine.query_entity(entity_name)
            if entities and len(entities) > 0:
                return entities[0]
        except Exception as e:
            self.logger.debug(f"从知识图谱查询实体失败: {e}")
        
        return None
    
    def _query_relations_from_graph(self, entity_name: str, relation_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """从知识图谱查询实体关系
        
        Args:
            entity_name: 实体名称
            relation_type: 关系类型（可选，如"mother", "father"等）
            
        Returns:
            关系列表
        """
        if not self.graph_query_engine:
            return []
        
        try:
            relations = self.graph_query_engine.query_relations(
                entity_name=entity_name,
                relation_type=relation_type
            )
            return relations or []
        except Exception as e:
            self.logger.debug(f"从知识图谱查询关系失败: {e}")
        
        return []
    
    def extract_historical_entities(self, query: str) -> Dict[str, Any]:
        """🚀 通用化：从查询中提取实体信息（不硬编码特定实体类型）
        
        Args:
            query: 查询文本
            
        Returns:
            提取的实体信息
        """
        entities = {
            "ordinal_entities": [],  # 序数+实体类型列表（通用）
            "person_name": None,
            "relationship": None,
            "query_type": None,
            "filtered_entities": []  # 筛选实体（如"assassinated president"）
        }
        
        query_lower = query.lower()
        
        # 🚀 通用化：提取所有序数+实体类型的模式（不限于president/first_lady）
        ordinal_entity_pattern = r'(\d+)(?:th|st|nd|rd)?\s+(\w+(?:\s+\w+)*)'
        ordinal_matches = re.findall(ordinal_entity_pattern, query_lower)
        
        for ordinal_str, entity_type in ordinal_matches:
            ordinal = int(ordinal_str)
            entity_type_clean = entity_type.strip()
            
            # 检查是否是筛选实体（如"assassinated president"、"elected mayor"）
            filter_keywords = ['assassinated', 'elected', 'appointed', 'first', 'second', 'third', 'last']
            is_filtered = any(keyword in entity_type_clean for keyword in filter_keywords)
            
            entities["ordinal_entities"].append({
                "ordinal": ordinal,
                "entity_type": entity_type_clean,
                "is_filtered": is_filtered,
                "full_pattern": f"{ordinal}th {entity_type_clean}"
            })
        
        # 🚀 通用化：提取关系（使用通用模式，不硬编码特定关系）
        relationship_patterns = {
            "mother_maiden_name": r'mother.*?maiden\s+name|maiden\s+name.*?mother',
            "mother_first_name": r'mother.*?first\s+name|first\s+name.*?mother',
            "mother": r'\bmother\b',
            "father": r'\bfather\b',
            "maiden_name": r'maiden\s+name|娘家姓',
            "first_name": r'first\s+name',
            "last_name": r'last\s+name|surname',
            "wife": r'\bwife\b',
            "husband": r'\bhusband\b',
            "spouse": r'\bspouse\b',
            "child": r'\bchild\b|children',
            "son": r'\bson\b',
            "daughter": r'\bdaughter\b'
        }
        
        for rel_type, pattern in relationship_patterns.items():
            if re.search(pattern, query_lower, re.IGNORECASE):
                entities["relationship"] = rel_type
                break
        
        # 🚀 通用化：提取筛选实体（不限于"assassinated president"）
        # 检测筛选词+实体类型的模式（如"second assassinated president"、"first female CEO"）
        filtered_pattern = r'(?:first|second|third|fourth|fifth|last|1st|2nd|3rd|4th|5th)\s+(\w+(?:\s+\w+)*)'
        filtered_matches = re.findall(filtered_pattern, query_lower)
        
        for filtered_entity in filtered_matches:
            # 检查是否包含筛选关键词
            if any(keyword in filtered_entity for keyword in ['assassinated', 'elected', 'appointed', 'female', 'male']):
                entities["filtered_entities"].append({
                    "entity_type": filtered_entity.strip(),
                    "full_pattern": filtered_entity.strip()
                })
        
        # 🚀 通用化：提取人名（使用语义理解管道，如果可用）
        try:
            from src.utils.semantic_understanding_pipeline import get_semantic_understanding_pipeline
            semantic_pipeline = get_semantic_understanding_pipeline()
            if semantic_pipeline:
                extracted_entities = semantic_pipeline.extract_entities_intelligent(query)
                # 优先提取PERSON类型的实体
                for entity in extracted_entities:
                    if entity.get('label') == 'PERSON':
                        entities["person_name"] = entity.get('text')
                        break
        except Exception as e:
            self.logger.debug(f"使用语义理解管道提取实体失败: {e}")
        
        # Fallback: 使用简单模式提取人名
        if not entities["person_name"]:
            name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
            name_matches = re.findall(name_pattern, query)
            if name_matches:
                entities["person_name"] = name_matches[0]
        
        # 确定查询类型（基于提取的实体）
        if entities["ordinal_entities"]:
            # 如果有序数实体，根据实体类型确定查询类型
            first_entity = entities["ordinal_entities"][0]
            entities["query_type"] = f"{first_entity['entity_type']}_query"
        elif entities["filtered_entities"]:
            entities["query_type"] = "filtered_entity_query"
        elif entities["person_name"] and entities["relationship"]:
            entities["query_type"] = "relationship_query"
        else:
            entities["query_type"] = "general_query"
        
        return entities
    
    def generate_enhanced_queries(self, query: str, entities: Dict[str, Any]) -> List[str]:
        """🚀 通用化：根据提取的实体生成增强查询（不硬编码特定实体类型）
        
        Args:
            query: 原始查询
            entities: 提取的实体信息
            
        Returns:
            增强的查询列表
        """
        enhanced_queries = [query]  # 保留原始查询
        
        # 🚀 通用化：为所有序数实体生成查询变体（不限于president/first_lady）
        if entities.get("ordinal_entities"):
            for ordinal_entity in entities["ordinal_entities"]:
                ordinal = ordinal_entity["ordinal"]
                entity_type = ordinal_entity["entity_type"]
                
                # 生成通用查询变体
                enhanced_queries.append(f"{ordinal}th {entity_type}")
                
                # 如果实体类型是角色/职位，生成带上下文的查询变体
                # 检测常见上下文（如"United States"、"US"等）
                context_keywords = ['united states', 'us', 'usa', 'american']
                query_lower = query.lower()
                for context in context_keywords:
                    if context in query_lower:
                        if context == 'united states':
                            enhanced_queries.append(f"{ordinal}th {entity_type} United States")
                            enhanced_queries.append(f"{ordinal}th {entity_type} of the United States")
                            enhanced_queries.append(f"{ordinal}th US {entity_type}")
                        elif context in ['us', 'usa']:
                            enhanced_queries.append(f"{ordinal}th {entity_type} US")
                            enhanced_queries.append(f"{ordinal}th {entity_type} of the US")
                        elif context == 'american':
                            enhanced_queries.append(f"{ordinal}th American {entity_type}")
                        break
        
        # 🚀 通用化：为筛选实体生成查询变体
        if entities.get("filtered_entities"):
            for filtered_entity in entities["filtered_entities"]:
                entity_type = filtered_entity["entity_type"]
                enhanced_queries.append(f"Who was the {entity_type}?")
                enhanced_queries.append(entity_type)
        
        # 🚀 通用化：为人名和关系生成查询变体（不硬编码特定关系）
        if entities.get("person_name") and entities.get("relationship"):
            person_name = entities["person_name"]
            relationship = entities["relationship"]
            
            # 根据关系类型生成查询（支持所有关系类型）
            relationship_queries = {
                "mother": [f"{person_name} mother", f"{person_name} family"],
                "father": [f"{person_name} father", f"{person_name} family"],
                "maiden_name": [f"{person_name} mother maiden name", f"{person_name} mother family name"],
                "mother_maiden_name": [f"{person_name} mother maiden name", f"{person_name} mother family name"],
                "mother_first_name": [f"{person_name} mother first name"],
                "first_name": [f"{person_name} first name"],
                "last_name": [f"{person_name} last name", f"{person_name} surname"],
                "wife": [f"{person_name} wife", f"{person_name} spouse"],
                "husband": [f"{person_name} husband", f"{person_name} spouse"],
                "spouse": [f"{person_name} spouse"],
                "child": [f"{person_name} child", f"{person_name} children"],
                "son": [f"{person_name} son"],
                "daughter": [f"{person_name} daughter"]
            }
            
            if relationship in relationship_queries:
                enhanced_queries.extend(relationship_queries[relationship])
            else:
                # 通用关系查询
                enhanced_queries.append(f"{person_name} {relationship}")
        
        return enhanced_queries
    
    def _query_entity_by_ordinal(self, entity_type: str, ordinal: int, context: str = "") -> Optional[Dict[str, Any]]:
        """🚀 P0修复：改进序数实体查询，优先使用知识图谱，生成多个查询变体
        
        Args:
            entity_type: 实体类型（如"president", "first lady"）
            ordinal: 序数（如15）
            context: 上下文（如"United States"）
            
        Returns:
            实体信息，如果不存在返回None
        """
        if not self.kms_service:
            return None
        
        # 🚀 P0修复：生成多个查询变体，提高检索成功率
        queries = []
        
        # 基础查询
        base_query = f"{ordinal}th {entity_type}"
        if context:
            base_query += f" {context}"
        queries.append(base_query)
        
        # 查询变体1: 添加"of the"
        if context:
            queries.append(f"{ordinal}th {entity_type} of the {context}")
        
        # 查询变体2: 使用"US"代替"United States"
        if "United States" in context:
            queries.append(f"{ordinal}th {entity_type} US")
            queries.append(f"{ordinal}th {entity_type} of the US")
        
        # 查询变体3: 使用"American"
        if "United States" in context:
            queries.append(f"{ordinal}th American {entity_type}")
        
        # 🚀 P0修复：优先使用知识图谱查询（如果可用）
        # 注意：不硬编码实体名称，完全依赖知识库查询
        # 知识图谱查询将在向量检索后通过关系查询进行补充
        
        # 🚀 P0修复：使用多个查询变体查询知识库
        all_results = []
        seen_ids = set()
        
        for query_variant in queries:
            # 🚀 P0修复：提高相似度阈值，从0.3提高到0.5，减少不相关结果
            results = self._query_knowledge_base(query_variant, top_k=5, similarity_threshold=0.5)
            if results:
                for result in results:
                    result_id = result.get('knowledge_id') or result.get('content', '')[:100]
                    if result_id not in seen_ids:
                        seen_ids.add(result_id)
                        all_results.append(result)
        
        # 🚀 P0修复：按相似度排序，优先使用高相似度的结果
        all_results.sort(
            key=lambda x: x.get('similarity_score', 0.0) or x.get('similarity', 0.0),
            reverse=True
        )
        
        # 🚀 P0修复：改进名称提取逻辑，过滤掉不相关的名称
        if all_results:
            for result in all_results:
                content = result.get('content', '') or result.get('text', '')
                if not content:
                    continue
                
                # 🚀 P0修复：验证结果相关性
                if not self._validate_result_relevance(result, base_query, entity_type, ordinal):
                    self.logger.debug(f"⚠️ [历史知识查询] 结果不相关，跳过: {content[:50]}")
                    continue
                
                # 过滤掉明显不相关的内容
                content_lower = content.lower()
                if content_lower == "united states" or content_lower.strip() == "united states":
                    continue  # 跳过"United States"这种不相关的结果
                
                # 🚀 P0修复：改进名称提取，优先提取与序数词相关的名称
                # 模式1: 完整人名（至少两个单词，首字母大写）
                name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
                name_matches = re.findall(name_pattern, content[:2000])  # 检查前2000字符
                
                if name_matches:
                    # 过滤掉明显不是人名的匹配（如"United States", "First Lady"等）
                    filtered_names = []
                    exclude_keywords = [
                        'United States', 'First Lady', 'President', 'American', 'US', 'USA',
                        'Financial Services',  # 🚀 P0修复：添加排除关键词
                        'National', 'Federal', 'Government', 'Department', 'Agency', 'Bureau',
                        'Service', 'Services', 'State', 'States'  # 🚀 P0修复：添加更多排除关键词
                    ]
                    
                    # 🚀 P0修复：序数词映射（用于查找相关内容）
                    ordinal_words = {
                        1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth",
                        6: "sixth", 7: "seventh", 8: "eighth", 9: "ninth", 10: "tenth",
                        11: "eleventh", 12: "twelfth", 13: "thirteenth", 14: "fourteenth",
                        15: "fifteenth", 16: "sixteenth", 17: "seventeenth", 18: "eighteenth",
                        19: "nineteenth", 20: "twentieth"
                    }
                    ordinal_str = f"{ordinal}th"
                    ordinal_word = ordinal_words.get(ordinal, "")
                    
                    # 🚀 P0修复：优先提取在序数词附近的人名
                    prioritized_names = []
                    other_names = []
                    
                    for name in name_matches:
                        name_lower = name.lower()
                        # 🚀 P0修复：更严格的排除检查（完全匹配或包含）
                        should_exclude = False
                        for keyword in exclude_keywords:
                            keyword_lower = keyword.lower()
                            # 完全匹配或作为完整单词包含
                            if name_lower == keyword_lower or \
                               (len(name_lower) <= len(keyword_lower) + 5 and keyword_lower in name_lower):
                                should_exclude = True
                                break
                        
                        if should_exclude:
                            continue
                        
                        # 检查是否包含常见人名特征
                        if len(name.split()) < 2:  # 至少两个单词
                            continue
                        
                        # 🚀 P0修复：检查名称是否在序数词附近（前后150字符内）
                        name_pos = content.find(name)
                        if name_pos >= 0:
                            # 查找序数词的位置
                            ordinal_positions = []
                            if ordinal_str in content.lower():
                                ordinal_positions.append(content.lower().find(ordinal_str))
                            if ordinal_word and ordinal_word in content.lower():
                                ordinal_positions.append(content.lower().find(ordinal_word))
                            
                            # 检查名称是否在序数词附近
                            is_near_ordinal = False
                            for ord_pos in ordinal_positions:
                                if ord_pos >= 0 and abs(name_pos - ord_pos) < 150:
                                    is_near_ordinal = True
                                    break
                            
                            if is_near_ordinal:
                                prioritized_names.append(name)
                            else:
                                other_names.append(name)
                        else:
                            other_names.append(name)
                    
                    # 🚀 P0修复：优先使用在序数词附近的人名
                    if prioritized_names:
                        # 验证名称是否合理
                        for name in prioritized_names:
                            if self._is_valid_person_name(name):
                                self.logger.info(f"✅ [历史知识查询] 找到与序数相关的名称: {name} (序数: {ordinal})")
                                return {
                                    "name": name,
                                    "source": "knowledge_base",
                                    "confidence": result.get('similarity_score', 0.7)
                                }
                    
                    # 如果没有找到在序数词附近的人名，使用其他人名（但降低置信度）
                    if other_names:
                        for name in other_names:
                            if self._is_valid_person_name(name):
                                self.logger.warning(f"⚠️ [历史知识查询] 找到名称但不在序数词附近: {name} (序数: {ordinal})，降低置信度")
                                return {
                                    "name": name,
                                    "source": "knowledge_base",
                                    "confidence": result.get('similarity_score', 0.7) * 0.7  # 降低置信度
                                }
        
        return None
    
    def _validate_result_relevance(self, result: Dict[str, Any], query: str, entity_type: str = "", ordinal: int = 0) -> bool:
        """🚀 P0新增：验证结果是否与查询相关
        
        Args:
            result: 检索结果
            query: 查询文本
            entity_type: 实体类型（如"first lady", "president"）
            ordinal: 序数（如15）
            
        Returns:
            如果结果相关返回True，否则返回False
        """
        try:
            content = result.get('content', '') or result.get('text', '')
            if not content:
                return False
            
            # 1. 检查相似度分数
            similarity = result.get('similarity_score', 0.0) or result.get('similarity', 0.0)
            if similarity < 0.4:  # 相似度阈值
                self.logger.debug(f"⚠️ [相关性验证] 相似度太低: {similarity:.3f}")
                return False
            
            # 2. 检查内容是否是明显不相关的内容（优先检查，避免后续处理）
            content_lower = content.lower().strip()
            exclude_patterns = [
                'financial services', 'united states', 'first lady', 'president',
                'national', 'federal', 'government', 'department', 'agency',
                'bureau', 'service', 'services', 'state', 'states'
            ]
            
            # 如果内容完全匹配排除模式，不相关
            if content_lower in exclude_patterns:
                self.logger.debug(f"⚠️ [相关性验证] 内容匹配排除模式: {content_lower}")
                return False
            
            # 3. 检查内容是否包含查询关键词
            query_lower = query.lower()
            
            # 提取查询中的关键实体
            key_terms = []
            if entity_type:
                key_terms.append(entity_type.lower())
            if ordinal > 0:
                # 检查内容中是否包含序数词（如"15th", "fifteenth"）
                ordinal_str = f"{ordinal}th"
                ordinal_words = {
                    1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth",
                    6: "sixth", 7: "seventh", 8: "eighth", 9: "ninth", 10: "tenth",
                    11: "eleventh", 12: "twelfth", 13: "thirteenth", 14: "fourteenth",
                    15: "fifteenth", 16: "sixteenth", 17: "seventeenth", 18: "eighteenth",
                    19: "nineteenth", 20: "twentieth"
                }
                if ordinal in ordinal_words:
                    key_terms.append(ordinal_words[ordinal])
                key_terms.append(ordinal_str)
            
            # 如果内容中不包含任何关键术语，可能不相关
            if key_terms:
                has_key_term = any(term in content_lower for term in key_terms)
                if not has_key_term:
                    self.logger.debug(f"⚠️ [相关性验证] 内容中不包含关键术语: {key_terms}")
                    return False
            
            # 4. 检查内容长度（太短的内容可能不完整）
            if len(content.strip()) < 5:
                self.logger.debug(f"⚠️ [相关性验证] 内容太短: {len(content)}字符")
                return False
            
            # 5. 🚀 通用化：如果查询是关于人物实体，检查内容是否包含人名
            # 检测是否是人物相关的实体类型（不限于first_lady/president）
            person_entity_indicators = ['president', 'first lady', 'prime minister', 'chancellor', 
                                       'governor', 'mayor', 'king', 'queen', 'emperor', 'empress',
                                       'ceo', 'director', 'manager', 'leader']
            
            is_person_entity = any(indicator in entity_type.lower() for indicator in person_entity_indicators)
            
            if is_person_entity:
                # 检查内容是否包含人名模式（至少两个首字母大写的单词）
                import re
                name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
                name_matches = re.findall(name_pattern, content[:500])
                
                if not name_matches:
                    # 没有找到人名，可能不相关
                    self.logger.debug(f"⚠️ [相关性验证] 查询关于{entity_type}（人物实体），但内容中没有找到人名")
                    return False
                
                # 验证找到的名称是否是合理的人名
                for name in name_matches:
                    name_lower = name.lower()
                    # 排除明显不是人名的匹配
                    if name_lower in exclude_patterns:
                        continue
                    # 如果找到了合理的人名，认为相关
                    if len(name.split()) >= 2:
                        return True
                
                # 如果所有匹配都被排除，不相关
                self.logger.debug(f"⚠️ [相关性验证] 内容中的人名都不合理")
                return False
            
            # 默认：如果通过了基本检查，认为相关
            return True
            
        except Exception as e:
            self.logger.debug(f"验证结果相关性失败: {e}")
            return True  # 验证失败时，默认通过（避免过度过滤）
    
    def _query_relationship(self, person_name: str, relationship: str) -> Optional[str]:
        """🚀 重构：通用方法，从知识库和知识图谱查询关系
        
        Args:
            person_name: 人名
            relationship: 关系类型（如"mother", "father", "mother_maiden_name"）
            
        Returns:
            关系实体名称，如果不存在返回None
        """
        # 1. 优先从知识图谱查询（如果可用）
        if self.graph_query_engine:
            # 查询实体
            entity = self._query_entity_from_graph(person_name)
            if entity:
                # 查询关系
                relation_type = relationship.replace("_", " ")  # "mother_maiden_name" -> "mother maiden name"
                relations = self._query_relations_from_graph(person_name, relation_type)
                
                if relations:
                    # 返回第一个关系的目标实体
                    relation = relations[0]
                    target_entity_name = relation.get('entity2_name')
                    if target_entity_name and target_entity_name != 'Unknown':
                        return target_entity_name
        
        # 2. 从向量知识库查询
        if self.kms_service:
            query = f"{person_name} {relationship}"
            results = self._query_knowledge_base(query, top_k=3)
            
            for result in results:
                content = result.get('content', '') or result.get('text', '')
                if content:
                    # 尝试提取关系信息
                    if "mother" in relationship.lower():
                        # 提取母亲姓名
                        patterns = [
                            r'mother[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
                            r'mother\'s name[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
                            r'mother was[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
                        ]
                        for pattern in patterns:
                            match = re.search(pattern, content, re.IGNORECASE)
                            if match:
                                return match.group(1)
                        
                        # 如果是maiden name，尝试提取
                        if "maiden" in relationship.lower():
                            patterns = [
                                r'maiden name[:\s]+([A-Z][a-z]+)',
                                r'maiden surname[:\s]+([A-Z][a-z]+)',
                                r'family name[:\s]+([A-Z][a-z]+)'
                            ]
                            for pattern in patterns:
                                match = re.search(pattern, content, re.IGNORECASE)
                                if match:
                                    return match.group(1)
        
        return None
    
    def get_historical_fact(self, entities: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """🚀 通用化：从知识库和知识图谱动态查询事实（不硬编码特定实体类型）
        
        Args:
            entities: 提取的实体信息
            
        Returns:
            事实信息，如果不存在返回None
        """
        if not self.kms_service:
            return None
        
        # 🚀 通用化：处理所有序数实体查询（不限于president/first_lady）
        if entities.get("ordinal_entities"):
            for ordinal_entity in entities["ordinal_entities"]:
                ordinal = ordinal_entity["ordinal"]
                entity_type = ordinal_entity["entity_type"]
                
                # 提取上下文（如"United States"）
                context = ""
                # 尝试从原始查询中提取上下文
                # 这里可以进一步优化，使用语义理解提取上下文
                
                # 查询实体
                entity_fact = self._query_entity_by_ordinal(entity_type, ordinal, context)
                
                if entity_fact:
                    entity_name = entity_fact.get("name")
                    if entity_name:
                        # 如果需要关系信息
                        if entities.get("relationship"):
                            relationship_fact = self._query_relationship(entity_name, entities["relationship"])
                            if relationship_fact:
                                return {
                                    "fact": relationship_fact,
                                    "source": entity_fact.get("source", "knowledge_base"),
                                    "confidence": entity_fact.get("confidence", 0.8)
                                }
                        
                        return {
                            "fact": entity_name,
                            "source": entity_fact.get("source", "knowledge_base"),
                            "confidence": entity_fact.get("confidence", 0.8)
                        }
        
        # 🚀 通用化：处理筛选实体查询（不限于"assassinated president"）
        if entities.get("filtered_entities"):
            for filtered_entity in entities["filtered_entities"]:
                entity_type = filtered_entity["entity_type"]
                
                # 从知识库查询筛选实体
                query = f"Who was the {entity_type}?"
                results = self._query_knowledge_base(query, top_k=3)
                
                if results:
                    for result in results:
                        content = result.get('content', '') or result.get('text', '')
                        if not content:
                            continue
                        
                        # 过滤不相关的内容
                        content_lower = content.lower().strip()
                        exclude_keywords = [
                            'united states', 'financial services', 'national', 'federal', 
                            'government', 'department', 'agency', 'bureau', 'service', 'services'
                        ]
                        if content_lower in exclude_keywords:
                            continue
                        
                        # 提取名称
                        name_match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', content[:500])
                        if name_match:
                            entity_name = name_match.group(1)
                            
                            # 验证名称是否合理
                            if not self._is_valid_person_name(entity_name):
                                continue
                            
                            # 如果需要关系信息
                            if entities.get("relationship"):
                                relationship_fact = self._query_relationship(entity_name, entities["relationship"])
                                if relationship_fact:
                                    return {
                                        "fact": relationship_fact,
                                        "source": "knowledge_base",
                                        "confidence": result.get('similarity_score', 0.8)
                                    }
                            
                            return {
                                "fact": entity_name,
                                "source": "knowledge_base",
                                "confidence": result.get('similarity_score', 0.8)
                            }
        
        # 🚀 通用化：处理人名和关系查询
        if entities.get("person_name") and entities.get("relationship"):
            person_name = entities["person_name"]
            relationship = entities["relationship"]
            
            relationship_fact = self._query_relationship(person_name, relationship)
            if relationship_fact:
                return {
                    "fact": relationship_fact,
                    "source": "knowledge_base",
                    "confidence": 0.8
                }
        
        return None
    
    def validate_fact_against_knowledge_base(self, fact: str, query: str) -> Dict[str, Any]:
        """验证事实是否与历史知识库一致
        
        Args:
            fact: 要验证的事实
            query: 原始查询
            
        Returns:
            验证结果
        """
        entities = self.extract_historical_entities(query)
        historical_fact = self.get_historical_fact(entities)
        
        if historical_fact:
            fact_clean = fact.strip()
            historical_fact_clean = historical_fact["fact"].strip()
            
            # 简单匹配检查
            if fact_clean.lower() == historical_fact_clean.lower():
                return {
                    "is_valid": True,
                    "confidence": historical_fact["confidence"],
                    "source": "historical_knowledge_base"
                }
            else:
                # 部分匹配检查
                if fact_clean.lower() in historical_fact_clean.lower() or historical_fact_clean.lower() in fact_clean.lower():
                    return {
                        "is_valid": True,
                        "confidence": historical_fact["confidence"] * 0.8,
                        "source": "historical_knowledge_base",
                        "note": "部分匹配"
                    }
                else:
                    return {
                        "is_valid": False,
                        "confidence": 0.0,
                        "source": "historical_knowledge_base",
                        "expected": historical_fact["fact"],
                        "actual": fact
                    }
        
        return {
            "is_valid": None,
            "confidence": 0.0,
            "source": "unknown",
            "note": "历史知识库中无此信息"
        }
    
    def _is_valid_person_name(self, name: str) -> bool:
        """🚀 P0新增：验证名称是否是合理的人名
        
        Args:
            name: 要验证的名称
            
        Returns:
            如果是合理的人名返回True，否则返回False
        """
        if not name or not isinstance(name, str):
            return False
        
        name_lower = name.lower().strip()
        
        # 🚀 P0修复：排除常见的地理/概念/组织名称
        exclude_keywords = [
            'united states', 'financial services', 'first lady', 'president',
            'american', 'us', 'usa', 'national', 'federal', 'government',
            'department', 'agency', 'bureau', 'service', 'services',
            'state', 'states', 'country', 'nation', 'republic'
        ]
        
        # 完全匹配检查
        if name_lower in exclude_keywords:
            return False
        
        # 包含检查（如果名称很短，可能是这些关键词的一部分）
        if len(name.split()) <= 2:
            for keyword in exclude_keywords:
                if keyword in name_lower or name_lower in keyword:
                    return False
        
        # 检查是否是合理的人名格式（至少两个单词，首字母大写，支持中间名缩写）
        # 支持格式：FirstName LastName, FirstName MiddleName LastName, FirstName A. LastName
        name_pattern = r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]*\.?)*(?:\s+[A-Z][a-z]+)+$'
        if not re.match(name_pattern, name):
            return False
        
        # 检查长度（人名通常不会太长）
        if len(name) > 50:
            return False
        
        return True
