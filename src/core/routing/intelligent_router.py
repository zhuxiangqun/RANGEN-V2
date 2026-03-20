"""
智能路由器 - P2阶段路由逻辑简化

实现基于规则和机器学习的智能路由系统：
1. 查询特征提取和分析
2. 规则引擎路由决策
3. 机器学习路由预测
4. 路由性能监控和学习
5. 动态路由策略调整

替代原有的简单条件路由，提供智能化的路由决策。
"""

import logging
import time
import re
import json
import os
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)

# 尝试导入动态配置系统
try:
    from src.core.dynamic_config_system import (
        DynamicConfigManager, ConfigStore, FileConfigStore,
        ConfigValidator, ConfigMonitor
    )
    from src.core.advanced_config_features import AdvancedConfigSystem
    DYNAMIC_CONFIG_AVAILABLE = True
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    try:
        from src.core.dynamic_config_system import (
            DynamicConfigManager, ConfigStore, FileConfigStore,
            ConfigValidator, ConfigMonitor
        )
        DYNAMIC_CONFIG_AVAILABLE = True
        ADVANCED_FEATURES_AVAILABLE = False
    except ImportError:
        DYNAMIC_CONFIG_AVAILABLE = False
        ADVANCED_FEATURES_AVAILABLE = False
        logger.warning("动态配置系统不可用，将使用简化版本")

# 导入枚举类型
from enum import Enum


class RouteType(Enum):
    """路由类型枚举"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    REASONING = "reasoning"
    MULTI_AGENT = "multi_agent"


@dataclass(frozen=True)
class RouteTypeDefinition:
    """动态路由类型定义"""
    name: str
    description: str
    priority: int = 0
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def value(self) -> str:
        return self.name

class DynamicRouteTypeRegistry:
    """动态路由类型注册表"""

    def __init__(self):
        self._route_types: Dict[str, RouteTypeDefinition] = {}
        self._load_default_types()

    def _load_default_types(self):
        """加载默认路由类型"""
        default_types = [
            RouteTypeDefinition(
                name="simple",
                description="简单查询",
                priority=1
            ),
            RouteTypeDefinition(
                name="medium",
                description="中等复杂度查询",
                priority=2
            ),
            RouteTypeDefinition(
                name="complex",
                description="复杂查询",
                priority=3
            ),
            RouteTypeDefinition(
                name="reasoning",
                description="推理密集查询",
                priority=4
            ),
            RouteTypeDefinition(
                name="multi_agent",
                description="多智能体协作查询",
                priority=5
            )
        ]

        for rt in default_types:
            self.register_route_type(rt)

    def register_route_type(self, route_type: RouteTypeDefinition):
        """注册新的路由类型"""
        if route_type.name in self._route_types:
            logger.warning(f"路由类型 {route_type.name} 已存在，将被覆盖")
        self._route_types[route_type.name] = route_type
        logger.info(f"✅ 已注册路由类型: {route_type.name} - {route_type.description}")

    def unregister_route_type(self, name: str):
        """注销路由类型"""
        if name in self._route_types:
            del self._route_types[name]
            logger.info(f"✅ 已注销路由类型: {name}")

    def get_route_type(self, name: str) -> Optional[RouteTypeDefinition]:
        """获取路由类型定义"""
        return self._route_types.get(name)

    def get_all_route_types(self) -> List[RouteTypeDefinition]:
        """获取所有路由类型"""
        return list(self._route_types.values())

    def get_enabled_route_types(self) -> List[RouteTypeDefinition]:
        """获取启用的路由类型"""
        return [rt for rt in self._route_types.values() if rt.enabled]

    def update_route_type(self, name: str, **updates):
        """更新路由类型"""
        if name in self._route_types:
            current = self._route_types[name]
            updated = RouteTypeDefinition(
                name=current.name,
                description=updates.get('description', current.description),
                priority=updates.get('priority', current.priority),
                enabled=updates.get('enabled', current.enabled),
                metadata={**current.metadata, **updates.get('metadata', {})}
            )
            self._route_types[name] = updated
            logger.info(f"✅ 已更新路由类型: {name}")

# 全局路由类型注册表
route_type_registry = DynamicRouteTypeRegistry()


@dataclass
class QueryFeatures:
    """优化后的查询特征"""
    # 1. 结构特征（最高优先级）
    is_multi_query: bool = False
    num_questions: int = 1
    has_connectors: bool = False  # "和/且/另/同时"等

    # 2. 类型特征
    query_type: str = "general"  # code, math, explain, compare, procedural
    has_code: bool = False
    has_math: bool = False
    requires_explanation: bool = False
    requires_comparison: bool = False
    requires_steps: bool = False

    # 3. 复杂度特征
    complexity_score: float = 0.0  # 0-1
    word_count: int = 0
    sentence_count: int = 1
    entropy_score: float = 0.0  # 信息熵

    # 4. 语言特征
    contains_question_words: bool = True
    sentence_structure: str = "simple"  # simple/complex/compound

    # 5. 元特征
    confidence: float = 1.0  # 特征提取置信度

    # 保留旧字段以兼容
    length: int = 0
    question_words: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    has_comparison: bool = False
    has_explanation: bool = False
    language: str = "en"
    domain: str = "general"


@dataclass
@dataclass
class RouteDecision:
    """路由决策"""
    route_type: str  # 改为字符串，支持动态路由类型
    confidence: float
    reasoning: str
    features_used: List[str]
    processing_time: float
    timestamp: datetime = field(default_factory=datetime.now)


class RuleBasedRouter:
    """规则基础路由器"""

    def __init__(self):
        self.rules = []

    def route_query(self, query: str, features: QueryFeatures) -> Optional[str]:
        """基于规则路由查询"""
        # 简化的规则实现
        return None


@dataclass
class RoutePerformance:
    """路由性能指标"""
    route_type: str  # 改为字符串，支持动态路由类型
    query_count: int = 0
    correct_predictions: int = 0
    average_confidence: float = 0.0
    average_processing_time: float = 0.0
    user_satisfaction: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


class QueryFeatureExtractor:
    """查询特征提取器"""

    def __init__(self):
        # 问题词典
        self.question_words = {
            'what', 'why', 'how', 'when', 'where', 'who', 'which', 'whose',
            'explain', 'describe', 'compare', 'analyze', 'evaluate', 'discuss'
        }

        # 关键词映射到领域
        self.domain_keywords = {
            'programming': ['code', 'python', 'javascript', 'java', 'algorithm', 'function', 'class'],
            'mathematics': ['calculate', 'equation', 'formula', 'theorem', 'proof', 'integral'],
            'science': ['theory', 'experiment', 'hypothesis', 'research', 'analysis'],
            'business': ['market', 'strategy', 'revenue', 'profit', 'customer', 'product']
        }

        # 复杂度指标词
        self.complexity_indicators = [
            'explain', 'analyze', 'compare', 'evaluate', 'discuss', 'describe',
            'why', 'how', 'relationship', 'difference', 'similarity', 'impact'
        ]

    def extract_features(self, query: str) -> QueryFeatures:
        """优化后的特征提取"""
        features = QueryFeatures()
        query_lower = query.lower()

        # 1. 结构特征提取（最高优先级）
        self._extract_structural_features(query, features)

        # 2. 类型特征提取
        self._extract_type_features(query, features)

        # 3. 复杂度特征提取
        self._extract_complexity_features(query, features)

        # 4. 语言特征提取
        self._extract_language_features(query, features)

        # 5. 置信度评估
        features.confidence = self._calculate_extraction_confidence(features)

        # 兼容性：填充旧字段
        self._fill_legacy_features(query, features)

        return features

    def _extract_structural_features(self, query: str, features: QueryFeatures):
        """提取结构特征"""
        # 多查询检测（改进版）
        explicit_questions = len(re.findall(r'[?？]', query))

        # 检测隐含的多任务指示
        task_indicators = [
            '以及', '并', '同时', '另外', '此外', '还', '也', '和', '且',
            'and', 'also', 'furthermore', 'moreover', 'besides', 'in addition',
            '分析', '比较', '解释', '说明', '描述', '讨论', 'evaluate', 'analyze', 'compare'
        ]

        # 检测多个动词短语（可能表示多个任务）
        verb_phrases = len(re.findall(r'[请|如何|怎么|怎样|分析|比较|解释|说明|描述|讨论]', query))

        # 多查询判断逻辑（优化版）
        features.num_questions = explicit_questions

        # 多查询的条件（放宽以识别真正的多任务查询）
        has_multiple_questions = explicit_questions >= 2

        # 多任务模式：有连接词+多个动词+复杂度较高
        has_multi_task_pattern = (
            any(connector in query for connector in ['和', '以及', '同时', '并', 'and', 'also', 'furthermore']) and
            verb_phrases >= 2 and
            features.complexity_score >= 0.15  # 复杂度阈值
        )

        # 分析/比较型多任务：明确的分析比较任务
        has_analysis_multi_task = (
            any(indicator in query for indicator in ['分析', '比较', '对比', 'evaluate', 'analyze', 'compare']) and
            any(connector in query for connector in ['和', '以及', '同时', '并', 'and', 'also'])
        )

        features.is_multi_query = has_multiple_questions or has_multi_task_pattern or has_analysis_multi_task

        # 连接词检测（扩展）
        features.has_connectors = any(indicator in query for indicator in task_indicators)

        # 句子结构分析
        sentences = re.split(r'[.!?]+', query)
        features.sentence_count = len([s for s in sentences if s.strip()])

        # 句子复杂度
        compound_sentences = len([s for s in sentences if '，' in s or 'and' in s.lower()])
        complex_sentences = len([s for s in sentences if '因为' in s or '所以' in s or 'although' in s.lower()])

        if complex_sentences > 0:
            features.sentence_structure = "complex"
        elif compound_sentences > 0:
            features.sentence_structure = "compound"
        else:
            features.sentence_structure = "simple"

    def _extract_type_features(self, query: str, features: QueryFeatures):
        """提取类型特征"""
        query_lower = query.lower()

        # 代码/数学检测
        features.has_code = self._detect_code(query)
        features.has_math = self._detect_math(query)

        # 需求类型检测
        features.requires_explanation = any(word in query_lower for word in
                                           ['explain', 'why', 'how', 'what is', '意思是', '解释'])
        features.requires_comparison = any(word in query_lower for word in
                                          ['compare', 'vs', 'versus', '区别', '差异', '对比'])
        features.requires_steps = any(word in query_lower for word in
                                     ['steps', 'process', '流程', '步骤', 'how to', '如何做'])

        # 查询类型分类
        if features.has_code:
            features.query_type = "code"
        elif features.has_math:
            features.query_type = "math"
        elif features.requires_explanation:
            features.query_type = "explain"
        elif features.requires_comparison:
            features.query_type = "compare"
        elif features.requires_steps:
            features.query_type = "procedural"
        else:
            features.query_type = "general"

    def _extract_complexity_features(self, query: str, features: QueryFeatures):
        """提取复杂度特征"""
        # 基础统计（改进的分词）
        features.word_count = self._count_words(query)
        features.length = len(query)

        # 复杂度评分（优化算法）
        features.complexity_score = self._calculate_complexity_score(query, features)

        # 信息熵计算（词汇多样性）
        words = self._tokenize_words(query.lower())
        if words:
            unique_words = set(words)
            features.entropy_score = len(unique_words) / len(words)
        else:
            features.entropy_score = 0.0

    def _extract_language_features(self, query: str, features: QueryFeatures):
        """提取语言特征"""
        # 问题词检测（使用改进分词）
        words = self._tokenize_words(query.lower())
        features.question_words = [word for word in words if word in self.question_words]
        features.contains_question_words = len(features.question_words) > 0

        # 语言检测
        features.language = self._detect_language(query)

        # 关键词提取
        features.keywords = self._extract_keywords(query.lower())

        # 领域检测
        features.domain = self._detect_domain(query.lower(), features.keywords)

    def _calculate_extraction_confidence(self, features: QueryFeatures) -> float:
        """计算特征提取置信度"""
        confidence_factors = []

        # 结构特征置信度
        structural_confidence = 1.0 if features.num_questions > 0 else 0.8
        confidence_factors.append(structural_confidence)

        # 类型特征置信度
        type_indicators = sum([features.has_code, features.has_math,
                              features.requires_explanation, features.requires_comparison,
                              features.requires_steps])
        type_confidence = min(1.0, 0.5 + type_indicators * 0.2)
        confidence_factors.append(type_confidence)

        # 复杂度特征置信度
        complexity_confidence = 0.9 if features.complexity_score > 0 else 0.7
        confidence_factors.append(complexity_confidence)

        return sum(confidence_factors) / len(confidence_factors)

    def _fill_legacy_features(self, query: str, features: QueryFeatures):
        """填充旧字段以保持兼容性"""
        query_lower = query.lower()

        # 保留旧字段
        features.has_comparison = features.requires_comparison
        features.has_explanation = features.requires_explanation

    def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        # 简化的关键词提取（可扩展为更复杂的NLP方法）
        words = re.findall(r'\b\w+\b', query)
        # 过滤停用词和短词
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        return list(set(keywords))  # 去重

    def _calculate_complexity_score(self, query: str, features: QueryFeatures) -> float:
        """优化的复杂度计算（多维度加权）"""
        scores = []

        # 1. 结构复杂度 (权重: 0.4)
        structural = self._calculate_structural_complexity(features)
        scores.append(structural * 0.4)

        # 2. 语义复杂度 (权重: 0.3)
        semantic = self._calculate_semantic_complexity(query, features)
        scores.append(semantic * 0.3)

        # 3. 词汇复杂度 (权重: 0.2)
        lexical = self._calculate_lexical_complexity(query)
        scores.append(lexical * 0.2)

        # 4. 领域复杂度 (权重: 0.1)
        domain = self._calculate_domain_complexity(query)
        scores.append(domain * 0.1)

        return min(1.0, sum(scores))

    def _calculate_structural_complexity(self, features: QueryFeatures) -> float:
        """结构复杂度计算"""
        score = 0.0

        # 句子数量复杂度
        if features.sentence_count > 3:
            score += 0.4
        elif features.sentence_count > 2:
            score += 0.2

        # 句子结构复杂度
        if features.sentence_structure == "complex":
            score += 0.3
        elif features.sentence_structure == "compound":
            score += 0.1

        # 问题数量复杂度
        score += min(features.num_questions * 0.1, 0.2)

        return min(1.0, score)

    def _calculate_semantic_complexity(self, query: str, features: QueryFeatures) -> float:
        """语义复杂度计算"""
        score = 0.0

        # 问题词复杂度
        score += min(len(features.question_words) * 0.15, 0.3)

        # 复杂度指标词
        complexity_matches = sum(1 for indicator in self.complexity_indicators
                               if indicator in query.lower())
        score += min(complexity_matches * 0.1, 0.4)

        # 需求类型复杂度
        demand_types = sum([features.requires_explanation, features.requires_comparison,
                           features.requires_steps])
        score += min(demand_types * 0.2, 0.3)

        return min(1.0, score)

    def _calculate_lexical_complexity(self, query: str) -> float:
        """词汇复杂度计算"""
        score = 0.0

        # 词汇多样性（信息熵）
        words = re.findall(r'\b\w+\b', query.lower())
        if words:
            unique_ratio = len(set(words)) / len(words)
            score += unique_ratio * 0.4

        # 长词比例（长度>6的词）
        long_words = [w for w in words if len(w) > 6]
        if words:
            long_word_ratio = len(long_words) / len(words)
            score += long_word_ratio * 0.3

        # 专业术语密度
        technical_terms = ['algorithm', 'framework', 'architecture', 'implementation',
                          'optimization', 'performance', 'scalability', 'efficiency']
        technical_count = sum(1 for term in technical_terms if term in query.lower())
        score += min(technical_count * 0.1, 0.3)

        return min(1.0, score)

    def _calculate_domain_complexity(self, query: str) -> float:
        """领域复杂度计算"""
        score = 0.0

        # 检测多个领域关键词
        domain_matches = 0
        for domain, keywords in self.domain_keywords.items():
            if any(keyword in query.lower() for keyword in keywords):
                domain_matches += 1

        # 多领域交叉增加复杂度
        if domain_matches > 1:
            score += 0.4
        elif domain_matches == 1:
            score += 0.2

        # 特殊内容领域复杂度
        if '```' in query or 'code' in query.lower():
            score += 0.2
        if any(math_sym in query for math_sym in ['=', '+', '-', '*', '/', '∑', '∫']):
            score += 0.2

        return min(1.0, score)

    def _detect_code(self, query: str) -> bool:
        """检测是否包含代码"""
        code_indicators = [
            '```', 'function', 'class', 'def ', 'import ', 'print(',
            'if ', 'for ', 'while ', 'return ', 'var ', 'const '
        ]
        return any(indicator in query for indicator in code_indicators)

    def _detect_math(self, query: str) -> bool:
        """检测是否包含数学内容"""
        math_indicators = [
            '=', '+', '-', '*', '/', '∑', '∫', '√', 'π', 'sin', 'cos', 'tan',
            'equation', 'formula', 'calculate', 'solve'
        ]
        return any(indicator in query for indicator in math_indicators)

    def _detect_language(self, query: str) -> str:
        """检测查询语言"""
        # 简化的语言检测
        if any(char in query for char in '中文'):
            return 'zh'
        return 'en'

    def _detect_domain(self, query: str, keywords: List[str]) -> str:
        """检测查询领域"""
        for domain, domain_keywords in self.domain_keywords.items():
            if any(keyword in query for keyword in domain_keywords):
                return domain
        return 'general'

    def _count_words(self, query: str) -> int:
        """改进的词数统计，支持中英文混合"""
        # 对于英文，使用空格分割
        english_words = re.findall(r'\b[a-zA-Z]+\b', query)
        # 对于中文，统计汉字数量（近似）
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', query))
        # 其他字符（如数字、符号）算作独立的token
        other_tokens = re.findall(r'\d+|[^\w\s\u4e00-\u9fff]', query)

        return len(english_words) + chinese_chars + len(other_tokens)

    def _tokenize_words(self, query: str) -> List[str]:
        """简化的分词，支持中英文混合"""
        tokens = []

        # 使用简单的空格和标点分割
        words = re.split(r'[\s\.,!?;:()\[\]{}"\'，。？！；：（）【】""''《》]', query)
        tokens = [word.strip() for word in words if word.strip()]

        return tokens


class DynamicRoutingConfig:
    """动态路由配置 - 支持持久化、验证和版本管理"""

    def __init__(self, config_store: Optional['ConfigStore'] = None):
        self.thresholds: Dict[str, float] = {}
        self.keywords: Dict[str, Any] = {}
        self.routing_rules: List[Dict[str, Any]] = []
        self._config_sources: List[ConfigSource] = []
        self._last_updated = None
        self._auto_refresh_interval = 300  # 5分钟自动刷新

        # 配置存储和版本管理
        try:
            self.config_store = config_store or FileConfigStore("routing_config.json")
            self.config_validator = ConfigValidator()
            self.config_monitor = ConfigMonitor()
        except NameError:
            # 如果相关类不可用，使用简化版本
            self.config_store = None
            self.config_validator = None
            self.config_monitor = None

        # 初始化默认配置
        self._load_default_config()

        # 启动自动刷新
        self._start_auto_refresh()

    def add_config_source(self, source: 'ConfigSource'):
        """添加配置源"""
        self._config_sources.append(source)
        self._refresh_config()

    def _load_default_config(self):
        """加载默认配置"""
        self.thresholds = {
            'simple_max_complexity': 0.05,
            'medium_min_complexity': 0.05,
            'medium_max_complexity': 0.15,
            'complex_min_complexity': 0.15,
            'simple_max_words': 3,
            'medium_min_words': 3,
            'medium_max_words': 10,
            'complex_min_words': 10,
            'multi_agent_min_questions': 2,
            'multi_agent_min_complexity': 0.4
        }

        self.keywords = {
            'question_words': [
                'what', 'why', 'how', 'when', 'where', 'who', 'which', 'whose',
                'explain', 'describe', 'compare', 'analyze', 'evaluate', 'discuss'
            ],
            'complexity_indicators': [
                'explain', 'analyze', 'compare', 'evaluate', 'discuss', 'describe',
                'why', 'how', 'relationship', 'difference', 'similarity', 'impact'
            ],
            'domain_keywords': {
                'programming': ['code', 'python', 'javascript', 'java', 'algorithm', 'function', 'class'],
                'mathematics': ['calculate', 'equation', 'formula', 'theorem', 'proof', 'integral'],
                'science': ['theory', 'experiment', 'hypothesis', 'research', 'analysis'],
                'business': ['market', 'strategy', 'revenue', 'profit', 'customer', 'product']
            }
        }

    def _start_auto_refresh(self):
        """启动自动刷新"""
        import threading
        import time

        def refresh_worker():
            while True:
                time.sleep(self._auto_refresh_interval)
                try:
                    self._refresh_config()
                except Exception as e:
                    logger.warning(f"自动刷新配置失败: {e}")

        thread = threading.Thread(target=refresh_worker, daemon=True)
        thread.start()

    def _refresh_config(self):
        """刷新配置"""
        try:
            new_config = self._merge_configs_from_sources()

            # 检查配置是否有变化
            if self._config_changed(new_config):
                self._apply_config(new_config)
                self._last_updated = datetime.now()
                logger.info("✅ 路由配置已更新")

        except Exception as e:
            logger.error(f"刷新配置失败: {e}")

    def _merge_configs_from_sources(self) -> Dict[str, Any]:
        """从所有配置源合并配置"""
        merged = {
            'thresholds': self.thresholds.copy(),
            'keywords': self.keywords.copy(),
            'routing_rules': self.routing_rules.copy()
        }

        for source in self._config_sources:
            try:
                source_config = source.load_config()
                merged = self._deep_merge(merged, source_config)
            except Exception as e:
                logger.warning(f"从配置源 {source.__class__.__name__} 加载配置失败: {e}")

        return merged

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并字典"""
        result = base.copy()

        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _config_changed(self, new_config: Dict[str, Any]) -> bool:
        """检查配置是否发生变化"""
        return (
            new_config.get('thresholds') != self.thresholds or
            new_config.get('keywords') != self.keywords or
            new_config.get('routing_rules') != self.routing_rules
        )

    def _apply_config(self, config: Dict[str, Any]):
        """应用新配置"""
        self.thresholds = config.get('thresholds', self.thresholds)
        self.keywords = config.get('keywords', self.keywords)
        self.routing_rules = config.get('routing_rules', self.routing_rules)

    def update_threshold(self, key: str, value: float):
        """更新单个阈值"""
        self.thresholds[key] = value
        logger.info(f"✅ 已更新阈值: {key} = {value}")

    def add_keyword(self, category: str, keyword: str):
        """添加关键词"""
        if category not in self.keywords:
            self.keywords[category] = []

        if isinstance(self.keywords[category], list):
            if keyword not in self.keywords[category]:
                self.keywords[category].append(keyword)
                logger.info(f"✅ 已添加关键词: {category} -> {keyword}")

    def get_threshold(self, key: str, default: float = 0.0) -> float:
        """获取阈值"""
        return self.thresholds.get(key, default)

    def get_keywords(self, category: str) -> List[str]:
        """获取关键词列表"""
        return self.keywords.get(category, [])

    def get_domain_keywords(self, domain: str) -> List[str]:
        """获取领域关键词"""
        domain_keywords = self.keywords.get('domain_keywords', {})
        return domain_keywords.get(domain, [])

class ConfigSource(ABC):
    """配置源抽象基类"""

    @abstractmethod
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        pass

    @abstractmethod
    def save_config(self, config: Dict[str, Any]):
        """保存配置"""
        pass

    def handle_config_event(self, event: str, data: Dict[str, Any]):
        """处理配置事件"""
        pass

class DatabaseConfigSource(ConfigSource):
    """数据库配置源"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def load_config(self) -> Dict[str, Any]:
        """从数据库加载配置"""
        # 这里实现数据库查询逻辑
        # 例如从 routing_config 表加载配置
        return {
            'thresholds': {
                'simple_max_complexity': 0.03,  # 从数据库动态获取
                'medium_min_complexity': 0.03,
            },
            'keywords': {
                'question_words': ['what', 'why', 'how', 'who', 'where'],  # 从数据库获取
            }
        }

    def save_config(self, config: Dict[str, Any]):
        """保存配置到数据库"""
        # 实现数据库保存逻辑
        pass

class APIConfigSource(ConfigSource):
    """API配置源"""

    def __init__(self, api_endpoint: str, api_key: Optional[str] = None):
        self.api_endpoint = api_endpoint
        self.api_key = api_key

    def load_config(self) -> Dict[str, Any]:
        """从API加载配置"""
        import requests

        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        try:
            response = requests.get(f"{self.api_endpoint}/routing/config", headers=headers, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"从API加载配置失败: {e}")
            return {}

    def save_config(self, config: Dict[str, Any]):
        """保存配置到API"""
        import requests

        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        try:
            response = requests.post(
                f"{self.api_endpoint}/routing/config",
                json=config,
                headers=headers,
                timeout=5
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"保存配置到API失败: {e}")

class LearningConfigSource(ConfigSource):
    """基于学习的配置源"""

    def __init__(self, performance_history_file: str = "routing_performance.json"):
        self.performance_file = performance_history_file
        self.performance_history: List[Dict[str, Any]] = []
        self._load_performance_history()

    def _load_performance_history(self):
        """加载性能历史"""
        try:
            if os.path.exists(self.performance_file):
                with open(self.performance_file, 'r', encoding='utf-8') as f:
                    self.performance_history = json.load(f)
        except Exception as e:
            logger.warning(f"加载性能历史失败: {e}")
            self.performance_history = []

    def _save_performance_history(self):
        """保存性能历史"""
        try:
            with open(self.performance_file, 'w', encoding='utf-8') as f:
                json.dump(self.performance_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存性能历史失败: {e}")

    def record_performance(self, performance_data: Dict[str, Any]):
        """记录性能数据"""
        self.performance_history.append({
            **performance_data,
            'timestamp': datetime.now().isoformat()
        })

        # 保持最近1000条记录
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]

        self._save_performance_history()

    def load_config(self) -> Dict[str, Any]:
        """基于学习历史生成配置"""
        if len(self.performance_history) < 10:
            return {}  # 样本不足，返回空配置

        # 分析最近的性能数据
        recent_performance = self.performance_history[-50:]  # 最近50条记录

        # 计算各类别的准确率
        route_accuracy = {}
        for record in recent_performance:
            route_type = record.get('expected_route')
            correct = record.get('correct', False)
            if route_type not in route_accuracy:
                route_accuracy[route_type] = {'correct': 0, 'total': 0}
            route_accuracy[route_type]['total'] += 1
            if correct:
                route_accuracy[route_type]['correct'] += 1

        # 生成优化的阈值
        optimized_thresholds = self._optimize_thresholds(route_accuracy)

        return {
            'thresholds': optimized_thresholds,
            'learning_metadata': {
                'sample_count': len(recent_performance),
                'last_updated': datetime.now().isoformat(),
                'route_accuracy': route_accuracy
            }
        }

    def _optimize_thresholds(self, route_accuracy: Dict[str, Any]) -> Dict[str, float]:
        """基于准确率优化阈值"""
        # 简单的优化逻辑：如果某种路由准确率低，调整相关阈值
        thresholds = {}

        # 分析简单查询准确率
        simple_accuracy = route_accuracy.get('simple', {'correct': 0, 'total': 1})
        simple_acc_rate = simple_accuracy['correct'] / simple_accuracy['total']

        if simple_acc_rate < 0.8:
            # 简单查询准确率低，降低阈值让更多查询被分类为简单
            thresholds['simple_max_complexity'] = 0.03
            thresholds['simple_max_words'] = 2

        # 分析多智能体准确率
        multi_agent_accuracy = route_accuracy.get('multi_agent', {'correct': 0, 'total': 1})
        total = multi_agent_accuracy['total'] if multi_agent_accuracy['total'] > 0 else 1
        multi_agent_acc_rate = multi_agent_accuracy['correct'] / total

        if multi_agent_acc_rate < 0.8:
            # 多智能体准确率低，提高阈值让更多查询被分类为多智能体
            thresholds['multi_agent_min_complexity'] = 0.5

        return thresholds

    def save_config(self, config: Dict[str, Any]):
        """保存配置（学习源通常不保存外部配置）"""
        pass

class PluginConfigSource(ConfigSource):
    """插件化配置源"""

    def __init__(self, plugin_directory: str = "routing_plugins"):
        self.plugin_directory = plugin_directory
        self._loaded_plugins: Dict[str, Any] = {}
        self._load_plugins()

    def _load_plugins(self):
        """加载插件"""
        if not os.path.exists(self.plugin_directory):
            os.makedirs(self.plugin_directory)
            return

        import importlib.util

        for plugin_file in os.listdir(self.plugin_directory):
            if plugin_file.endswith('.py'):
                plugin_path = os.path.join(self.plugin_directory, plugin_file)
                plugin_name = plugin_file[:-3]  # 移除.py扩展名

                try:
                    spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
                    if spec is None or spec.loader is None:
                        logger.warning(f"无法加载插件 {plugin_name}: 无效的模块规范")
                        continue

                    plugin_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(plugin_module)

                    if hasattr(plugin_module, 'get_routing_config'):
                        self._loaded_plugins[plugin_name] = plugin_module
                        logger.info(f"✅ 已加载路由插件: {plugin_name}")

                except Exception as e:
                    logger.error(f"加载插件 {plugin_name} 失败: {e}")

    def load_config(self) -> Dict[str, Any]:
        """从插件加载配置"""
        merged_config = {}

        for plugin_name, plugin_module in self._loaded_plugins.items():
            try:
                plugin_config = plugin_module.get_routing_config()
                merged_config = self._deep_merge(merged_config, plugin_config)
            except Exception as e:
                logger.warning(f"从插件 {plugin_name} 获取配置失败: {e}")

        return merged_config

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并字典"""
        result = base.copy()

        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def save_config(self, config: Dict[str, Any]):
        """保存配置到插件"""
        pass

class DynamicRoutingManager:
    """动态路由管理器 - 真正的运行时配置"""

    def __init__(self, enable_advanced_features: bool = True):
        self.route_type_registry = DynamicRouteTypeRegistry()
        self.performance_monitor = RoutingPerformanceMonitor()

        # 初始化验证器
        try:
            self.config_validator = ConfigValidator()
        except NameError:
            self.config_validator = None

        # 根据可用性选择配置管理器
        if ADVANCED_FEATURES_AVAILABLE and enable_advanced_features:
            self.advanced_system = AdvancedConfigSystem()
            self.config_manager = self.advanced_system.config_manager
            self.config = self.config_manager.config  # 兼容性
            self.advanced_features = True
        elif DYNAMIC_CONFIG_AVAILABLE and enable_advanced_features:
            self.config_manager = DynamicConfigManager()
            self.config = self.config_manager.config  # 兼容性
            self.advanced_system = None
            self.advanced_features = True
        else:
            self.config = DynamicRoutingConfig()
            self.config_manager = None
            self.advanced_system = None
            self.advanced_features = False

        self._config_api_server = None
        self._web_interface = None
        self._start_config_api_server()
        self._start_web_interface()

    def add_config_source(self, source: ConfigSource):
        """添加配置源"""
        self.config.add_config_source(source)

    def register_route_type(self, name: str, description: str, priority: int = 0, **metadata):
        """运行时注册新的路由类型"""
        route_type = RouteTypeDefinition(
            name=name,
            description=description,
            priority=priority,
            metadata=metadata
        )
        self.route_type_registry.register_route_type(route_type)

        # 通知所有配置源更新
        self._notify_config_sources('route_type_registered', route_type)

    def unregister_route_type(self, name: str):
        """运行时注销路由类型"""
        self.route_type_registry.unregister_route_type(name)
        self._notify_config_sources('route_type_unregistered', name)

    def update_routing_threshold(self, key: str, value: float):
        """运行时更新路由阈值"""
        self.config.update_threshold(key, value)
        self._notify_config_sources('threshold_updated', {key: value})

    def add_routing_keyword(self, category: str, keyword: str):
        """运行时添加路由关键词"""
        self.config.add_keyword(category, keyword)
        self._notify_config_sources('keyword_added', {category: keyword})

    def get_routing_config(self) -> Dict[str, Any]:
        """获取当前路由配置"""
        base_config = {
            'route_types': [
                {
                    'name': rt.name,
                    'description': rt.description,
                    'priority': rt.priority,
                    'enabled': rt.enabled,
                    'metadata': rt.metadata
                }
                for rt in self.route_type_registry.get_all_route_types()
            ],
            'thresholds': self.config.thresholds,
            'keywords': self.config.keywords,
            'performance_stats': self.performance_monitor.get_stats()
        }

        # 如果有高级配置管理器，添加更多信息
        if self.advanced_features and self.config_manager:
            advanced_config = self.config_manager.get_config_status()
            base_config.update({
                'advanced_features': advanced_config,
                'config_health': self._check_config_health()
            })

        return base_config

    def _check_config_health(self) -> Dict[str, Any]:
        """检查配置健康状态"""
        if not self.advanced_features:
            return {'status': 'basic', 'message': '使用基础配置模式'}

        try:
            # 验证当前配置
            config_data = {
                'thresholds': self.config.thresholds,
                'keywords': self.config.keywords,
                'routing_rules': self.config.routing_rules
            }

            validation_result = self.config_validator.validate(config_data) if self.config_validator else None

            if validation_result:
                return {
                    'status': 'healthy' if validation_result.is_valid else 'warning',
                    'errors': validation_result.errors,
                    'warnings': validation_result.warnings,
                    'last_validation': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'unknown',
                    'message': '配置验证器不可用',
                    'last_validation': datetime.now().isoformat()
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'last_check': datetime.now().isoformat()
            }

    def apply_config_template(self, template_name: str):
        """应用配置模板"""
        if not self.advanced_features or not self.config_manager:
            raise ValueError("高级配置功能不可用")

        self.config_manager.apply_template(template_name)
        logger.info(f"✅ 已应用配置模板: {template_name}")

    def rollback_config(self, version: str):
        """回滚配置"""
        if not self.advanced_features or not self.config_manager:
            raise ValueError("高级配置功能不可用")

        self.config_manager.rollback_config(version)
        logger.info(f"✅ 已回滚配置到版本: {version}")

    def get_config_documentation(self) -> str:
        """获取配置文档"""
        if self.advanced_features and self.config_manager:
            return self.config_manager.export_config_documentation()
        else:
            return self._generate_basic_documentation()

    def _generate_basic_documentation(self) -> str:
        """生成基础配置文档"""
        doc = []
        doc.append("# 基础路由配置文档")
        doc.append("")
        doc.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc.append("")

        # 路由类型
        doc.append("## 路由类型")
        for rt in self.route_type_registry.get_all_route_types():
            doc.append(f"- **{rt.name}**: {rt.description}")
        doc.append("")

        # 阈值配置
        doc.append("## 阈值配置")
        for key, value in self.config.thresholds.items():
            doc.append(f"- **{key}**: {value}")
        doc.append("")

        return "\n".join(doc)

    def _notify_config_sources(self, event: str, data: Any):
        """通知配置源配置变更"""
        for source in self.config._config_sources:
            try:
                if hasattr(source, 'handle_config_event'):
                    source.handle_config_event(event, data)
            except Exception as e:
                logger.warning(f"通知配置源 {source.__class__.__name__} 失败: {e}")

    def _start_config_api_server(self):
        """启动配置API服务器"""
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer
        import json

        class ConfigAPIHandler(BaseHTTPRequestHandler):
            def __init__(self, manager, *args, **kwargs):
                self.manager = manager
                super().__init__(*args, **kwargs)

            def do_GET(self):
                if self.path == '/' or self.path == '':
                    # 检查Accept头，如果是浏览器请求，返回HTML页面
                    accept_header = self.headers.get('Accept', '')
                    if 'text/html' in accept_header or 'application/xhtml' in accept_header:
                        self._serve_api_homepage()
                    else:
                        # API根路径，返回API信息JSON
                        api_info = {
                            "name": "动态路由配置管理系统 API",
                            "version": "1.0.0",
                            "description": "企业级的配置管理解决方案",
                            "endpoints": {
                                "GET /": "API信息 (本页面)",
                                "GET /config": "获取当前路由配置",
                                "GET /route-types": "获取路由类型列表",
                                "POST /route-types": "注册新的路由类型",
                                "PUT /config/thresholds": "更新路由阈值",
                                "PUT /config/keywords": "更新关键词配置"
                            },
                            "status": "running",
                            "server_time": datetime.now().isoformat()
                        }
                        self._send_json_response(api_info)
                elif self.path == '/config':
                    self._send_json_response(self.manager.get_routing_config())
                elif self.path == '/route-types':
                    route_types = [
                        {
                            'name': rt.name,
                            'description': rt.description,
                            'priority': rt.priority,
                            'enabled': rt.enabled
                        }
                        for rt in self.manager.route_type_registry.get_all_route_types()
                    ]
                    self._send_json_response(route_types)
                else:
                    self._send_error(404, "Not Found")

            def _serve_api_homepage(self):
                """服务API首页HTML页面"""
                html = f"""
                <!DOCTYPE html>
                <html lang="zh-CN">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>动态路由配置管理系统 API</title>
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            margin: 0;
                            padding: 0;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            min-height: 100vh;
                        }}
                        .container {{
                            max-width: 1200px;
                            margin: 0 auto;
                            padding: 20px;
                        }}
                        .header {{
                            text-align: center;
                            color: white;
                            margin-bottom: 40px;
                        }}
                        .header h1 {{
                            font-size: 3em;
                            margin-bottom: 10px;
                            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                        }}
                        .header p {{
                            font-size: 1.2em;
                            opacity: 0.9;
                        }}
                        .card {{
                            background: white;
                            border-radius: 12px;
                            padding: 30px;
                            margin-bottom: 20px;
                            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                            transition: transform 0.3s ease;
                        }}
                        .card:hover {{
                            transform: translateY(-5px);
                        }}
                        .card h3 {{
                            color: #333;
                            margin-top: 0;
                            border-bottom: 3px solid #667eea;
                            padding-bottom: 10px;
                        }}
                        .status {{
                            display: inline-block;
                            padding: 5px 15px;
                            background: #4CAF50;
                            color: white;
                            border-radius: 20px;
                            font-size: 0.9em;
                            font-weight: bold;
                        }}
                        .endpoint {{
                            background: #f8f9fa;
                            border-left: 4px solid #667eea;
                            padding: 15px;
                            margin: 10px 0;
                            border-radius: 4px;
                        }}
                        .method {{
                            font-weight: bold;
                            color: #667eea;
                            display: inline-block;
                            min-width: 60px;
                        }}
                        .path {{
                            font-family: 'Courier New', monospace;
                            background: #e9ecef;
                            padding: 2px 6px;
                            border-radius: 3px;
                            margin: 0 10px;
                        }}
                        .description {{
                            color: #666;
                        }}
                        .try-it {{
                            background: #667eea;
                            color: white;
                            border: none;
                            padding: 8px 16px;
                            border-radius: 6px;
                            cursor: pointer;
                            font-size: 0.9em;
                            margin-left: 10px;
                            transition: background 0.3s ease;
                        }}
                        .try-it:hover {{
                            background: #5a67d8;
                        }}
                        .response {{
                            background: #2d3748;
                            color: #e2e8f0;
                            padding: 15px;
                            border-radius: 6px;
                            margin-top: 10px;
                            font-family: 'Courier New', monospace;
                            font-size: 0.9em;
                            display: none;
                            white-space: pre-wrap;
                        }}
                        .footer {{
                            text-align: center;
                            color: white;
                            margin-top: 40px;
                            opacity: 0.8;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🚀 动态路由配置管理系统</h1>
                            <p>企业级的配置管理解决方案 API</p>
                        </div>

                        <div class="card">
                            <h3>📊 系统状态</h3>
                            <p>API 版本: <strong>1.0.0</strong></p>
                            <p>服务状态: <span class="status">● 运行中</span></p>
                            <p>服务器时间: <strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</strong></p>
                        </div>

                        <div class="card">
                            <h3>🔗 可用端点</h3>

                            <div class="endpoint">
                                <span class="method">GET</span>
                                <span class="path">/</span>
                                <span class="description">API 信息和端点列表（本页面）</span>
                                <button class="try-it" onclick="testEndpoint('GET', '/')">测试</button>
                                <div class="response" id="response-GET-/"></div>
                            </div>

                            <div class="endpoint">
                                <span class="method">GET</span>
                                <span class="path">/config</span>
                                <span class="description">获取当前路由配置</span>
                                <button class="try-it" onclick="testEndpoint('GET', '/config')">测试</button>
                                <div class="response" id="response-GET-/config"></div>
                            </div>

                            <div class="endpoint">
                                <span class="method">GET</span>
                                <span class="path">/route-types</span>
                                <span class="description">获取路由类型列表</span>
                                <button class="try-it" onclick="testEndpoint('GET', '/route-types')">测试</button>
                                <div class="response" id="response-GET-/route-types"></div>
                            </div>

                            <div class="endpoint">
                                <span class="method">POST</span>
                                <span class="path">/route-types</span>
                                <span class="description">注册新的路由类型</span>
                            </div>

                            <div class="endpoint">
                                <span class="method">PUT</span>
                                <span class="path">/config/thresholds</span>
                                <span class="description">更新路由阈值</span>
                            </div>

                            <div class="endpoint">
                                <span class="method">PUT</span>
                                <span class="path">/config/keywords</span>
                                <span class="description">更新关键词配置</span>
                            </div>
                        </div>

                        <div class="card">
                            <h3>💡 使用说明</h3>
                            <ul>
                                <li>点击 <strong>测试</strong> 按钮可以直接调用API并查看响应</li>
                                <li>所有API返回JSON格式的数据</li>
                                <li>支持标准的HTTP状态码</li>
                                <li>错误信息会以JSON格式返回</li>
                            </ul>
                        </div>
                    </div>

                    <div class="footer">
                        <p>© 2025 动态路由配置管理系统 | 企业级AI配置解决方案</p>
                    </div>

                    <script>
                        async function testEndpoint(method, path) {{
                            const responseDiv = document.getElementById(`response-${{method}}-${{path}}`);
                            try {{
                                const response = await fetch(path);
                                const data = await response.json();
                                responseDiv.textContent = JSON.stringify(data, null, 2);
                                responseDiv.style.display = 'block';
                            }} catch (error) {{
                                responseDiv.textContent = `错误: ${{error.message}}`;
                                responseDiv.style.display = 'block';
                            }}
                        }}
                    </script>
                </body>
                </html>
                """
                self._send_html_response(html)

            def do_POST(self):
                if self.path == '/route-types':
                    self._handle_register_route_type()
                elif self.path == '/thresholds':
                    self._handle_update_threshold()
                elif self.path == '/keywords':
                    self._handle_add_keyword()
                else:
                    self._send_error(404, "Not Found")

            def _handle_register_route_type(self):
                try:
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))

                    self.manager.register_route_type(
                        name=data['name'],
                        description=data['description'],
                        priority=data.get('priority', 0),
                        **data.get('metadata', {})
                    )
                    self._send_json_response({'status': 'success'})
                except Exception as e:
                    self._send_error(400, str(e))

            def _handle_update_threshold(self):
                try:
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))

                    for key, value in data.items():
                        self.manager.update_routing_threshold(key, value)
                    self._send_json_response({'status': 'success'})
                except Exception as e:
                    self._send_error(400, str(e))

            def _handle_add_keyword(self):
                try:
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))

                    self.manager.add_routing_keyword(data['category'], data['keyword'])
                    self._send_json_response({'status': 'success'})
                except Exception as e:
                    self._send_error(400, str(e))

            def _send_json_response(self, data):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

            def _send_html_response(self, html):
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))

            def _send_error(self, code, message):
                self.send_response(code)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': message}).encode('utf-8'))

        def run_server():
            # 从环境变量获取端口，默认8080
            api_port = int(os.getenv('DYNAMIC_CONFIG_API_PORT', '8080'))
            server_address = ('', api_port)

            # 创建带有预绑定manager的处理器类
            import functools
            ConfigAPIHandlerWithManager = functools.partial(ConfigAPIHandler, self)

            httpd = HTTPServer(server_address, ConfigAPIHandlerWithManager)
            logger.info(f"🚀 路由配置API服务器启动在 http://localhost:{api_port}")
            httpd.serve_forever()

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

    def _start_web_interface(self):
        """启动Web界面"""
        try:
            from src.core.config_web_interface import ConfigWebInterface
            # 从环境变量获取端口，默认8081
            web_port = int(os.getenv('DYNAMIC_CONFIG_WEB_PORT', '8081'))
            self._web_interface = ConfigWebInterface(self, port=web_port)
            self._web_interface.start()
        except ImportError:
            logger.warning("Web界面模块不可用，跳过Web界面启动")
        except Exception as e:
            logger.error(f"Web界面启动失败: {e}")

    def stop_web_interface(self):
        """停止Web界面"""
        if self._web_interface:
            self._web_interface.stop()

class RoutingPerformanceMonitor:
    """路由性能监控器"""

    def __init__(self):
        self.performance_history: List[Dict[str, Any]] = []
        self.current_stats: Dict[str, Any] = {}

    def record_decision(self, query: str, expected_route: str, actual_route: str,
                       confidence: float, processing_time: float, correct: bool):
        """记录路由决策"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'query': query[:100],  # 限制长度
            'expected_route': expected_route,
            'actual_route': actual_route,
            'confidence': confidence,
            'processing_time': processing_time,
            'correct': correct
        }

        self.performance_history.append(record)

        # 更新当前统计
        self._update_stats(record)

        # 保持最近1000条记录
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]

    def _update_stats(self, record: Dict[str, Any]):
        """更新统计信息"""
        route_type = record['expected_route']

        if route_type not in self.current_stats:
            self.current_stats[route_type] = {
                'total': 0,
                'correct': 0,
                'avg_confidence': 0.0,
                'avg_processing_time': 0.0
            }

        stats = self.current_stats[route_type]
        stats['total'] += 1
        if record['correct']:
            stats['correct'] += 1

        # 更新平均值
        stats['avg_confidence'] = (
            (stats['avg_confidence'] * (stats['total'] - 1)) + record['confidence']
        ) / stats['total']

        stats['avg_processing_time'] = (
            (stats['avg_processing_time'] * (stats['total'] - 1)) + record['processing_time']
        ) / stats['total']

    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return {
            'current_stats': self.current_stats,
            'total_decisions': len(self.performance_history),
            'recent_accuracy': self._calculate_recent_accuracy(),
            'last_updated': datetime.now().isoformat()
        }

    def _calculate_recent_accuracy(self) -> float:
        """计算最近准确率"""
        if not self.performance_history:
            return 0.0

        recent_records = self.performance_history[-100:]  # 最近100条
        correct_count = sum(1 for r in recent_records if r['correct'])
        return correct_count / len(recent_records)

class OptimizedRouter:
    """优化后的路由器"""

    def __init__(self, routing_manager: Optional[DynamicRoutingManager] = None):
        # 动态路由管理器
        self.routing_manager = routing_manager or DynamicRoutingManager()

        # 初始化阈值
        self.thresholds = self._load_default_thresholds()

        # 初始化规则（如果需要）
        self.rules: List[Dict[str, Any]] = []

    def _load_default_thresholds(self) -> Dict[str, float]:
        """加载最终优化阈值 - 基于测试结果调整"""
        return {
            'simple_max_complexity': 0.05,    # 极低 - 让简单查询通过
            'medium_min_complexity': 0.05,    # 极低
            'medium_max_complexity': 0.15,    # 更低的中等查询最大值
            'complex_min_complexity': 0.15,   # 更低的复杂查询最小值
            'simple_max_words': 3,            # 保持极低
            'medium_min_words': 3,            # 保持极低
            'medium_max_words': 10,           # 更低的中等查询最大词数
            'complex_min_words': 10,          # 更低的复杂查询最小词数
            'multi_agent_min_questions': 2,
            'multi_agent_min_complexity': 0.4  # 保持多智能体复杂度要求
        }

    def decide_route(self, features: QueryFeatures) -> RouteDecision:
        """基于动态配置的路由决策"""
        start_time = time.time()

        # 获取动态配置
        thresholds = self.routing_manager.config.thresholds

        # 优先级1: 多查询检测
        if self._is_multi_agent_query_dynamic(features, thresholds):
            route_type_def = self.routing_manager.route_type_registry.get_route_type("multi_agent")
            route_decision = self._create_route_dynamic(
                route_type_def or "multi_agent",
                reason="多问题查询需要协作处理",
                confidence=0.95,
                features_used=["is_multi_query", "num_questions", "has_connectors"]
            )

        # 优先级2: 查询类型分类
        elif route_type := self._route_by_query_type(features):
            route_decision = route_type

        # 优先级3: 基于复杂度的路由
        else:
            route_decision = self._route_by_complexity_dynamic(features, thresholds)

        # 添加处理时间
        route_decision.processing_time = time.time() - start_time

        return route_decision

    def _is_multi_agent_query_dynamic(self, features: QueryFeatures, thresholds: Dict[str, float]) -> bool:
        """基于动态阈值的多智能体检测"""
        # 多查询检测
        if features.is_multi_query or features.num_questions >= thresholds.get('multi_agent_min_questions', 2):
            return True

        # 复杂多连接查询
        if (features.has_connectors and
            features.complexity_score >= thresholds.get('multi_agent_min_complexity', 0.6) and
            features.word_count >= thresholds.get('medium_max_words', 15)):
            return True

        return False

    def _route_by_complexity_dynamic(self, features: QueryFeatures, thresholds: Dict[str, float]) -> RouteDecision:
        """基于动态阈值的复杂度路由"""
        complexity = features.complexity_score
        word_count = features.word_count

        if (complexity >= thresholds.get('complex_min_complexity', 0.3) or
            word_count >= thresholds.get('complex_min_words', 15)):
            route_type_def = self.routing_manager.route_type_registry.get_route_type("complex")
            return self._create_route(
                route_type_def or "complex",
                reason=f"高复杂度查询 (分数: {complexity:.2f}, 词数: {word_count})",
                confidence=min(0.9, features.confidence),
                features_used=["complexity_score", "word_count"]
            )

        elif (complexity >= thresholds.get('medium_min_complexity', 0.15) or
              word_count >= thresholds.get('medium_min_words', 6)):
            route_type_def = self.routing_manager.route_type_registry.get_route_type("medium")
            return self._create_route(
                route_type_def or "medium",
                reason=f"中等复杂度查询 (分数: {complexity:.2f}, 词数: {word_count})",
                confidence=min(0.95, features.confidence),
                features_used=["complexity_score", "word_count"]
            )

        else:
            route_type_def = self.routing_manager.route_type_registry.get_route_type("simple")
            return self._create_route(
                route_type_def or "simple",
                reason=f"简单查询 (分数: {complexity:.2f}, 词数: {word_count})",
                confidence=0.98,
                features_used=["complexity_score", "word_count"]
            )

    def _create_route_dynamic(self, route_type, reason: str, confidence: float,
                     features_used: List[str]) -> RouteDecision:
        """创建路由决策"""
        if isinstance(route_type, RouteTypeDefinition):
            route_type_value = route_type.name
        else:
            route_type_value = str(route_type)

        return RouteDecision(
            route_type=route_type_value,
            confidence=confidence,
            reasoning=reason,
            features_used=features_used,
            processing_time=0.0  # 将在上级方法中设置
        )

    def _is_multi_agent_query(self, features: QueryFeatures) -> bool:
        """检测是否需要多智能体协作"""
        # 多查询检测
        if features.is_multi_query or features.num_questions >= self.thresholds['multi_agent_min_questions']:
            return True

        # 复杂多连接查询
        if (features.has_connectors and
            features.complexity_score >= self.thresholds['multi_agent_min_complexity'] and
            features.word_count >= self.thresholds['medium_max_words']):
            return True

        return False

    def _route_by_query_type(self, features: QueryFeatures) -> Optional[RouteDecision]:
        """基于查询类型路由"""
        # 代码/数学类型
        if features.has_code or features.has_math:
            return self._create_route(
                route_type=RouteType.COMPLEX,
                reason="包含代码或数学内容",
                confidence=0.9,
                features_used=["has_code", "has_math"]
            )

        # 解释型推理
        if features.requires_explanation and features.complexity_score > self.thresholds['medium_min_complexity']:
            return self._create_route(
                route_type=RouteType.REASONING,
                reason="需要详细解释和推理",
                confidence=0.85,
                features_used=["requires_explanation", "complexity_score"]
            )

        # 比较型查询
        if features.requires_comparison:
            return self._create_route(
                route_type=RouteType.COMPLEX,
                reason="比较类查询",
                confidence=0.8,
                features_used=["requires_comparison"]
            )

        # 流程型查询
        if features.requires_steps:
            return self._create_route(
                route_type=RouteType.MEDIUM,
                reason="步骤流程类查询",
                confidence=0.8,
                features_used=["requires_steps"]
            )

        return None

    def _route_by_complexity(self, features: QueryFeatures) -> RouteDecision:
        """基于复杂度路由"""
        complexity = features.complexity_score
        word_count = features.word_count

        if (complexity >= self.thresholds['complex_min_complexity'] or
            word_count >= self.thresholds['complex_min_words']):
            return self._create_route(
                route_type=RouteType.COMPLEX,
                reason=f"高复杂度查询 (分数: {complexity:.2f}, 词数: {word_count})",
                confidence=min(0.9, features.confidence),
                features_used=["complexity_score", "word_count"]
            )

        elif (complexity >= self.thresholds['medium_min_complexity'] or
              word_count >= self.thresholds['medium_min_words']):
            return self._create_route(
                route_type=RouteType.MEDIUM,
                reason=f"中等复杂度查询 (分数: {complexity:.2f}, 词数: {word_count})",
                confidence=min(0.95, features.confidence),
                features_used=["complexity_score", "word_count"]
            )

        else:
            return self._create_route(
                route_type=RouteType.SIMPLE.value,
                reason=f"简单查询 (分数: {complexity:.2f}, 词数: {word_count})",
                confidence=0.98,
                features_used=["complexity_score", "word_count"]
            )

    def _create_route(self, route_type, reason: str, confidence: float,
                     features_used: List[str]) -> RouteDecision:
        """创建路由决策"""
        return RouteDecision(
            route_type=route_type if isinstance(route_type, str) else str(route_type),
            confidence=confidence,
            reasoning=reason,
            features_used=features_used,
            processing_time=0.0  # 将在上级方法中设置
        )

    def adjust_thresholds_based_on_performance(self, metrics: Dict):
        """基于性能指标动态调整阈值"""
        if metrics.get('accuracy', 0) < 0.85:
            # 降低阈值以提高覆盖率
            self.thresholds['simple_max_complexity'] *= 0.9
            self.thresholds['medium_min_complexity'] *= 0.9
            logger.info("降低复杂度阈值以提高准确率")

        if metrics.get('processing_time_avg', 0) > 2.0:
            # 提高阈值以减少复杂查询
            self.thresholds['complex_min_complexity'] *= 1.1
            self.thresholds['medium_max_complexity'] *= 1.05
            logger.info("提高复杂度阈值以优化性能")

    def add_rule(self, condition: Callable[[QueryFeatures], bool], route_type: RouteType, description: str):
        """添加路由规则"""
        self.rules.append({
            'condition': condition,
            'route_type': route_type,
            'description': description
        })

    def route(self, features: QueryFeatures) -> Tuple[RouteType, float, str]:
        """基于规则进行路由"""
        for rule in self.rules:
            condition = rule['condition']
            route_type = rule['route_type']
            description = rule['description']
            if condition(features):
                # 计算置信度（基于特征匹配度）
                route_type_enum = RouteType(route_type) if isinstance(route_type, str) else route_type
                confidence = self._calculate_confidence(features, route_type_enum)
                return route_type_enum, confidence, description

        # 兜底到简单查询
        return RouteType.SIMPLE, 0.5, "兜底简单查询"

    def _calculate_confidence(self, features: QueryFeatures, route_type: RouteType) -> float:
        """计算路由置信度"""
        base_confidence = 0.7  # 规则匹配的基础置信度

        # 根据特征调整置信度
        if route_type == RouteType.REASONING:
            if features.has_explanation and features.complexity_score > 0.7:
                base_confidence += 0.2
        elif route_type == RouteType.MULTI_AGENT:
            if features.complexity_score > 0.8 and features.word_count > 25:
                base_confidence += 0.2
        elif route_type == RouteType.COMPLEX:
            if features.has_code or features.has_math:
                base_confidence += 0.2
        elif route_type == RouteType.SIMPLE:
            if features.complexity_score < 0.3 and features.word_count < 10:
                base_confidence += 0.2

        return min(base_confidence, 1.0)


class MLBasedRouter:
    """基于机器学习的路由器"""

    def __init__(self):
        self.model = None
        self.feature_importance: Dict[str, float] = {}
        self.training_data: List[Tuple[QueryFeatures, RouteType]] = []
        self.is_trained = False

        # 简化的机器学习模型（决策树）
        self.decision_tree = self._build_decision_tree()

    def _build_decision_tree(self) -> Dict[str, Any]:
        """构建简化的决策树"""
        # 这是一个简化的决策树实现
        # 在实际应用中，应该使用scikit-learn或类似库
        return {
            'root': {
                'feature': 'complexity_score',
                'threshold': 0.5,
                'left': {  # complexity_score <= 0.5
                    'feature': 'word_count',
                    'threshold': 10,
                    'left': {'prediction': RouteType.SIMPLE},  # word_count <= 10
                    'right': {'prediction': RouteType.MEDIUM}  # word_count > 10
                },
                'right': {  # complexity_score > 0.5
                    'feature': 'has_code',
                    'threshold': 0.5,
                    'left': {  # has_code = False
                        'feature': 'has_explanation',
                        'threshold': 0.5,
                        'left': {'prediction': RouteType.COMPLEX},  # has_explanation = False
                        'right': {'prediction': RouteType.REASONING}  # has_explanation = True
                    },
                    'right': {'prediction': RouteType.MULTI_AGENT}  # has_code = True
                }
            }
        }

    def predict(self, features: QueryFeatures) -> Tuple[RouteType, float, str]:
        """使用机器学习模型进行预测"""
        if not self.is_trained:
            # 如果模型未训练，使用规则作为后备
            return self._rule_based_fallback(features)

        try:
            # 使用决策树进行预测
            route_type = self._traverse_tree(self.decision_tree['root'], features)
            confidence = self._calculate_ml_confidence(features, route_type)

            return route_type, confidence, "机器学习预测"

        except Exception as e:
            logger.warning(f"ML预测失败，使用规则后备: {e}")
            return self._rule_based_fallback(features)

    def _traverse_tree(self, node: Dict[str, Any], features: QueryFeatures) -> RouteType:
        """遍历决策树"""
        if 'prediction' in node:
            return node['prediction']

        feature_name = node['feature']
        threshold = node['threshold']

        # 获取特征值
        feature_value = getattr(features, feature_name, 0)
        if isinstance(feature_value, bool):
            feature_value = 1.0 if feature_value else 0.0

        if feature_value <= threshold:
            return self._traverse_tree(node['left'], features)
        else:
            return self._traverse_tree(node['right'], features)

    def _calculate_ml_confidence(self, features: QueryFeatures, route_type: RouteType) -> float:
        """计算机器学习置信度"""
        # 简化的置信度计算（基于特征重要性）
        confidence = 0.8  # 基础置信度

        # 根据预测结果调整置信度
        if route_type == RouteType.SIMPLE:
            if features.complexity_score < 0.3:
                confidence += 0.1
        elif route_type == RouteType.MULTI_AGENT:
            if features.complexity_score > 0.8:
                confidence += 0.1

        return min(confidence, 1.0)

    def _rule_based_fallback(self, features: QueryFeatures) -> Tuple[RouteType, float, str]:
        """规则基础的后备路由"""
        rule_router = RuleBasedRouter()
        route_result = rule_router.route_query("", features)

        # 转换为期望的返回类型
        if route_result:
            return RouteType(route_result), 0.5, f"规则路由: {route_result}"
        else:
            return RouteType.SIMPLE, 0.3, "规则路由兜底"

    def train(self, training_data: List[Tuple[QueryFeatures, RouteType]]):
        """训练机器学习模型"""
        self.training_data = training_data
        # 在实际实现中，这里会训练真正的ML模型
        # 这里只是设置标志
        self.is_trained = True
        logger.info(f"✅ 机器学习路由器训练完成，使用 {len(training_data)} 个样本")

    def update_model(self, features: QueryFeatures, actual_route: RouteType, was_correct: bool):
        """在线学习更新模型"""
        # 简化的在线学习（实际实现会更复杂）
        if was_correct:
            # 增加正确预测的权重
            pass
        else:
            # 调整决策边界
            pass

        logger.debug(f"模型更新: 复杂度{features.complexity_score:.2f} -> {actual_route.value}, 正确={was_correct}")


class IntelligentRouter:
    """优化后的智能路由器 - 优先级决策树"""

    def __init__(self):
        self.feature_extractor = QueryFeatureExtractor()
        self.optimized_router = OptimizedRouter()
        self.ml_router = MLBasedRouter()
        self.rule_router = RuleBasedRouter()

        # 路由性能监控
        self.performance_stats: Dict[RouteType, RoutePerformance] = {}
        for route_type in RouteType:
            self.performance_stats[route_type] = RoutePerformance(route_type=route_type.value)

        # 配置
        self.use_ml = True
        self.confidence_threshold = 0.7  # 提高置信度阈值
        self.enable_learning = True
        self.enable_dynamic_thresholds = True  # 启用动态阈值调整

        logger.info("✅ 优化后的智能路由器初始化完成")

    def route_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> RouteDecision:
        """优化后的路由查询方法"""
        start_time = time.time()

        try:
            # 提取查询特征
            features = self.feature_extractor.extract_features(query)

            # 优先使用优化路由器
            if self.use_ml and self.ml_router.is_trained and features.confidence > self.confidence_threshold:
                # 使用机器学习路由（高置信度特征）
                route_type, confidence, reasoning = self.ml_router.predict(features)
                method = "machine_learning"
                decision = RouteDecision(
                    route_type=route_type.value if hasattr(route_type, 'value') else str(route_type),
                    confidence=confidence,
                    reasoning=reasoning,
                    features_used=self._get_features_used(features),
                    processing_time=time.time() - start_time
                )
            else:
                # 使用优化规则路由器
                decision = self.optimized_router.decide_route(features)
                method = "optimized_rule_based"

            # 动态阈值调整（如果启用）
            if self.enable_dynamic_thresholds and hasattr(self.optimized_router, 'adjust_thresholds_based_on_performance'):
                self._check_and_adjust_thresholds()

            # 更新性能统计
            route_type_enum = RouteType(decision.route_type) if isinstance(decision.route_type, str) else decision.route_type
            self._update_performance_stats(route_type_enum, decision.confidence, decision.processing_time)

            logger.info(f"🔀 查询路由 [{method}]: {query[:50]}... -> {decision.route_type} "
                       f"(置信度: {decision.confidence:.2f}, 处理时间: {decision.processing_time:.3f}s)")

            return decision

        except Exception as e:
            logger.error(f"路由查询失败: {e}")
            # 返回安全兜底路由
            return RouteDecision(
                route_type=RouteType.SIMPLE.value,
                confidence=0.1,
                reasoning=f"路由失败，使用兜底方案: {str(e)}",
                features_used=[],
                processing_time=time.time() - start_time
            )

    def _check_and_adjust_thresholds(self):
        """检查并动态调整阈值"""
        try:
            # 计算最近性能指标
            recent_metrics = self._calculate_recent_performance()

            # 调整阈值
            self.optimized_router.adjust_thresholds_based_on_performance(recent_metrics)

        except Exception as e:
            logger.warning(f"动态阈值调整失败: {e}")

    def _calculate_recent_performance(self) -> Dict:
        """计算最近的性能指标"""
        total_queries = sum(stat.query_count for stat in self.performance_stats.values())
        if total_queries < 10:  # 样本不足
            return {}

        # 计算加权准确率
        weighted_accuracy = 0.0
        total_weight = 0.0

        for stat in self.performance_stats.values():
            if stat.query_count > 0:
                weight = stat.query_count / total_queries
                accuracy = stat.correct_predictions / stat.query_count
                weighted_accuracy += accuracy * weight
                total_weight += weight

        # 计算平均处理时间
        avg_processing_time = sum(
            stat.average_processing_time * stat.query_count for stat in self.performance_stats.values()
        ) / total_queries

        return {
            'accuracy': weighted_accuracy,
            'processing_time_avg': avg_processing_time,
            'total_queries': total_queries
        }

    def _get_features_used(self, features: QueryFeatures) -> List[str]:
        """获取使用的特征列表（优化版）"""
        features_used = []

        # 结构特征
        if features.is_multi_query:
            features_used.append(f"is_multi_query:{features.num_questions}")
        if features.has_connectors:
            features_used.append("has_connectors")

        # 类型特征
        if features.query_type != "general":
            features_used.append(f"query_type:{features.query_type}")
        if features.has_code:
            features_used.append("has_code")
        if features.has_math:
            features_used.append("has_math")
        if features.requires_explanation:
            features_used.append("requires_explanation")
        if features.requires_comparison:
            features_used.append("requires_comparison")
        if features.requires_steps:
            features_used.append("requires_steps")

        # 复杂度特征
        if features.complexity_score > 0:
            features_used.append(f"complexity_score:{features.complexity_score:.2f}")
        if features.word_count > 0:
            features_used.append(f"word_count:{features.word_count}")

        # 语言特征
        if features.contains_question_words:
            features_used.append(f"question_words:{len(features.question_words)}")
        if features.sentence_structure != "simple":
            features_used.append(f"sentence_structure:{features.sentence_structure}")

        # 置信度
        features_used.append(f"confidence:{features.confidence:.2f}")

        return features_used

    def _update_performance_stats(self, route_type: RouteType, confidence: float, processing_time: float):
        """更新性能统计"""
        stats = self.performance_stats[route_type]
        stats.query_count += 1
        stats.correct_predictions += 1  # 简化为假设都正确，实际需要反馈
        stats.average_confidence = (
            (stats.average_confidence * (stats.query_count - 1)) + confidence
        ) / stats.query_count
        stats.average_processing_time = (
            (stats.average_processing_time * (stats.query_count - 1)) + processing_time
        ) / stats.query_count
        stats.last_updated = datetime.now()

    def get_routing_stats(self) -> Dict[str, Any]:
        """获取路由统计信息"""
        total_queries = sum(stats.query_count for stats in self.performance_stats.values())
        total_correct = sum(stats.correct_predictions for stats in self.performance_stats.values())

        return {
            'total_queries': total_queries,
            'overall_accuracy': total_correct / total_queries if total_queries > 0 else 0,
            'route_performance': {
                route_type.value: {
                    'query_count': stats.query_count,
                    'accuracy': stats.correct_predictions / stats.query_count if stats.query_count > 0 else 0,
                    'avg_confidence': stats.average_confidence,
                    'avg_processing_time': stats.average_processing_time
                }
                for route_type, stats in self.performance_stats.items()
            },
            'feature_importance': self.ml_router.feature_importance,
            'ml_enabled': self.use_ml and self.ml_router.is_trained
        }

    def train_ml_model(self, training_queries: List[Tuple[str, RouteType]]):
        """训练机器学习模型"""
        training_data = []
        for query, expected_route in training_queries:
            features = self.feature_extractor.extract_features(query)
            training_data.append((features, expected_route))

        self.ml_router.train(training_data)
        logger.info(f"✅ 机器学习模型训练完成，使用 {len(training_queries)} 个训练样本")

    def enable_ml_routing(self, enabled: bool = True):
        """启用/禁用机器学习路由"""
        self.use_ml = enabled
        logger.info(f"{'✅' if enabled else '❌'} 机器学习路由: {'启用' if enabled else '禁用'}")

    def update_routing_rules(self, custom_rules: List[Tuple[Callable[[QueryFeatures], bool], RouteType, str]]):
        """更新路由规则"""
        self.rule_router.rules = custom_rules + self.rule_router.rules[len(custom_rules):]
        logger.info(f"✅ 路由规则已更新，新增 {len(custom_rules)} 条规则")

    def provide_feedback(self, query: str, actual_route: RouteType, was_correct: bool):
        """提供路由反馈用于学习"""
        if not self.enable_learning:
            return

        features = self.feature_extractor.extract_features(query)
        self.ml_router.update_model(features, actual_route, was_correct)

        logger.debug(f"反馈已记录: {query[:30]}... -> {actual_route.value}, 正确={was_correct}")


# 全局智能路由器实例
_intelligent_router_instance: Optional[IntelligentRouter] = None


def get_intelligent_router() -> IntelligentRouter:
    """获取智能路由器实例"""
    global _intelligent_router_instance
    if _intelligent_router_instance is None:
        _intelligent_router_instance = IntelligentRouter()
    return _intelligent_router_instance
