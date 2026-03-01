#!/usr/bin/env python3
"""
Unified Rule Registry - 统一规则注册系统

将硬编码的关键词、规则、模式抽取到统一配置
支持动态扩展和热更新
"""
from typing import Dict, List, Set, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import os


class RuleCategory(Enum):
    """规则类别"""
    QUERY_CLASSIFICATION = "query_classification"      # 查询分类
    ERROR_DETECTION = "error_detection"               # 错误检测
    CONTENT_FILTERING = "content_filtering"           # 内容过滤
    PATTERN_MATCHING = "pattern_matching"             # 模式匹配
    ENTITY_EXTRACTION = "entity_extraction"           # 实体提取
    SENTIMENT_ANALYSIS = "sentiment_analysis"         # 情感分析


@dataclass
class RuleDefinition:
    """规则定义"""
    name: str
    category: RuleCategory
    keywords: List[str]
    patterns: List[str] = field(default_factory=list)
    weight: float = 1.0
    description: str = ""
    enabled: bool = True


class UnifiedRuleRegistry:
    """统一规则注册表"""
    
    def __init__(self):
        self._rules: Dict[str, RuleDefinition] = {}
        self._category_rules: Dict[RuleCategory, List[RuleDefinition]] = {}
        self._keyword_index: Dict[str, List[str]] = {}  # keyword -> rule names
        self._initialized = False
    
    def register(self, rule: RuleDefinition) -> None:
        """注册规则"""
        self._rules[rule.name] = rule
        
        # 按类别索引
        if rule.category not in self._category_rules:
            self._category_rules[rule.category] = []
        self._category_rules[rule.category].append(rule)
        
        # 关键词索引
        for keyword in rule.keywords:
            keyword_lower = keyword.lower()
            if keyword_lower not in self._keyword_index:
                self._keyword_index[keyword_lower] = []
            self._keyword_index[keyword_lower].append(rule.name)
    
    def register_batch(self, rules: List[RuleDefinition]) -> None:
        """批量注册规则"""
        for rule in rules:
            self.register(rule)
        self._initialized = True
    
    def match(self, text: str, category: Optional[RuleCategory] = None) -> List[tuple[str, float]]:
        """
        匹配文本返回匹配的规则及权重
        返回: [(rule_name, weight), ...]
        """
        text_lower = text.lower()
        matches = []
        
        # 确定要检查的规则
        rules_to_check = (
            self._category_rules.get(category, []) 
            if category else 
            self._rules.values()
        )
        
        for rule in rules_to_check:
            if not rule.enabled:
                continue
            
            # 检查关键词匹配
            for keyword in rule.keywords:
                if keyword.lower() in text_lower:
                    matches.append((rule.name, rule.weight))
                    break
            
            # 检查正则模式
            for pattern in rule.patterns:
                import re
                if re.search(pattern, text, re.IGNORECASE):
                    matches.append((rule.name, rule.weight))
                    break
        
        # 按权重排序
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    def classify(self, text: str) -> Dict[str, float]:
        """分类文本，返回各类别的置信度"""
        result = {}
        
        for category in RuleCategory:
            matches = self.match(text, category)
            if matches:
                # 计算类别置信度
                confidence = sum(w for _, w in matches)
                result[category.value] = min(confidence, 1.0)
        
        return result
    
    def get_rules(self, category: Optional[RuleCategory] = None) -> List[RuleDefinition]:
        """获取规则列表"""
        if category:
            return self._category_rules.get(category, [])
        return list(self._rules.values())
    
    def enable(self, name: str) -> bool:
        """启用规则"""
        if name in self._rules:
            self._rules[name].enabled = True
            return True
        return False
    
    def disable(self, name: str) -> bool:
        """禁用规则"""
        if name in self._rules:
            self._rules[name].enabled = False
            return True
        return False
    
    def load_from_file(self, path: str) -> None:
        """从JSON文件加载规则"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item in data.get('rules', []):
            rule = RuleDefinition(
                name=item['name'],
                category=RuleCategory(item['category']),
                keywords=item.get('keywords', []),
                patterns=item.get('patterns', []),
                weight=item.get('weight', 1.0),
                description=item.get('description', ''),
                enabled=item.get('enabled', True)
            )
            self.register(rule)
    
    def save_to_file(self, path: str) -> None:
        """保存规则到JSON文件"""
        data = {
            'rules': [
                {
                    'name': r.name,
                    'category': r.category.value,
                    'keywords': r.keywords,
                    'patterns': r.patterns,
                    'weight': r.weight,
                    'description': r.description,
                    'enabled': r.enabled
                }
                for r in self._rules.values()
            ]
        }
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# 全局规则注册表
_rule_registry = UnifiedRuleRegistry()


# =============================================================================
# 内置规则
# =============================================================================

def _register_builtin_rules():
    """注册内置规则"""
    
    # 查询分类规则
    query_rules = [
        RuleDefinition(
            name="factual_query",
            category=RuleCategory.QUERY_CLASSIFICATION,
            keywords=["多少", "几个", "数量", "how many", "number", "count", "who is", "什么是"],
            weight=1.0,
            description="事实查询"
        ),
        RuleDefinition(
            name="comparison_query", 
            category=RuleCategory.QUERY_CLASSIFICATION,
            keywords=["比较", "区别", "差异", "compare", "difference", "vs", "versus", "better"],
            weight=1.0,
            description="比较查询"
        ),
        RuleDefinition(
            name="procedural_query",
            category=RuleCategory.QUERY_CLASSIFICATION,
            keywords=["如何", "怎么", "方法", "how to", "method", "步骤", "流程"],
            weight=1.0,
            description="程序性查询"
        ),
        RuleDefinition(
            name="causal_query",
            category=RuleCategory.QUERY_CLASSIFICATION,
            keywords=["为什么", "原因", "why", "because", "cause", "reason", "由于"],
            weight=1.0,
            description="因果查询"
        ),
        RuleDefinition(
            name="temporal_query",
            category=RuleCategory.QUERY_CLASSIFICATION,
            keywords=["何时", "什么时候", "when", "时间", "日期", "year", "month", "day"],
            weight=1.0,
            description="时间查询"
        ),
    ]
    
    # 错误检测规则
    error_rules = [
        RuleDefinition(
            name="retryable_error",
            category=RuleCategory.ERROR_DETECTION,
            keywords=["timeout", "connection", "network", "unavailable", "rate limit"],
            weight=1.0,
            description="可重试错误"
        ),
        RuleDefinition(
            name="fatal_error",
            category=RuleCategory.ERROR_DETECTION,
            keywords=["config", "invalid", "missing", "not found", "permission"],
            weight=1.0,
            description="致命错误"
        ),
    ]
    
    _rule_registry.register_batch(query_rules + error_rules)


# 初始化内置规则
_register_builtin_rules()


# =============================================================================
# 便捷访问函数
# =============================================================================

def get_registry() -> UnifiedRuleRegistry:
    """获取规则注册表"""
    return _rule_registry


def classify_query(query: str) -> Dict[str, float]:
    """分类查询"""
    return _rule_registry.classify(query)


def match_keywords(text: str, category: Optional[RuleCategory] = None) -> List[tuple[str, float]]:
    """匹配关键词"""
    return _rule_registry.match(text, category)
