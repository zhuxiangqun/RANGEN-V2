#!/usr/bin/env python3
"""
业务层 - 责任链模式实现
Business Handler Chain Pattern Implementations

提供规则处理器基类和具体处理器实现
"""
from abc import ABC, abstractmethod
from typing import Any, Optional
from src.core.services import get_core_logger


class RuleHandler(ABC):
    """规则处理器基类"""
    
    def __init__(self):
        self.next_handler: Optional['RuleHandler'] = None
    
    def set_next(self, handler: 'RuleHandler') -> 'RuleHandler':
        """设置下一个处理器"""
        self.next_handler = handler
        return handler
    
    def handle(self, rule_name: str, data: Any) -> bool:
        """处理规则"""
        try:
            # 验证规则名称
            if not rule_name or not isinstance(rule_name, str):
                return False
            
            # 验证数据
            if data is None:
                return False
            
            # 根据规则名称处理
            if rule_name == 'validation':
                return self._handle_validation_rule(data)
            elif rule_name == 'transformation':
                return self._handle_transformation_rule(data)
            elif rule_name == 'filtering':
                return self._handle_filtering_rule(data)
            elif rule_name == 'aggregation':
                return self._handle_aggregation_rule(data)
            else:
                return self._handle_default_rule(rule_name, data)
                
        except Exception as e:
            # 规则处理失败
            return False
    
    def _handle_validation_rule(self, data: Any) -> bool:
        """处理验证规则"""
        if isinstance(data, dict):
            # 检查必需字段
            required_fields = ['id', 'name']
            return all(field in data for field in required_fields)
        elif isinstance(data, (str, int, float)):
            return True
        else:
            return False
    
    def _handle_transformation_rule(self, data: Any) -> bool:
        """处理转换规则"""
        if isinstance(data, dict):
            # 转换数据格式
            return True
        elif isinstance(data, list):
            # 转换列表数据
            return len(data) > 0
        else:
            return False
    
    def _handle_filtering_rule(self, data: Any) -> bool:
        """处理过滤规则"""
        if isinstance(data, list):
            # 过滤列表数据
            return len(data) > 0
        elif isinstance(data, dict):
            # 过滤字典数据
            return len(data) > 0
        else:
            return False
    
    def _handle_aggregation_rule(self, data: Any) -> bool:
        """处理聚合规则"""
        if isinstance(data, list):
            # 聚合列表数据
            return len(data) > 0
        elif isinstance(data, dict):
            # 聚合字典数据
            return len(data) > 0
        else:
            return False
    
    def _handle_default_rule(self, rule_name: str, data: Any) -> bool:
        """处理默认规则"""
        # 默认规则：数据不为空即可
        return data is not None


class ValidationRuleHandler(RuleHandler):
    """验证规则处理器"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_core_logger("validation_rule_handler")
    
    def handle(self, rule_name: str, data: Any) -> bool:
        """处理验证规则"""
        try:
            if rule_name.startswith('validation_'):
                # 执行验证逻辑
                from src.layers.business_layer import _execute_validation_logic
                return _execute_validation_logic(rule_name, data)
            elif self.next_handler:
                return self.next_handler.handle(rule_name, data)
            return False
        except Exception as e:
            self.logger.error(f"验证规则处理失败: {e}")
            return False


class ProcessingRuleHandler(RuleHandler):
    """处理规则处理器"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_core_logger("processing_rule_handler")
    
    def handle(self, rule_name: str, data: Any) -> bool:
        """处理处理规则"""
        try:
            if rule_name.startswith('processing_'):
                # 执行处理逻辑
                from src.layers.business_layer import _execute_processing_logic
                return _execute_processing_logic(rule_name, data)
            elif self.next_handler:
                return self.next_handler.handle(rule_name, data)
            return False
        except Exception as e:
            self.logger.error(f"处理规则处理失败: {e}")
            return False


class DefaultRuleHandler(RuleHandler):
    """默认规则处理器"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_core_logger("default_rule_handler")
    
    def handle(self, rule_name: str, data: Any) -> bool:
        """处理默认规则"""
        try:
            # 执行默认处理逻辑
            from src.layers.business_layer import _execute_default_logic
            return _execute_default_logic(rule_name, data)
        except Exception as e:
            self.logger.error(f"默认规则处理失败: {e}")
            return False
