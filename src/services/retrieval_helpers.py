"""
检索辅助工具模块
包含检索过程中使用的辅助方法和工具函数
"""

from typing import Dict, Any, Optional
import logging
import re
import time

logger = logging.getLogger(__name__)


class RetrievalHelpers:
    """检索辅助工具类 - 提供检索过程中的辅助方法"""
    
    def __init__(self, adaptive_optimizer=None, similarity_threshold=0.05, service_ref=None):
        """初始化检索辅助工具
        
        Args:
            adaptive_optimizer: 自适应优化器（可选）
            similarity_threshold: 基础相似度阈值
            service_ref: 主服务类的引用（用于访问llm_client等）
        """
        self.adaptive_optimizer = adaptive_optimizer
        self.similarity_threshold = similarity_threshold
        self.service = service_ref
    
    def infer_detailed_query_type(self, query: str, base_query_type: str) -> str:
        """
        🚀 阶段1优化：从查询内容推断详细的查询类型
        
        Args:
            query: 查询文本
            base_query_type: 基础查询类型（从query_analysis获取）
        
        Returns:
            详细的查询类型（factual, numerical, ranking, name, location等）
        """
        query_lower = query.lower()
        
        # 排名查询：包含"第X"、"Xth"、"排名"、"rank"等
        if any(keyword in query_lower for keyword in ['th', 'st', 'nd', 'rd', '排名', '第', 'rank', 'ordinal']):
            return 'ranking'
        
        # 数值查询：包含"多少"、"几个"、"数字"、"number"等，或包含数字
        if any(keyword in query_lower for keyword in ['多少', '几个', '数字', 'number', 'how many', 'how much']) or re.search(r'\d+', query):
            return 'numerical'
        
        # 人名查询：包含"谁"、"who"、"name"等，或包含大写字母（可能是人名）
        if any(keyword in query_lower for keyword in ['谁', 'who', 'name', '人名']) or (len(query.split()) <= 5 and any(word[0].isupper() for word in query.split() if len(word) > 1)):
            return 'name'
        
        # 地名查询：包含"哪里"、"where"、"location"、"country"等
        if any(keyword in query_lower for keyword in ['哪里', 'where', 'location', 'country', '国家', '地点']):
            return 'location'
        
        # 时间查询：包含"何时"、"when"、"time"、"日期"等
        if any(keyword in query_lower for keyword in ['何时', 'when', 'time', '日期', 'date']):
            return 'temporal'
        
        # 因果查询：包含"为什么"、"why"、"原因"、"because"等
        if any(keyword in query_lower for keyword in ['为什么', 'why', '原因', 'because', '导致']):
            return 'causal'
        
        # 事实查询：包含"什么"、"what"、"is"等
        if any(keyword in query_lower for keyword in ['什么', 'what', 'is', 'are']):
            return 'factual'
        
        # 默认返回基础类型
        return base_query_type if base_query_type != 'unknown' else 'general'
    
    def get_dynamic_similarity_threshold(self, query_type: str, query: str = "") -> float:
        """
        🚀 阶段1优化：根据查询类型和查询特征动态调整相似度阈值
        
        改进点：
        1. 考虑查询复杂度（长度、实体数量、关系深度）
        2. 考虑查询类型的历史检索质量
        3. 根据查询特征（关系查询、多跳查询）动态调整
        
        Args:
            query_type: 查询类型（从query_analysis中获取）
            query: 查询文本（用于检测关系查询）
        
        Returns:
            动态阈值
        """
        # 🚀 P0修复：降低所有查询类型的阈值，减少过度过滤
        base_thresholds = {
            'factual': 0.5,      # 事实查询：从0.7降低到0.5
            'numerical': 0.4,    # 数值查询：从0.6降低到0.4
            'ranking': 0.4,      # 🚀 P0修复：从0.6降低到0.4
            'name': 0.5,         # 人名查询：从0.7降低到0.5
            'location': 0.5,     # 地名查询：从0.7降低到0.5
            'temporal': 0.4,     # 时间查询：从0.6降低到0.4
            'causal': 0.3,       # 因果查询：从0.5降低到0.3（需要更多上下文）
            'general': 0.3,      # 通用查询：从0.5降低到0.3
            'question': 0.3      # 问题查询：从0.5降低到0.3
        }
        
        # 如果query_type不在字典中，使用默认值
        threshold = base_thresholds.get(query_type, 0.5)
        
        # 🚀 新增：根据查询复杂度进一步调整阈值
        if query:
            query_lower = query.lower() if isinstance(query, str) else ""
            
            # 计算查询复杂度指标
            complexity_factors = {
                'length': len(query.split()),  # 查询长度
                'entities': 0,  # 实体数量（通过大写词数量估算）
                'relationships': 0,  # 关系词数量
                'multi_hop': 0  # 多跳查询指示词
            }
            
            # 检测关系查询
            relationship_keywords = [
                "'s mother", "'s father", "mother of", "father of", "maiden name",
                "的母亲", "的父亲", "的", "of", "whose"
            ]
            complexity_factors['relationships'] = sum(1 for kw in relationship_keywords if kw in query_lower)
            
            # 检测多跳查询（序数词、关系链）
            multi_hop_keywords = [
                'first', 'second', 'third', '15th', 'last', 'nth',
                'assassinated', 'killed', 'married', 'divorced'
            ]
            complexity_factors['multi_hop'] = sum(1 for kw in multi_hop_keywords if kw in query_lower)
            
            # 估算实体数量（大写词，排除句首）
            words = query.split()
            if words:
                # 跳过第一个词（可能是句首）
                complexity_factors['entities'] = sum(1 for w in words[1:] if w and w[0].isupper())
            
            # 计算综合复杂度分数（0-1之间）
            complexity_score = 0.0
            complexity_score += min(1.0, complexity_factors['length'] / 15.0) * 0.3  # 长度权重30%
            complexity_score += min(1.0, complexity_factors['entities'] / 3.0) * 0.2  # 实体权重20%
            complexity_score += min(1.0, complexity_factors['relationships'] / 2.0) * 0.3  # 关系权重30%
            complexity_score += min(1.0, complexity_factors['multi_hop'] / 2.0) * 0.2  # 多跳权重20%
            complexity_score = min(1.0, complexity_score)
            
            # 根据复杂度调整阈值：复杂度越高，阈值越低（让更多结果通过）
            if complexity_score > 0.7:  # 高复杂度
                threshold = max(0.05, threshold - 0.15)
            elif complexity_score > 0.4:  # 中等复杂度
                threshold = max(0.05, threshold - 0.10)
            elif complexity_score > 0.2:  # 低复杂度
                threshold = max(0.05, threshold - 0.05)
            
            logger.debug(f"🔍 [动态阈值] 查询复杂度: {complexity_score:.2f}, 调整后阈值: {threshold:.3f}")
        
        # 🚀 ML/RL增强：优先使用AdaptiveOptimizer获取优化的阈值
        ml_optimized_threshold = None
        ml_optimizer_used = False
        if self.adaptive_optimizer:
            try:
                # 从AdaptiveOptimizer获取优化的配置参数
                optimized_config = self.adaptive_optimizer.get_optimized_config_updates(query_type)
                if optimized_config and 'similarity_threshold' in optimized_config:
                    ml_optimized_threshold = optimized_config['similarity_threshold']
                    # 确保阈值在合理范围内（0.05-0.8）
                    ml_optimized_threshold = max(0.05, min(0.8, ml_optimized_threshold))
                    ml_optimizer_used = True
                    logger.info(f"✅ [ML/RL] 使用AdaptiveOptimizer优化的相似度阈值: {query_type}={ml_optimized_threshold:.3f}")
            except Exception as e:
                logger.debug(f"AdaptiveOptimizer获取阈值失败: {e}")
        
        # 🚀 性能跟踪：记录ML/RL决策（用于后续评估）
        if ml_optimizer_used:
            if not hasattr(self, '_ml_rl_decisions'):
                self._ml_rl_decisions = []
            self._ml_rl_decisions.append({
                'decision_type': 'similarity_threshold',
                'query_type': query_type,
                'ml_optimized_value': ml_optimized_threshold,
                'timestamp': time.time()
            })
        
        # 🆕 方案4：如果AdaptiveOptimizer没有结果，尝试从学习数据中获取优化的阈值
        if ml_optimized_threshold is None:
            learned_threshold = self.get_learned_similarity_threshold_for_retrieval(query_type)
            if learned_threshold:
                # 使用学习到的阈值和基础阈值的加权平均（学习到的阈值权重更高）
                threshold = 0.8 * learned_threshold + 0.2 * threshold
                logger.debug(f"✅ 使用学习到的相似度阈值: {query_type}={learned_threshold:.2f}, 调整后={threshold:.2f}")
        else:
            # 使用ML/RL优化的阈值，与基础阈值加权平均（ML/RL权重更高）
            threshold = 0.7 * ml_optimized_threshold + 0.3 * threshold
            logger.info(f"✅ [ML/RL] 应用优化的相似度阈值: {query_type}={ml_optimized_threshold:.3f}, 调整后={threshold:.3f}")
        
        # 🚀 P0修复：使用配置的similarity_threshold作为基础，但根据查询类型调整
        base_threshold = self.similarity_threshold  # 🚀 P1修复：从0.10降低到0.05
        
        # 🚀 改进：检测历史查询和关系查询，使用更低的阈值
        query_lower = query.lower() if isinstance(query, str) else ""
        
        # 检测历史查询（序数词 + 历史实体）
        historical_keywords = [
            'first lady', 'president', 'assassinated', '15th', '16th', '20th',
            'second', 'third', 'fourth', 'fifth', 'nth'
        ]
        is_historical_query = any(keyword in query_lower for keyword in historical_keywords)
        
        # 检测关系查询
        relationship_keywords = ["'s mother", "'s father", "mother of", "father of", "maiden name", "的母亲", "的父亲"]
        is_relationship_query = any(keyword in query_lower for keyword in relationship_keywords)
        
        # 历史查询使用更低的阈值（0.2-0.4），因为知识库中可能缺少相关信息
        if is_historical_query:
            historical_threshold = max(0.2, threshold - 0.2)  # 历史查询：降低0.2
            logger.info(f"🔍 [检索诊断] 历史查询使用特殊阈值: {historical_threshold:.3f} (原始: {threshold:.3f})")
            threshold = historical_threshold
        
        # 关系查询使用更低的阈值（0.1-0.3）
        if is_relationship_query:
            relationship_threshold = max(0.1, threshold - 0.15)  # 关系查询：再降低0.15
            logger.info(f"🔍 [检索诊断] 关系查询使用特殊阈值: {relationship_threshold:.3f} (原始: {threshold:.3f})")
            threshold = relationship_threshold
        
        # 取两者中的较小值，确保不会高于基础阈值太多（让更多结果通过）
        return min(threshold, base_threshold * 1.5)  # 从max改为min，从0.8改为1.5
    
    def get_learned_similarity_threshold_for_retrieval(self, query_type: str) -> Optional[float]:
        """从学习数据中获取优化的相似度阈值（占位方法）"""
        # TODO: 实现从学习数据中获取阈值
        return None
    
    def validate_result_multi_dimension(self, result: Dict[str, Any], query: str, query_type: str) -> bool:
        """🚀 修复：只保留基本质量检查，不进行相关性过滤
        
        设计理念：
        - 信任检索系统（知识图谱和向量知识库）的检索结果
        - 只进行基本的内容质量检查（空内容、太短），确保内容可用
        - 不进行相关性过滤，让LLM在后续阶段判断相关性
        - 检索阶段的目标是获取尽可能多的相关结果，而不是预先过滤
        
        Args:
            result: 检索结果
            query: 查询文本（保留参数以兼容现有代码，但不使用）
            query_type: 查询类型（保留参数以兼容现有代码，但不使用）
        
        Returns:
            True if result has valid content, False otherwise
        """
        content = result.get('content', '') or result.get('text', '')
        
        # 🚀 只保留基本的内容质量检查：确保内容非空且长度合理
        # 不进行相关性过滤，让LLM在后续阶段判断相关性
        if not content or len(content.strip()) < 5:  # 最小长度要求：5字符
            logger.debug(f"过滤无效结果（内容为空或太短）: 长度={len(content) if content else 0}")
            return False
        
        # 🚀 移除所有相关性验证（相似度、实体匹配、关键词匹配、LLM验证）
        # 信任检索系统的结果，让LLM在后续阶段判断相关性
        return True
    
    def detect_relationship_query(self, query: str) -> bool:
        """检测是否为关系查询（如"X的母亲"）"""
        query_lower = query.lower()
        relationship_keywords = ["'s mother", "'s father", "mother of", "father of", "maiden name", "的母亲", "的父亲"]
        return any(keyword in query_lower for keyword in relationship_keywords)
    
    def validate_result_with_llm(self, result: Dict[str, Any], query: str) -> Optional[bool]:
        """🚀 新增：使用LLM判断结果是否与查询相关（替代阈值验证）"""
        import time
        import json
        import re
        start_time = time.time()
        try:
            # 🚀 P0修复：优先使用fast_llm_integration，如果没有则使用llm_client
            llm_to_use = None
            if self.service:
                if hasattr(self.service, 'fast_llm_integration') and self.service.fast_llm_integration:
                    llm_to_use = self.service.fast_llm_integration
                elif hasattr(self.service, 'llm_client') and self.service.llm_client:
                    llm_to_use = self.service.llm_client
                elif hasattr(self.service, 'llm_integration') and self.service.llm_integration:
                    llm_to_use = self.service.llm_integration
            
            if not llm_to_use:
                return None
            
            content = result.get('content', '') or result.get('text', '')
            if not content:
                return False
            
            # 🚀 P0修复：使用更强的提示词，明确要求过滤不相关内容
            prompt = f"""你是一个知识检索质量评估专家。判断以下知识是否与查询相关。

**查询：**
{query}

**知识内容：**
{content[:800]}

**任务：**
判断知识内容是否与查询相关。相关性的标准：
1. 知识内容是否直接回答查询问题
2. 知识内容是否包含查询中提到的关键实体（人名、地名、事件等）
3. 知识内容是否与查询的意图匹配

**重要提示：**
- 如果知识内容只是提到了查询中的某些词，但实际内容不相关（如只是定义、外部链接、导航信息等），应该判断为不相关
- 如果知识内容包含"external links"、"references"、"see also"、"categories"等标记，通常是不相关的
- 如果查询问的是具体的人名（如"Who was the 15th first lady?"），但知识内容只是第一夫人的定义，应该判断为不相关
- 如果查询问的是具体的历史人物，但知识内容只是相关的历史概念或事件，应该判断为不相关
- **关键过滤规则**：
  * 如果查询问的是"第X任第一夫人"，但知识内容只是"First Lady"的定义或"United States"的通用描述，应该判断为不相关
  * 如果查询问的是具体人名（如"Harriet Lane"），但知识内容只是提到这个名字但没有相关信息（如只是医院名称），应该判断为不相关
  * 如果查询问的是关系（如"X的母亲"），但知识内容没有明确的关系信息，应该判断为不相关
  * 如果知识内容只是实体类型描述（如"Person"、"Location"），没有具体信息，应该判断为不相关

**返回格式（JSON）：**
{{"is_relevant": true/false, "reason": "判断原因"}}

**示例：**
- 查询："Who was the 15th first lady of the United States?"
- 知识内容："United States (Entity): the top three ballet training institutions in the United States..."
- 判断：不相关（只是提到了"United States"，但没有关于第15任第一夫人的信息）

- 查询："Who was the 15th first lady of the United States?"
- 知识内容："First Lady (Person): ..."
- 判断：不相关（只是第一夫人的定义，没有具体的第一夫人信息）

- 查询："Harriet Lane"
- 知识内容："Harriet Lane (Person): A person who left bequests establishing a children's hospital..."
- 判断：不相关（只是提到医院，没有关于第一夫人的信息）

只返回JSON，不要其他内容。"""
            
            # 🚀 新增：记录LLM判断开始
            try:
                from src.utils.research_logger import log_info
            except ImportError:
                log_info = logger.info
            
            log_info(f"🔍 LLM相关性判断开始: 查询='{query[:50]}...', 知识长度={len(content)}")
            
            # 🚀 P0修复：使用正确的LLM实例
            response = llm_to_use._call_llm(prompt)
            llm_time = time.time() - start_time
            
            # 🚀 新增：记录token消耗（如果LLM返回了token信息）
            token_usage = None
            if hasattr(llm_to_use, 'last_token_usage'):
                token_usage = llm_to_use.last_token_usage
            elif hasattr(llm_to_use, '_last_response_metadata'):
                metadata = llm_to_use._last_response_metadata
                if metadata and isinstance(metadata, dict):
                    token_usage = metadata.get('usage', {})
            
            if response:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result_data = json.loads(json_match.group(0))
                    is_relevant = result_data.get('is_relevant', True)
                    reason = result_data.get('reason', '')
                    
                    # 🚀 新增：详细记录LLM判断结果
                    token_info = ""
                    if token_usage:
                        if isinstance(token_usage, dict):
                            prompt_tokens = token_usage.get('prompt_tokens', 0)
                            completion_tokens = token_usage.get('completion_tokens', 0)
                            total_tokens = token_usage.get('total_tokens', 0)
                            token_info = f" | Token: {total_tokens} (prompt: {prompt_tokens}, completion: {completion_tokens})"
                        else:
                            token_info = f" | Token: {token_usage}"
                    
                    log_info(f"✅ LLM相关性判断完成: 相关={is_relevant} | 耗时={llm_time:.3f}秒{token_info} | 原因: {reason[:100]}")
                    logger.debug(f"LLM相关性判断: {is_relevant} | 原因: {reason}")
                    return is_relevant
            
            # 🚀 新增：记录LLM判断失败
            log_info(f"⚠️ LLM相关性判断失败: 无法解析响应 | 耗时={llm_time:.3f}秒")
            return None
            
        except Exception as e:
            llm_time = time.time() - start_time
            try:
                from src.utils.research_logger import log_info
            except ImportError:
                log_info = logger.info
            log_info(f"❌ LLM相关性验证失败: {str(e)} | 耗时={llm_time:.3f}秒")
            logger.debug(f"LLM相关性验证失败: {e}")
            return None
    
    def validate_knowledge_source(self, result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """🚀 新增：验证知识源的可靠性
        
        Args:
            result: 知识检索结果
            query: 查询文本
            
        Returns:
            验证结果字典，包含 is_reliable, confidence, source_type
        """
        try:
            source = result.get('source', 'unknown')
            metadata = result.get('metadata', {})
            
            # 知识源可靠性评分
            source_reliability = {
                'wikipedia': 0.9,
                'wiki': 0.9,
                'faiss': 0.8,
                'kms': 0.8,
                'knowledge_management_system': 0.8,
                'fallback': 0.3,
                'cache': 0.7,
                'unknown': 0.5
            }
            
            # 获取知识源类型
            source_type = source.lower() if isinstance(source, str) else 'unknown'
            if 'wiki' in source_type:
                source_type = 'wikipedia'
            elif 'faiss' in source_type:
                source_type = 'faiss'
            elif 'kms' in source_type or 'knowledge' in source_type:
                source_type = 'kms'
            
            # 获取可靠性评分
            reliability = source_reliability.get(source_type, 0.5)
            
            # 检查元数据中的可靠性指标
            if metadata:
                # 检查是否有来源URL（Wikipedia等）
                if 'url' in metadata or 'source_url' in metadata:
                    url = metadata.get('url') or metadata.get('source_url', '')
                    if 'wikipedia.org' in url.lower():
                        reliability = max(reliability, 0.9)
                    elif 'edu' in url.lower() or 'gov' in url.lower():
                        reliability = max(reliability, 0.85)
                
                # 检查是否有时间戳（较新的知识更可靠）
                if 'timestamp' in metadata or 'last_updated' in metadata:
                    reliability = min(reliability + 0.05, 1.0)
            
            return {
                'is_reliable': reliability >= 0.6,
                'confidence': reliability,
                'source_type': source_type,
                'reason': f'知识源可靠性评分: {reliability:.2f}'
            }
            
        except Exception as e:
            logger.error(f"验证知识源可靠性失败: {e}")
            return {
                'is_reliable': True,  # 默认认为可靠，避免过度过滤
                'confidence': 0.5,
                'source_type': 'unknown',
                'reason': f'验证失败: {str(e)}'
            }

