"""
配置驱动的动态路由 - 阶段2.4
支持动态路由规则配置和热更新
"""
import logging
import json
import time
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum

from src.core.langgraph_unified_workflow import ResearchSystemState

logger = logging.getLogger(__name__)


class RouteCondition(Enum):
    """路由条件类型"""
    LESS_THAN = "<"
    LESS_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="
    GREATER_THAN = ">"
    GREATER_EQUAL = ">="
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    REGEX = "regex"


@dataclass
class RouteRule:
    """路由规则"""
    name: str
    priority: int = 0  # 优先级（数字越大优先级越高）
    conditions: List[Dict[str, Any]] = field(default_factory=list)  # 条件列表
    target_path: str = "complex"  # 目标路径
    enabled: bool = True  # 是否启用
    description: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    def evaluate(self, state: ResearchSystemState) -> bool:
        """评估规则是否匹配
        
        Args:
            state: 工作流状态
        
        Returns:
            是否匹配
        """
        if not self.enabled:
            return False
        
        for condition in self.conditions:
            if not self._evaluate_condition(condition, state):
                return False
        
        return True
    
    def _evaluate_condition(self, condition: Dict[str, Any], state: ResearchSystemState) -> bool:
        """评估单个条件"""
        field_name = condition.get('field')
        operator = condition.get('operator', '==')
        value = condition.get('value')
        
        if field_name not in state:
            return False
        
        field_value = state[field_name]
        
        try:
            if operator == RouteCondition.LESS_THAN.value:
                return field_value < value
            elif operator == RouteCondition.LESS_EQUAL.value:
                return field_value <= value
            elif operator == RouteCondition.EQUAL.value:
                return field_value == value
            elif operator == RouteCondition.NOT_EQUAL.value:
                return field_value != value
            elif operator == RouteCondition.GREATER_THAN.value:
                return field_value > value
            elif operator == RouteCondition.GREATER_EQUAL.value:
                return field_value >= value
            elif operator == RouteCondition.IN.value:
                return field_value in value if isinstance(value, (list, tuple)) else False
            elif operator == RouteCondition.NOT_IN.value:
                return field_value not in value if isinstance(value, (list, tuple)) else True
            elif operator == RouteCondition.CONTAINS.value:
                return value in str(field_value) if isinstance(field_value, (str, list)) else False
            elif operator == RouteCondition.REGEX.value:
                import re
                return bool(re.search(value, str(field_value)))
            else:
                logger.warning(f"未知的操作符: {operator}")
                return False
        except Exception as e:
            logger.warning(f"评估条件失败: {e}")
            return False


class ConfigurableRouter:
    """配置驱动的动态路由器
    
    支持：
    - 动态路由规则配置
    - 路由规则热更新
    - 规则优先级
    - 条件表达式
    """
    
    def __init__(self, config_center=None):
        """
        Args:
            config_center: 统一配置中心（可选）
        """
        self.config_center = config_center
        self.rules: List[RouteRule] = []
        self.default_path = "complex"  # 默认路径
        
        # 从配置中心加载路由规则
        self._load_rules_from_config()
        
        # 如果没有规则，创建默认规则
        if not self.rules:
            self._create_default_rules()
    
    def _load_rules_from_config(self):
        """从配置中心加载路由规则"""
        if not self.config_center:
            try:
                from src.utils.unified_centers import get_unified_config_center
                self.config_center = get_unified_config_center()
            except Exception as e:
                logger.warning(f"无法获取统一配置中心: {e}")
                return
        
        try:
            # 从配置中心获取路由规则
            routing_config = self.config_center.get_config_section("routing")
            if routing_config and 'rules' in routing_config:
                rules_data = routing_config['rules']
                if isinstance(rules_data, str):
                    rules_data = json.loads(rules_data)
                
                for rule_data in rules_data:
                    try:
                        rule = RouteRule(**rule_data)
                        self.rules.append(rule)
                    except Exception as e:
                        logger.warning(f"加载路由规则失败: {e}")
                
                logger.info(f"✅ 从配置中心加载了 {len(self.rules)} 个路由规则")
        except Exception as e:
            logger.warning(f"从配置中心加载路由规则失败: {e}")
    
    def _create_default_rules(self):
        """创建默认路由规则"""
        default_rules = [
            RouteRule(
                name="simple_query_rule",
                priority=10,
                conditions=[
                    {"field": "complexity_score", "operator": "<", "value": 3.0}
                ],
                target_path="simple",
                description="简单查询：复杂度 < 3.0"
            ),
            RouteRule(
                name="complex_query_rule",
                priority=5,
                conditions=[
                    {"field": "complexity_score", "operator": ">=", "value": 3.0}
                ],
                target_path="complex",
                description="复杂查询：复杂度 >= 3.0"
            )
        ]
        
        self.rules.extend(default_rules)
        logger.info(f"✅ 创建了 {len(default_rules)} 个默认路由规则")
    
    def add_rule(self, rule: RouteRule) -> bool:
        """添加路由规则
        
        Args:
            rule: 路由规则
        
        Returns:
            是否成功
        """
        try:
            # 检查是否已存在同名规则
            existing_rule = next((r for r in self.rules if r.name == rule.name), None)
            if existing_rule:
                # 更新现有规则
                existing_rule.priority = rule.priority
                existing_rule.conditions = rule.conditions
                existing_rule.target_path = rule.target_path
                existing_rule.enabled = rule.enabled
                existing_rule.description = rule.description
                existing_rule.updated_at = time.time()
                logger.info(f"✅ 更新路由规则: {rule.name}")
            else:
                # 添加新规则
                self.rules.append(rule)
                logger.info(f"✅ 添加路由规则: {rule.name}")
            
            # 按优先级排序
            self.rules.sort(key=lambda r: r.priority, reverse=True)
            
            # 保存到配置中心（如果可用）
            self._save_rules_to_config()
            
            return True
        except Exception as e:
            logger.error(f"添加路由规则失败: {e}")
            return False
    
    def remove_rule(self, rule_name: str) -> bool:
        """删除路由规则
        
        Args:
            rule_name: 规则名称
        
        Returns:
            是否成功
        """
        try:
            self.rules = [r for r in self.rules if r.name != rule_name]
            logger.info(f"✅ 删除路由规则: {rule_name}")
            
            # 保存到配置中心
            self._save_rules_to_config()
            
            return True
        except Exception as e:
            logger.error(f"删除路由规则失败: {e}")
            return False
    
    def _save_rules_to_config(self):
        """保存路由规则到配置中心"""
        if not self.config_center:
            return
        
        try:
            rules_data = [
                {
                    "name": rule.name,
                    "priority": rule.priority,
                    "conditions": rule.conditions,
                    "target_path": rule.target_path,
                    "enabled": rule.enabled,
                    "description": rule.description
                }
                for rule in self.rules
            ]
            
            self.config_center.set_config_value("routing", "rules", json.dumps(rules_data))
            logger.debug(f"✅ 保存了 {len(rules_data)} 个路由规则到配置中心")
        except Exception as e:
            logger.warning(f"保存路由规则到配置中心失败: {e}")
    
    def route(self, state: ResearchSystemState) -> str:
        """根据状态和规则决定路由路径
        
        Args:
            state: 工作流状态
        
        Returns:
            路由路径
        """
        # 按优先级顺序评估规则
        for rule in self.rules:
            if rule.evaluate(state):
                logger.info(f"✅ [路由] 规则 '{rule.name}' 匹配，路由到: {rule.target_path}")
                return rule.target_path
        
        # 如果没有规则匹配，使用默认路径
        logger.info(f"ℹ️ [路由] 没有规则匹配，使用默认路径: {self.default_path}")
        return self.default_path
    
    def get_rules(self) -> List[RouteRule]:
        """获取所有路由规则"""
        return self.rules.copy()
    
    def reload_rules(self):
        """重新加载路由规则（热更新）"""
        old_count = len(self.rules)
        self.rules.clear()
        self._load_rules_from_config()
        if not self.rules:
            self._create_default_rules()
        
        new_count = len(self.rules)
        logger.info(f"🔄 [路由] 重新加载路由规则: {old_count} -> {new_count}")


# 全局路由器实例
_global_router: Optional[ConfigurableRouter] = None


def get_configurable_router() -> ConfigurableRouter:
    """获取配置驱动的路由器实例（单例）"""
    global _global_router
    if _global_router is None:
        _global_router = ConfigurableRouter()
    return _global_router

