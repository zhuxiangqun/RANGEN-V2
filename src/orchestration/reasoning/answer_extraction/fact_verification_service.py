"""
通用事实验证服务 - 基于证据和知识库的答案验证与修正
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class FactVerificationStrategy(ABC):
    """事实验证策略基类"""
    
    @abstractmethod
    def verify(
        self, 
        answer: str, 
        query: str, 
        evidence: List[Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str], float]:
        """验证答案
        
        Args:
            answer: 待验证的答案
            query: 查询文本
            evidence: 证据列表
            context: 上下文信息
            
        Returns:
            (是否有效, 修正后的答案(如果需要), 置信度)
        """
        pass


class EvidenceConsistencyStrategy(FactVerificationStrategy):
    """基于证据一致性的验证策略"""
    
    def verify(
        self, 
        answer: str, 
        query: str, 
        evidence: List[Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str], float]:
        """验证答案是否与证据一致
        
        策略：
        1. 检查答案是否在证据中出现
        2. 检查答案是否与证据中的关键信息一致
        3. 如果证据中有更准确的答案，返回修正后的答案
        """
        if not evidence:
            return True, None, 0.5  # 无证据时，无法验证
        
        answer_lower = answer.lower().strip()
        evidence_texts = []
        
        # 提取证据文本
        for ev in evidence:
            content = ev.content if hasattr(ev, 'content') else str(ev)
            if content:
                evidence_texts.append(content.lower())
        
        if not evidence_texts:
            return True, None, 0.5
        
        # 检查答案是否在证据中出现
        answer_in_evidence = any(answer_lower in text for text in evidence_texts)
        
        # 如果答案不在证据中，尝试从证据中提取更准确的答案
        if not answer_in_evidence:
            # 使用简单的关键词匹配查找可能的正确答案
            corrected_answer = self._extract_answer_from_evidence(query, evidence_texts)
            if corrected_answer and corrected_answer.lower() != answer_lower:
                logger.warning(
                    f"⚠️ [证据一致性验证] 答案不在证据中: {answer} -> {corrected_answer}"
                )
                return False, corrected_answer, 0.7
        
        # 如果答案在证据中，检查一致性
        if answer_in_evidence:
            # 计算答案在证据中的出现频率（作为置信度指标）
            occurrence_count = sum(text.count(answer_lower) for text in evidence_texts)
            confidence = min(0.9, 0.5 + (occurrence_count * 0.1))
            return True, None, confidence
        
        return True, None, 0.5
    
    def _extract_answer_from_evidence(
        self, 
        query: str, 
        evidence_texts: List[str]
    ) -> Optional[str]:
        """从证据中提取可能的答案"""
        # 简单的实现：查找查询中的关键实体，然后在证据中查找相关实体
        # 这是一个基础实现，可以后续扩展为更智能的提取逻辑
        import re
        
        # 提取查询中的关键实体（人名、地名等）
        entity_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
        query_entities = re.findall(entity_pattern, query)
        
        # 在证据中查找这些实体
        for entity in query_entities:
            entity_lower = entity.lower()
            for text in evidence_texts:
                if entity_lower in text:
                    # 尝试提取实体周围的上下文，找到可能的答案
                    # 这里可以扩展为更智能的提取逻辑
                    pass
        
        return None


class KnowledgeBaseVerificationStrategy(FactVerificationStrategy):
    """基于知识库的验证策略"""
    
    def __init__(self, knowledge_service=None):
        self.knowledge_service = knowledge_service
    
    def verify(
        self, 
        answer: str, 
        query: str, 
        evidence: List[Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str], float]:
        """使用知识库验证答案
        
        策略：
        1. 从查询中提取关键实体和关系
        2. 查询知识库获取正确答案
        3. 比较提取的答案和知识库答案
        4. 如果不一致，返回知识库中的答案
        """
        if not self.knowledge_service:
            return True, None, 0.5
        
        try:
            # 从查询中提取关键信息
            query_entities = self._extract_entities_from_query(query)
            
            # 构建知识库查询
            kb_query = self._build_knowledge_base_query(query, query_entities)
            
            # 查询知识库
            kb_results = self.knowledge_service.query_knowledge(
                query=kb_query,
                top_k=5,
                similarity_threshold=0.6
            )
            
            if not kb_results or not kb_results.get('knowledge'):
                return True, None, 0.5
            
            # 从知识库结果中提取答案
            kb_answer = self._extract_answer_from_kb_results(kb_results['knowledge'], query)
            
            if kb_answer:
                answer_lower = answer.lower().strip()
                kb_answer_lower = kb_answer.lower().strip()
                
                # 如果知识库答案与提取答案不一致
                if kb_answer_lower != answer_lower and kb_answer_lower not in answer_lower:
                    # 检查知识库答案是否在证据中出现（提高置信度）
                    evidence_texts = [
                        ev.content.lower() if hasattr(ev, 'content') else str(ev).lower()
                        for ev in evidence
                    ]
                    kb_answer_in_evidence = any(kb_answer_lower in text for text in evidence_texts)
                    
                    if kb_answer_in_evidence:
                        logger.warning(
                            f"⚠️ [知识库验证] 答案不一致: {answer} -> {kb_answer} "
                            f"(知识库答案在证据中出现)"
                        )
                        return False, kb_answer, 0.8
            
            return True, None, 0.7
            
        except Exception as e:
            logger.debug(f"知识库验证失败: {e}")
            return True, None, 0.5
    
    def _extract_entities_from_query(self, query: str) -> List[str]:
        """从查询中提取实体"""
        import re
        entity_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
        return re.findall(entity_pattern, query)
    
    def _build_knowledge_base_query(self, query: str, entities: List[str]) -> str:
        """构建知识库查询"""
        # 简化实现：直接使用原始查询
        # 可以扩展为更智能的查询构建逻辑
        return query
    
    def _extract_answer_from_kb_results(
        self, 
        kb_results: List[Dict[str, Any]], 
        query: str
    ) -> Optional[str]:
        """从知识库结果中提取答案"""
        if not kb_results:
            return None
        
        # 简化实现：返回第一个结果的内容
        # 可以扩展为更智能的答案提取逻辑
        first_result = kb_results[0]
        content = first_result.get('content', '')
        
        # 简单的答案提取：查找人名、地名等实体
        import re
        entity_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
        entities = re.findall(entity_pattern, content)
        
        if entities:
            return entities[0]
        
        return None


class LLMConsistencyStrategy(FactVerificationStrategy):
    """基于LLM一致性的验证策略"""
    
    def __init__(self, llm_integration=None):
        self.llm_integration = llm_integration
    
    def verify(
        self, 
        answer: str, 
        query: str, 
        evidence: List[Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str], float]:
        """使用LLM验证答案一致性
        
        策略：
        1. 使用LLM检查答案是否与证据一致
        2. 如果LLM发现不一致，尝试从证据中提取正确答案
        """
        if not self.llm_integration:
            return True, None, 0.5
        
        try:
            # 构建验证提示
            evidence_text = "\n".join([
                ev.content if hasattr(ev, 'content') else str(ev)
                for ev in evidence[:3]  # 只使用前3个证据
            ])
            
            prompt = f"""请验证以下答案是否与证据一致。

查询: {query}
提取的答案: {answer}

证据:
{evidence_text}

请回答：
1. 答案是否与证据一致？(是/否)
2. 如果不一致，正确的答案应该是什么？

只返回JSON格式：
{{
    "is_consistent": true/false,
    "correct_answer": "正确答案或null"
}}"""
            
            # 调用LLM
            response = self.llm_integration.generate_response(
                prompt,
                temperature=0.1,
                max_tokens=200
            )
            
            # 解析响应
            import json
            try:
                result = json.loads(response)
                is_consistent = result.get('is_consistent', True)
                correct_answer = result.get('correct_answer')
                
                if not is_consistent and correct_answer:
                    logger.warning(
                        f"⚠️ [LLM一致性验证] 答案不一致: {answer} -> {correct_answer}"
                    )
                    return False, correct_answer, 0.75
                
                return True, None, 0.8
                
            except json.JSONDecodeError:
                return True, None, 0.5
                
        except Exception as e:
            logger.debug(f"LLM一致性验证失败: {e}")
            return True, None, 0.5


class FactVerificationService:
    """通用事实验证服务"""
    
    def __init__(
        self,
        knowledge_service=None,
        llm_integration=None,
        strategies: Optional[List[FactVerificationStrategy]] = None
    ):
        self.knowledge_service = knowledge_service
        self.llm_integration = llm_integration
        
        # 初始化验证策略（按优先级排序）
        if strategies:
            self.strategies = strategies
        else:
            self.strategies = [
                EvidenceConsistencyStrategy(),
                KnowledgeBaseVerificationStrategy(knowledge_service),
                LLMConsistencyStrategy(llm_integration),
            ]
        
        self.logger = logging.getLogger(__name__)
    
    def verify_and_correct(
        self,
        answer: str,
        query: str,
        evidence: List[Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """验证答案并返回修正结果
        
        Args:
            answer: 待验证的答案
            query: 查询文本
            evidence: 证据列表
            context: 上下文信息
            
        Returns:
            验证结果字典：
            {
                'is_valid': bool,
                'corrected_answer': Optional[str],
                'confidence': float,
                'verification_method': str,
                'reasons': List[str]
            }
        """
        if not answer or not answer.strip():
            return {
                'is_valid': False,
                'corrected_answer': None,
                'confidence': 0.0,
                'verification_method': 'none',
                'reasons': ['答案为空']
            }
        
        # 依次尝试各个验证策略
        for strategy in self.strategies:
            try:
                is_valid, corrected_answer, confidence = strategy.verify(
                    answer, query, evidence, context
                )
                
                # 如果策略发现需要修正，返回修正结果
                if not is_valid and corrected_answer:
                    return {
                        'is_valid': False,
                        'corrected_answer': corrected_answer,
                        'confidence': confidence,
                        'verification_method': strategy.__class__.__name__,
                        'reasons': [f'通过{strategy.__class__.__name__}验证发现答案不一致']
                    }
                
                # 如果策略验证通过但置信度较低，继续尝试其他策略
                if is_valid and confidence < 0.6:
                    continue
                
                # 如果策略验证通过且置信度较高，返回结果
                if is_valid:
                    return {
                        'is_valid': True,
                        'corrected_answer': None,
                        'confidence': confidence,
                        'verification_method': strategy.__class__.__name__,
                        'reasons': []
                    }
                    
            except Exception as e:
                self.logger.debug(f"验证策略 {strategy.__class__.__name__} 执行失败: {e}")
                continue
        
        # 所有策略都无法确定，返回默认结果
        return {
            'is_valid': True,
            'corrected_answer': None,
            'confidence': 0.5,
            'verification_method': 'default',
            'reasons': ['所有验证策略都无法确定']
        }

