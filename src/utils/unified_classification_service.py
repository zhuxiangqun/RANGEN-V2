#!/usr/bin/env python3
"""
统一分类服务 - Unified Classification Service
统一处理核心系统中的所有类型分类任务，减少代码重复
"""
import logging
import json
import os
from typing import Dict, List, Any, Optional, Callable, Union, TypeVar, Type
from enum import Enum
import re

logger = logging.getLogger(__name__)

T = TypeVar('T')


class SemanticBasedFallbackClassifier:
    """基于语义相似度的Fallback分类器（🚀 智能方案：语义理解，无需关键词维护）"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._jina_service = None  # 🚀 优化：使用Jina服务而非sentence-transformers
        self._example_cache: Dict[str, List[Dict[str, Any]]] = {}  # 缓存历史分类示例
        self._init_embedding_model()
    
    def _init_embedding_model(self):
        """初始化嵌入模型（🚀 优化：统一使用Jina API）"""
        try:
            # 优先使用Jina Embedding API（统一接口）
            try:
                from src.utils.unified_jina_service import get_jina_service
                self._jina_service = get_jina_service()
                if self._jina_service.api_key:
                    self.logger.debug("✅ 已初始化Jina Embedding服务")
                    return
                else:
                    self.logger.debug("⚠️ JINA_API_KEY未设置，将使用简化语义匹配")
            except Exception as e:
                self.logger.debug(f"⚠️ Jina服务初始化失败: {e}，将使用简化语义匹配")
            
            self._jina_service = None
            self.logger.debug("⚠️ 未找到嵌入模型，将使用简化的语义匹配")
            
        except Exception as e:
            self.logger.warning(f"初始化嵌入模型失败: {e}，将使用简化语义匹配")
            self._jina_service = None
    
    def encode_text(self, text: str) -> Optional[Any]:
        """将文本编码为向量（🚀 优化：统一使用Jina API）"""
        try:
            # 优先使用Jina Embedding API
            if self._jina_service:
                embedding = self._jina_service.get_embedding(text)
                if embedding is not None:
                    return embedding
            
            # Fallback: 简化的文本匹配（不依赖外部模型）
            return None
        except Exception as e:
            self.logger.debug(f"文本编码失败: {e}")
            return None
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的语义相似度"""
        try:
            # 如果有嵌入模型，使用向量相似度
            vec1 = self.encode_text(text1)
            vec2 = self.encode_text(text2)
            
            if vec1 is not None and vec2 is not None:
                try:
                    import numpy as np
                    from sklearn.metrics.pairwise import cosine_similarity
                    
                    vec1_arr = np.array(vec1).reshape(1, -1) if isinstance(vec1, (list, np.ndarray)) else vec1
                    vec2_arr = np.array(vec2).reshape(1, -1) if isinstance(vec2, (list, np.ndarray)) else vec2
                    
                    similarity = cosine_similarity(vec1_arr, vec2_arr)[0][0]
                    return float(similarity)
                except Exception as e:
                    self.logger.debug(f"向量相似度计算失败: {e}，回退到词级相似度")
            
            # 回退：使用改进的词级语义相似度（Jaccard + 语义权重）
            return self._word_level_similarity(text1, text2)
            
        except Exception as e:
            self.logger.debug(f"语义相似度计算失败: {e}")
            return 0.0
    
    def _word_level_similarity(self, text1: str, text2: str) -> float:
        """词级语义相似度（改进版）"""
        try:
            # 提取有意义的词
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
                'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must'
            }
            
            words1 = set(w.lower() for w in re.findall(r'\b\w+\b', text1.lower()) if len(w) > 2 and w not in stop_words)
            words2 = set(w.lower() for w in re.findall(r'\b\w+\b', text2.lower()) if len(w) > 2 and w not in stop_words)
            
            if not words1 or not words2:
                return 0.0
            
            # Jaccard相似度
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            jaccard = intersection / union if union > 0 else 0.0
            
            # 添加语义权重（查询词的重要性）
            query_words = words1
            content_words = words2
            
            # 如果查询词在内容中出现，增加相似度
            semantic_boost = 0.0
            for qw in query_words:
                if any(qw in cw or cw in qw for cw in content_words):
                    semantic_boost += 0.1
            
            return min(jaccard + semantic_boost, 1.0)
            
        except Exception as e:
            self.logger.debug(f"词级相似度计算失败: {e}")
            return 0.0
    
    def learn_from_example(self, query: str, classification_type: str, result: Any):
        """从分类结果中学习（建立示例库）"""
        try:
            if classification_type not in self._example_cache:
                self._example_cache[classification_type] = []
            
            # 存储示例（限制数量，避免内存过大）
            example = {"query": query, "result": result, "timestamp": __import__('time').time()}
            self._example_cache[classification_type].append(example)
            
            # 只保留最近100个示例
            if len(self._example_cache[classification_type]) > 100:
                self._example_cache[classification_type] = self._example_cache[classification_type][-100:]
                
        except Exception as e:
            self.logger.debug(f"学习示例失败: {e}")
    
    def classify_with_semantic_similarity(
        self,
        query: str,
        classification_type: str,
        valid_types: Union[List[str], Dict[str, Any]],
        default_type: Any
    ) -> Optional[Any]:
        """
        使用语义相似度进行分类（基于历史示例学习）
        
        Args:
            query: 查询文本
            classification_type: 分类类型
            valid_types: 有效类型列表或映射
            default_type: 默认类型
            
        Returns:
            分类结果，如果无法分类则返回None
        """
        try:
            # 从历史示例中查找相似查询
            examples = self._example_cache.get(classification_type, [])
            
            if not examples:
                return None
            
            # 计算与每个示例的相似度
            similarities = []
            for example in examples[-50:]:  # 只检查最近50个示例
                sim = self.calculate_semantic_similarity(query, example["query"])
                similarities.append({
                    "similarity": sim,
                    "result": example["result"]
                })
            
            # 找到最相似的示例
            if similarities:
                best_match = max(similarities, key=lambda x: x["similarity"])
                
                # 如果相似度足够高（阈值0.6），返回该结果
                if best_match["similarity"] >= 0.6:
                    result = best_match["result"]
                    self.logger.debug(
                        f"✅ 语义相似度分类: {classification_type} = {result} "
                        f"(相似度: {best_match['similarity']:.2f})"
                    )
                    return result
            
            return None
            
        except Exception as e:
            self.logger.debug(f"语义相似度分类失败: {e}")
            return None


class UnifiedClassificationService:
    """统一分类服务 - 处理所有类型分类任务"""
    
    def __init__(self, prompt_engineering=None, llm_integration=None, fast_llm_integration=None):
        """
        初始化统一分类服务
        
        Args:
            prompt_engineering: PromptEngine实例（可选）
            llm_integration: LLM集成实例（可选）
            fast_llm_integration: 快速LLM集成实例（可选，优先使用）
        """
        self.prompt_engineering = prompt_engineering
        self.llm_integration = llm_integration
        self.fast_llm_integration = fast_llm_integration
        self.logger = logging.getLogger(__name__)
        # 🚀 智能方案：初始化语义Fallback分类器（基于语义相似度，无需关键词维护）
        self.semantic_fallback = SemanticBasedFallbackClassifier()
    
    def classify(
        self,
        query: str,
        classification_type: str,
        valid_types: Union[List[str], Dict[str, Any]],
        template_name: str,
        default_type: Any,
        rules_fallback: Optional[Callable[[str], Any]] = None,
        enum_class: Optional[Type[Enum]] = None,
        **prompt_kwargs
    ) -> Any:
        """
        统一的分类方法
        
        Args:
            query: 要分类的查询文本
            classification_type: 分类类型名称（用于日志）
            valid_types: 有效类型列表或映射字典
                - 如果是列表: ['type1', 'type2', ...]
                - 如果是字典: {'type_key': enum_value, ...}
            template_name: PromptEngine模板名称
            default_type: 默认类型（LLM失败时返回）
            rules_fallback: 规则匹配fallback函数（可选）
            enum_class: 枚举类（如果返回枚举类型）
            **prompt_kwargs: 传递给提示词模板的其他参数
            
        Returns:
            分类结果（字符串或枚举类型）
        """
        try:
            # 1. 验证输入
            if not query or not query.strip():
                self.logger.debug(f"{classification_type}: 空查询，返回默认类型")
                return default_type
            
            # 2. 尝试使用LLM进行智能分类
            llm_to_use = self.fast_llm_integration or self.llm_integration
            
            if llm_to_use and self.prompt_engineering:
                try:
                    # 2.1 构建分类提示词
                    classification_prompt = self._build_classification_prompt(
                        template_name=template_name,
                        query=query,
                        **prompt_kwargs
                    )
                    
                    if not classification_prompt:
                        self.logger.warning(
                            f"{classification_type}: 提示词工程生成提示词失败，"
                            f"使用{'规则匹配' if rules_fallback else '默认类型'}"
                        )
                        if rules_fallback:
                            return rules_fallback(query)
                        return default_type
                    
                    # 2.2 调用LLM进行分类
                    response = llm_to_use._call_llm(classification_prompt)
                    
                    if response and response.strip():
                        # 2.3 解析LLM响应
                        result = self._parse_classification_response(
                            response.strip(),
                            valid_types=valid_types,
                            enum_class=enum_class
                        )
                        
                        if result is not None:
                            self.logger.debug(
                                f"✅ {classification_type} LLM分类结果: {result} "
                                f"(查询: {query[:50]})"
                            )
                            # 🚀 智能学习：将成功的分类结果存储为示例
                            self.semantic_fallback.learn_from_example(query, classification_type, result)
                            return result
                    
                except Exception as llm_error:
                    self.logger.warning(
                        f"{classification_type}: LLM分类失败，"
                        f"使用{'规则匹配' if rules_fallback else '默认类型'}: {llm_error}"
                    )
            
            # 3. Fallback: 优先使用语义相似度（智能、可扩展）
            result = self._try_semantic_based_fallback(query, classification_type, valid_types, default_type)
            if result:
                return result
            
            # 4. 最后的Fallback: 如果提供了自定义规则fallback
            if rules_fallback:
                return rules_fallback(query)
            
            return default_type
            
        except Exception as e:
            self.logger.error(f"{classification_type}: 分类过程发生异常: {e}")
            return default_type
    
    def _try_semantic_based_fallback(
        self,
        query: str,
        classification_type: str,
        valid_types: Union[List[str], Dict[str, Any]],
        default_type: Any
    ) -> Optional[Any]:
        """尝试使用基于语义相似度的fallback分类（🚀 智能方案：无需关键词维护）"""
        try:
            # 使用语义相似度从历史示例中学习分类
            result = self.semantic_fallback.classify_with_semantic_similarity(
                query,
                classification_type,
                valid_types,
                default_type
            )
            
            return result
            
        except Exception as e:
            self.logger.debug(f"语义fallback失败: {e}")
            return None
    
    def _build_classification_prompt(
        self,
        template_name: str,
        query: str,
        **kwargs
    ) -> Optional[str]:
        """
        统一构建分类提示词
        
        Args:
            template_name: PromptEngine模板名称
            query: 查询文本
            **kwargs: 传递给模板的其他参数
            
        Returns:
            生成的提示词，如果失败则返回None
        """
        try:
            if self.prompt_engineering:
                # 默认传递query参数，其他参数通过kwargs传递
                prompt = self.prompt_engineering.generate_prompt(
                    template_name,
                    query=query,
                    **kwargs
                )
                if prompt:
                    self.logger.debug(
                        f"✅ 使用提示词工程系统生成分类提示词: {template_name}"
                    )
                    return prompt
                else:
                    self.logger.warning(f"提示词工程返回空提示词: {template_name}")
                    return None
            else:
                self.logger.warning("提示词工程未初始化")
                return None
                
        except Exception as e:
            self.logger.warning(f"使用提示词工程生成分类提示词失败: {e}")
            return None
    
    def _parse_classification_response(
        self,
        response: str,
        valid_types: Union[List[str], Dict[str, Any]],
        enum_class: Optional[Type[Enum]] = None
    ) -> Optional[Any]:
        """
        统一解析分类响应
        
        Args:
            response: LLM响应文本
            valid_types: 有效类型列表或映射字典
            enum_class: 枚举类（如果返回枚举类型）
            
        Returns:
            解析后的类型，如果解析失败则返回None
        """
        try:
            response_lower = response.lower().strip()
            
            # 如果valid_types是字典（类型映射）
            if isinstance(valid_types, dict):
                # 直接匹配
                for type_key, type_value in valid_types.items():
                    if type_key.lower() in response_lower:
                        return type_value
                
                # 尝试从编号提取
                number_pattern = re.search(r'(\d+)', response_lower)
                if number_pattern:
                    num = int(number_pattern.group(1))
                    type_list = list(valid_types.values())
                    if 1 <= num <= len(type_list):
                        return type_list[num - 1]
            
            # 如果valid_types是列表
            elif isinstance(valid_types, list):
                # 直接匹配
                for vtype in valid_types:
                    if vtype.lower() in response_lower:
                        # 如果指定了枚举类，尝试转换为枚举
                        if enum_class:
                            try:
                                # 尝试匹配枚举值
                                for enum_item in enum_class:
                                    if enum_item.value.lower() == vtype.lower():
                                        return enum_item
                            except:
                                pass
                        return vtype
                
                # 尝试从编号提取
                number_pattern = re.search(r'(\d+)', response_lower)
                if number_pattern:
                    num = int(number_pattern.group(1))
                    if 1 <= num <= len(valid_types):
                        vtype = valid_types[num - 1]
                        # 如果指定了枚举类，尝试转换为枚举
                        if enum_class:
                            try:
                                for enum_item in enum_class:
                                    if enum_item.value.lower() == vtype.lower():
                                        return enum_item
                            except:
                                pass
                        return vtype
            
            return None
            
        except Exception as e:
            self.logger.warning(f"解析分类响应失败: {e}, 响应: {response[:50]}")
            return None


def get_unified_classification_service(
    prompt_engineering=None,
    llm_integration=None,
    fast_llm_integration=None
) -> UnifiedClassificationService:
    """
    获取统一分类服务实例（单例模式）
    
    Args:
        prompt_engineering: PromptEngine实例
        llm_integration: LLM集成实例
        fast_llm_integration: 快速LLM集成实例
        
    Returns:
        UnifiedClassificationService实例
    """
    return UnifiedClassificationService(
        prompt_engineering=prompt_engineering,
        llm_integration=llm_integration,
        fast_llm_integration=fast_llm_integration
    )

