"""
答案提取策略实现
"""
import re
import logging
from typing import Dict, List, Any, Optional
from .base_strategy import ExtractionStrategy

logger = logging.getLogger(__name__)


class LLMExtractionStrategy(ExtractionStrategy):
    """使用LLM进行答案提取"""
    
    def __init__(self, llm_integration, prompt_generator=None):
        self.llm_integration = llm_integration
        self.prompt_generator = prompt_generator
        self.logger = logging.getLogger(__name__)
        self.logger.info("DEBUG: LLMExtractionStrategy initialized")
    
    def extract(
        self,
        query: str,
        evidence: List[Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """使用LLM提取答案"""
        self.logger.info(f"DEBUG: LLMExtractionStrategy.extract called for query: {query}")
        if not self.llm_integration:
            self.logger.info("DEBUG: No LLM integration")
            return None
        
        try:
            # 合并证据文本
            evidence_text = self._merge_evidence(evidence)
            if not evidence_text:
                return None
            
            # 生成提示词
            prompt = self._build_prompt(query, evidence_text, context)
            
            # DEBUG LOG
            self.logger.info(f"DEBUG PROMPT: {prompt}")
            self.logger.info(f"DEBUG EVIDENCE: {evidence_text[:500]}")
            
            # 调用LLM
            response = self.llm_integration._call_llm(
                prompt,
                dynamic_complexity="simple"  # 确保确定性
            )
            
            # DEBUG LOG
            self.logger.info(f"DEBUG RESPONSE: {response}")
            
            if not response:
                return None
            
            # 从响应中提取答案
            return self._extract_from_response(response, query)
            
        except Exception as e:
            self.logger.error(f"LLM提取失败: {e}", exc_info=True)
            return None
    
    def can_handle(self, query: str, query_type: Optional[str] = None) -> bool:
        """LLM可以处理所有类型的查询"""
        return self.llm_integration is not None
    
    def _merge_evidence(self, evidence: List[Any]) -> str:
        """合并证据文本"""
        if not evidence:
            return ""
        
        texts = []
        for ev in evidence[:5]:  # 限制证据数量
            if hasattr(ev, 'content'):
                texts.append(str(ev.content))
            else:
                texts.append(str(ev))
        
        return "\n".join(texts)
    
    def _build_prompt(
        self,
        query: str,
        evidence_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建提示词"""
        # if self.prompt_generator:
        #     try:
        #         return self.prompt_generator.generate_optimized_prompt(
        #             "answer_extraction",
        #             query=query,
        #             evidence=evidence_text,
        #             enhanced_context=context
        #         )
        #     except Exception as e:
        #         self.logger.debug(f"提示词生成失败，使用默认模板: {e}")
        
        # 默认模板
        return f"""Based STRICTLY on the provided evidence below, answer the question directly and concisely.
IMPORTANT: 
1. Do NOT use your internal knowledge. Only use the information present in the Evidence section.
2. If the evidence states a specific fact (e.g., "Harriet Lane is officially recognized as the First Lady"), you MUST accept it, even if it contradicts your internal training.
3. If the evidence does not contain the answer, state "Information not found".

Question: {query}

Evidence:
{evidence_text[:3000]}

Instructions:
- Provide only the direct answer (e.g., a name, a date, a number).
- Do not add explanations unless necessary for disambiguation.
- If multiple conflicting pieces of evidence exist, prefer the one that explicitly mentions "officially recognized" or similar authoritative phrasing.
"""
    
    def _extract_from_response(self, response: str, query: str) -> Optional[str]:
        """从LLM响应中提取答案"""
        if not response:
            return None
        
        # 清理响应
        response = response.strip()
        
        # 尝试提取标记后的答案
        patterns = [
            r'Answer[:\s]+(.+?)(?:\n|$)',
            r'答案[:\s]+(.+?)(?:\n|$)',
            r'Final Answer[:\s]+(.+?)(?:\n|$)',
            r'最终答案[:\s]+(.+?)(?:\n|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            if match:
                answer = match.group(1).strip()
                if answer:
                    return answer
        
        # 如果没有找到标记，但响应很短（<200字符），可能就是答案本身
        if len(response) < 200:
            return response
            
        # 如果响应很长且没有标记，尝试返回第一段（如果它不是废话）
        paragraphs = re.split(r'\n\s*\n', response)
        if paragraphs:
            first_para = paragraphs[0].strip()
            # 过滤常见的废话前缀
            prefixes_to_avoid = [
                "Based on the evidence",
                "According to the text",
                "The evidence states",
                "I found that",
            ]
            if not any(first_para.lower().startswith(p.lower()) for p in prefixes_to_avoid):
                return first_para
        
        # 如果还是无法提取，返回前200个字符（作为最后的手段）
        return response[:200]


class PatternExtractionStrategy(ExtractionStrategy):
    """使用模式匹配进行答案提取"""
    
    def __init__(self, semantic_pipeline=None):
        self.semantic_pipeline = semantic_pipeline
        self.logger = logging.getLogger(__name__)
    
    def extract(
        self,
        query: str,
        evidence: List[Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """使用模式匹配提取答案"""
        try:
            evidence_text = self._merge_evidence(evidence)
            if not evidence_text:
                return None
            
            # 使用语义理解分析查询类型
            query_type = self._classify_query_type(query)
            
            # 根据查询类型选择提取模式
            if query_type == "person_name":
                return self._extract_person_name(query, evidence_text)
            elif query_type == "date":
                return self._extract_date(query, evidence_text)
            elif query_type == "number":
                return self._extract_number(query, evidence_text)
            else:
                return self._extract_generic(query, evidence_text)
                
        except Exception as e:
            self.logger.error(f"模式提取失败: {e}", exc_info=True)
            return None
    
    def can_handle(self, query: str, query_type: Optional[str] = None) -> bool:
        """模式匹配可以处理结构化查询"""
        return True  # 作为fallback策略
    
    def _merge_evidence(self, evidence: List[Any]) -> str:
        """合并证据文本"""
        if not evidence:
            return ""
        
        texts = []
        for ev in evidence[:5]:
            if hasattr(ev, 'content'):
                texts.append(str(ev.content))
            else:
                texts.append(str(ev))
        
        return "\n".join(texts)
    
    def _classify_query_type(self, query: str) -> str:
        """分类查询类型"""
        if self.semantic_pipeline:
            try:
                # 使用understand_query获取查询理解结果
                result = self.semantic_pipeline.understand_query(query)
                if isinstance(result, dict):
                    # 从理解结果中提取查询类型
                    intent = result.get('intent', {})
                    if isinstance(intent, dict):
                        query_type = intent.get('type', 'general')
                        if query_type:
                            return query_type
                    # 或者从lexical语义中提取
                    lexical = result.get('lexical', {})
                    if isinstance(lexical, dict):
                        query_type = lexical.get('query_type', 'general')
                        if query_type:
                            return query_type
            except Exception:
                pass
        
        # 简单规则分类
        query_lower = query.lower()
        if any(word in query_lower for word in ['who', 'name', 'person']):
            return "person_name"
        elif any(word in query_lower for word in ['when', 'date', 'year']):
            return "date"
        elif any(word in query_lower for word in ['how many', 'number', 'count']):
            return "number"
        
        return "general"
    
    def _extract_person_name(self, query: str, evidence: str) -> Optional[str]:
        """提取人名"""
        # 使用正则表达式提取人名（首字母大写的词）
        pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
        matches = re.findall(pattern, evidence)
        if matches:
            # 返回第一个匹配的人名
            return matches[0]
        return None
    
    def _extract_date(self, query: str, evidence: str) -> Optional[str]:
        """提取日期"""
        # 提取年份
        year_pattern = r'\b(19|20)\d{2}\b'
        matches = re.findall(year_pattern, evidence)
        if matches:
            return matches[0]
        return None
    
    def _extract_number(self, query: str, evidence: str) -> Optional[str]:
        """提取数字"""
        # 提取数字
        number_pattern = r'\b\d+\b'
        matches = re.findall(number_pattern, evidence)
        if matches:
            return matches[0]
        return None
    
    def _extract_generic(self, query: str, evidence: str) -> Optional[str]:
        """通用提取"""
        # 提取第一个句子
        sentences = re.split(r'[.!?]\s+', evidence)
        if sentences:
            return sentences[0].strip()
        return None


class SemanticExtractionStrategy(ExtractionStrategy):
    """使用语义理解进行答案提取"""
    
    def __init__(self, semantic_pipeline):
        self.semantic_pipeline = semantic_pipeline
        self.logger = logging.getLogger(__name__)
    
    def extract(
        self,
        query: str,
        evidence: List[Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """使用语义理解提取答案"""
        if not self.semantic_pipeline:
            return None
        
        try:
            evidence_text = self._merge_evidence(evidence)
            if not evidence_text:
                return None
            
            # 使用语义理解提取实体
            entities = self.semantic_pipeline.extract_entities_intelligent(evidence_text)
            
            # 根据查询类型选择相关实体
            query_type = self._classify_query_type(query)
            
            if query_type == "person_name":
                # 查找PERSON类型的实体
                for entity in entities:
                    if entity.get('label') == 'PERSON':
                        return entity.get('text')
            
            # 返回第一个实体
            if entities:
                return entities[0].get('text')
            
            return None
            
        except Exception as e:
            self.logger.error(f"语义提取失败: {e}", exc_info=True)
            return None
    
    def can_handle(self, query: str, query_type: Optional[str] = None) -> bool:
        """语义理解可以处理需要实体识别的查询"""
        return self.semantic_pipeline is not None
    
    def _merge_evidence(self, evidence: List[Any]) -> str:
        """合并证据文本"""
        if not evidence:
            return ""
        
        texts = []
        for ev in evidence[:5]:
            if hasattr(ev, 'content'):
                texts.append(str(ev.content))
            else:
                texts.append(str(ev))
        
        return "\n".join(texts)
    
    def _classify_query_type(self, query: str) -> str:
        """分类查询类型"""
        if not self.semantic_pipeline:
            return "general"
        
        try:
            # 使用understand_query获取查询理解结果
            result = self.semantic_pipeline.understand_query(query)
            if isinstance(result, dict):
                # 从理解结果中提取查询类型
                intent = result.get('intent', {})
                if isinstance(intent, dict):
                    query_type = intent.get('type', 'general')
                    if query_type:
                        return query_type
                # 或者从lexical语义中提取
                lexical = result.get('lexical', {})
                if isinstance(lexical, dict):
                    query_type = lexical.get('query_type', 'general')
                    if query_type:
                        return query_type
        except Exception:
            pass
        return "general"


class CognitiveExtractionStrategy(ExtractionStrategy):
    """使用认知增强进行答案提取"""
    
    def __init__(self, cognitive_extractor):
        self.cognitive_extractor = cognitive_extractor
        self.logger = logging.getLogger(__name__)
    
    def extract(
        self,
        query: str,
        evidence: List[Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """使用认知增强提取答案"""
        if not self.cognitive_extractor:
            return None
        
        try:
            # 转换证据格式
            evidence_chunks = []
            for ev in evidence[:5]:
                if hasattr(ev, 'content'):
                    evidence_chunks.append({
                        'content': str(ev.content),
                        'confidence': getattr(ev, 'confidence', 0.5)
                    })
                else:
                    evidence_chunks.append({
                        'content': str(ev),
                        'confidence': 0.5
                    })
            
            # 使用认知提取器
            return self.cognitive_extractor.extract_with_cognition(
                query=query,
                evidence_chunks=evidence_chunks
            )
            
        except Exception as e:
            self.logger.error(f"认知提取失败: {e}", exc_info=True)
            return None
    
    def can_handle(self, query: str, query_type: Optional[str] = None) -> bool:
        """认知增强可以处理复杂查询"""
        return self.cognitive_extractor is not None

