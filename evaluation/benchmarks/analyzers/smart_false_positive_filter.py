#!/usr/bin/env python3
"""
智能误报过滤器
基于代码语义和设计模式分析，过滤掉合理的"未实现"方法
"""

import ast
import re
import logging
from typing import List, Dict, Any, Set
from dataclasses import dataclass
from enum import Enum


class ImplementationIssueType(Enum):
    """实现问题类型"""
    UNIMPLEMENTED_METHOD = "unimplemented_method"
    SIMPLIFIED_IMPLEMENTATION = "simplified_implementation"
    PLACEHOLDER_CODE = "placeholder_code"
    MISSING_LOGIC = "missing_logic"
    EMPTY_FUNCTION = "empty_function"
    DUMMY_RETURN = "dummy_return"
    INCOMPLETE_IMPLEMENTATION = "incomplete_implementation"


@dataclass
class ImplementationIssue:
    """实现问题"""
    file_path: str
    line_number: int
    issue_type: ImplementationIssueType
    severity: str
    description: str
    suggestion: str
    code_snippet: str
    confidence: float = 0.0


@dataclass
class FilterRule:
    """过滤规则"""
    name: str
    description: str
    condition_func: callable
    confidence: float = 1.0


class SmartFalsePositiveFilter:
    """智能误报过滤器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.filter_rules = self._initialize_filter_rules()
    
    def _initialize_filter_rules(self) -> List[FilterRule]:
        """初始化过滤规则"""
        return [
            # 1. 抽象方法规则
            FilterRule(
                name="abstract_method",
                description="抽象方法或接口方法",
                condition_func=self._is_abstract_method,
                confidence=1.0
            ),
            
            # 2. 设计模式方法规则
            FilterRule(
                name="design_pattern_method",
                description="设计模式相关方法",
                condition_func=self._is_design_pattern_method,
                confidence=0.9
            ),
            
            # 3. 配置和状态方法规则
            FilterRule(
                name="config_state_method",
                description="配置和状态相关方法",
                condition_func=self._is_config_state_method,
                confidence=0.8
            ),
            
            # 4. 工具和辅助方法规则
            FilterRule(
                name="utility_method",
                description="工具和辅助方法",
                condition_func=self._is_utility_method,
                confidence=0.7
            ),
            
            # 5. 回退和默认方法规则
            FilterRule(
                name="fallback_method",
                description="回退和默认方法",
                condition_func=self._is_fallback_method,
                confidence=0.8
            ),
            
            # 6. 测试和调试方法规则
            FilterRule(
                name="test_debug_method",
                description="测试和调试方法",
                condition_func=self._is_test_debug_method,
                confidence=0.9
            ),
            
            # 7. 工厂和构建方法规则
            FilterRule(
                name="factory_builder_method",
                description="工厂和构建方法",
                condition_func=self._is_factory_builder_method,
                confidence=0.8
            ),
            
            # 8. 事件和回调方法规则
            FilterRule(
                name="event_callback_method",
                description="事件和回调方法",
                condition_func=self._is_event_callback_method,
                confidence=0.8
            ),
            
            # 9. 验证和检查方法规则
            FilterRule(
                name="validation_method",
                description="验证和检查方法",
                condition_func=self._is_validation_method,
                confidence=0.7
            ),
            
            # 10. 装饰器和元类方法规则
            FilterRule(
                name="decorator_metaclass_method",
                description="装饰器和元类方法",
                condition_func=self._is_decorator_metaclass_method,
                confidence=0.9
            )
        ]
    
    def filter_issues(self, issues: List[ImplementationIssue], file_content: str = "") -> List[ImplementationIssue]:
        """过滤误报问题"""
        filtered_issues = []
        
        for issue in issues:
            if self._should_filter_issue(issue, file_content):
                self.logger.debug(f"过滤误报: {issue.description} (规则: {self._get_matching_rule(issue, file_content)})")
                continue
            
            filtered_issues.append(issue)
        
        self.logger.info(f"过滤前: {len(issues)} 个问题, 过滤后: {len(filtered_issues)} 个问题")
        return filtered_issues
    
    def _should_filter_issue(self, issue: ImplementationIssue, file_content: str) -> bool:
        """判断是否应该过滤该问题"""
        for rule in self.filter_rules:
            if rule.condition_func(issue, file_content):
                return True
        return False
    
    def _get_matching_rule(self, issue: ImplementationIssue, file_content: str) -> str:
        """获取匹配的过滤规则"""
        for rule in self.filter_rules:
            if rule.condition_func(issue, file_content):
                return rule.name
        return "none"
    
    # ==================== 过滤规则实现 ====================
    
    def _is_abstract_method(self, issue: ImplementationIssue, file_content: str) -> bool:
        """检查是否是抽象方法"""
        method_name = self._extract_method_name(issue.code_snippet)
        
        # 检查方法名是否暗示抽象性
        abstract_keywords = ['abstract', 'interface', 'protocol', 'contract', 'template', 'base']
        if any(keyword in method_name.lower() for keyword in abstract_keywords):
            return True
        
        # 检查是否有@abstractmethod装饰器
        if '@abstractmethod' in issue.code_snippet or 'abstractmethod' in issue.code_snippet:
            return True
        
        # 检查是否在抽象基类中
        if self._is_in_abstract_class(issue, file_content):
            return True
        
        return False
    
    def _is_design_pattern_method(self, issue: ImplementationIssue, file_content: str) -> bool:
        """检查是否是设计模式方法"""
        method_name = self._extract_method_name(issue.code_snippet)
        
        # 设计模式相关方法名
        pattern_keywords = [
            'factory', 'builder', 'singleton', 'observer', 'strategy', 'adapter',
            'decorator', 'facade', 'proxy', 'command', 'state', 'visitor',
            'template', 'iterator', 'mediator', 'memento', 'chain', 'flyweight'
        ]
        
        if any(keyword in method_name.lower() for keyword in pattern_keywords):
            return True
        
        # 检查是否在模式类中
        if self._is_in_pattern_class(issue, file_content):
            return True
        
        return False
    
    def _is_config_state_method(self, issue: ImplementationIssue, file_content: str) -> bool:
        """检查是否是配置和状态方法"""
        method_name = self._extract_method_name(issue.code_snippet)
        
        # 配置和状态相关方法名（但不过滤硬编码配置值问题）
        config_keywords = [
            'get_', 'set_', 'is_', 'has_', 'can_', 'should_', 'will_',
            'status', 'state', 'ready', 'valid', 'empty', 'enabled', 'disabled'
        ]
        
        # 如果问题类型是硬编码配置值，不过滤
        if hasattr(issue, 'issue_type') and 'hardcoded' in str(issue.issue_type).lower():
            return False
        
        # 如果描述包含硬编码相关词汇，不过滤
        if 'hardcoded' in issue.description.lower() or '硬编码' in issue.description:
            return False
        
        if any(method_name.lower().startswith(keyword) for keyword in config_keywords):
            return True
        
        return False
    
    def _is_utility_method(self, issue: ImplementationIssue, file_content: str) -> bool:
        """检查是否是工具方法"""
        method_name = self._extract_method_name(issue.code_snippet)
        
        # 工具方法关键词
        utility_keywords = [
            'util', 'helper', 'format', 'parse', 'convert', 'transform',
            'validate', 'check', 'verify', 'normalize', 'sanitize',
            'encode', 'decode', 'serialize', 'deserialize'
        ]
        
        if any(keyword in method_name.lower() for keyword in utility_keywords):
            return True
        
        return False
    
    def _is_fallback_method(self, issue: ImplementationIssue, file_content: str) -> bool:
        """检查是否是回退方法"""
        method_name = self._extract_method_name(issue.code_snippet)
        
        # 回退方法关键词
        fallback_keywords = [
            'fallback', 'default', 'backup', 'alternative', 'emergency',
            'simple', 'basic', 'minimal', 'placeholder', 'stub'
        ]
        
        if any(keyword in method_name.lower() for keyword in fallback_keywords):
            return True
        
        # 检查方法体是否包含回退逻辑
        if any(keyword in issue.code_snippet.lower() for keyword in ['fallback', 'default', 'backup']):
            return True
        
        return False
    
    def _is_test_debug_method(self, issue: ImplementationIssue, file_content: str) -> bool:
        """检查是否是测试和调试方法"""
        method_name = self._extract_method_name(issue.code_snippet)
        
        # 测试和调试方法关键词
        test_keywords = [
            'test_', 'debug_', 'mock_', 'fake_', 'dummy_', 'stub_',
            'setup', 'teardown', 'fixture', 'assert', 'verify'
        ]
        
        if any(method_name.lower().startswith(keyword) for keyword in test_keywords):
            return True
        
        return False
    
    def _is_factory_builder_method(self, issue: ImplementationIssue, file_content: str) -> bool:
        """检查是否是工厂和构建方法"""
        method_name = self._extract_method_name(issue.code_snippet)
        
        # 工厂和构建方法关键词
        factory_keywords = [
            'create', 'build', 'make', 'construct', 'generate', 'produce',
            'factory', 'builder', 'manufacturer', 'assembler'
        ]
        
        if any(keyword in method_name.lower() for keyword in factory_keywords):
            return True
        
        return False
    
    def _is_event_callback_method(self, issue: ImplementationIssue, file_content: str) -> bool:
        """检查是否是事件和回调方法"""
        method_name = self._extract_method_name(issue.code_snippet)
        
        # 事件和回调方法关键词
        event_keywords = [
            'on_', 'handle_', 'callback', 'event', 'notify', 'trigger',
            'listen', 'observe', 'watch', 'monitor'
        ]
        
        if any(method_name.lower().startswith(keyword) for keyword in event_keywords):
            return True
        
        return False
    
    def _is_validation_method(self, issue: ImplementationIssue, file_content: str) -> bool:
        """检查是否是验证方法"""
        method_name = self._extract_method_name(issue.code_snippet)
        
        # 验证方法关键词
        validation_keywords = [
            'validate', 'check', 'verify', 'assert', 'ensure', 'confirm',
            'is_valid', 'is_correct', 'is_proper', 'is_safe'
        ]
        
        if any(keyword in method_name.lower() for keyword in validation_keywords):
            return True
        
        return False
    
    def _is_decorator_metaclass_method(self, issue: ImplementationIssue, file_content: str) -> bool:
        """检查是否是装饰器和元类方法"""
        method_name = self._extract_method_name(issue.code_snippet)
        
        # 装饰器和元类方法关键词
        decorator_keywords = [
            'decorator', 'wrapper', 'decorate', 'wrap', 'enhance',
            'metaclass', 'meta', 'classmethod', 'staticmethod'
        ]
        
        if any(keyword in method_name.lower() for keyword in decorator_keywords):
            return True
        
        # 检查是否有装饰器语法
        if '@' in issue.code_snippet:
            return True
        
        return False
    
    # ==================== 辅助方法 ====================
    
    def _extract_method_name(self, code_snippet: str) -> str:
        """从代码片段中提取方法名"""
        lines = code_snippet.split('\n')
        for line in lines:
            if 'def ' in line:
                match = re.search(r'def\s+(\w+)', line)
                if match:
                    return match.group(1)
        return ""
    
    def _is_in_abstract_class(self, issue: ImplementationIssue, file_content: str) -> bool:
        """检查是否在抽象类中"""
        # 查找包含该方法的类
        lines = file_content.split('\n')
        method_line = issue.line_number
        
        # 确保行号在有效范围内
        if method_line <= 0 or method_line > len(lines):
            return False
        
        # 向上查找类定义
        for i in range(method_line - 1, -1, -1):
            if i >= len(lines):
                continue
            line = lines[i].strip()
            if line.startswith('class '):
                # 检查类是否有抽象相关关键词
                abstract_keywords = ['Abstract', 'Base', 'Interface', 'Protocol', 'ABC']
                if any(keyword in line for keyword in abstract_keywords):
                    return True
                break
        
        return False
    
    def _is_in_pattern_class(self, issue: ImplementationIssue, file_content: str) -> bool:
        """检查是否在设计模式类中"""
        lines = file_content.split('\n')
        method_line = issue.line_number
        
        # 确保行号在有效范围内
        if method_line <= 0 or method_line > len(lines):
            return False
        
        # 向上查找类定义
        for i in range(method_line - 1, -1, -1):
            if i >= len(lines):
                continue
            line = lines[i].strip()
            if line.startswith('class '):
                # 检查类名是否包含模式关键词
                pattern_keywords = ['Factory', 'Builder', 'Singleton', 'Observer', 'Strategy', 'Adapter']
                if any(keyword in line for keyword in pattern_keywords):
                    return True
                break
        
        return False
