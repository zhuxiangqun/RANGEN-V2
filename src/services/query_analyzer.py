"""
查询分析器模块
负责查询的预处理、分析和分类
"""

from typing import Dict, Any, List, Optional
import logging
import re

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """查询分析器 - 负责查询的预处理、分析和分类"""
    
    def __init__(self, unified_config_center=None, fast_llm_integration=None):
        """初始化查询分析器
        
        Args:
            unified_config_center: 统一配置中心（可选）
            fast_llm_integration: 快速LLM集成（可选）
        """
        self.unified_config_center = unified_config_center
        self.fast_llm_integration = fast_llm_integration
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """查询分析 - 真正的分析逻辑"""
        try:
            analysis = {
                "original_query": query,
                "query_type": self.classify_query_type(query),
                "keywords": self.extract_keywords(query),
                "entities": self.extract_entities(query),
                "intent": self.analyze_intent(query),
                "complexity": self.assess_complexity(query),
                "domain": self.identify_domain(query),
                "confidence": 0.8
            }
            return analysis
        except Exception as e:
            logger.error(f"查询分析失败: {e}")
            return {
                "original_query": query,
                "query_type": "unknown",
                "keywords": [],
                "entities": [],
                "intent": "unknown",
                "complexity": "medium",
                "domain": "general",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def classify_query_type(self, query: str) -> str:
        """分类查询类型 - 🚀 优化：优先使用规则匹配，LLM作为回退"""
        try:
            # 🚀 性能优化：优先使用快速规则匹配
            # 只有当规则无法确定时，才调用LLM
            
            query_lower = query.lower()
            
            # 规则1: 事实类查询 (Factual)
            if any(w in query_lower for w in ['what is', 'who is', 'where is', 'when was', 'fact about']):
                return 'factual'
                
            # 规则2: 数值类查询 (Numerical)
            if any(w in query_lower for w in ['how many', 'how much', 'number of', 'count', 'amount']):
                return 'numerical'
                
            # 规则3: 时间类查询 (Temporal)
            if any(w in query_lower for w in ['when', 'what time', 'what year', 'date of', 'timeline']):
                return 'temporal'
                
            # 规则4: 因果类查询 (Causal)
            if any(w in query_lower for w in ['why', 'reason for', 'cause of', 'because']):
                return 'causal'
                
            # 规则5: 比较类查询 (Comparative)
            if any(w in query_lower for w in ['compare', 'difference between', 'vs', 'versus', 'better than']):
                return 'comparative'
                
            # 规则6: 过程类查询 (Procedural)
            if any(w in query_lower for w in ['how to', 'steps to', 'procedure for', 'guide']):
                return 'procedural'
            
            # 规则7: 多跳查询 (Multi-hop) - 复杂关系
            if any(w in query_lower for w in ["'s mother", "mother of", "father of", "wife of", "husband of"]):
                return 'multi_hop'

            # 🚀 如果规则匹配失败，再尝试使用统一分类服务（LLM判断）
            # 设置较短的超时时间，避免长时间阻塞
            from src.utils.unified_classification_service import get_unified_classification_service
            
            try:
                classification_service = get_unified_classification_service()
                
                # 定义有效的查询类型
                valid_types = [
                    'factual', 'numerical', 'temporal', 'causal', 'comparative',
                    'analytical', 'procedural', 'spatial', 'multi_hop', 'general', 'question'
                ]
                
                # 使用统一分类服务进行分类
                # 🚀 优化：使用缓存，减少重复调用
                query_type = classification_service.classify(
                    query=query,
                    classification_type="query_type",
                    valid_types=valid_types,
                    template_name="query_type_classification",
                    default_type="general",
                    rules_fallback=self._classify_query_type_fallback,
                    timeout=2.0  # 🚀 限制超时时间为2秒
                )
                
                return query_type
                
            except Exception as e:
                logger.debug(f"⚠️ 使用统一分类服务失败或超时: {e}，使用fallback")
                return self._classify_query_type_fallback(query)
                
        except Exception as e:
            logger.warning(f"查询类型分类失败: {e}")
            return "general"
    
    def _classify_query_type_fallback(self, query: str) -> str:
        """Fallback查询类型分类（仅在统一服务不可用时使用）"""
        # 简单的规则判断
        if "?" in query or "？" in query:
            return "question"
        else:
            return "general"
    
    def extract_keywords(self, query: str) -> List[str]:
        """提取关键词 - 简化版"""
        # 🚀 优化：不硬编码停用词，让系统自然理解
        words = re.findall(r'\b\w+\b', query.lower())
        # 只保留长度>1的词
        return [word for word in words if len(word) > 1]
    
    def extract_entities(self, query: str) -> List[str]:
        """提取实体"""
        try:
            # 简单的实体识别
            entities = []
            # 识别可能的实体（这里使用简单的模式匹配）
            patterns = [
                r'\b[A-Z][a-z]+\b',  # 大写开头的词
                r'\b\d+\b',  # 数字
                r'"[^"]*"',  # 引号内的内容
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, query)
                entities.extend(matches)
            
            return list(set(entities))  # 去重
        except Exception as e:
            logger.error(f"实体提取失败: {e}")
            return []
    
    def analyze_intent(self, query: str) -> str:
        """分析查询意图 - 通用化"""
        # 🚀 优化：不做硬编码意图判断
        return "information"
    
    def assess_complexity(self, query: str) -> str:
        """评估查询复杂度 - 🚀 重构：使用统一复杂度服务（LLM判断）"""
        try:
            from src.utils.unified_complexity_model_service import get_unified_complexity_model_service
            complexity_service = get_unified_complexity_model_service()
            complexity_result = complexity_service.assess_complexity(
                query=query,
                query_type=None,
                evidence_count=0,
                use_cache=True
            )
            return complexity_result.level.value  # 'simple', 'medium', 'complex'
        except Exception as e:
            logger.warning(f"⚠️ 使用统一复杂度服务失败: {e}，使用fallback")
            # Fallback: 简单的规则判断
            try:
                word_count = len(query.split())
                if word_count <= 5:
                    return "simple"
                elif word_count <= 15:
                    return "medium"
                else:
                    return "complex"
            except Exception as e2:
                logger.error(f"复杂度评估失败: {e2}")
                return "medium"
    
    def identify_domain(self, query: str) -> str:
        """识别查询领域 - 通用化"""
        # 🚀 优化：不做硬编码领域判断，返回通用域
        # 让系统根据查询内容自然识别
        return "general"
    
    def preprocess_query(self, query: str) -> str:
        """查询预处理 - 真正的预处理逻辑"""
        try:
            if not query or not query.strip():
                return ""
            
            # 1. 清理查询
            cleaned_query = query.strip()
            
            # 2. 标准化格式
            normalized_query = self.normalize_query_format(cleaned_query)
            
            # 3. 扩展查询
            expanded_query = self.expand_query(normalized_query)
            
            # 4. 优化查询结构
            # 简单的查询优化：移除重复词
            words = expanded_query.split()
            optimized_query = ' '.join(sorted(set(words), key=words.index))
            
            return optimized_query
            
        except Exception as e:
            logger.error(f"查询预处理失败: {e}")
            return query
    
    def normalize_query_format(self, query: str) -> str:
        """标准化查询格式"""
        try:
            # 移除多余空格
            normalized = re.sub(r'\s+', ' ', query)
            
            # 统一标点符号
            normalized = normalized.replace('？', '?').replace('！', '!')
            
            # 转换为小写（保留中文）
            normalized = normalized.lower()
            
            return normalized
        except Exception as e:
            logger.error(f"查询格式标准化失败: {e}")
            return query
    
    def expand_query(self, query: str) -> str:
        """扩展查询 - 通用化：不硬编码同义词"""
        # 🚀 优化：不做硬编码同义词扩展
        # 让检索系统自然匹配相关内容，而不是预设关键词
        return query
    
    def expand_query_with_llm(self, query: str, query_type: str) -> Optional[List[str]]:
        """🚀 修复：使用LLM智能扩展查询，生成多个查询变体"""
        try:
            # 如果fast_llm_integration不可用，返回None
            if not self.fast_llm_integration:
                return None
            
            prompt = f"""Generate 2-3 query variations for the following search query. Each variation should:
1. Use different wording but maintain the same intent
2. Include relevant synonyms or related terms
3. Be suitable for knowledge base search

**Original Query**: {query}
**Query Type**: {query_type}

**Return ONLY a JSON array of query strings, no explanations:**
["query1", "query2", "query3"]

Query variations:"""
            
            response = self.fast_llm_integration._call_llm(prompt)
            if response:
                response_str = str(response) if response else ""
                if response_str:
                    # 尝试解析JSON响应
                    import json
                    # 提取JSON数组
                    json_match = re.search(r'\[.*?\]', response_str, re.DOTALL)
                    if json_match:
                        try:
                            queries = json.loads(json_match.group())
                            if isinstance(queries, list) and len(queries) > 0:
                                # 确保包含原始查询
                                if query not in queries:
                                    queries.insert(0, query)
                                return queries
                        except json.JSONDecodeError:
                            pass
                    # 如果JSON解析失败，尝试按行分割
                    lines = [line.strip() for line in response_str.split('\n') if line.strip()]
                    if len(lines) > 1:
                        return [query] + lines[:3]  # 包含原始查询和最多3个变体
        except Exception as e:
            logger.debug(f"LLM查询扩展失败: {e}")
        
        # Fallback: 返回原始查询
        return [query]
    
    def normalize_query_for_retrieval(self, query: str) -> str:
        """🚀 源头解决：标准化查询用于检索（移除问号前的句号等格式问题）
        
        🚀 改进：保留查询中的关键信息（如"Who was"），避免过度简化
        """
        try:
            if not query:
                return query
            
            normalized = query.strip()
            
            # 🚀 关键修复：移除问号前的句号（如 "United States.?" -> "United States?"）
            # 这会影响embedding的生成，导致检索失败
            if '.' in normalized and '?' in normalized:
                question_mark_pos = normalized.find('?')
                if question_mark_pos != -1:
                    before_question = normalized[:question_mark_pos]
                    if before_question.endswith('.'):
                        # 移除问号前的句号
                        normalized = before_question.rstrip('.') + '?' + normalized[question_mark_pos + 1:]
                        logger.debug(f"🔍 [查询标准化] 移除问号前的句号: {query[:80]}... -> {normalized[:80]}...")
            
            # 🚀 改进：保留查询中的关键信息，避免过度简化
            # 对于包含"Who was"、"What is"等疑问词的查询，保留这些信息
            # 这些信息有助于理解查询意图，提高检索准确性
            # 不进行过度简化，只做基本的格式清理
            
            # 统一中文和英文标点符号
            normalized = normalized.replace('？', '?').replace('！', '!')
            
            # 移除多余空格（但保留单词之间的单个空格）
            normalized = re.sub(r'\s+', ' ', normalized).strip()
            
            return normalized
            
        except Exception as e:
            logger.error(f"查询检索标准化失败: {e}")
            return query
    
    def validate_query_input(self, query: str, max_query_length: int = 2000) -> bool:
        """验证查询输入"""
        try:
            if not query or not query.strip():
                return False
            
            if len(query) > max_query_length:
                return False
            
            # 检查是否包含有效字符
            if not re.search(r'[a-zA-Z\u4e00-\u9fff]', query):
                return False
            
            return True
        except Exception:
            return False
    
    def assess_query_complexity_score(self, query: str) -> float:
        """评估查询复杂度（返回0-1的分数）- 🚀 重构：使用统一复杂度服务（LLM判断）"""
        try:
            from src.utils.unified_complexity_model_service import get_unified_complexity_model_service
            complexity_service = get_unified_complexity_model_service()
            complexity_result = complexity_service.assess_complexity(
                query=query,
                query_type=None,
                evidence_count=0,
                use_cache=True
            )
            # 将复杂度评分（0-10）转换为0-1分数
            return complexity_result.score / 10.0
        except Exception as e:
            logger.warning(f"⚠️ 使用统一复杂度服务失败: {e}，使用fallback")
            # Fallback: 简单的规则判断
            try:
                # 基于多个因素评估复杂度
                factors = {
                    'length': min(len(query.split()) / 20, 1.0),
                    'special_chars': min(len(re.findall(r'[!@#$%^&*()]', query)) / 5, 1.0),
                    'numbers': min(len(re.findall(r'\d', query)) / 10, 1.0),
                    'questions': 1.0 if '?' in query else 0.0
                }
                
                # 加权平均
                complexity = sum(factors.values()) / len(factors)
                return min(complexity, 1.0)
            except Exception as e2:
                logger.error(f"复杂度评估失败: {e2}")
                return 0.5

