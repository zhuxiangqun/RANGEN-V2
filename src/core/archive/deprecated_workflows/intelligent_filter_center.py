"""
Intelligent Filter Center - Smart, extensible filtering system
Replaces fixed keyword-based filtering with intelligent, configurable approaches
"""

import logging
from typing import List, Dict, Any, Optional, Callable
import re
from dataclasses import dataclass
from enum import Enum

try:
    from ..utils.unified_centers import get_unified_config_center  # type: ignore
except ImportError:
    def get_unified_config_center():  # type: ignore
        class MockConfigCenter:
            def get_env_config(self, section: str, key: str, default: Any = None) -> Any:
                return default
            def get_config_value(self, section: str, key: str, default: Any = None) -> Any:
                return default
        return MockConfigCenter()  # type: ignore


class FilterStrategy(Enum):
    """Filtering strategies"""
    SEMANTIC = "semantic"  # Semantic similarity-based filtering
    PATTERN = "pattern"  # Pattern-based filtering (regex, fuzzy)
    STATISTICAL = "statistical"  # Statistical analysis
    HYBRID = "hybrid"  # Combination of multiple strategies
    ML = "ml"  # Machine learning-based (if available)


@dataclass
class FilterRule:
    """A filter rule configuration"""
    name: str
    category: str  # e.g., "invalid_answer", "meaningless_content"
    strategy: FilterStrategy
    patterns: Optional[List[str]] = None  # For pattern-based
    semantic_threshold: Optional[float] = None  # For semantic similarity (0-1)
    statistical_threshold: Optional[Dict[str, float]] = None  # For statistical filtering
    weight: float = 1.0  # Weight for hybrid filtering
    enabled: bool = True


class IntelligentFilterCenter:
    """Intelligent filtering center with multiple strategies"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.config_center = None
        
        try:
            self.config_center = get_unified_config_center()
        except Exception:
            self.logger.warning("Failed to initialize config center, using defaults")
        
        # 🚀 统一规则管理：初始化统一规则管理中心
        self.rule_manager = None
        try:
            from src.utils.unified_rule_manager import get_unified_rule_manager
            self.rule_manager = get_unified_rule_manager()
            self.logger.info("✅ 统一规则管理中心已初始化（智能过滤中心）")
        except Exception as e:
            self.logger.debug(f"统一规则管理中心初始化失败（可选功能）: {e}")
        
        # Load filter rules from config
        self.filter_rules: Dict[str, List[FilterRule]] = {}
        self._load_filter_rules()
        
        # Semantic similarity cache (for performance)
        self._similarity_cache: Dict[str, float] = {}
        
        # Statistical models
        self._statistical_models: Dict[str, Dict[str, float]] = {}
        self._initialize_statistical_models()
    
    def _load_filter_rules(self) -> None:
        """Load filter rules from configuration"""
        try:
            # Try to load from config center
            if self.config_center:
                rules_config = self.config_center.get_env_config(
                    "filtering", "filter_rules", None
                )
                if rules_config and isinstance(rules_config, dict):
                    self._parse_rules_from_config(rules_config)
                    return
        except Exception as e:
            self.logger.debug(f"Could not load rules from config center: {e}")
        
        # Load default rules
        self._load_default_rules()
    
    def _load_default_rules(self) -> None:
        """Load default filter rules"""
        # Invalid answer rules
        invalid_answer_rules = [
            FilterRule(
                name="invalid_answer_exact",
                category="invalid_answer",
                strategy=FilterStrategy.PATTERN,
                patterns=[
                    # English
                    r"^(unable to determine|cannot determine|cannot find|no answer|unable to|cannot answer|unclear|uncertain|unknown|not sure|no clear answer)$",
                    # Chinese
                    r"^(无法确定|不确定|不知道|无法找到|无法回答|不清楚|不明确|无明确答案)$",
                    # 🚀 优化：过滤JSON格式的查询内容
                    r"^\{['\"]Unnamed:\s*0['\"]",  # {'Unnamed: 0': 或 {"Unnamed: 0":
                    r"^\{.*'Unnamed'",  # {'Unnamed':
                    r"^\{.*\"Unnamed\"",  # {"Unnamed":
                    r"^\{.*'Prompt'",  # {'Prompt':
                    r"^\{.*\"Prompt\"",  # {"Prompt":
                ],
                weight=1.0
            ),
            # 🚀 优化：添加API错误消息检测规则（高权重，优先匹配）
            FilterRule(
                name="api_error_messages",
                category="invalid_answer",
                strategy=FilterStrategy.PATTERN,
                patterns=[
                    # API超时错误消息（精确匹配 - 不区分大小写）
                    r"^(?:reasoning|analysis|extraction|detection|task)\s+failed\s+due\s+to\s+api\s+timeout.*",
                    # API错误消息（包含"task failed"和"api timeout"）
                    r".*task\s+failed.*api\s+timeout.*",
                    r".*task\s+failed.*due\s+to.*timeout.*",
                    # API错误消息（部分匹配）
                    r"(?:^|.*\s)(?:api\s+)?(?:call|request)?\s*(?:failed|error|timeout).*(?:please\s+try\s+again|try\s+again\s+later)",
                    r"(?:^|.*\s)(?:check\s+)?(?:network\s+)?(?:connection|connection\s+failed).*(?:try\s+again|please)",
                    # 通用错误消息模式
                    r"^(?:failed|error|timeout|exception).*(?:please|try\s+again|later)",
                ],
                weight=10.0  # 🚀 提高权重，确保API错误消息优先被识别
            ),
            FilterRule(
                name="invalid_answer_prefix",
                category="invalid_answer",
                strategy=FilterStrategy.PATTERN,
                patterns=[
                    r"^(the answer is:\s*)?(unable to determine|cannot determine)",
                    r"^(答案是：)?(无法确定|不确定|不知道)",
                ],
                weight=0.8
            ),
            FilterRule(
                name="invalid_answer_semantic",
                category="invalid_answer",
                strategy=FilterStrategy.SEMANTIC,
                semantic_threshold=0.85,  # High similarity threshold
                weight=0.6
            ),
        ]
        
        # Meaningless content rules
        meaningless_content_rules = [
            FilterRule(
                name="meaningless_metadata",
                category="meaningless_content",
                strategy=FilterStrategy.PATTERN,
                patterns=[
                    r"^(涉及的数字|涉及的关键词|问题主题|问题:|numbers found|entities found|query:|question:)$",
                    r"^(based on|according to|related to)\s*$",
                ],
                weight=1.0
            ),
            # 🚀 P0修复：添加元数据字段检测规则（动态扩展）
            FilterRule(
                name="metadata_fields",
                category="meaningless_content",
                strategy=FilterStrategy.PATTERN,
                patterns=[
                    # 元数据字段前缀（冒号前）
                    r"^(doi|url|http|https|www|page|pages|pp|vol|volume|issn|isbn|pmid|arxiv|ref|reference|fig|figure|table|chapter|section|para|paragraph|line|lines|p\.|pp\.):",
                    # 元数据字段值（只包含数字和分隔符的短字符串）
                    r"^[\d\s\.\-\/\\]{1,20}$",
                    # 单位缩写单独出现
                    r"^(mi|km|m|cm|mm|ft|in|yd|lb|kg|g|mg)$",
                    # 页码、卷号等
                    r"^(p\.|pp\.|vol\.|no\.|ch\.|sec\.)\s*\d+$",
                ],
                weight=1.5  # 高权重，优先匹配
            ),
            FilterRule(
                name="meaningless_prefix",
                category="meaningless_content",
                strategy=FilterStrategy.PATTERN,
                patterns=[
                    r"^(问题|答案|基于|根据|涉及|question|answer|based|according)\s+",
                ],
                weight=0.7
            ),
            FilterRule(
                name="low_informativeness",
                category="meaningless_content",
                strategy=FilterStrategy.STATISTICAL,
                statistical_threshold={
                    "min_length": 10,
                    "min_unique_chars_ratio": 0.3,
                    "max_repetition_ratio": 0.6,
                    "min_word_count": 2,
                },
                weight=0.8
            ),
            FilterRule(
                name="repetitive_patterns",
                category="meaningless_content",
                strategy=FilterStrategy.STATISTICAL,
                statistical_threshold={
                    "max_char_repetition_ratio": 0.4,
                    "max_word_repetition_ratio": 0.3,
                    "max_sequence_repetition_ratio": 0.5,
                },
                weight=0.9
            ),
        ]
        
        # Organize rules by category
        self.filter_rules = {
            "invalid_answer": invalid_answer_rules,
            "meaningless_content": meaningless_content_rules,
        }
    
    def _parse_rules_from_config(self, rules_config: Dict[str, Any]) -> None:
        """Parse filter rules from configuration dictionary"""
        for category, rules_list in rules_config.items():
            if not isinstance(rules_list, list):
                continue
            
            parsed_rules = []
            for rule_dict in rules_list:
                try:
                    strategy = FilterStrategy(rule_dict.get("strategy", "pattern"))
                    rule = FilterRule(
                        name=rule_dict.get("name", "unnamed"),
                        category=category,
                        strategy=strategy,
                        patterns=rule_dict.get("patterns"),
                        semantic_threshold=rule_dict.get("semantic_threshold"),
                        statistical_threshold=rule_dict.get("statistical_threshold"),
                        weight=rule_dict.get("weight", 1.0),
                        enabled=rule_dict.get("enabled", True)
                    )
                    parsed_rules.append(rule)
                except Exception as e:
                    self.logger.warning(f"Failed to parse rule: {e}")
            
            if parsed_rules:
                self.filter_rules[category] = parsed_rules
    
    def _initialize_statistical_models(self) -> None:
        """Initialize statistical models for filtering"""
        # These can be trained on historical data in the future
        # For now, use heuristic thresholds
        self._statistical_models = {
            "content_quality": {
                "min_length": 10,
                "min_unique_chars_ratio": 0.3,
                "max_repetition_ratio": 0.6,
                "min_word_count": 2,
                "max_special_char_ratio": 0.6,
            },
            "repetitive_patterns": {
                "max_char_repetition_ratio": 0.4,
                "max_word_repetition_ratio": 0.3,
                "max_sequence_repetition_ratio": 0.5,
            }
        }
    
    def is_invalid_answer(self, answer: str, strategy: FilterStrategy = FilterStrategy.HYBRID) -> bool:
        """Check if answer is invalid using intelligent filtering"""
        if not answer or not answer.strip():
            return True
        
        answer = answer.strip()
        answer_lower = answer.lower()
        
        # 🚀 修复：优先检查API错误消息（高优先级，直接拒绝）
        # 首先检查常见的API错误关键词（快速路径）
        # 🚀 统一规则管理：从统一规则管理中心获取API错误关键词列表（不再硬编码）
        api_error_keywords = []
        if self.rule_manager:
            try:
                api_error_keywords = self.rule_manager.get_keywords('api_error_keywords')
            except Exception as e:
                self.logger.debug(f"从统一规则管理中心获取API错误关键词失败: {e}")
        
        # Fallback：使用硬编码列表（向后兼容）
        if not api_error_keywords:
            api_error_keywords = [
                "reasoning task failed due to api timeout",
                "task failed due to api timeout",
                "api call failed",
                "api timeout",
                "please try again later",
                "check network connection"
            ]
        
        for keyword in api_error_keywords:
            if keyword in answer_lower:
                self.logger.debug(f"检测到API错误关键词: {keyword} in {answer_lower[:50]}...")
                return True
        
        # 然后检查API错误规则（更全面的模式匹配）
        invalid_rules = self.filter_rules.get("invalid_answer", [])
        api_error_rule = None
        for rule in invalid_rules:
            if rule.name == "api_error_messages" and rule.enabled:
                api_error_rule = rule
                break
        
        if api_error_rule:
            if self._pattern_match(answer, api_error_rule):
                # API错误消息直接拒绝，不需要通过混合过滤器
                self.logger.debug(f"API错误规则匹配成功: {answer[:50]}...")
                return True
            else:
                if api_error_rule.patterns:
                    self.logger.debug(f"API错误规则匹配失败: rule={api_error_rule.name}, patterns={len(api_error_rule.patterns)}")
        
        # Use hybrid strategy by default
        if strategy == FilterStrategy.HYBRID:
            return self._hybrid_filter(answer, "invalid_answer")
        
        return self._apply_filter_strategy(answer, "invalid_answer", strategy)
    
    def is_meaningless_content(self, content: str, strategy: FilterStrategy = FilterStrategy.HYBRID) -> bool:
        """Check if content is meaningless using intelligent filtering"""
        if not content or not content.strip():
            return True
        
        content = content.strip()
        
        if strategy == FilterStrategy.HYBRID:
            return self._hybrid_filter(content, "meaningless_content")
        
        return self._apply_filter_strategy(content, "meaningless_content", strategy)
    
    def _apply_filter_strategy(self, text: str, category: str, strategy: FilterStrategy) -> bool:
        """Apply a specific filtering strategy"""
        rules = self.filter_rules.get(category, [])
        
        for rule in rules:
            if not rule.enabled or rule.strategy != strategy:
                continue
            
            if rule.strategy == FilterStrategy.PATTERN:
                if self._pattern_match(text, rule):
                    return True
            
            elif rule.strategy == FilterStrategy.SEMANTIC:
                if self._semantic_match(text, rule):
                    return True
            
            elif rule.strategy == FilterStrategy.STATISTICAL:
                if self._statistical_match(text, rule):
                    return True
        
        return False
    
    def _hybrid_filter(self, text: str, category: str) -> bool:
        """Apply hybrid filtering (combination of multiple strategies)"""
        rules = self.filter_rules.get(category, [])
        
        # 🚀 修复：如果没有规则，默认认为答案有效（返回False表示不是无效答案）
        if not rules:
            return False
        
        # Calculate weighted scores
        total_score = 0.0
        total_weight = 0.0
        
        for rule in rules:
            if not rule.enabled:
                continue
            
            match = False
            if rule.strategy == FilterStrategy.PATTERN:
                match = self._pattern_match(text, rule)
            elif rule.strategy == FilterStrategy.SEMANTIC:
                match = self._semantic_match(text, rule)
            elif rule.strategy == FilterStrategy.STATISTICAL:
                match = self._statistical_match(text, rule)
            
            if match:
                total_score += rule.weight
            total_weight += rule.weight
        
        # 🚀 修复：如果没有启用的规则，默认认为答案有效
        if total_weight == 0:
            return False
        
        # If total score exceeds threshold, consider it invalid/meaningless
        # Threshold: 50% of total weight
        threshold = total_weight * 0.5
        is_invalid = total_score >= threshold
        
        # 🚀 修复：添加调试日志，帮助诊断问题
        if is_invalid:
            self.logger.debug(
                f"答案被判定为无效: {text[:50]}... "
                f"(score={total_score:.2f}, threshold={threshold:.2f}, weight={total_weight:.2f})"
            )
        
        return is_invalid
    
    def _pattern_match(self, text: str, rule: FilterRule) -> bool:
        """Check if text matches pattern rules"""
        if not rule.patterns:
            return False
        
        text_lower = text.lower().strip()
        
        for pattern in rule.patterns:
            try:
                # Try regex pattern
                if re.search(pattern, text_lower, re.IGNORECASE):
                    self.logger.debug(f"模式匹配成功: pattern={pattern[:50]}..., text={text_lower[:50]}...")
                    return True
            except re.error as regex_error:
                # Fallback to simple substring matching
                pattern_lower = pattern.lower()
                # 如果是regex字符串，尝试提取文字部分
                if pattern_lower in text_lower:
                    self.logger.debug(f"子串匹配成功: pattern={pattern_lower[:50]}..., text={text_lower[:50]}...")
                    return True
                else:
                    self.logger.debug(f"模式匹配失败: pattern={pattern[:50]}..., error={regex_error}")
        
        return False
    
    def _semantic_match(self, text: str, rule: FilterRule) -> bool:
        """Check semantic similarity with invalid/meaningless patterns"""
        if rule.semantic_threshold is None:
            return False
        
        # Try to use embeddings if available
        try:
            similarity = self._calculate_semantic_similarity(text, rule)
            return similarity >= rule.semantic_threshold
        except Exception as e:
            self.logger.debug(f"Semantic similarity calculation failed: {e}")
            # Fallback to pattern matching if semantic similarity fails
            return False
    
    def _calculate_semantic_similarity(self, text: str, rule: FilterRule) -> float:
        """Calculate semantic similarity between text and rule patterns"""
        # Check cache first
        cache_key = f"{text}_{rule.name}"
        if cache_key in self._similarity_cache:
            return self._similarity_cache[cache_key]
        
        # For now, use simple word overlap as semantic similarity
        # In the future, can use embeddings (sentence transformers, etc.)
        if not rule.patterns:
            return 0.0
        
        # Extract words from text
        text_words = set(re.findall(r'\b\w+\b', text.lower()))
        
        max_similarity = 0.0
        for pattern in rule.patterns:
            # Extract words from pattern
            pattern_words = set(re.findall(r'\b\w+\b', pattern.lower()))
            
            if not pattern_words:
                continue
            
            # Calculate Jaccard similarity
            intersection = len(text_words & pattern_words)
            union = len(text_words | pattern_words)
            
            if union > 0:
                similarity = intersection / union
                max_similarity = max(max_similarity, similarity)
        
        # Cache result
        self._similarity_cache[cache_key] = max_similarity
        
        return max_similarity
    
    def _statistical_match(self, text: str, rule: FilterRule) -> bool:
        """Check if text matches statistical criteria"""
        if not rule.statistical_threshold:
            return False
        
        thresholds = rule.statistical_threshold
        
        # Length check
        if "min_length" in thresholds and len(text) < thresholds["min_length"]:
            return True
        
        # Unique characters ratio
        if "min_unique_chars_ratio" in thresholds:
            unique_chars = len(set(text.lower()))
            ratio = unique_chars / len(text) if len(text) > 0 else 0
            if ratio < thresholds["min_unique_chars_ratio"]:
                return True
        
        # Repetition ratio
        if "max_repetition_ratio" in thresholds:
            words = text.split()
            if len(words) > 0:
                unique_words = len(set(word.lower() for word in words))
                repetition_ratio = 1.0 - (unique_words / len(words))
                if repetition_ratio > thresholds["max_repetition_ratio"]:
                    return True
        
        # Word count
        if "min_word_count" in thresholds:
            word_count = len(text.split())
            if word_count < thresholds["min_word_count"]:
                return True
        
        # Special characters ratio
        if "max_special_char_ratio" in thresholds:
            special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
            ratio = special_chars / len(text) if len(text) > 0 else 0
            if ratio > thresholds["max_special_char_ratio"]:
                return True
        
        # Character repetition check (for detecting repetitive patterns)
        if "max_char_repetition_ratio" in thresholds:
            char_counts = {}
            for char in text.lower():
                char_counts[char] = char_counts.get(char, 0) + 1
            if char_counts:
                max_char_count = max(char_counts.values())
                if max_char_count > len(text) * thresholds["max_char_repetition_ratio"]:
                    return True
        
        # Word repetition check
        if "max_word_repetition_ratio" in thresholds:
            words = text.split()
            if len(words) > 0:
                word_counts = {}
                for word in words:
                    word_counts[word.lower()] = word_counts.get(word.lower(), 0) + 1
                max_word_count = max(word_counts.values())
                if max_word_count > len(words) * thresholds["max_word_repetition_ratio"]:
                    return True
        
        # Sequence repetition check (detects repeated character/word sequences)
        if "max_sequence_repetition_ratio" in thresholds:
            # Check for repeated character sequences
            for i in range(2, min(10, len(text) // 2)):
                pattern = text[:i]
                if text.count(pattern) > len(text) // (i * 2):
                    return True
            
            # Check for repeated word sequences
            words = text.split()
            if len(words) > 2:
                for i in range(1, min(5, len(words) // 2)):
                    pattern = ' '.join(words[:i])
                    if ' '.join(words).count(pattern) > len(words) // (i * 2):
                        return True
        
        return False
    
    def clean_answer(self, answer: str) -> str:
        """Clean and validate answer using intelligent filtering"""
        if not answer:
            return ""
        
        answer = answer.strip()
        
        # Check if invalid
        if self.is_invalid_answer(answer):
            return ""
        
        # Remove common prefixes
        prefixes = [
            r"^(the\s+)?answer\s+is\s*:?\s*",
            r"^final\s+answer\s+is\s*:?\s*",
            r"^答案是\s*:?\s*",
            r"^最终答案是\s*:?\s*",
        ]
        
        cleaned = answer
        for prefix in prefixes:
            cleaned = re.sub(prefix, "", cleaned, flags=re.IGNORECASE).strip()
            if cleaned != answer:
                break
        
        # Final validation
        # 🚀 修复：允许单字符数字答案（如 "6", "0", "4" 等）
        if len(cleaned) < 1:
            return ""
        # 如果长度是1，检查是否是数字或字母（可能是有效答案）
        if len(cleaned) == 1:
            # 单字符数字或字母是有效的（如 "6", "A", "0"）
            if cleaned.isdigit() or cleaned.isalpha():
                return cleaned
            # 其他单字符可能无效
            return ""
        
        return cleaned
    
    def add_custom_rule(self, rule: FilterRule) -> None:
        """Add a custom filter rule dynamically"""
        if rule.category not in self.filter_rules:
            self.filter_rules[rule.category] = []
        
        self.filter_rules[rule.category].append(rule)
        self.logger.info(f"Added custom filter rule: {rule.name} (category: {rule.category})")
    
    def remove_rule(self, category: str, rule_name: str) -> None:
        """Remove a filter rule"""
        if category in self.filter_rules:
            self.filter_rules[category] = [
                rule for rule in self.filter_rules[category]
                if rule.name != rule_name
            ]
            self.logger.info(f"Removed filter rule: {rule_name} (category: {category})")
    
    def update_rule(self, category: str, rule_name: str, updates: Dict[str, Any]) -> None:
        """Update a filter rule"""
        if category not in self.filter_rules:
            return
        
        for rule in self.filter_rules[category]:
            if rule.name == rule_name:
                for key, value in updates.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                self.logger.info(f"Updated filter rule: {rule_name} (category: {category})")
                return
    
    def get_rules(self, category: Optional[str] = None) -> Dict[str, List[FilterRule]]:
        """Get filter rules (optionally filtered by category)"""
        if category:
            return {category: self.filter_rules.get(category, [])}
        return self.filter_rules.copy()


# Global instance (singleton pattern)
_filter_center_instance: Optional[IntelligentFilterCenter] = None


def get_intelligent_filter_center(config: Optional[Dict[str, Any]] = None) -> IntelligentFilterCenter:
    """Get or create the global intelligent filter center instance"""
    global _filter_center_instance
    
    if _filter_center_instance is None:
        _filter_center_instance = IntelligentFilterCenter(config)
    
    return _filter_center_instance

