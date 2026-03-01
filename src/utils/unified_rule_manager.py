#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一规则管理中心 - 统一管理所有规则、模式、关键词、阈值

设计目标：
1. 统一管理所有硬编码的规则、模式、关键词、阈值
2. 优先使用语义理解，减少硬编码依赖
3. 支持灵活配置，易于调整和优化
4. 提高代码可维护性和可扩展性

使用方式：
    from src.utils.unified_rule_manager import get_unified_rule_manager
    
    rule_manager = get_unified_rule_manager()
    keywords = rule_manager.get_keywords('non_person_indicators', context=answer)
    match = rule_manager.match_pattern('final_answer', text)
    is_valid = rule_manager.validate('answer_length', answer, {'min': 2, 'max': 100})
    threshold = rule_manager.get_threshold('semantic_similarity', context='answer_validation')
"""
import re
import logging
from typing import Dict, List, Any, Optional, Callable, Match as ReMatch
from collections import defaultdict

logger = logging.getLogger(__name__)


class UnifiedRuleManager:
    """统一规则管理中心
    
    统一管理所有规则、模式、关键词、阈值，优先使用语义理解。
    """
    
    def __init__(self, config_center=None, semantic_pipeline=None):
        """初始化统一规则管理中心
        
        Args:
            config_center: 统一配置中心实例
            semantic_pipeline: 语义理解管道实例
        """
        self.logger = logging.getLogger(__name__)
        self.config_center = config_center
        self.semantic_pipeline = semantic_pipeline
        
        # 初始化各个子管理器
        self.keyword_manager = KeywordManager(config_center)
        self.pattern_manager = PatternManager(config_center)
        self.rule_manager = RuleManager(config_center)
        self.threshold_manager = ThresholdManager(config_center)
        self.semantic_enhancer = SemanticEnhancer(semantic_pipeline)
        
        self.logger.info("✅ 统一规则管理中心已初始化")
    
    def get_keywords(self, category: str, context: Optional[str] = None) -> List[str]:
        """获取关键词列表（优先使用语义理解）
        
        Args:
            category: 关键词类别（如'non_person_indicators', 'place_keywords'等）
            context: 上下文文本（用于语义理解）
            
        Returns:
            关键词列表
        """
        # 1. 优先使用语义理解
        if self.semantic_enhancer and context:
            semantic_keywords = self.semantic_enhancer.get_semantic_keywords(category, context)
            if semantic_keywords:
                self.logger.debug(f"使用语义理解获取关键词: {category}, 数量: {len(semantic_keywords)}")
                return semantic_keywords
        
        # 2. Fallback到配置中心
        return self.keyword_manager.get_keywords(category)
    
    def match_pattern(self, pattern_type: str, text: str) -> Optional[ReMatch]:
        """匹配模式（优先使用语义理解）
        
        Args:
            pattern_type: 模式类型（如'final_answer', 'date', 'number'等）
            text: 要匹配的文本
            
        Returns:
            匹配结果，如果未匹配返回None
        """
        # 1. 优先使用语义理解
        if self.semantic_enhancer:
            semantic_match = self.semantic_enhancer.match_semantic_pattern(pattern_type, text)
            if semantic_match:
                return semantic_match
        
        # 2. Fallback到模式匹配
        return self.pattern_manager.match(pattern_type, text)
    
    def validate(self, rule_type: str, value: Any, context: Optional[Dict] = None) -> bool:
        """验证规则（优先使用语义理解）
        
        Args:
            rule_type: 规则类型（如'answer_length', 'alnum_ratio'等）
            value: 要验证的值
            context: 上下文信息
            
        Returns:
            验证结果
        """
        # 1. 优先使用语义理解
        if self.semantic_enhancer and context:
            semantic_result = self.semantic_enhancer.validate_semantic(rule_type, value, context)
            if semantic_result is not None:
                return semantic_result
        
        # 2. Fallback到规则验证
        return self.rule_manager.validate(rule_type, value, context)
    
    def get_threshold(self, threshold_type: str, context: Optional[str] = None) -> float:
        """获取阈值
        
        Args:
            threshold_type: 阈值类型（如'semantic_similarity', 'confidence'等）
            context: 上下文（用于获取上下文相关的阈值）
            
        Returns:
            阈值
        """
        return self.threshold_manager.get_threshold(threshold_type, context)


class KeywordManager:
    """关键词管理器
    
    管理所有关键词列表，支持从配置中心读取。
    """
    
    def __init__(self, config_center=None):
        """初始化关键词管理器
        
        Args:
            config_center: 统一配置中心实例
        """
        self.config_center = config_center
        self._cache = {}
        self.logger = logging.getLogger(__name__)
    
    def get_keywords(self, category: str) -> List[str]:
        """获取关键词列表
        
        Args:
            category: 关键词类别
            
        Returns:
            关键词列表（如果不存在返回空列表，不再硬编码默认值）
        """
        # 1. 检查缓存
        if category in self._cache:
            return self._cache[category]
        
        # 2. 从配置中心读取
        if self.config_center:
            try:
                keywords = self.config_center.get_config_value('keywords', category, None)
                if keywords and isinstance(keywords, list):
                    self._cache[category] = keywords
                    return keywords
            except Exception as e:
                self.logger.debug(f"从配置中心获取关键词失败: {e}")
        
        # 3. 返回空列表（不再硬编码默认值）
        self.logger.debug(f"关键词类别 '{category}' 不存在，返回空列表")
        return []
    
    def add_keywords(self, category: str, keywords: List[str]):
        """添加关键词
        
        Args:
            category: 关键词类别
            keywords: 关键词列表
        """
        existing = self.get_keywords(category)
        self._cache[category] = list(set(existing + keywords))
        
        # 更新配置中心
        if self.config_center:
            try:
                self.config_center.set_config_value('keywords', category, self._cache[category])
            except Exception as e:
                self.logger.debug(f"更新配置中心失败: {e}")


class PatternManager:
    """模式管理器
    
    管理所有正则表达式模式，支持模式组合和扩展。
    """
    
    def __init__(self, config_center=None):
        """初始化模式管理器
        
        Args:
            config_center: 统一配置中心实例
        """
        self.config_center = config_center
        self._patterns = {}
        self.logger = logging.getLogger(__name__)
        self._load_patterns()
    
    def _load_patterns(self):
        """加载模式定义"""
        # 从配置中心加载
        if self.config_center:
            try:
                patterns = self.config_center.get_config_value('patterns', None, {})
                if patterns and isinstance(patterns, dict):
                    self._patterns.update(patterns)
            except Exception as e:
                self.logger.debug(f"从配置中心加载模式失败: {e}")
    
    def match(self, pattern_type: str, text: str) -> Optional[ReMatch]:
        """匹配模式
        
        Args:
            pattern_type: 模式类型
            text: 要匹配的文本
            
        Returns:
            匹配结果，如果未匹配返回None
        """
        patterns = self._patterns.get(pattern_type, [])
        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match
            except Exception as e:
                self.logger.debug(f"模式匹配失败: {pattern}, 错误: {e}")
        return None
    
    def add_pattern(self, pattern_type: str, pattern: str):
        """添加模式
        
        Args:
            pattern_type: 模式类型
            pattern: 正则表达式模式
        """
        if pattern_type not in self._patterns:
            self._patterns[pattern_type] = []
        self._patterns[pattern_type].append(pattern)
        
        # 更新配置中心
        if self.config_center:
            try:
                self.config_center.set_config_value('patterns', pattern_type, self._patterns[pattern_type])
            except Exception as e:
                self.logger.debug(f"更新配置中心失败: {e}")


class RuleManager:
    """规则管理器
    
    管理所有验证规则，支持规则组合和扩展。
    """
    
    def __init__(self, config_center=None):
        """初始化规则管理器
        
        Args:
            config_center: 统一配置中心实例
        """
        self.config_center = config_center
        self._rules = {}
        self.logger = logging.getLogger(__name__)
        self._load_rules()
    
    def _load_rules(self):
        """加载规则定义"""
        # 从配置中心加载
        if self.config_center:
            try:
                rules = self.config_center.get_config_value('rules', None, {})
                if rules and isinstance(rules, dict):
                    # 将配置转换为规则函数
                    for rule_type, rule_config in rules.items():
                        self._rules[rule_type] = self._create_rule(rule_type, rule_config)
            except Exception as e:
                self.logger.debug(f"从配置中心加载规则失败: {e}")
    
    def _create_rule(self, rule_type: str, rule_config: Dict) -> Callable:
        """创建规则函数
        
        Args:
            rule_type: 规则类型
            rule_config: 规则配置
            
        Returns:
            规则函数
        """
        if rule_type == 'answer_length':
            min_len = rule_config.get('min', 2)
            max_len = rule_config.get('max', 100)
            return lambda value, context: min_len <= len(str(value)) <= max_len
        
        elif rule_type == 'alnum_ratio':
            min_ratio = rule_config.get('min', 0.7)
            return lambda value, context: (
                sum(1 for c in str(value) if c.isalnum() or c.isspace()) / len(str(value))
                if len(str(value)) > 0 else 0
            ) >= min_ratio
        
        # 默认规则：总是通过
        return lambda value, context: True
    
    def validate(self, rule_type: str, value: Any, context: Optional[Dict] = None) -> bool:
        """验证规则
        
        Args:
            rule_type: 规则类型
            value: 要验证的值
            context: 上下文信息
            
        Returns:
            验证结果（如果规则不存在，默认返回True）
        """
        rule = self._rules.get(rule_type)
        if not rule:
            self.logger.debug(f"规则类型 '{rule_type}' 不存在，默认通过")
            return True  # 默认通过
        
        try:
            return rule(value, context or {})
        except Exception as e:
            self.logger.debug(f"规则验证失败: {rule_type}, 错误: {e}")
            return True  # 验证失败，保守地通过


class ThresholdManager:
    """阈值管理器
    
    管理所有阈值，支持上下文相关的阈值。
    """
    
    def __init__(self, config_center=None):
        """初始化阈值管理器
        
        Args:
            config_center: 统一配置中心实例
        """
        self.config_center = config_center
        self._thresholds = {}
        self.logger = logging.getLogger(__name__)
        self._load_thresholds()
    
    def _load_thresholds(self):
        """加载阈值定义"""
        # 默认阈值（避免硬编码0.5导致过严）
        self._thresholds = {
            'semantic_similarity': 0.3,
            'query_answer_consistency': 0.25, # 降低一致性阈值，避免误杀
            'evidence_relevance': 0.4,
            'confidence': 0.6,
            'evidence_match_ratio': 0.2,
            'ordinal_difference': 10
        }
        
        # 从配置中心加载
        if self.config_center:
            try:
                thresholds = self.config_center.get_config_value('thresholds', None, {})
                if thresholds and isinstance(thresholds, dict):
                    self._thresholds.update(thresholds)
            except Exception as e:
                self.logger.debug(f"从配置中心加载阈值失败: {e}")
    
    def get_threshold(self, threshold_type: str, context: Optional[str] = None) -> float:
        """获取阈值
        
        Args:
            threshold_type: 阈值类型
            context: 上下文（用于获取上下文相关的阈值）
            
        Returns:
            阈值（如果不存在，返回默认值0.5）
        """
        # 支持上下文相关的阈值
        if context:
            key = f"{threshold_type}:{context}"
            if key in self._thresholds:
                return self._thresholds[key]
        
        # Fallback到默认阈值
        return self._thresholds.get(threshold_type, 0.5)
    
    def set_threshold(self, threshold_type: str, value: float, context: Optional[str] = None):
        """设置阈值
        
        Args:
            threshold_type: 阈值类型
            value: 阈值
            context: 上下文
        """
        key = f"{threshold_type}:{context}" if context else threshold_type
        self._thresholds[key] = value
        
        # 更新配置中心
        if self.config_center:
            try:
                self.config_center.set_config_value('thresholds', key, value)
            except Exception as e:
                self.logger.debug(f"更新配置中心失败: {e}")


class SemanticEnhancer:
    """语义增强器
    
    提供基于语义理解的功能，优先使用语义理解。
    """
    
    def __init__(self, semantic_pipeline=None):
        """初始化语义增强器
        
        Args:
            semantic_pipeline: 语义理解管道实例
        """
        self.pipeline = semantic_pipeline
        self.logger = logging.getLogger(__name__)
        
        # 延迟加载语义理解管道
        if not self.pipeline:
            try:
                from src.utils.semantic_understanding_pipeline import get_semantic_understanding_pipeline
                self.pipeline = get_semantic_understanding_pipeline()
            except Exception as e:
                self.logger.debug(f"获取语义理解管道失败: {e}")
    
    def get_semantic_keywords(self, category: str, context: str) -> Optional[List[str]]:
        """使用语义理解获取关键词
        
        Args:
            category: 关键词类别（如'PERSON', 'ORG', 'GPE'等）
            context: 上下文文本
            
        Returns:
            关键词列表，如果无法获取返回None
        """
        if not self.pipeline:
            return None
        
        try:
            # 使用NER提取实体
            entities = self.pipeline.extract_entities_intelligent(context)
            if entities:
                # 根据类别过滤实体
                category_upper = category.upper()
                if category_upper in ['PERSON', 'ORG', 'GPE', 'LOC', 'FAC']:
                    filtered = [e['text'] for e in entities if e.get('label') == category_upper]
                    if filtered:
                        return filtered
        except Exception as e:
            self.logger.debug(f"语义关键词提取失败: {e}")
        
        return None
    
    def match_semantic_pattern(self, pattern_type: str, text: str) -> Optional[ReMatch]:
        """使用语义理解匹配模式
        
        Args:
            pattern_type: 模式类型（如'person', 'date', 'number'等）
            text: 要匹配的文本
            
        Returns:
            匹配结果，如果无法匹配返回None
        """
        if not self.pipeline:
            return None
        
        try:
            # 根据模式类型使用不同的语义理解方法
            if pattern_type == 'person':
                entities = self.pipeline.extract_entities_intelligent(text)
                person_entities = [e for e in entities if e.get('label') == 'PERSON']
                if person_entities:
                    # 创建一个Match对象
                    match_text = person_entities[0]['text']
                    # 使用正则表达式找到匹配位置
                    pattern = re.escape(match_text)
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        return match
            
            elif pattern_type == 'date':
                entities = self.pipeline.extract_entities_intelligent(text)
                date_entities = [e for e in entities if e.get('label') == 'DATE']
                if date_entities:
                    match_text = date_entities[0]['text']
                    pattern = re.escape(match_text)
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        return match
            
            elif pattern_type == 'number':
                # 使用NER可能无法很好地识别数字，这里使用正则作为fallback
                number_pattern = r'\b\d+(?:\.\d+)?%?\b'
                match = re.search(number_pattern, text)
                if match:
                    return match
        except Exception as e:
            self.logger.debug(f"语义模式匹配失败: {e}")
        
        return None
    
    def validate_semantic(self, rule_type: str, value: Any, context: Optional[Dict] = None) -> Optional[bool]:
        """使用语义理解验证
        
        Args:
            rule_type: 规则类型（如'relevance', 'type_consistency'等）
            value: 要验证的值
            context: 上下文信息
            
        Returns:
            验证结果，如果无法验证返回None
        """
        if not self.pipeline or not context:
            return None
        
        try:
            # 根据规则类型使用不同的语义理解方法
            if rule_type == 'relevance':
                query = context.get('query', '')
                evidence = context.get('evidence', '')
                if query and evidence:
                    similarity = self.pipeline.calculate_semantic_similarity(query, evidence)
                    threshold = context.get('threshold', 0.3)
                    return similarity >= threshold
            
            elif rule_type == 'type_consistency':
                query = context.get('query', '')
                answer = str(value)
                if query and answer:
                    # 提取查询和答案的实体类型
                    query_entities = self.pipeline.extract_entities_intelligent(query)
                    answer_entities = self.pipeline.extract_entities_intelligent(answer)
                    
                    if query_entities and answer_entities:
                        query_types = {e.get('label') for e in query_entities}
                        answer_types = {e.get('label') for e in answer_entities}
                        
                        # 检查类型一致性
                        if 'PERSON' in query_types and answer_types & {'ORG', 'GPE', 'LOC', 'FAC'}:
                            return False  # 类型不一致
                        return True  # 类型一致或无法判断
        except Exception as e:
            self.logger.debug(f"语义验证失败: {e}")
        
        return None


# 全局实例（延迟初始化）
_global_rule_manager = None


def get_unified_rule_manager(config_center=None, semantic_pipeline=None) -> UnifiedRuleManager:
    """获取统一规则管理中心实例（单例模式）
    
    Args:
        config_center: 统一配置中心实例
        semantic_pipeline: 语义理解管道实例
        
    Returns:
        统一规则管理中心实例
    """
    global _global_rule_manager
    
    if _global_rule_manager is None:
        # 如果没有提供，尝试从统一中心获取
        if config_center is None:
            try:
                from src.utils.unified_centers import get_unified_config_center
                config_center = get_unified_config_center()
            except Exception as e:
                logger.debug(f"获取统一配置中心失败: {e}")
        
        if semantic_pipeline is None:
            try:
                from src.utils.semantic_understanding_pipeline import get_semantic_understanding_pipeline
                semantic_pipeline = get_semantic_understanding_pipeline()
            except Exception as e:
                logger.debug(f"获取语义理解管道失败: {e}")
        
        _global_rule_manager = UnifiedRuleManager(
            config_center=config_center,
            semantic_pipeline=semantic_pipeline
        )
    
    return _global_rule_manager

