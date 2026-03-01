"""
默认配置常量 - 避免硬编码
"""

# 默认正则表达式模式
DEFAULT_REGEX = {
    "year_pattern": r'\d{4}',
    "entity_pattern": r'[A-Z][a-z]+',
    "email_pattern": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    "phone_pattern": r'\d{get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")),11}',
    "url_pattern": r'https?://[^\s/$.?#].[^\s]*'
}

# 默认关键词配置
DEFAULT_KEYWORDS = {
    "question_words": ["what", "how", "when", "where", "why", "who", "which", "whose"],
    "comparison": ["compare", "versus", "vs", "better", "worse", "than", "versus"],
    "analysis": ["analyze", "examine", "investigate", "study", "explore", "research"]
}

# 默认数学常量
DEFAULT_MATH_CONSTANTS = {
    "golden_ratio": 1.618033988749895,
    "pi_factor": 3.141592653589793,
    "e_factor": 2.718281828459045
}
