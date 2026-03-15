#!/usr/bin/env python3
"""智能上下文管理模块 - 从UnifiedIntelligentCenter中分离出来"""

import time
import re
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter
import logging

# 智能配置系统导入
from src.utils.smart_config_system import get_smart_config, create_query_context

logger = logging.getLogger(__name__)


class IntelligentContextManager:
    """智能上下文管理器"""
    
    def __init__(self, config_center):
        self.config_center = config_center
        self.context_compression_config = self._setup_compression_config()
        self.context_memory = {
            'dynamic_memory': {},
            'static_memory': {},
            'hybrid_memory': {}
        }
    
    def _setup_compression_config(self) -> Dict[str, Any]:
        """设置压缩配置"""
        return {
            'compression_ratio': 0.config.DEFAULT_MAX_RETRIES,
            'min_compression_ratio': config.DEFAULT_LOW_DECIMAL_THRESHOLD,
            'max_compression_ratio': get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")),
            'quality_threshold': config.DEFAULT_HIGH_MEDIUM_THRESHOLD,
            'memory_modes': {
                'dynamic': {
                    'update_frequency': config.DEFAULT_LOW_DECIMAL_THRESHOLD,
                    'decay_factor': config.DEFAULT_HIGH_THRESHOLD
                },
                'static': {
                    'persistence_threshold': get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")),
                    'update_frequency': config.DEFAULT_LOW_THRESHOLD
                },
                'hybrid': {
                    'dynamic_weight': config.DEFAULT_MEDIUM_HIGH_THRESHOLD,
                    'static_weight': config.DEFAULT_MEDIUM_LOW_THRESHOLD
                }
            }
        }
    
    def dynamic_context_compression(self, content: str) -> Dict[str, Any]:
        """动态上下文压缩"""
        try:
            # 提取语义主干
            semantic_main = self._extract_semantic_main(content)
            
            # 提取关键信息
            key_info = self._extract_key_information(content)
            
            # 动态压缩
            compressed_content = self._compress_content_dynamically(
                content, semantic_main, key_info
            )
            
            # 计算信息密度
            density = self._calculate_information_density(content, compressed_content)
            
            return {
                'compressed_content': compressed_content,
                'semantic_main': semantic_main,
                'key_info': key_info,
                'compression_ratio': len(compressed_content) / len(content) if content else get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")),
                'information_density': density,
                'compression_type': 'dynamic'
            }
            
        except Exception as e:
            logger.error("动态上下文压缩失败: %s", e)
            return {
                'compressed_content': content,
                'compression_ratio': get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")),
                'compression_type': 'dynamic',
                'error': str(e)
            }
    
    def hybrid_context_compression(self, content: str) -> Dict[str, Any]:
        """混合上下文压缩"""
        try:
            # 动态压缩
            dynamic_result = self.dynamic_context_compression(content)
            
            # 静态压缩（基于规则）
            static_result = self._compress_content_statically(content)
            
            # 混合压缩
            hybrid_content = self._combine_original_and_summary(
                content, dynamic_result['compressed_content'], static_result
            )
            
            return {
                'compressed_content': hybrid_content,
                'dynamic_compression': dynamic_result,
                'static_compression': static_result,
                'compression_ratio': len(hybrid_content) / len(content) if content else get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")),
                'compression_type': 'hybrid'
            }
            
        except Exception as e:
            logger.error("混合上下文压缩失败: %s", e)
            return {
                'compressed_content': content,
                'compression_ratio': get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")),
                'compression_type': 'hybrid',
                'error': str(e)
            }
    
    def manage_context_memory(self, context_id: str, content: str, 
                            mode: str = 'dynamic') -> Dict[str, Any]:
        """管理上下文记忆"""
        try:
            # 分析内容
            analysis = self._analyze_content_for_memory(content)
            
            if mode == 'dynamic':
                return self._process_dynamic_memory(context_id, content, analysis)
            elif mode == 'static':
                return self._process_static_memory(context_id, content, analysis)
            elif mode == 'hybrid':
                return self._process_hybrid_memory(context_id, content, analysis)
            else:
                raise ValueError(f"不支持的记忆模式: {mode}")
                
        except Exception as e:
            logger.error("上下文记忆管理失败: %s", e)
            return {'error': str(e), 'content': content}
    
    def _extract_semantic_main(self, content: str) -> str:
        """提取语义主干"""
        try:
            # 简单的关键词提取
            words = re.findall(r'\b\w+\b', content.lower())
            word_freq = Counter(words)
            
            # 过滤停用词
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            filtered_words = {word: freq for word, freq in word_freq.items() 
                            if word not in stop_words and len(word) > 2}
            
            # 选择高频词作为语义主干
            top_words = sorted(filtered_words.items(), key=lambda x: x[1], reverse=True)[:5]
            return ' '.join([word for word, _ in top_words])
            
        except Exception as e:
            logger.warning("语义主干提取失败: %s", e)
            return content[:config.DEFAULT_LIMIT] + "..." if len(content) > config.DEFAULT_LIMIT else content
    
    def _extract_key_information(self, content: str) -> List[str]:
        """提取关键信息"""
        try:
            # 提取句子
            sentences = re.split(r'[.!?]+', content)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            # 简单的关键信息提取
            key_sentences = []
            for sentence in sentences:
                if len(sentence) > 20:  # 过滤太短的句子
                    # 检查是否包含重要词汇
                    important_words = ['重要', '关键', '主要', '核心', 'essential', 'important', 'key', 'main']
                    if any(word in sentence.lower() for word in important_words):
                        key_sentences.append(sentence)
            
            return key_sentences[:config.DEFAULT_MAX_RETRIES]  # 最多返回3个关键句子
            
        except Exception as e:
            logger.warning("关键信息提取失败: %s", e)
            return [content[:config.DEFAULT_TEXT_LIMIT] + "..." if len(content) > config.DEFAULT_TEXT_LIMIT else content]
    
    def _compress_content_dynamically(self, content: str, semantic_main: str, 
                                    key_info: List[str]) -> str:
        """动态压缩内容"""
        try:
            # 组合语义主干和关键信息
            compressed_parts = [semantic_main] + key_info
            compressed_content = ' '.join(compressed_parts)
            
            # 确保压缩比例在合理范围内
            target_ratio = self.context_compression_config['compression_ratio']
            target_length = int(len(content) * target_ratio)
            
            if len(compressed_content) > target_length:
                # 进一步压缩
                compressed_content = compressed_content[:target_length] + "..."
            
            return compressed_content
            
        except Exception as e:
            logger.warning("动态内容压缩失败: %s", e)
            return content[:500] + "..." if len(content) > config.DEFAULT_MEDIUM_TEXT_LIMIT else content
    
    def _compress_content_statically(self, content: str) -> str:
        """静态压缩内容（基于规则）"""
        try:
            # 提取第一句和最后一句
            sentences = re.split(r'[.!?]+', content)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if len(sentences) <= 2:
                return content
            
            # 取第一句、中间一句（如果有）、最后一句
            compressed = [sentences[0]]
            if len(sentences) > 2:
                mid_idx = len(sentences) // 2
                compressed.append(sentences[mid_idx])
            compressed.append(sentences[-1])
            
            return ' '.join(compressed)
            
        except Exception as e:
            logger.warning("静态内容压缩失败: %s", e)
            return content[:config.DEFAULT_TIMEOUT0] + "..." if len(content) > config.DEFAULT_TIMEOUT0 else content
    
    def _calculate_information_density(self, original: str, compressed: str) -> float:
        """计算信息密度"""
        try:
            if not original or not compressed:
                return get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))
            
            # 简单的信息密度计算
            original_words = len(re.findall(r'\b\w+\b', original))
            compressed_words = len(re.findall(r'\b\w+\b', compressed))
            
            if original_words == 0:
                return get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))
            
            return min(get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")), compressed_words / original_words)
            
        except Exception as e:
            logger.warning("信息密度计算失败: %s", e)
            return get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))
    
    def _combine_original_and_summary(self, original: str, summary: str, 
                                    static_summary: str) -> str:
        """结合原文和摘要"""
        try:
            # 计算混合比例
            dynamic_weight = self.context_compression_config['memory_modes']['hybrid']['dynamic_weight']
            static_weight = self.context_compression_config['memory_modes']['hybrid']['static_weight']
            
            # 组合内容
            combined = f"{summary} {static_summary}"
            
            # 确保不超过目标长度
            target_length = int(len(original) * self.context_compression_config['compression_ratio'])
            if len(combined) > target_length:
                combined = combined[:target_length] + "..."
            
            return combined
            
        except Exception as e:
            logger.warning("内容组合失败: %s", e)
            return summary
    
    def _analyze_content_for_memory(self, content: str) -> Dict[str, Any]:
        """分析内容用于记忆"""
        try:
            return {
                'length': len(content),
                'word_count': len(re.findall(r'\b\w+\b', content)),
                'sentence_count': len(re.split(r'[.!?]+', content)),
                'complexity': self._calculate_content_complexity(content),
                'timestamp': time.time()
            }
        except Exception as e:
            logger.warning("内容分析失败: %s", e)
            return {'length': len(content), 'timestamp': time.time()}
    
    def _calculate_content_complexity(self, content: str) -> float:
        """计算内容复杂度"""
        try:
            words = re.findall(r'\b\w+\b', content.lower())
            if not words:
                return get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))
            
            # 计算平均词长
            avg_word_length = sum(len(word) for word in words) / len(words)
            
            # 计算词汇多样性
            unique_words = len(set(words))
            diversity = unique_words / len(words) if words else 0
            
            # 综合复杂度
            complexity = (avg_word_length / 10.0 + diversity) / get_smart_config("DEFAULT_TWO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_two_value"))
            return min(get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")), complexity)
            
        except Exception as e:
            logger.warning("复杂度计算失败: %s", e)
            return get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))
    
    def _process_dynamic_memory(self, context_id: str, content: str, 
                              analysis: Dict[str, Any]) -> Dict[str, Any]:
        """处理动态记忆"""
        try:
            current_time = time.time()
            
            # 计算动态权重
            dynamic_weight = self.context_compression_config['memory_modes']['dynamic']['update_frequency']
            decay_factor = self.context_compression_config['memory_modes']['dynamic']['decay_factor']
            
            # 如果已存在，进行衰减更新
            existing = self.context_memory['dynamic_memory'].get(context_id, {})
            if context_id in self.context_memory['dynamic_memory']:
                time_diff = current_time - existing.get('last_update', current_time)
                decayed_weight = existing.get('weight', get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value"))) * (decay_factor ** (time_diff / 3config.DEFAULT_TIMEOUT_MINUTES0))
                new_weight = min(get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")), decayed_weight + dynamic_weight)
            else:
                new_weight = dynamic_weight
            
            # 动态压缩内容
            compressed_result = self.dynamic_context_compression(content)
            
            dynamic_memory = {
                'content': compressed_result['compressed_content'],
                'weight': new_weight,
                'last_update': current_time,
                'update_count': existing.get('update_count', 0) + 1,
                'analysis': analysis,
                'compression_info': compressed_result
            }
            
            self.context_memory['dynamic_memory'][context_id] = dynamic_memory
            return dynamic_memory
            
        except Exception as e:
            logger.warning("动态记忆处理失败: %s", e)
            return {'error': str(e), 'content': content}
    
    def _process_static_memory(self, context_id: str, content: str, 
                             analysis: Dict[str, Any]) -> Dict[str, Any]:
        """处理静态记忆"""
        try:
            current_time = time.time()
            
            # 静态记忆：持久化存储，权重较高
            persistence_threshold = self.context_compression_config['memory_modes']['static']['persistence_threshold']
            
            # 静态压缩内容
            compressed_result = self._compress_content_statically(content)
            
            static_memory = {
                'content': compressed_result,
                'weight': persistence_threshold,
                'last_update': current_time,
                'analysis': analysis,
                'memory_type': 'static'
            }
            
            self.context_memory['static_memory'][context_id] = static_memory
            return static_memory
            
        except Exception as e:
            logger.warning("静态记忆处理失败: %s", e)
            return {'error': str(e), 'content': content}
    
    def _process_hybrid_memory(self, context_id: str, content: str, 
                             analysis: Dict[str, Any]) -> Dict[str, Any]:
        """处理混合记忆"""
        try:
            # 处理动态和静态记忆
            dynamic_result = self._process_dynamic_memory(context_id, content, analysis)
            static_result = self._process_static_memory(context_id, content, analysis)
            
            # 混合记忆
            hybrid_memory = {
                'dynamic_memory': dynamic_result,
                'static_memory': static_result,
                'hybrid_content': self._combine_original_and_summary(
                    content, 
                    dynamic_result.get('content', ''),
                    static_result.get('content', '')
                ),
                'memory_type': 'hybrid',
                'timestamp': time.time()
            }
            
            self.context_memory['hybrid_memory'][context_id] = hybrid_memory
            return hybrid_memory
            
        except Exception as e:
            logger.warning("混合记忆处理失败: %s", e)
            return {'error': str(e), 'content': content}
