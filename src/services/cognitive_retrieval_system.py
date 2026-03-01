"""
认知增强检索系统

基于深度理解、推理和自我修正的智能检索系统，不依赖硬编码规则。
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CognitiveAnalysis:
    """认知分析结果"""
    query_type: str  # 查询类型：fact_retrieval, relation_reasoning, multi_hop_reasoning, temporal_reasoning, comparison
    knowledge_structure: Dict[str, Any]  # 知识结构需求
    inference_path: List[str]  # 推理路径
    challenges: List[str]  # 挑战点
    alternative_expressions: List[str]  # 替代表述


@dataclass
class SemanticUnit:
    """语义单元"""
    text: str  # 语义单元文本
    unit_type: str  # 单元类型：concept, relation, temporal, context
    retrieval_queries: List[str]  # 检索查询列表
    expected_content: str  # 期望内容描述
    integration_logic: str  # 集成逻辑


@dataclass
class Perspective:
    """认知视角"""
    name: str  # 视角名称
    description: str  # 视角描述
    query_template: str  # 查询模板


class SemanticDecomposer:
    """语义分解器：将复杂查询分解为可检索的语义单元"""
    
    def __init__(self, llm_integration=None):
        self.llm_integration = llm_integration
        self.logger = logging.getLogger(__name__)
    
    def decompose_query(self, query: str) -> List[SemanticUnit]:
        """将复杂查询分解为可检索的语义单元
        
        Args:
            query: 复杂查询
            
        Returns:
            语义单元列表
        """
        try:
            # 如果LLM可用，使用LLM进行智能分解
            if self.llm_integration:
                return self._decompose_with_llm(query)
            else:
                # 否则使用启发式方法
                return self._decompose_heuristic(query)
        except Exception as e:
            self.logger.error(f"语义分解失败: {e}", exc_info=True)
            return self._decompose_heuristic(query)
    
    def _decompose_with_llm(self, query: str) -> List[SemanticUnit]:
        """使用LLM进行语义分解"""
        try:
            prompt = f"""将以下复杂查询分解为可独立检索的语义单元：

查询: {query}

分解要求：
1. **概念分解**：将复合概念分解为基本概念
2. **关系分解**：将隐式关系分解为显式关系
3. **时序分解**：将时间约束分解为可检索的时间点/段
4. **上下文分解**：将上下文依赖分解为独立上下文

例如：
"第二个被刺杀的美国总统" 分解为：
- 被刺杀的美国总统列表
- 刺杀事件的时间顺序
- "第二个"的序数含义

返回JSON格式：
{{
    "units": [
        {{
            "text": "语义单元文本",
            "unit_type": "concept|relation|temporal|context",
            "expected_content": "期望内容描述",
            "integration_logic": "如何集成到最终答案"
        }}
    ]
}}
"""
            response = self.llm_integration._call_llm(prompt)
            if response:
                import json
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                    units = []
                    for unit_data in result.get('units', []):
                        unit = SemanticUnit(
                            text=unit_data.get('text', ''),
                            unit_type=unit_data.get('unit_type', 'concept'),
                            retrieval_queries=self._generate_queries_for_unit(unit_data),
                            expected_content=unit_data.get('expected_content', ''),
                            integration_logic=unit_data.get('integration_logic', '')
                        )
                        units.append(unit)
                    return units
        except Exception as e:
            self.logger.debug(f"LLM语义分解失败: {e}，使用启发式方法")
        
        return self._decompose_heuristic(query)
    
    def _decompose_heuristic(self, query: str) -> List[SemanticUnit]:
        """使用启发式方法进行语义分解"""
        units = []
        query_lower = query.lower()
        
        # 1. 提取序数词 + 实体类型（如"15th first lady"、"second assassinated president"）
        ordinal_pattern = r'(\d+)(?:st|nd|rd|th)?\s+(\w+(?:\s+\w+)*)'
        ordinal_matches = re.finditer(ordinal_pattern, query_lower)
        for match in ordinal_matches:
            ordinal = match.group(1)
            entity_type = match.group(2)
            units.append(SemanticUnit(
                text=f"{ordinal}th {entity_type}",
                unit_type="concept",
                retrieval_queries=[
                    f"{ordinal}th {entity_type}",
                    f"{ordinal}th US {entity_type}",
                    f"{ordinal}th {entity_type} United States"
                ],
                expected_content=f"关于第{ordinal}任{entity_type}的信息",
                integration_logic="提取具体名称"
            ))
        
        # 2. 提取关系查询（如"mother"、"father"）
        relation_pattern = r"(mother|father|wife|husband|daughter|son|parent|spouse|maiden\s+name|surname)"
        relation_matches = re.finditer(relation_pattern, query_lower)
        for match in relation_matches:
            relation = match.group(1)
            units.append(SemanticUnit(
                text=relation,
                unit_type="relation",
                retrieval_queries=[
                    f"{relation} of",
                    f"who is {relation}",
                    f"what is {relation}"
                ],
                expected_content=f"关于{relation}关系的信息",
                integration_logic="提取关系对象"
            ))
        
        # 3. 如果没有找到特定模式，返回整个查询作为一个单元
        if not units:
            units.append(SemanticUnit(
                text=query,
                unit_type="concept",
                retrieval_queries=[query],
                expected_content="直接回答查询的信息",
                integration_logic="直接使用"
            ))
        
        return units
    
    def _generate_queries_for_unit(self, unit_data: Dict[str, Any]) -> List[str]:
        """为语义单元生成多样化查询"""
        queries = []
        text = unit_data.get('text', '')
        
        if not text:
            return queries
        
        # 1. 直接查询
        queries.append(text)
        
        # 2. 添加上下文变体
        if 'first lady' in text.lower():
            queries.append(f"US {text}")
            queries.append(f"United States {text}")
        
        if 'president' in text.lower():
            queries.append(f"US {text}")
            queries.append(f"American {text}")
        
        return queries


class MultiPerspectiveGenerator:
    """多视角生成器：为查询生成多个认知视角"""
    
    def __init__(self, llm_integration=None):
        self.llm_integration = llm_integration
        self.logger = logging.getLogger(__name__)
    
    def generate_perspectives(self, query: str) -> List[Perspective]:
        """为查询生成多个认知视角
        
        Args:
            query: 查询文本
            
        Returns:
            视角列表
        """
        try:
            # 如果LLM可用，使用LLM生成视角
            if self.llm_integration:
                return self._generate_with_llm(query)
            else:
                # 否则使用启发式方法
                return self._generate_heuristic(query)
        except Exception as e:
            self.logger.error(f"多视角生成失败: {e}", exc_info=True)
            return self._generate_heuristic(query)
    
    def _generate_with_llm(self, query: str) -> List[Perspective]:
        """使用LLM生成视角"""
        try:
            prompt = f"""为以下查询生成多个认知视角：

查询: {query}

可能的视角包括：
1. **时间视角**：关注时间线和历史背景
2. **关系视角**：关注实体间的关系网络
3. **属性视角**：关注实体的属性和特征
4. **比较视角**：关注与其他实体的比较
5. **因果视角**：关注因果关系和影响
6. **层级视角**：关注层级结构和分类

返回JSON格式：
{{
    "perspectives": [
        {{
            "name": "视角名称",
            "description": "视角描述",
            "query_template": "查询模板"
        }}
    ]
}}
"""
            response = self.llm_integration._call_llm(prompt)
            if response:
                import json
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                    perspectives = []
                    for persp_data in result.get('perspectives', []):
                        perspective = Perspective(
                            name=persp_data.get('name', ''),
                            description=persp_data.get('description', ''),
                            query_template=persp_data.get('query_template', query)
                        )
                        perspectives.append(perspective)
                    return perspectives
        except Exception as e:
            self.logger.debug(f"LLM多视角生成失败: {e}，使用启发式方法")
        
        return self._generate_heuristic(query)
    
    def _generate_heuristic(self, query: str) -> List[Perspective]:
        """使用启发式方法生成视角"""
        perspectives = []
        query_lower = query.lower()
        
        # 1. 时间视角（如果查询包含序数词或时间相关词）
        if re.search(r'\d+(?:st|nd|rd|th)|first|second|third|last', query_lower):
            perspectives.append(Perspective(
                name="时间视角",
                description="关注时间线和历史背景",
                query_template=query
            ))
        
        # 2. 关系视角（如果查询包含关系词）
        if re.search(r'mother|father|wife|husband|daughter|son|parent|spouse', query_lower):
            perspectives.append(Perspective(
                name="关系视角",
                description="关注实体间的关系网络",
                query_template=query
            ))
        
        # 3. 属性视角（如果查询包含属性词）
        if re.search(r'name|first name|last name|surname|maiden name', query_lower):
            perspectives.append(Perspective(
                name="属性视角",
                description="关注实体的属性和特征",
                query_template=query
            ))
        
        # 如果没有找到特定模式，返回默认视角
        if not perspectives:
            perspectives.append(Perspective(
                name="通用视角",
                description="通用查询视角",
                query_template=query
            ))
        
        return perspectives


class CognitiveRetrievalSystem:
    """认知增强检索系统"""
    
    def __init__(self, vector_store=None, llm_integration=None, kms_service=None):
        self.vector_store = vector_store
        self.llm_integration = llm_integration
        self.kms_service = kms_service
        self.decomposer = SemanticDecomposer(llm_integration)
        self.perspective_generator = MultiPerspectiveGenerator(llm_integration)
        self.logger = logging.getLogger(__name__)
        self.cognitive_states = {}  # 跟踪查询的理解状态
    
    def analyze_cognitive_needs(self, query: str) -> CognitiveAnalysis:
        """深度分析查询的认知需求
        
        Args:
            query: 查询文本
            
        Returns:
            认知分析结果
        """
        try:
            query_lower = query.lower()
            
            # 1. 查询类型分析
            query_type = "general"
            if re.search(r'mother|father|wife|husband|daughter|son|parent|spouse', query_lower):
                query_type = "relation_reasoning"
            elif re.search(r'\d+(?:st|nd|rd|th)|first|second|third', query_lower):
                query_type = "multi_hop_reasoning"
            elif re.search(r'when|date|year|time', query_lower):
                query_type = "temporal_reasoning"
            
            # 2. 知识结构分析
            knowledge_structure = {
                "entities": self._extract_entities(query),
                "relations": self._extract_relations(query),
                "temporal_constraints": self._extract_temporal_constraints(query)
            }
            
            # 3. 推理路径规划
            inference_path = self._plan_inference_path(query, knowledge_structure)
            
            # 4. 挑战点识别
            challenges = self._identify_challenges(query, knowledge_structure)
            
            # 5. 替代表述
            alternative_expressions = self._generate_alternative_expressions(query)
            
            return CognitiveAnalysis(
                query_type=query_type,
                knowledge_structure=knowledge_structure,
                inference_path=inference_path,
                challenges=challenges,
                alternative_expressions=alternative_expressions
            )
        except Exception as e:
            self.logger.error(f"认知需求分析失败: {e}", exc_info=True)
            return CognitiveAnalysis(
                query_type="general",
                knowledge_structure={},
                inference_path=[],
                challenges=[],
                alternative_expressions=[query]
            )
    
    def _extract_entities(self, query: str) -> List[str]:
        """提取查询中的实体"""
        entities = []
        # 提取人名模式
        name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
        entities.extend(re.findall(name_pattern, query))
        return entities
    
    def _extract_relations(self, query: str) -> List[str]:
        """提取查询中的关系"""
        relations = []
        relation_pattern = r'\b(mother|father|wife|husband|daughter|son|parent|spouse|maiden\s+name|surname)\b'
        relations.extend(re.findall(relation_pattern, query.lower()))
        return relations
    
    def _extract_temporal_constraints(self, query: str) -> List[str]:
        """提取查询中的时间约束"""
        constraints = []
        temporal_pattern = r'\d+(?:st|nd|rd|th)|first|second|third|last'
        constraints.extend(re.findall(temporal_pattern, query.lower()))
        return constraints
    
    def _plan_inference_path(self, query: str, knowledge_structure: Dict[str, Any]) -> List[str]:
        """规划推理路径"""
        path = []
        query_lower = query.lower()
        
        # 如果包含序数词 + 实体类型，需要先找到实体
        if re.search(r'\d+(?:st|nd|rd|th)\s+\w+', query_lower):
            path.append("找到序数实体")
        
        # 如果包含关系词，需要找到关系对象
        if re.search(r'mother|father|wife|husband', query_lower):
            path.append("找到关系对象")
        
        # 如果包含属性词，需要提取属性
        if re.search(r'first name|last name|surname|maiden name', query_lower):
            path.append("提取属性")
        
        return path
    
    def _identify_challenges(self, query: str, knowledge_structure: Dict[str, Any]) -> List[str]:
        """识别挑战点"""
        challenges = []
        query_lower = query.lower()
        
        # 检查是否包含占位符
        if '[' in query and ']' in query:
            challenges.append("占位符未替换")
        
        # 检查是否包含多跳推理
        if len(knowledge_structure.get('entities', [])) > 1:
            challenges.append("多跳推理")
        
        # 检查是否包含时间约束
        if knowledge_structure.get('temporal_constraints'):
            challenges.append("时间约束")
        
        return challenges
    
    def _generate_alternative_expressions(self, query: str) -> List[str]:
        """生成替代表述"""
        alternatives = [query]
        query_lower = query.lower()
        
        # 生成同义词变体
        if 'first lady' in query_lower:
            alternatives.append(query_lower.replace('first lady', 'president\'s wife'))
        
        if 'assassinated president' in query_lower:
            alternatives.append(query_lower.replace('assassinated president', 'president who was assassinated'))
        
        return alternatives
    
    def retrieve_with_cognitive_enhancement(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """使用认知增强进行检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            检索结果列表
        """
        try:
            # 1. 认知需求分析
            cognitive_analysis = self.analyze_cognitive_needs(query)
            self.logger.info(f"🔍 [认知分析] 查询类型: {cognitive_analysis.query_type}, 挑战点: {cognitive_analysis.challenges}")
            
            # 2. 语义分解
            semantic_units = self.decomposer.decompose_query(query)
            self.logger.info(f"🔍 [语义分解] 分解为 {len(semantic_units)} 个语义单元")
            
            # 3. 多视角生成
            perspectives = self.perspective_generator.generate_perspectives(query)
            self.logger.info(f"🔍 [多视角] 生成 {len(perspectives)} 个视角")
            
            # 4. 执行多策略检索
            all_results = []
            
            # 策略1: 基于语义单元的检索
            for unit in semantic_units:
                for retrieval_query in unit.retrieval_queries:
                    if self.kms_service:
                        results = self.kms_service.query_knowledge(
                            query=retrieval_query,
                            top_k=top_k,
                            use_graph=True
                        )
                        if results:
                            all_results.extend(results)
            
            # 策略2: 基于多视角的检索
            for perspective in perspectives:
                if self.kms_service:
                    results = self.kms_service.query_knowledge(
                        query=perspective.query_template,
                        top_k=top_k,
                        use_graph=True
                    )
                    if results:
                        all_results.extend(results)
            
            # 策略3: 基于替代表述的检索
            for alt_query in cognitive_analysis.alternative_expressions:
                if alt_query != query and self.kms_service:
                    results = self.kms_service.query_knowledge(
                        query=alt_query,
                        top_k=top_k,
                        use_graph=True
                    )
                    if results:
                        all_results.extend(results)
            
            # 5. 去重和排序
            seen_ids = set()
            unique_results = []
            for result in all_results:
                result_id = result.get('knowledge_id') or result.get('content', '')[:100]
                if result_id not in seen_ids:
                    seen_ids.add(result_id)
                    unique_results.append(result)
            
            # 🚀 P0修复：按相似度排序，使用knowledge_id作为次要排序键确保稳定性
            unique_results.sort(
                key=lambda x: (
                    x.get('similarity_score', 0.0) or x.get('similarity', 0.0),
                    x.get('knowledge_id', '') or x.get('content', '')[:100]  # 使用knowledge_id或content作为次要排序键
                ),
                reverse=True
            )
            
            return unique_results[:top_k]
            
        except Exception as e:
            self.logger.error(f"认知增强检索失败: {e}", exc_info=True)
            # 回退到基本检索
            if self.kms_service:
                return self.kms_service.query_knowledge(query=query, top_k=top_k) or []
            return []

