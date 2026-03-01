#!/usr/bin/env python3
"""
机器学习驱动的动态规则生成器 - 简化版本
功能已合并到utils模块中
"""

import logging
import re
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from src.utils.security_utils import security_utils


@dataclass
class Rule:
    """规则类"""
    name: str
    pattern: str
    rule_type: str
    action: str
    priority: int = 0
    description: str = ""


class RuleType:
    """规则类型常量"""
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"
    FILTERING = "filtering"
    ROUTING = "routing"


class RuleEngine:
    """规则引擎 - 简化版本"""
    
    def __init__(self):
        """初始化规则引擎"""
        self.rules: List[Rule] = []
        self.logger = logging.getLogger(__name__)
    
    def add_rule(self, rule: Rule) -> bool:
        """添加规则"""
        try:
            # 验证规则
            if not self._validate_rule(rule):
                return False
            
            # 检查规则是否已存在
            if self._rule_exists(rule):
                self.logger.warning(f"规则已存在: {rule.description}")
                return False
            
            # 添加规则
            self.rules.append(rule)
            
            # 记录规则添加历史
            self._record_rule_addition(rule)
            
            self.logger.info(f"规则添加成功: {rule.description}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加规则失败: {e}")
            return False
    
    def _validate_rule(self, rule: Rule) -> bool:
        """验证规则"""
        if not isinstance(rule, Rule):
            return False
        
        if not rule.pattern or not rule.description:
            return False
        
        # 验证正则表达式
        try:
            re.compile(rule.pattern)
            return True
        except re.error:
            return False
    
    def _rule_exists(self, rule: Rule) -> bool:
        """检查规则是否已存在"""
        for existing_rule in self.rules:
            if (existing_rule.pattern == rule.pattern and 
                existing_rule.description == rule.description):
                return True
        return False
    
    def _record_rule_addition(self, rule: Rule):
        """记录规则添加历史"""
        if not hasattr(self, 'rule_history'):
            self.rule_history = []
        
        self.rule_history.append({
            'action': 'add_rule',
            'rule': rule,
            'timestamp': time.time()
        })
    
    def validate_input_data(self, pattern: str) -> bool:
        """验证输入数据"""
        try:
            # 验证输入参数
            if not isinstance(pattern, str) or not pattern.strip():
                return False
            
            # 验证正则表达式模式
            re.compile(pattern)
            return True
        except re.error:
            return False
        except Exception as e:
            self.logger.error(f"验证输入数据失败: {e}")
            return False
    
    def apply_rules(self, data: str) -> Any:
        """应用规则"""
        try:
            result = data
            for rule in sorted(self.rules, key=lambda r: r.priority, reverse=True):
                if rule.rule_type == RuleType.VALIDATION:
                    if not re.search(rule.pattern, result):
                        return {
                            "error": f"验证失败: 不匹配模式 {rule.pattern}",
                            "rule_name": rule.name,
                            "input": result,
                            "timestamp": time.time()
                        }
                elif rule.rule_type == RuleType.TRANSFORMATION:
                    result = re.sub(rule.pattern, rule.action, result)
                elif rule.rule_type == RuleType.FILTERING:
                    if re.search(rule.pattern, result):
                        return {
                            "error": f"过滤失败: 匹配到过滤模式 {rule.pattern}",
                            "rule_name": rule.name,
                            "input": result,
                            "timestamp": time.time()
                        }
            
            return result
            
        except Exception as e:
            self.logger.error(f"应用规则失败: {e}")
            return {
                "error": f"应用规则失败: {e}",
                "input": data,
                "timestamp": time.time(),
                "rule_count": len(self.rules)
            }


class MLRuleGenerator:
    """机器学习驱动的动态规则生成器 - 简化版本"""
    
    def __init__(self):
        """初始化规则生成器"""
        self.logger = logging.getLogger(__name__)
        self.rule_engine = RuleEngine()
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """初始化默认规则"""
        # 添加基本规则
        self.rule_engine.add_rule(
            rule=Rule(
                name="basic_validation",
                pattern=r"^[a-zA-Z0-9\s]+$",
                rule_type=RuleType.VALIDATION,
                action="",
                priority=1,
                description="基本字符验证"
            )
        )
        
        self.rule_engine.add_rule(
            rule=Rule(
                name="xss_filter",
                pattern=r"<script.*?>.*?</script>",
                rule_type=RuleType.FILTERING,
                action="",
                priority=2,
                description="XSS过滤"
            )
        )
    
    def generate_rule(self, pattern: str, rule_type: str, action: str, 
                     priority: int = 0, description: str = "") -> Optional[Rule]:
        """生成规则"""
        try:
            # 验证输入
            if not self.rule_engine.validate_input_data(pattern):
                self.logger.warning("规则模式验证失败")
                return None
            
            # 创建规则
            rule = Rule(
                name=f"generated_rule_{int(time.time())}",
                pattern=pattern,
                rule_type=rule_type,
                action=action,
                priority=priority,
                description=description
            )
            
            # 添加到规则引擎
            if self.rule_engine.add_rule(rule):
                self.logger.info(f"规则生成成功: {description}")
                return rule
            else:
                self.logger.error("规则添加失败")
                return None
                
        except Exception as e:
            self.logger.error(f"规则生成失败: {e}")
            return None
    
    def process_data(self, data: str) -> Any:
        """处理数据"""
        try:
            return self.rule_engine.apply_rules(data)
        except Exception as e:
            self.logger.error(f"数据处理失败: {e}")
            return {
                "error": f"数据处理失败: {e}",
                "input": data,
                "timestamp": time.time()
            }
    
    def get_rules(self) -> List[Rule]:
        """获取所有规则"""
        return self.rule_engine.rules.copy()
    
    def clear_rules(self):
        """清空规则"""
        self.rule_engine.rules.clear()
        self.logger.info("规则已清空")


# 全局实例
_ml_rule_generator = None

def get_ml_rule_generator() -> MLRuleGenerator:
    """获取ML规则生成器实例"""
    global _ml_rule_generator
    if _ml_rule_generator is None:
        _ml_rule_generator = MLRuleGenerator()
    return _ml_rule_generator