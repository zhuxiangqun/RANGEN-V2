"""
统一智能处理基础类
集中管理所有重复的智能处理函数
集成动态参数优化功能
"""

import logging
import re
import time
from typing import List, Dict, Any, Optional, Tuple, Union

# 导入统一中心系统的函数 - 使用延迟导入避免循环导入
def get_smart_config(key: str, context: Optional[Dict[str, Any]] = None) -> Any:
    """获取智能配置 - 延迟导入版本"""
    try:
        from .unified_centers import get_smart_config as _get_smart_config
        return _get_smart_config(key, context)
    except ImportError:
        logger.warning("统一中心系统不可用，使用默认配置")
        return None

def create_query_context(query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """创建查询上下文 - 延迟导入版本"""
    try:
        from .unified_centers import create_query_context as _create_query_context
        return _create_query_context(query, user_id)
    except ImportError:
        logger.warning("统一中心系统不可用，使用默认上下文")
        return {
            "query": query,
            "user_id": user_id,
            "timestamp": time.time()
        }

logger = logging.getLogger(__name__)


class UnifiedIntelligentProcessor:
    """统一智能处理基础类"""

    def __init__(self):
        """初始化统一智能处理器"""
        self.dynamic_config = {}
        self.parameter_optimizer = None
        self.pattern_config = None
        self.ml_rule_generator = None
        logger.info("统一智能处理基础类初始化完成")
    
    def _validate_extraction_input(self, content: str, query: str) -> bool:
        """验证提取输入"""
        if not isinstance(content, str) or not content.strip():
            return False
        
        if not isinstance(query, str):
            return False
        
        return True
    
    def _create_extraction_error(self, message: str) -> Dict[str, Any]:
        """创建提取错误"""
        return {
            'error': True,
            'message': message,
            'timestamp': time.time()
        }

    def perform_universal_intelligent_extraction(self, content: str, query: str = "") -> Dict[str, Any]:
        """通用智能信息提取"""
        try:
            # 验证输入
            if not self._validate_extraction_input(content, query):
                return self._create_extraction_error("Invalid input parameters")
            
            start_time = time.time()
            
            # 创建上下文
            context = create_query_context("high_threshold")
            optimization_result = {
                "status": "default", 
                "performance": get_smart_config("high_threshold", context)
            }
            
            # 获取默认配置
            context_zero = create_query_context("default_zero_value")
            default_confidence = 0.7
            default_extraction_time = get_smart_config("DEFAULT_ZERO_VALUE", context_zero)

            # 执行各种分析
            semantic_analysis = self.analyze_content_semantically(content)
            features = self.extract_intelligent_features(content)
            entities = self.extract_content_entities(content)
            relationships = self.extract_content_relationships(content)
            context_analysis = self.understand_content_context(content)

            extraction_result = {
                'content_length': len(content),
                'query_length': len(query),
                'extraction_time': time.time() - start_time,
                'confidence': default_confidence,
                'extracted_features': features,
                'semantic_analysis': semantic_analysis,
                'entities': entities,
                'relationships': relationships,
                'context': context_analysis,
                'optimization_result': optimization_result
            }

            return extraction_result

        except Exception as e:
            logger.error(f"通用智能信息提取失败: {e}")
            return self._create_error_result("extraction", str(e))

    def perform_universal_intelligent_reasoning(self, content: str, query: str = "") -> Dict[str, Any]:
        """通用智能推理"""
        try:
            start_time = time.time()
            
            # 创建上下文
            context = create_query_context("high_threshold")
            optimization_result = {
                "status": "default",
                "performance": get_smart_config("high_threshold", context)
            }
            
            # 获取默认配置
            context_zero = create_query_context("default_zero_value")
            default_confidence = 0.7
            default_reasoning_time = get_smart_config("DEFAULT_ZERO_VALUE", context_zero)

            # 执行推理分析
            intent = self.analyze_intent(content)
            entities = self.extract_content_entities(content)
            relationships = self.extract_content_relationships(content)
            context_analysis = self.understand_content_context(content)
            semantic_features = self.extract_semantic_features(content)
            contextual_features = self.extract_contextual_features(content)
            inferred_features = self.extract_inferred_features(content)

            reasoning_result = {
                'intent': intent,
                'entities': entities,
                'relationships': relationships,
                'context': context_analysis,
                'semantic_features': semantic_features,
                'contextual_features': contextual_features,
                'inferred_features': inferred_features,
                'intent_analysis': self._analyze_intent_details(intent),
                'entity_analysis': self._analyze_entity_details(entities),
                'context_analysis': self._analyze_context_details(context_analysis),
                'general_analysis': self._analyze_general_details(content),
                'reasoning_time': time.time() - start_time,
                'confidence': default_confidence,
                'optimization_result': optimization_result
            }

            return reasoning_result

        except Exception as e:
            logger.error(f"通用智能推理失败: {e}")
            return self._create_error_result("reasoning", str(e))

    def analyze_content_semantically(self, content: str) -> Dict[str, Any]:
        """语义内容分析"""
        try:
            analysis = {
                'semantic_keywords': [],
                'semantic_concepts': [],
                'semantic_similarity': 0.0,
                'semantic_complexity': 0.0
            }

            # 提取语义关键词
            keywords = self.extract_semantic_keywords(content)
            analysis['semantic_keywords'] = keywords

            # 识别语义概念
            concepts = self._identify_semantic_concepts(content)
            analysis['semantic_concepts'] = concepts

            # 计算语义相似性
            similarity = self._calculate_semantic_similarity(content)
            analysis['semantic_similarity'] = similarity

            # 评估语义复杂度
            complexity = self._assess_semantic_complexity(content)
            analysis['semantic_complexity'] = complexity

            return analysis

        except Exception as e:
            logger.error(f"语义内容分析失败: {e}")
            return {
                'semantic_keywords': [],
                'semantic_concepts': [],
                'semantic_similarity': 0.0,
                'semantic_complexity': 0.0
            }

    def extract_intelligent_features(self, content: str) -> Dict[str, Any]:
        """提取智能特征"""
        try:
            features = {
                'text_features': self._extract_text_features(content),
                'semantic_features': self.extract_semantic_features(content),
                'contextual_features': self.extract_contextual_features(content),
                'inferred_features': self.extract_inferred_features(content),
                'adaptive_features': self._extract_adaptive_features(content)
            }
            return features

        except Exception as e:
            logger.error(f"智能特征提取失败: {e}")
            return {
                'text_features': {'word_count': len(content.split()), 'char_count': len(content)},
                'semantic_features': {'complexity': 0.5, 'density': 0.5},
                'contextual_features': {'relevance': 0.5},
                'inferred_features': {'confidence': 0.5},
                'adaptive_features': {'adaptability': 0.5}
            }

    def extract_content_entities(self, content: str) -> List[Dict[str, Any]]:
        """提取内容实体"""
        try:
            entities = []
            
            # 提取命名实体
            named_entities = self._extract_named_entities(content)
            entities.extend(named_entities)
            
            # 提取概念实体
            concept_entities = self._extract_concept_entities(content)
            entities.extend(concept_entities)
            
            # 提取关系实体
            relation_entities = self._extract_relation_entities(content)
            entities.extend(relation_entities)
            
            return entities

        except Exception as e:
            logger.error(f"内容实体提取失败: {e}")
            return [{
                "entity": "error_entity",
                "type": "error",
                "confidence": 0.0,
                "error": str(e),
                "timestamp": time.time()
            }]

    def extract_content_relationships(self, content: str) -> List[Dict[str, Any]]:
        """提取内容关系"""
        try:
            relationships = []
            
            # 提取语义关系
            semantic_relations = self._extract_semantic_relations(content)
            relationships.extend(semantic_relations)
            
            # 提取语法关系
            syntactic_relations = self._extract_syntactic_relations(content)
            relationships.extend(syntactic_relations)
            
            # 提取逻辑关系
            logical_relations = self._extract_logical_relations(content)
            relationships.extend(logical_relations)
            
            return relationships

        except Exception as e:
            logger.error(f"内容关系提取失败: {e}")
            return [{
                "relationship": "error_relationship",
                "type": "error",
                "confidence": 0.0,
                "error": str(e),
                "timestamp": time.time()
            }]

    def understand_content_context(self, content: str) -> Dict[str, Any]:
        """理解内容上下文"""
        try:
            context = {
                'domain_context': self._analyze_domain_context(content),
                'temporal_context': self._analyze_temporal_context(content),
                'spatial_context': self._analyze_spatial_context(content),
                'social_context': self._analyze_social_context(content),
                'cultural_context': self._analyze_cultural_context(content)
            }
            return context

        except Exception as e:
            logger.error(f"内容上下文理解失败: {e}")
            return {
                'domain_context': {'domain': 'general', 'confidence': 0.5},
                'temporal_context': {'time_reference': 'present', 'confidence': 0.5},
                'spatial_context': {'location': 'unknown', 'confidence': 0.5},
                'social_context': {'audience': 'general', 'confidence': 0.5},
                'cultural_context': {'culture': 'neutral', 'confidence': 0.5}
            }

    def analyze_intent(self, content: str) -> str:
        """分析意图"""
        try:
            # 生成自适应关键词
            keywords = self.generate_adaptive_keywords(content, "intent_analysis")
            
            # 基于关键词分析意图
            intent = self._classify_intent_from_keywords(keywords)
            
            return intent

        except Exception as e:
            logger.error(f"意图分析失败: {e}")
            return "general"

    def extract_semantic_features(self, content: str) -> Dict[str, Any]:
        """提取语义特征"""
        try:
            features = {
                'keywords': self.extract_semantic_keywords(content),
                'concepts': self._identify_semantic_concepts(content),
                'sentiment': self._analyze_sentiment(content),
                'topics': self._extract_topics(content),
                'entities': self._extract_semantic_entities(content)
            }
            return features

        except Exception as e:
            logger.error(f"语义特征提取失败: {e}")
            return {
                "error": f"语义特征提取失败: {e}",
                "status": "extraction_failed",
                "timestamp": time.time(),
                "fallback_features": {
                    "complexity": 0.5,
                    "density": 0.5,
                    "coherence": 0.5
                }
            }

    def extract_contextual_features(self, content: str) -> Dict[str, Any]:
        """提取上下文特征"""
        try:
            features = {
                'domain': self._identify_domain(content),
                'style': self._analyze_style(content),
                'complexity': self._assess_complexity(content),
                'coherence': self._assess_coherence(content),
                'relevance': self._assess_relevance(content)
            }
            return features

        except Exception as e:
            logger.error(f"上下文特征提取失败: {e}")
            return {
                "error": f"上下文特征提取失败: {e}",
                "status": "extraction_failed",
                "timestamp": time.time(),
                "fallback_features": {
                    "relevance": 0.5,
                    "context": "unknown",
                    "domain": "general"
                }
            }

    def extract_inferred_features(self, content: str) -> Dict[str, Any]:
        """提取推断特征"""
        try:
            features = {
                'implications': self._extract_implications(content),
                'assumptions': self._extract_assumptions(content),
                'conclusions': self._extract_conclusions(content),
                'patterns': self._extract_patterns(content),
                'trends': self._extract_trends(content)
            }
            return features

        except Exception as e:
            logger.error(f"推断特征提取失败: {e}")
            return {}

    def extract_semantic_keywords(self, content: str) -> List[str]:
        """提取语义关键词"""
        try:
            # 使用自适应关键词生成
            keywords = self.generate_adaptive_keywords(content, "semantic_extraction")
            return keywords

        except Exception as e:
            logger.error(f"语义关键词提取失败: {e}")
            return []

    def generate_adaptive_keywords(self, content: str, context: str = "") -> List[str]:
        """生成自适应关键词"""
        try:
            # 基础关键词提取
            words = content.split()
            
            # 过滤和清理
            keywords = []
            for word in words:
                # 移除标点符号
                clean_word = re.sub(r'[^\w]', '', word)
                if len(clean_word) > 2:  # 过滤短词
                    keywords.append(clean_word.lower())
            
            # 去重并限制数量
            unique_keywords = list(set(keywords))
            return unique_keywords[:10]

        except Exception as e:
            logger.error(f"自适应关键词生成失败: {e}")
            return []

    def _get_adaptive_value(self, key: str, default_value: Any = None) -> Any:
        """获取自适应值"""
        try:
            # 从动态配置中获取值
            if key in self.dynamic_config:
                return self.dynamic_config[key]
            
            # 从智能配置中获取值
            context = create_query_context(key)
            value = get_smart_config(key, context)
            
            if value is not None:
                return value
            
            return default_value

        except Exception as e:
            logger.error(f"获取自适应值失败: {e}")
            return default_value

    def _create_error_result(self, operation: str, error: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            'operation': operation,
            'error': error,
            'confidence': 0.0,
            'processing_time': 0.0,
            'timestamp': time.time(),
            'success': False
        }

    # 私有辅助方法
    def _identify_semantic_concepts(self, content: str) -> List[str]:
        """识别语义概念"""
        # 简单的概念识别实现
        concepts = []
        words = content.split()
        
        # 基于词频和长度的概念识别
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            if len(clean_word) > 4:  # 长词更可能是概念
                concepts.append(clean_word.lower())
        
        return list(set(concepts))[:5]

    def _calculate_semantic_similarity(self, content: str) -> float:
        """计算语义相似性"""
        try:
            if not content or not content.strip():
                return 0.0
            
            # 使用多种方法计算语义相似性
            similarity_scores = []
            
            # 1. 基于词汇多样性的相似性
            words = content.lower().split()
            unique_words = len(set(words))
            total_words = len(words)
            
            if total_words > 0:
                diversity = unique_words / total_words
                similarity_scores.append(min(diversity * 2, 1.0))
            
            # 2. 基于语义关键词的相似性
            semantic_keywords = ['分析', '处理', '计算', '推理', '学习', '优化', '智能', '算法', '数据', '模型']
            keyword_count = sum(1 for word in words if word in semantic_keywords)
            if total_words > 0:
                keyword_similarity = keyword_count / total_words
                similarity_scores.append(min(keyword_similarity * 3, 1.0))
            
            # 3. 基于句子结构的相似性
            sentences = [s.strip() for s in content.split('.') if s.strip()]
            if sentences:
                avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
                structure_similarity = min(avg_sentence_length / 15, 1.0)
                similarity_scores.append(structure_similarity)
            
            # 4. 基于概念密度的相似性
            concept_indicators = ['因为', '所以', '因此', '然而', '但是', '而且', '或者', '如果', '那么']
            concept_count = sum(1 for indicator in concept_indicators if indicator in content)
            if total_words > 0:
                concept_density = concept_count / total_words
                similarity_scores.append(min(concept_density * 5, 1.0))
            
            # 计算加权平均相似性
            if similarity_scores:
                weights = [0.3, 0.25, 0.25, 0.2]
                weighted_similarity = sum(s * w for s, w in zip(similarity_scores, weights))
                return min(weighted_similarity, 1.0)
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error(f"语义相似性计算失败: {e}")
            return 0.0

    def _assess_semantic_complexity(self, content: str) -> float:
        """评估语义复杂度"""
        try:
            if not content or not content.strip():
                return 0.0
            
            complexity_indicators = []
            
            # 1. 句子长度复杂度
            sentences = [s.strip() for s in content.split('.') if s.strip()]
            if sentences:
                avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
                length_complexity = min(avg_sentence_length / 20, 1.0)
                complexity_indicators.append(length_complexity)
            
            # 2. 词汇复杂度
            words = content.lower().split()
            if words:
                # 长词比例
                long_words = [w for w in words if len(w) > 6]
                long_word_ratio = len(long_words) / len(words)
                complexity_indicators.append(min(long_word_ratio * 2, 1.0))
                
                # 专业词汇比例
                technical_terms = ['算法', '模型', '优化', '分析', '推理', '学习', '智能', '处理', '计算', '数据']
                technical_count = sum(1 for word in words if word in technical_terms)
                technical_ratio = technical_count / len(words)
                complexity_indicators.append(min(technical_ratio * 3, 1.0))
            
            # 3. 语法复杂度
            # 从句和复合句检测
            complex_indicators = ['因为', '所以', '然而', '但是', '而且', '或者', '如果', '那么', '虽然', '尽管']
            complex_count = sum(1 for indicator in complex_indicators if indicator in content)
            if words:
                complex_ratio = complex_count / len(words)
                complexity_indicators.append(min(complex_ratio * 4, 1.0))
            
            # 4. 概念密度
            concept_indicators = ['定义', '概念', '原理', '方法', '技术', '系统', '架构', '设计', '实现', '应用']
            concept_count = sum(1 for indicator in concept_indicators if indicator in content)
            if words:
                concept_density = concept_count / len(words)
                complexity_indicators.append(min(concept_density * 5, 1.0))
            
            # 计算加权平均复杂度
            if complexity_indicators:
                weights = [0.25, 0.25, 0.25, 0.25]
                weighted_complexity = sum(c * w for c, w in zip(complexity_indicators, weights))
                return min(weighted_complexity, 1.0)
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error(f"语义复杂度评估失败: {e}")
            return 0.0

    def _extract_text_features(self, content: str) -> List[float]:
        """提取文本特征"""
        features = []
        
        # 基础特征
        features.append(len(content))  # 长度
        features.append(len(content.split()))  # 词数
        features.append(len(content.split('.')))  # 句子数
        features.append(len(set(content.split())))  # 唯一词数
        
        # 字符特征
        features.append(content.count(' '))  # 空格数
        features.append(content.count('\n'))  # 换行数
        features.append(len([c for c in content if c.isupper()]))  # 大写字母数
        features.append(len([c for c in content if c.isdigit()]))  # 数字数
        
        # 填充到固定长度
        while len(features) < 10:
            features.append(0.0)
        
        return features[:10]

    def _extract_adaptive_features(self, content: str) -> Dict[str, Any]:
        """提取自适应特征"""
        return {
            'length_category': 'short' if len(content) < 100 else 'medium' if len(content) < 500 else 'long',
            'complexity_level': 'simple' if self._assess_semantic_complexity(content) < 0.3 else 'complex',
            'content_type': self._classify_content_type(content)
        }

    def _classify_content_type(self, content: str) -> str:
        """分类内容类型"""
        try:
            if not content or not content.strip():
                return 'general'
            
            content_lower = content.lower()
            type_scores = {}
            
            # 1. 问题类型检测
            question_indicators = ['?', 'how', 'what', 'why', 'when', 'where', 'who', 'which', '是否', '如何', '什么', '为什么', '哪里', '谁', '哪个']
            question_score = sum(1 for indicator in question_indicators if indicator in content_lower)
            type_scores['question'] = question_score
            
            # 2. 分析类型检测
            analysis_indicators = ['analysis', 'analyze', 'evaluate', 'assess', 'examine', 'investigate', '研究', '分析', '评估', '检查', '调查']
            analysis_score = sum(1 for indicator in analysis_indicators if indicator in content_lower)
            type_scores['analysis'] = analysis_score
            
            # 3. 数据类型检测
            data_indicators = ['data', 'information', 'fact', 'statistics', 'number', 'figure', '数据', '信息', '事实', '统计', '数字', '图表']
            data_score = sum(1 for indicator in data_indicators if indicator in content_lower)
            type_scores['data'] = data_score
            
            # 4. 指令类型检测
            instruction_indicators = ['please', 'should', 'must', 'need', 'require', 'command', '请', '应该', '必须', '需要', '要求', '命令']
            instruction_score = sum(1 for indicator in instruction_indicators if indicator in content_lower)
            type_scores['instruction'] = instruction_score
            
            # 5. 描述类型检测
            description_indicators = ['describe', 'explain', 'tell', 'show', 'present', '介绍', '解释', '说明', '展示', '呈现']
            description_score = sum(1 for indicator in description_indicators if indicator in content_lower)
            type_scores['description'] = description_score
            
            # 6. 比较类型检测
            comparison_indicators = ['compare', 'versus', 'vs', 'difference', 'similar', '对比', '比较', '差异', '相似']
            comparison_score = sum(1 for indicator in comparison_indicators if indicator in content_lower)
            type_scores['comparison'] = comparison_score
            
            # 选择得分最高的类型
            if type_scores:
                max_score = max(type_scores.values())
                if max_score > 0:
                    for content_type, score in type_scores.items():
                        if score == max_score:
                            return content_type
            
            # 默认返回通用类型
            return 'general'
            
        except Exception as e:
            self.logger.error(f"内容类型分类失败: {e}")
            return 'general'

    def _extract_named_entities(self, content: str) -> List[Dict[str, Any]]:
        """提取命名实体"""
        entities = []
        words = content.split()
        
        # 简单的命名实体识别
        for i, word in enumerate(words):
            if word[0].isupper() and len(word) > 2:  # 首字母大写的词
                entities.append({
                    'text': word,
                    'type': 'PERSON',
                    'start': i,
                    'end': i + 1,
                    'confidence': 0.7
                })
        
        return entities[:5]

    def _extract_concept_entities(self, content: str) -> List[Dict[str, Any]]:
        """提取概念实体"""
        try:
            if not content or not content.strip():
                return []
            
            entities = []
            concepts = self._identify_semantic_concepts(content)
            
            for concept in concepts:
                # 计算概念置信度
                confidence = _calculate_concept_confidence(concept, content)
                
                # 确定概念类型
                concept_type = _classify_concept_type(concept)
                
                entities.append({
                    'text': concept,
                    'type': concept_type,
                    'confidence': confidence,
                    'start': content.lower().find(concept.lower()),
                    'end': content.lower().find(concept.lower()) + len(concept)
                })
            
            # 按置信度排序并返回前10个
            entities.sort(key=lambda x: x['confidence'], reverse=True)
            return entities[:10]
            
        except Exception as e:
            self.logger.error(f"概念实体提取失败: {e}")
            return []

    def _extract_relation_entities(self, content: str) -> List[Dict[str, Any]]:
        """提取关系实体"""
        entities = []
        
        # 识别关系词
        relation_words = ['and', 'or', 'but', 'because', 'therefore', 'however']
        words = content.lower().split()
        
        for i, word in enumerate(words):
            if word in relation_words:
                entities.append({
                    'text': word,
                    'type': 'RELATION',
                    'start': i,
                    'end': i + 1,
                    'confidence': 0.8
                })
        
        return entities

    def _extract_semantic_relations(self, content: str) -> List[Dict[str, Any]]:
        """提取语义关系"""
        relations = []
        
        # 简单的语义关系识别
        if 'because' in content.lower():
            relations.append({
                'type': 'CAUSAL',
                'confidence': 0.7,
                'description': '因果关系'
            })
        
        if 'and' in content.lower():
            relations.append({
                'type': 'CONJUNCTION',
                'confidence': 0.6,
                'description': '并列关系'
            })
        
        return relations

    def _extract_syntactic_relations(self, content: str) -> List[Dict[str, Any]]:
        """提取语法关系"""
        relations = []
        
        # 基于标点符号的语法关系
        if '.' in content:
            relations.append({
                'type': 'SENTENCE_BOUNDARY',
                'confidence': 0.9,
                'description': '句子边界'
            })
        
        return relations

    def _extract_logical_relations(self, content: str) -> List[Dict[str, Any]]:
        """提取逻辑关系"""
        relations = []
        
        # 逻辑关系词
        logical_words = ['therefore', 'however', 'moreover', 'furthermore']
        
        for word in logical_words:
            if word in content.lower():
                relations.append({
                    'type': 'LOGICAL',
                    'confidence': 0.8,
                    'description': f'逻辑关系: {word}'
                })
        
        return relations

    def _analyze_domain_context(self, content: str) -> str:
        """分析领域上下文"""
        # 基于关键词的领域识别
        domains = {
            'technology': ['computer', 'software', 'algorithm', 'data'],
            'science': ['research', 'experiment', 'theory', 'hypothesis'],
            'business': ['market', 'profit', 'strategy', 'management'],
            'education': ['learning', 'teaching', 'student', 'knowledge']
        }
        
        content_lower = content.lower()
        for domain, keywords in domains.items():
            if any(keyword in content_lower for keyword in keywords):
                return domain
        
        return 'general'

    def _analyze_temporal_context(self, content: str) -> Dict[str, Any]:
        """分析时间上下文"""
        return {
            'tense': 'present',  # 简化实现
            'time_references': [],
            'temporal_markers': []
        }

    def _analyze_spatial_context(self, content: str) -> Dict[str, Any]:
        """分析空间上下文"""
        return {
            'location_references': [],
            'spatial_relations': []
        }

    def _analyze_social_context(self, content: str) -> Dict[str, Any]:
        """分析社会上下文"""
        return {
            'social_entities': [],
            'social_relations': []
        }

    def _analyze_cultural_context(self, content: str) -> Dict[str, Any]:
        """分析文化上下文"""
        return {
            'cultural_references': [],
            'cultural_markers': []
        }

    def _classify_intent_from_keywords(self, keywords: List[str]) -> str:
        """基于关键词分类意图"""
        if not keywords:
            return 'general'
        
        # 意图分类规则
        intent_patterns = {
            'question': ['what', 'how', 'why', 'when', 'where', 'who'],
            'request': ['please', 'could', 'would', 'can'],
            'analysis': ['analyze', 'evaluate', 'assess', 'examine'],
            'information': ['tell', 'explain', 'describe', 'show']
        }
        
        for intent, patterns in intent_patterns.items():
            if any(pattern in keywords for pattern in patterns):
                return intent
        
        return 'general'

    def _analyze_intent_details(self, intent: str) -> Dict[str, Any]:
        """分析意图详情"""
        return {
            'intent_type': intent,
            'confidence': 0.8,
            'complexity': 'simple'
        }

    def _analyze_entity_details(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析实体详情"""
        return {
            'entity_count': len(entities),
            'entity_types': list(set(e.get('type', 'UNKNOWN') for e in entities)),
            'confidence': 0.7
        }

    def _analyze_context_details(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析上下文详情"""
        return {
            'context_domains': list(context.keys()),
            'complexity': 'medium',
            'confidence': 0.6
        }

    def _analyze_general_details(self, content: str) -> Dict[str, Any]:
        """分析通用详情"""
        return {
            'length': len(content),
            'complexity': self._assess_semantic_complexity(content),
            'type': self._classify_content_type(content)
        }

    def _analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """分析情感"""
        # 简单的情感分析
        positive_words = ['good', 'great', 'excellent', 'positive', 'happy']
        negative_words = ['bad', 'terrible', 'negative', 'sad', 'angry']
        
        content_lower = content.lower()
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            sentiment = 'positive'
        elif negative_count > positive_count:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'confidence': 0.6,
            'positive_score': positive_count,
            'negative_score': negative_count
        }

    def _extract_topics(self, content: str) -> List[str]:
        """提取主题"""
        # 基于关键词的主题提取
        keywords = self.generate_adaptive_keywords(content, "topic_extraction")
        return keywords[:3]

    def _extract_semantic_entities(self, content: str) -> List[Dict[str, Any]]:
        """提取语义实体"""
        return self.extract_content_entities(content)

    def _identify_domain(self, content: str) -> str:
        """识别领域"""
        return self._analyze_domain_context(content)

    def _analyze_style(self, content: str) -> str:
        """分析风格"""
        # 基于句子长度的风格分析
        sentences = content.split('.')
        avg_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        if avg_length < 10:
            return 'concise'
        elif avg_length > 20:
            return 'detailed'
        else:
            return 'balanced'

    def _assess_complexity(self, content: str) -> float:
        """评估复杂度"""
        return self._assess_semantic_complexity(content)

    def _assess_coherence(self, content: str) -> float:
        """评估连贯性"""
        # 基于句子连接的连贯性评估
        sentences = content.split('.')
        if len(sentences) < 2:
            return 1.0
        
        # 简单的连贯性计算
        coherence = min(len(sentences) / 10, 1.0)
        return coherence

    def _assess_relevance(self, content: str) -> float:
        """评估相关性"""
        # 基于关键词密度的相关性评估
        keywords = self.generate_adaptive_keywords(content, "relevance")
        relevance = min(len(keywords) / 20, 1.0)
        return relevance

    def _extract_implications(self, content: str) -> List[str]:
        """提取含义"""
        implications = []
        
        # 基于逻辑词的含义提取
        if 'therefore' in content.lower():
            implications.append('逻辑结论')
        
        if 'however' in content.lower():
            implications.append('对比关系')
        
        return implications

    def _extract_assumptions(self, content: str) -> List[str]:
        """提取假设"""
        assumptions = []
        
        # 基于假设词的假设提取
        assumption_words = ['assume', 'suppose', 'if', 'when']
        for word in assumption_words:
            if word in content.lower():
                assumptions.append(f'基于{word}的假设')
        
        return assumptions


# 辅助方法实现
def _calculate_concept_confidence(concept: str, content: str) -> float:
    """计算概念置信度"""
    try:
        if not concept or not content:
            return 0.0
        
        confidence_factors = []
        
        # 1. 概念长度因子
        length_factor = min(len(concept) / 10, 1.0)
        confidence_factors.append(length_factor)
        
        # 2. 概念出现频率因子
        concept_lower = concept.lower()
        content_lower = content.lower()
        frequency = content_lower.count(concept_lower)
        frequency_factor = min(frequency / 3, 1.0)
        confidence_factors.append(frequency_factor)
        
        # 3. 概念上下文因子
        context_indicators = ['定义', '概念', '原理', '方法', '技术', '系统', '架构', '设计', '实现', '应用']
        context_count = sum(1 for indicator in context_indicators if indicator in content_lower)
        context_factor = min(context_count / 5, 1.0)
        confidence_factors.append(context_factor)
        
        # 4. 概念专业性因子
        technical_terms = ['算法', '模型', '优化', '分析', '推理', '学习', '智能', '处理', '计算', '数据']
        technical_count = sum(1 for term in technical_terms if term in concept_lower)
        technical_factor = min(technical_count / 2, 1.0)
        confidence_factors.append(technical_factor)
        
        # 计算加权平均置信度
        if confidence_factors:
            weights = [0.2, 0.3, 0.3, 0.2]
            weighted_confidence = sum(c * w for c, w in zip(confidence_factors, weights))
            return min(weighted_confidence, 1.0)
        else:
            return 0.0
            
    except Exception as e:
        return 0.0


def _classify_concept_type(concept: str) -> str:
    """分类概念类型（🚀 智能方案：使用语义匹配，无需硬编码关键词）"""
    try:
        if not concept:
            return 'UNKNOWN'
        
        # 🚀 智能方案：使用语义相似度进行分类
        try:
            from src.utils.unified_classification_service import SemanticBasedFallbackClassifier
            
            semantic_classifier = SemanticBasedFallbackClassifier()
            
            # 定义概念类型的示例（用于语义匹配）
            concept_examples = {
                'TECHNICAL': ['algorithm implementation', 'machine learning model', 'computational method'],
                'METHOD': ['approach technique', 'system architecture', 'design pattern'],
                'DOMAIN': ['field of study', 'professional domain', 'subject area'],
                'ABSTRACT': ['theoretical concept', 'definition principle', 'abstract idea'],
                'GENERAL': ['general concept', 'common term', 'basic idea']
            }
            
            # 计算与每种类型的语义相似度
            max_similarity = 0.0
            best_type = 'GENERAL'
            
            for ctype, examples in concept_examples.items():
                for example in examples:
                    similarity = semantic_classifier.calculate_semantic_similarity(concept, example)
                    if similarity > max_similarity:
                        max_similarity = similarity
                        best_type = ctype
            
            # 如果相似度足够高，返回该类型
            if max_similarity >= 0.4:
                return best_type
            
            return 'GENERAL'
            
        except Exception as e:
            # Fallback: 返回通用类型
            return 'GENERAL'
        
    except Exception as e:
        return 'UNKNOWN'

    def _extract_conclusions(self, content: str) -> List[str]:
        """提取结论"""
        conclusions = []
        
        # 基于结论词的结论提取
        conclusion_words = ['conclusion', 'therefore', 'thus', 'hence']
        for word in conclusion_words:
            if word in content.lower():
                conclusions.append(f'基于{word}的结论')
        
        return conclusions

    def _extract_patterns(self, content: str) -> List[str]:
        """提取模式"""
        patterns = []
        
        # 基于重复的模式提取
        words = content.lower().split()
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 找出高频词
        for word, freq in word_freq.items():
            if freq > 2:
                patterns.append(f'重复模式: {word}')
        
        return patterns[:3]

    def _extract_trends(self, content: str) -> List[str]:
        """提取趋势"""
        trends = []
        
        # 基于趋势词的趋势提取
        trend_words = ['increase', 'decrease', 'rise', 'fall', 'grow', 'decline']
        for word in trend_words:
            if word in content.lower():
                trends.append(f'趋势: {word}')
        
        return trends