"""
StepGenerator配置文件
集中管理所有硬编码的配置项，提高可扩展性和可维护性
"""
from typing import Dict, List, Any, Set
from dataclasses import dataclass, field


@dataclass
class ValidationConfig:
    """验证相关配置"""
    # 相似度阈值 - 提高阈值以过滤不相关步骤
    semantic_similarity_threshold: float = 0.3
    topic_overlap_threshold: float = 0.2
    hallucination_detection_threshold: float = 0.3

    # 不相关关键词列表
    irrelevant_keywords: Set[str] = field(default_factory=lambda: {
        'novel', 'book', 'movie', 'film', 'award', 'actor', 'actress',
        'author', 'writer', 'chinese academy of sciences', 'beijing', 'china'
    })

    # 幻觉实体检测
    hallucinated_entities: Set[str] = field(default_factory=lambda: {
        'chinese academy of sciences',
        'beijing institute',
        'china science academy',
        'chinese scientific institution'
    })

    # 可疑模式
    suspicious_patterns: List[str] = field(default_factory=lambda: [
        r'\b(chinese|china|beijing)\b.*\b(academy|sciences?|institute)\b',
        r'\b(academy of sciences?|scientific institute)\b.*\b(china|chinese)\b',
        r'\b(fictional|imaginary|made.up)\b.*\b(book|novel|author)\b'
    ])


@dataclass
class DomainConfig:
    """领域相关配置"""
    # 领域关键词映射
    domain_keywords: Dict[str, List[str]] = field(default_factory=lambda: {
        'politics': ['president', 'first lady', 'government', 'political', 'election', 'assassinated'],
        'history': ['historical', 'century', 'war', 'revolution', 'era', '15th', '2nd'],
        'entertainment': ['movie', 'film', 'award', 'actor', 'actress', 'oscar', 'cinema'],
        'literature': ['book', 'author', 'write', 'novel', 'children', 'bear', 'bee', 'bronte'],
        'science': ['research', 'study', 'technology', 'computer', 'space', 'academy', 'institute'],
        'sports': ['game', 'team', 'player', 'championship', 'win', 'score'],
        'mathematics': ['calculate', 'compute', 'number', 'math', 'numerical', 'dewey', 'decimal'],
        'architecture': ['building', 'tower', 'height', 'feet', 'tallest', 'rank', 'city'],
        'geography': ['country', 'capital', 'city', 'location', 'place', 'where', 'map'],
        'education': ['school', 'university', 'college', 'student', 'teacher', 'learn'],
        'business': ['company', 'market', 'money', 'price', 'sell', 'buy', 'economy'],
        'health': ['medical', 'doctor', 'patient', 'disease', 'treatment', 'hospital'],
        'technology': ['software', 'hardware', 'internet', 'digital', 'online', 'app']
    })

    # 领域推理指示器
    domain_inference_indicators: Dict[str, str] = field(default_factory=lambda: {
        'politics': '政治领域推理',
        'entertainment': '娱乐领域推理',
        'literature': '文学领域推理',
        'science': '科学领域推理',
        'sports': '体育领域推理',
        'mathematics': '数学领域推理',
        'architecture': '建筑领域推理',
        'geography': '地理领域推理',
        'education': '教育领域推理',
        'business': '商业领域推理',
        'health': '医疗领域推理',
        'technology': '科技领域推理'
    })


@dataclass
class QueryTypeConfig:
    """查询类型相关配置"""
    # 查询类型关键词
    query_type_keywords: Dict[str, List[str]] = field(default_factory=lambda: {
        'fact_retrieval': ['what is', 'who is', 'where is', 'when is', 'how many', 'what are'],
        'multi_hop_facts': ['whose', 'where', 'which', 'relationship', 'connection', 'link'],
        'historical_relation': ['president', 'first lady', 'assassinated', 'mother', 'father', 'wife', 'husband'],
        'comparative_analysis': ['compare', 'versus', 'vs', 'difference', 'better', 'rank', 'ranking'],
        'numerical_reasoning': ['calculate', 'compute', 'equals', 'dewey', 'decimal', 'number'],
        'multi_domain': ['building', 'tower', 'height', 'feet', 'bronte', 'book', 'published'],
        'causal_reasoning': ['why', 'because', 'cause', 'effect', 'reason', 'result'],
        'hypothetical': ['imagine', 'suppose', 'if', 'assume', 'scenario', 'what if'],
        'computational': ['solve', 'calculate', 'compute', 'formula', 'equation', 'math']
    })

    # 复杂查询指示器
    complex_query_indicators: List[str] = field(default_factory=lambda: [
        'whose', 'where', 'which', 'relationship', 'connection', 'compare',
        'calculate', 'compute', 'dewey', 'decimal', 'building', 'tower',
        'height', 'rank', 'ranking', 'mother', 'father', 'president'
    ])


@dataclass
class GenerationConfig:
    """生成相关配置"""
    # LLM参数
    default_temperature: float = 0.1
    retry_temperature: float = 0.5
    max_tokens: int = 2000
    timeout_seconds: int = 30

    # 重试配置
    max_retry_attempts: int = 5
    retry_delay_seconds: float = 1.0

    # 复杂度阈值
    complexity_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'simple_max': 3.0,
        'medium_min': 3.0,
        'medium_max': 6.0,
        'complex_min': 6.0,
        'thinking_mode_min': 4.0
    })

    # 步骤数量限制
    max_steps_per_query: int = 8
    min_steps_per_query: int = 1

    # 并行处理
    enable_parallel_processing: bool = False
    max_parallel_groups: int = 3


@dataclass
class StepGeneratorConfig:
    """StepGenerator完整配置"""
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    domain: DomainConfig = field(default_factory=DomainConfig)
    query_type: QueryTypeConfig = field(default_factory=QueryTypeConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'StepGeneratorConfig':
        """从字典创建配置"""
        config = cls()

        # 更新验证配置
        if 'validation' in config_dict:
            for key, value in config_dict['validation'].items():
                if hasattr(config.validation, key):
                    setattr(config.validation, key, value)

        # 更新领域配置
        if 'domain' in config_dict:
            for key, value in config_dict['domain'].items():
                if hasattr(config.domain, key):
                    setattr(config.domain, key, value)

        # 更新查询类型配置
        if 'query_type' in config_dict:
            for key, value in config_dict['query_type'].items():
                if hasattr(config.query_type, key):
                    setattr(config.query_type, key, value)

        # 更新生成配置
        if 'generation' in config_dict:
            for key, value in config_dict['generation'].items():
                if hasattr(config.generation, key):
                    setattr(config.generation, key, value)

        return config

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'validation': {
                'semantic_similarity_threshold': self.validation.semantic_similarity_threshold,
                'topic_overlap_threshold': self.validation.topic_overlap_threshold,
                'hallucination_detection_threshold': self.validation.hallucination_detection_threshold,
                'irrelevant_keywords': list(self.validation.irrelevant_keywords),
                'hallucinated_entities': list(self.validation.hallucinated_entities),
                'suspicious_patterns': self.validation.suspicious_patterns
            },
            'domain': {
                'domain_keywords': self.domain.domain_keywords,
                'domain_inference_indicators': self.domain.domain_inference_indicators
            },
            'query_type': {
                'query_type_keywords': self.query_type.query_type_keywords,
                'complex_query_indicators': self.query_type.complex_query_indicators
            },
            'generation': {
                'default_temperature': self.generation.default_temperature,
                'retry_temperature': self.generation.retry_temperature,
                'max_tokens': self.generation.max_tokens,
                'timeout_seconds': self.generation.timeout_seconds,
                'max_retry_attempts': self.generation.max_retry_attempts,
                'retry_delay_seconds': self.generation.retry_delay_seconds,
                'complexity_thresholds': self.generation.complexity_thresholds,
                'max_steps_per_query': self.generation.max_steps_per_query,
                'min_steps_per_query': self.generation.min_steps_per_query,
                'enable_parallel_processing': self.generation.enable_parallel_processing,
                'max_parallel_groups': self.generation.max_parallel_groups
            }
        }

    def add_domain(self, domain_name: str, keywords: List[str], indicator: str = ""):
        """添加新领域"""
        self.domain.domain_keywords[domain_name] = keywords
        if indicator:
            self.domain.domain_inference_indicators[domain_name] = indicator

    def remove_domain(self, domain_name: str):
        """移除领域"""
        if domain_name in self.domain.domain_keywords:
            del self.domain.domain_keywords[domain_name]
        if domain_name in self.domain.domain_inference_indicators:
            del self.domain.domain_inference_indicators[domain_name]

    def add_query_type(self, type_name: str, keywords: List[str]):
        """添加新查询类型"""
        self.query_type.query_type_keywords[type_name] = keywords

    def remove_query_type(self, type_name: str):
        """移除查询类型"""
        if type_name in self.query_type.query_type_keywords:
            del self.query_type.query_type_keywords[type_name]


# 全局默认配置实例
_default_config = StepGeneratorConfig()


def get_default_config() -> StepGeneratorConfig:
    """获取默认配置"""
    return _default_config


def load_config_from_file(file_path: str) -> StepGeneratorConfig:
    """从文件加载配置"""
    import json
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        return StepGeneratorConfig.from_dict(config_dict)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return get_default_config()


def save_config_to_file(config: StepGeneratorConfig, file_path: str):
    """保存配置到文件"""
    import json
    try:
        config_dict = config.to_dict()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=2)
        print(f"配置已保存到: {file_path}")
    except Exception as e:
        print(f"保存配置文件失败: {e}")
