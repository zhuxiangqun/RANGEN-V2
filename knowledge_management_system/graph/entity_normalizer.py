#!/usr/bin/env python3
"""
实体名称规范化工具
统一处理实体名称的格式，减少重复实体
"""

import re
from typing import Dict, Optional
from ..utils.logger import get_logger

logger = get_logger()


class EntityNormalizer:
    """实体名称规范化器"""
    
    # 常见缩写映射
    COMMON_ABBREVIATIONS = {
        # 人名缩写
        'jr': 'Junior',
        'sr': 'Senior',
        'jr.': 'Junior',
        'sr.': 'Senior',
        # 地名缩写
        'u.s.': 'United States',
        'us': 'United States',
        'u.s.a.': 'United States',
        'usa': 'United States',
        'uk': 'United Kingdom',
        'u.k.': 'United Kingdom',
        # 组织缩写
        'inc.': 'Incorporated',
        'inc': 'Incorporated',
        'ltd.': 'Limited',
        'ltd': 'Limited',
        'corp.': 'Corporation',
        'corp': 'Corporation',
        'co.': 'Company',
        'co': 'Company',
    }
    
    # 需要首字母大写的词（除了介词、连词等）
    CAPITALIZE_WORDS = {
        'of', 'the', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'with', 'by',
        'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being',
        'a', 'an', 'the',  # 冠词
    }
    
    @staticmethod
    def normalize_entity_name(
        name: str,
        entity_type: Optional[str] = None
    ) -> str:
        """
        规范化实体名称
        
        Args:
            name: 原始实体名称
            entity_type: 实体类型（Person、Location、Organization等），用于应用特定规则
        
        Returns:
            规范化后的实体名称
        """
        if not name or not name.strip():
            return ""
        
        # 步骤1: 基本清理
        normalized = name.strip()
        
        # 去除换行符、制表符等
        normalized = re.sub(r'[\n\r\t]+', ' ', normalized)
        
        # 去除多余空格
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # 去除首尾空白
        normalized = normalized.strip()
        
        if not normalized:
            return ""
        
        # 步骤2: 处理缩写（在大小写规范化之前）
        normalized = EntityNormalizer._expand_abbreviations(normalized)
        
        # 步骤3: 统一大小写（根据实体类型）- 需要重新应用，因为缩写展开可能改变了大小写
        normalized = EntityNormalizer._normalize_case(normalized, entity_type)
        
        # 步骤4: 处理撇号后的大写（如 "O'Brien"）
        normalized = EntityNormalizer._fix_apostrophe_case(normalized)
        
        # 步骤5: 清理标点符号（保留必要的连字符、撇号和点号）
        normalized = EntityNormalizer._clean_punctuation(normalized, entity_type)
        
        # 步骤6: 再次规范化大小写（确保所有词都正确大写）
        normalized = EntityNormalizer._normalize_case(normalized, entity_type)
        
        # 步骤7: 最终清理
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    @staticmethod
    def _expand_abbreviations(text: str) -> str:
        """
        展开常见缩写
        
        Args:
            text: 原始文本
        
        Returns:
            展开缩写后的文本
        """
        # 将文本转换为小写进行匹配（但保留原始大小写结构）
        words = text.split()
        expanded_words = []
        
        for word in words:
            # 检查是否是单字母+点号（如 "A."），保留原样不展开
            if re.match(r'^[A-Za-z]\.$', word):
                expanded_words.append(word)
                continue
            
            # 去除标点符号进行匹配
            word_clean = re.sub(r'[^\w]', '', word.lower())
            
            if word_clean in EntityNormalizer.COMMON_ABBREVIATIONS:
                # 展开缩写，保持原始大小写风格
                expanded = EntityNormalizer.COMMON_ABBREVIATIONS[word_clean]
                
                # 如果原词首字母大写，展开词也首字母大写
                if word[0].isupper():
                    expanded = expanded.capitalize()
                
                # 不添加标点符号（缩写展开后不需要标点）
                expanded_words.append(expanded)
            else:
                # 保留原始词（包括标点符号，如 "A."）
                expanded_words.append(word)
        
        return ' '.join(expanded_words)
    
    @staticmethod
    def _normalize_case(text: str, entity_type: Optional[str] = None) -> str:
        """
        统一大小写规则
        
        Args:
            text: 原始文本
            entity_type: 实体类型
        
        Returns:
            规范化大小写后的文本
        """
        if not text:
            return text
        
        # 如果已经是全大写或全小写，需要规范化
        is_all_upper = text.isupper()
        is_all_lower = text.islower()
        
        if is_all_upper or is_all_lower:
            # 根据实体类型应用不同规则
            if entity_type == "Person":
                # 人名：每个词首字母大写（除了介词、连词等）
                return EntityNormalizer._title_case_person_name(text)
            elif entity_type in ["Location", "Organization"]:
                # 地名和组织名：每个词首字母大写（除了介词、连词等）
                return EntityNormalizer._title_case_location_org(text)
            else:
                # 默认：标题格式（每个词首字母大写）
                return EntityNormalizer._title_case(text)
        
        # 无论是否全大写/全小写，都应用规范化规则
        # 根据实体类型应用不同规则
        if entity_type == "Person":
            return EntityNormalizer._title_case_person_name(text)
        elif entity_type in ["Location", "Organization"]:
            return EntityNormalizer._title_case_location_org(text)
        else:
            return EntityNormalizer._title_case(text)
    
    @staticmethod
    def _title_case_person_name(text: str) -> str:
        """
        人名标题格式：每个词首字母大写（除了介词、连词等）
        
        Args:
            text: 原始文本
        
        Returns:
            标题格式的文本
        """
        words = text.split()
        result = []
        
        for i, word in enumerate(words):
            # 处理带点号的缩写（如 "A."）
            has_period = word.endswith('.')
            word_base = word.rstrip('.')
            word_base_lower = word_base.lower()
            
            # 单字母缩写（如 "A"）总是大写
            if len(word_base) == 1:
                capitalized = word_base.upper()
                if has_period:
                    capitalized += '.'
                result.append(capitalized)
            # 第一个词和最后一个词总是首字母大写
            elif i == 0 or i == len(words) - 1:
                capitalized = word_base.capitalize()
                if has_period:
                    capitalized += '.'
                result.append(capitalized)
            # 中间词：如果是介词、连词等，保持小写；否则首字母大写
            elif word_base_lower in EntityNormalizer.CAPITALIZE_WORDS:
                # 保持小写，但保留点号
                if has_period:
                    result.append(word_base_lower + '.')
                else:
                    result.append(word_base_lower)
            else:
                capitalized = word_base.capitalize()
                if has_period:
                    capitalized += '.'
                result.append(capitalized)
        
        return ' '.join(result)
    
    @staticmethod
    def _fix_apostrophe_case(text: str) -> str:
        """
        修复撇号后的大写（如 "O'Brien" -> "O'Brien"）
        
        Args:
            text: 原始文本
        
        Returns:
            修复后的文本
        """
        # 匹配撇号后的字母，将其大写
        def uppercase_after_apostrophe(match):
            return match.group(0)[0] + match.group(0)[1].upper() + match.group(0)[2:]
        
        # 匹配撇号后跟小写字母的情况
        text = re.sub(r"([''])([a-z])", lambda m: m.group(1) + m.group(2).upper(), text)
        
        return text
    
    @staticmethod
    def _title_case_location_org(text: str) -> str:
        """
        地名/组织名标题格式：每个词首字母大写（除了介词、连词等）
        
        Args:
            text: 原始文本
        
        Returns:
            标题格式的文本
        """
        words = text.split()
        result = []
        
        for i, word in enumerate(words):
            word_lower = word.lower()
            
            # 第一个词总是首字母大写
            if i == 0:
                result.append(word.capitalize())
            # 其他词：如果是介词、连词等，保持小写；否则首字母大写
            elif word_lower in EntityNormalizer.CAPITALIZE_WORDS:
                result.append(word_lower)
            else:
                result.append(word.capitalize())
        
        return ' '.join(result)
    
    @staticmethod
    def _title_case(text: str) -> str:
        """
        标准标题格式：每个词首字母大写
        
        Args:
            text: 原始文本
        
        Returns:
            标题格式的文本
        """
        return text.title()
    
    @staticmethod
    def _clean_punctuation(text: str, entity_type: Optional[str] = None) -> str:
        """
        清理标点符号，保留必要的连字符、撇号和点号（用于缩写）
        
        Args:
            text: 原始文本
            entity_type: 实体类型（用于判断是否保留点号）
        
        Returns:
            清理后的文本
        """
        # 保留连字符（用于复合词，如 "New York"）
        # 保留撇号（用于所有格，如 "O'Brien"）
        # 保留点号（仅用于单字母缩写，如 "A."）
        # 移除其他标点符号（逗号、分号等）
        
        # 先处理特殊情况：保留连字符和撇号
        # 将特殊字符替换为占位符
        text = text.replace('-', '___HYPHEN___')
        text = text.replace("'", '___APOSTROPHE___')
        text = text.replace("'", '___APOSTROPHE___')
        
        # 处理点号：只保留单字母缩写后的点号（如 "A."）
        # 先标记单字母+点号的模式，避免被后续清理移除
        words = text.split()
        processed_words = []
        single_letter_periods = {}  # 记录单字母+点号的位置
        
        for i, word in enumerate(words):
            # 如果单词是单字母+点号（如 "A."），标记并保留
            if re.match(r'^[A-Za-z]\.$', word):
                processed_words.append('___SINGLE_LETTER_PERIOD___')
                single_letter_periods[i] = word
            else:
                # 移除点号
                processed_words.append(word.replace('.', ''))
        text = ' '.join(processed_words)
        
        # 移除其他标点符号（逗号、分号、冒号等）
        text = re.sub(r'[^\w\s]', '', text)
        
        # 恢复单字母+点号
        words_final = text.split()
        for i, period_word in single_letter_periods.items():
            if i < len(words_final):
                words_final[i] = period_word
        text = ' '.join(words_final).replace('___SINGLE_LETTER_PERIOD___', '')
        
        # 恢复特殊字符
        text = text.replace('___HYPHEN___', '-')
        text = text.replace('___APOSTROPHE___', "'")
        
        return text


def normalize_entity_name(
    name: str,
    entity_type: Optional[str] = None
) -> str:
    """
    规范化实体名称（便捷函数）
    
    Args:
        name: 原始实体名称
        entity_type: 实体类型（Person、Location、Organization等）
    
    Returns:
        规范化后的实体名称
    """
    return EntityNormalizer.normalize_entity_name(name, entity_type)

