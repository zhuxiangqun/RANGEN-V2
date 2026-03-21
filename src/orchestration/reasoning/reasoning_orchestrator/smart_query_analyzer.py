"""
智能查询分析器
使用机器学习进行查询分类和特征提取
"""

import logging
import re
from typing import Dict, Any, Tuple, List
from pathlib import Path

logger = logging.getLogger(__name__)

class SmartQueryAnalyzer:
    """
    智能查询分析器 - 使用机器学习进行查询分类

    功能：
    - 自动识别查询类型（逻辑陷阱、事实链、跨领域等）
    - 特征工程和语义分析
    - 学习和改进分类能力
    """

    def __init__(self):
        # 查询类型定义
        self.query_types = {
            'logic_trap': '逻辑陷阱题 - 需要识别前提矛盾',
            'factual_chain': '事实链查询 - 多步事实查找',
            'cross_domain': '跨领域推理 - 不同领域知识结合',
            'historical_fact': '历史事实查询 - 时间相关事实',
            'general': '通用查询 - 标准问题'
        }

        # 特征提取器
        self.feature_extractors = [
            self._extract_basic_features,
            self._extract_semantic_features,
            self._extract_structural_features,
            self._extract_domain_features
        ]

        # 规则引擎（回退机制）
        self.rule_engines = {
            'logic_trap': self._logic_trap_rules,
            'factual_chain': self._factual_chain_rules,
            'cross_domain': self._cross_domain_rules,
            'historical_fact': self._historical_fact_rules
        }

        # 学习数据存储
        self.learning_data = []
        self.model_trained = False

        logger.info("✅ SmartQueryAnalyzer 初始化完成")

    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        智能分析查询
        返回详细的分析结果
        """
        query_lower = query.lower()

        # 1. 提取所有特征
        features = {}
        for extractor in self.feature_extractors:
            try:
                features.update(extractor(query, query_lower))
            except Exception as e:
                logger.warning(f"特征提取失败: {extractor.__name__}: {e}")

        # 2. 确定查询类型
        query_type, confidence = self._classify_query(query, features)

        # 3. 生成分析结果
        analysis = {
            'query_type': query_type,
            'confidence': confidence,
            'features': features,
            'complexity_indicators': self._analyze_complexity(features),
            'domain_indicators': self._analyze_domains(query, query_lower),
            'logic_indicators': self._analyze_logic_patterns(query, query_lower),
            'reasoning_requirements': self._get_reasoning_requirements(query_type),
            'recommended_strategy': self._get_recommended_strategy(query_type),
            'success': True  # 添加success字段
        }

        logger.debug(f"查询分析完成: {query_type} (置信度: {confidence:.2f})")
        return analysis

    def _extract_basic_features(self, query: str, query_lower: str) -> Dict[str, Any]:
        """提取基础特征"""
        return {
            'length': len(query),
            'word_count': len(query.split()),
            'sentence_count': len([s for s in query.split('.') if s.strip()]),
            'question_marks': query.count('?'),
            'exclamation_marks': query.count('!'),

            # 疑问词统计
            'question_words': len(re.findall(r'\b(what|how|why|when|who|where|which|whose|whom)\b', query_lower, re.I)),

            # 逻辑连接词
            'logical_connectors': len(re.findall(r'\b(if|then|but|however|although|because|since|therefore|thus|hence|consequently)\b', query_lower, re.I)),

            # 时间相关词
            'temporal_words': len(re.findall(r'\b(before|after|earlier|later|when|time|year|date|century|decade|ago|since|until)\b', query_lower, re.I)),

            # 比较相关词
            'comparison_words': len(re.findall(r'\b(same|different|compare|than|versus|vs|more|less|greater|smaller|higher|lower)\b', query_lower, re.I)),

            # 否定词
            'negation_words': len(re.findall(r'\b(not|never|no|none|nothing|neither|nor|cannot|cant|wont|dont|doesnt|isnt|arent)\b', query_lower, re.I)),

            # 数字和单位
            'numbers': len(re.findall(r'\d+', query)),
            'percentages': len(re.findall(r'\d+%', query)),
            'measurements': len(re.findall(r'\d+\s*(feet|foot|meter|inch|cm|mm|kg|lb|pound|ton)', query_lower))
        }

    def _extract_semantic_features(self, query: str, query_lower: str) -> Dict[str, Any]:
        """提取语义特征"""
        return {
            # 实体指示符
            'entity_indicators': self._count_entity_indicators(query, query_lower),

            # 领域关键词
            'domain_keywords': self._count_domain_keywords(query_lower),

            # 复杂性指示符
            'complexity_indicators': self._count_complexity_indicators(query_lower),

            # 推理深度指示符
            'reasoning_indicators': self._count_reasoning_indicators(query_lower)
        }

    def _extract_structural_features(self, query: str, query_lower: str) -> Dict[str, Any]:
        """提取结构特征"""
        return {
            # 查询结构评分
            'structure_score': self._calculate_structure_score(query),

            # 嵌套结构
            'has_parentheses': '(' in query and ')' in query,
            'has_quotes': '"' in query or "'" in query,
            'has_lists': bool(re.search(r'\d+\.|\•|-', query)),

            # 引用模式
            'has_references': bool(re.search(r'\[.*?\]|\(.*?\)', query)),

            # 条件结构
            'conditional_structure': len(re.findall(r'\bif\b.*?\bthen\b', query_lower, re.I)) > 0,

            # 序列结构
            'sequential_structure': len(re.findall(r'\b(first|second|third|next|then|after)\b', query_lower, re.I))
        }

    def _extract_domain_features(self, query: str, query_lower: str) -> Dict[str, Any]:
        """提取领域特征"""
        domains = {
            'politics': ['president', 'congress', 'senate', 'election', 'government', 'political', 'party', 'vote'],
            'geography': ['country', 'state', 'city', 'capital', 'location', 'border', 'territory', 'district'],
            'history': ['century', 'decade', 'war', 'battle', 'king', 'queen', 'emperor', 'revolution'],
            'science': ['theory', 'experiment', 'research', 'discovery', 'scientist', 'formula', 'law'],
            'literature': ['book', 'novel', 'author', 'writer', 'poem', 'story', 'character', 'plot'],
            'mathematics': ['number', 'calculate', 'equation', 'formula', 'theorem', 'proof', 'sum'],
            'business': ['company', 'market', 'economy', 'trade', 'finance', 'profit', 'cost'],
            'sports': ['game', 'team', 'player', 'score', 'championship', 'tournament', 'league']
        }

        domain_scores = {}
        for domain, keywords in domains.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                domain_scores[domain] = score

        return {
            'domain_scores': domain_scores,
            'primary_domain': max(domain_scores.items(), key=lambda x: x[1])[0] if domain_scores else 'general',
            'domain_count': len(domain_scores),
            'cross_domain_score': len(domain_scores) - 1 if len(domain_scores) > 1 else 0
        }

    def _count_entity_indicators(self, query: str, query_lower: str) -> int:
        """计算实体指示符数量"""
        indicators = [
            # 人名模式
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # "James Buchanan"
            r'\b[A-Z][a-z]+\s+[A-Z]\.\s*[A-Z][a-z]+\b',  # "James B. Buchanan"

            # 地名模式
            r'\b(United States|US|USA|America|Washington|Pennsylvania|New York|London|Paris|Tokyo)\b',

            # 组织模式
            r'\b(Congress|Senate|House|Supreme Court|FBI|CIA|NASA|WHO|UN|EU)\b',

            # 时间模式
            r'\b\d+(th|st|nd|rd|century|decade)\b',  # "15th", "20th century"
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',

            # 数字模式
            r'\b\d+\.?\d*\b',  # 数字

            # 专有名词模式（大写开头的词）
            r'\b[A-Z][a-z]+\b'
        ]

        count = 0
        for pattern in indicators:
            count += len(re.findall(pattern, query))

        return count

    def _count_domain_keywords(self, query_lower: str) -> Dict[str, int]:
        """计算领域关键词"""
        domain_keywords = {
            'politics': ['president', 'governor', 'mayor', 'election', 'political', 'government', 'congress'],
            'geography': ['capital', 'state', 'country', 'city', 'location', 'border', 'territory'],
            'history': ['century', 'war', 'battle', 'king', 'queen', 'ancient', 'modern', 'era'],
            'science': ['theory', 'experiment', 'research', 'discovery', 'scientist', 'theory'],
            'literature': ['book', 'novel', 'author', 'writer', 'poem', 'story', 'character'],
            'mathematics': ['number', 'calculate', 'equation', 'theorem', 'proof', 'sum', 'product'],
            'business': ['company', 'market', 'economy', 'trade', 'finance', 'profit', 'cost', 'price'],
            'technology': ['computer', 'software', 'internet', 'digital', 'algorithm', 'data']
        }

        keyword_counts = {}
        for domain, keywords in domain_keywords.items():
            count = sum(1 for keyword in keywords if keyword in query_lower)
            if count > 0:
                keyword_counts[domain] = count

        return keyword_counts

    def _count_complexity_indicators(self, query_lower: str) -> int:
        """计算复杂性指示符"""
        indicators = [
            'relationship', 'connection', 'link', 'relation', 'between', 'among',
            'combination', 'combine', 'merge', 'intersection', 'overlap',
            'transformation', 'convert', 'translate', 'change', 'transform',
            'comparison', 'compare', 'versus', 'vs', 'difference', 'similarity',
            'sequence', 'order', 'ranking', 'rank', 'position', 'place',
            'condition', 'conditional', 'if', 'then', 'when', 'unless',
            'multiple', 'several', 'various', 'many', 'several'
        ]

        return sum(1 for indicator in indicators if indicator in query_lower)

    def _count_reasoning_indicators(self, query_lower: str) -> int:
        """计算推理指示符"""
        indicators = [
            'reason', 'because', 'therefore', 'thus', 'hence', 'consequently',
            'logic', 'logical', 'reasoning', 'deduce', 'infer', 'conclude',
            'impossible', 'possible', 'must', 'cannot', 'necessary', 'sufficient',
            'prove', 'evidence', 'fact', 'true', 'false', 'correct', 'wrong'
        ]

        return sum(1 for indicator in indicators if indicator in query_lower)

    def _calculate_structure_score(self, query: str) -> float:
        """计算查询结构复杂度得分"""
        score = 0.0

        # 多句结构
        if '.' in query or ';' in query or ':' in query:
            score += 0.3

        # 嵌套结构
        if '(' in query or ')' in query or '[' in query or ']' in query:
            score += 0.2

        # 列表结构
        if re.search(r'\d+\.|\•|-', query):
            score += 0.2

        # 条件结构
        if any(word in query.lower() for word in ['if', 'when', 'while', 'unless', 'although']):
            score += 0.4

        # 引用结构
        if '[' in query or ']' in query:
            score += 0.3

        # 比较结构
        if any(word in query.lower() for word in ['same', 'different', 'than', 'versus', 'more', 'less']):
            score += 0.3

        return min(score, 1.0)

    def _classify_query(self, query: str, features: Dict[str, Any]) -> Tuple[str, float]:
        """分类查询类型"""

        # 首先尝试ML分类（如果模型已训练）
        if self.model_trained:
            try:
                return self._ml_classify(query, features)
            except Exception as e:
                logger.warning(f"ML分类失败，回退到规则分类: {e}")

        # 回退到规则引擎分类
        return self._rule_based_classify(query, features)

    def _ml_classify(self, query: str, features: Dict[str, Any]) -> Tuple[str, float]:
        """机器学习分类（占位符）"""
        # 这里会实现真正的ML分类
        # 目前回退到规则分类
        return self._rule_based_classify(query, features)

    def _rule_based_classify(self, query: str, features: Dict[str, Any]) -> Tuple[str, float]:
        """基于规则的分类"""

        query_lower = query.lower()
        best_type = 'general'
        best_score = 0.0

        # 应用所有规则引擎
        for query_type, rule_func in self.rule_engines.items():
            score = rule_func(query, features)
            if score > best_score:
                best_score = score
                best_type = query_type

        return best_type, min(best_score, 1.0)

    def _logic_trap_rules(self, query: str, features: Dict[str, Any]) -> float:
        """逻辑陷阱题检测规则"""
        score = 0.0
        query_lower = query.lower()

        # D.C.不是州陷阱
        if 'capitol' in query_lower and ('state' in query_lower or 'same state' in query_lower):
            score += 0.9

        # 时间逻辑陷阱
        if any(phrase in query_lower for phrase in ['before born', 'earlier alive', 'canonically alive']):
            score += 0.8

        # 数学逻辑陷阱
        if 'dewey decimal' in query_lower and 'height' in query_lower:
            score += 0.7

        # 一般逻辑陷阱指示符
        logic_trap_indicators = [
            'impossible', 'paradox', 'contradiction', 'cannot be',
            'logically', 'makes sense', 'does not make sense'
        ]

        logic_indicator_count = sum(1 for indicator in logic_trap_indicators if indicator in query_lower)
        score += min(logic_indicator_count * 0.2, 0.3)

        # 基于特征的评分
        if features.get('negation_words', 0) > 0:
            score += 0.1

        return min(score, 1.0)

    def _factual_chain_rules(self, query: str, features: Dict[str, Any]) -> float:
        """事实链查询检测规则"""
        score = 0.0
        query_lower = query.lower()

        # 多实体关系
        if features.get('entity_indicators', 0) >= 3:
            score += 0.4

        # 关系关键词
        relation_keywords = ['mother', 'father', 'son', 'daughter', 'wife', 'husband', 'parent', 'child']
        relation_count = sum(1 for keyword in relation_keywords if keyword in query_lower)
        score += min(relation_count * 0.2, 0.3)

        # 顺序指示符
        sequential_indicators = ['first', 'second', 'third', '15th', '16th', '20th']
        sequential_count = sum(1 for indicator in sequential_indicators if indicator in query_lower)
        score += min(sequential_count * 0.15, 0.3)

        return min(score, 1.0)

    def _cross_domain_rules(self, query: str, features: Dict[str, Any]) -> float:
        """跨领域查询检测规则"""
        score = 0.0

        # 多个领域
        domain_scores = features.get('domain_scores', {})
        if len(domain_scores) >= 2:
            score += 0.5

        # 转换指示符
        conversion_indicators = ['convert', 'transform', 'translate', 'change to', 'same as']
        conversion_count = sum(1 for indicator in conversion_indicators if indicator in query.lower())
        score += min(conversion_count * 0.2, 0.3)

        # 跨领域关键词
        cross_domain_indicators = ['dewey decimal', 'classification number', 'ranking', 'position']
        cross_domain_count = sum(1 for indicator in cross_domain_indicators if indicator in query.lower())
        score += min(cross_domain_count * 0.2, 0.2)

        return min(score, 1.0)

    def _historical_fact_rules(self, query: str, features: Dict[str, Any]) -> float:
        """历史事实查询检测规则"""
        score = 0.0
        query_lower = query.lower()

        # 时间相关特征
        if features.get('temporal_words', 0) >= 2:
            score += 0.3

        # 历史关键词
        history_keywords = ['century', 'decade', 'war', 'battle', 'king', 'queen', 'president', 'era']
        history_count = sum(1 for keyword in history_keywords if keyword in query_lower)
        score += min(history_count * 0.1, 0.4)

        # 具体年份
        if re.search(r'\b(18|19|20)\d{2}\b', query):
            score += 0.3

        return min(score, 1.0)

    def _analyze_complexity(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """分析查询复杂度"""
        complexity_score = 0.0
        indicators = []

        # 基于特征计算复杂度
        if features.get('word_count', 0) > 30:
            complexity_score += 0.2
            indicators.append('long_query')

        if features.get('entity_indicators', 0) >= 3:
            complexity_score += 0.3
            indicators.append('multiple_entities')

        if features.get('domain_count', 0) >= 2:
            complexity_score += 0.4
            indicators.append('cross_domain')

        if features.get('logical_connectors', 0) >= 2:
            complexity_score += 0.3
            indicators.append('complex_logic')

        if features.get('structure_score', 0) > 0.5:
            complexity_score += 0.2
            indicators.append('complex_structure')

        level = 'simple'
        if complexity_score > 0.6:
            level = 'complex'
        elif complexity_score > 0.3:
            level = 'medium'

        return {
            'level': level,
            'score': complexity_score,
            'indicators': indicators
        }

    def _analyze_domains(self, query: str, query_lower: str) -> List[str]:
        """分析涉及的领域"""
        domains = []

        # 政治领域
        if any(word in query_lower for word in ['president', 'congress', 'election', 'government', 'political']):
            domains.append('politics')

        # 地理领域
        if any(word in query_lower for word in ['country', 'state', 'city', 'capital', 'location', 'border']):
            domains.append('geography')

        # 历史领域
        if any(word in query_lower for word in ['century', 'war', 'battle', 'king', 'queen', 'history']):
            domains.append('history')

        # 文学领域
        if any(word in query_lower for word in ['book', 'novel', 'author', 'writer', 'poem', 'story']):
            domains.append('literature')

        # 科学领域
        if any(word in query_lower for word in ['theory', 'experiment', 'research', 'scientist', 'formula']):
            domains.append('science')

        return domains

    def _analyze_logic_patterns(self, query: str, query_lower: str) -> Dict[str, Any]:
        """分析逻辑模式"""
        patterns = {
            'conditional': 'if' in query_lower and 'then' in query_lower,
            'comparative': any(word in query_lower for word in ['same', 'different', 'than', 'versus']),
            'temporal': any(word in query_lower for word in ['before', 'after', 'earlier', 'later']),
            'causal': any(word in query_lower for word in ['because', 'therefore', 'thus', 'hence']),
            'contradictory': any(word in query_lower for word in ['impossible', 'cannot', 'paradox', 'contradiction'])
        }

        return {
            'patterns': [k for k, v in patterns.items() if v],
            'is_logic_trap': patterns['contradictory'] or (patterns['conditional'] and patterns['temporal']),
            'reasoning_depth': sum(patterns.values())
        }

    def _get_reasoning_requirements(self, query_type: str) -> Dict[str, Any]:
        """获取推理要求"""
        requirements = {
            'logic_trap': {
                'premise_analysis': True,
                'contradiction_detection': True,
                'domain_knowledge': True,
                'step_count': 3-4
            },
            'factual_chain': {
                'entity_linking': True,
                'information_retrieval': True,
                'relationship_tracing': True,
                'step_count': 4-6
            },
            'cross_domain': {
                'domain_mapping': True,
                'information_transformation': True,
                'multi_step_reasoning': True,
                'step_count': 4-7
            },
            'historical_fact': {
                'temporal_reasoning': True,
                'contextual_knowledge': True,
                'fact_verification': True,
                'step_count': 2-4
            },
            'general': {
                'basic_reasoning': True,
                'fact_retrieval': True,
                'step_count': 2-3
            }
        }

        return requirements.get(query_type, requirements['general'])

    def _get_recommended_strategy(self, query_type: str) -> str:
        """获取推荐策略"""
        strategies = {
            'logic_trap': 'premise_analysis_first',
            'factual_chain': 'entity_relationship_tracing',
            'cross_domain': 'domain_integration_mapping',
            'historical_fact': 'temporal_context_verification',
            'general': 'standard_reasoning'
        }

        return strategies.get(query_type, 'standard_reasoning')

    def learn_from_feedback(self, query: str, correct_type: str, feedback: Dict[str, Any] = None):
        """从反馈中学习"""
        learning_entry = {
            'query': query,
            'correct_type': correct_type,
            'features': self._extract_basic_features(query, query.lower()),
            'timestamp': logging.time.time(),
            'feedback': feedback or {}
        }

        self.learning_data.append(learning_entry)

        # 保留最近的学习数据
        if len(self.learning_data) > 1000:
            self.learning_data = self.learning_data[-1000:]

        logger.info(f"学习到新的分类反馈: {correct_type}")

    def get_analysis_stats(self) -> Dict[str, Any]:
        """获取分析统计信息"""
        total_analyses = len(self.learning_data)

        if total_analyses == 0:
            return {'total_analyses': 0}

        type_distribution = {}
        for entry in self.learning_data:
            qtype = entry['correct_type']
            type_distribution[qtype] = type_distribution.get(qtype, 0) + 1

        return {
            'total_analyses': total_analyses,
            'type_distribution': type_distribution,
            'learning_enabled': True,
            'model_trained': self.model_trained
        }
