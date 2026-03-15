#!/usr/bin/env python3
"""
基于AST深度分析的未实现方法检测器
完全基于代码结构分析，不依赖正则表达式
"""

import ast
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, List, Optional
from base_analyzer import BaseAnalyzer
from smart_false_positive_filter import SmartFalsePositiveFilter, ImplementationIssue, ImplementationIssueType


# ImplementationIssueType 和 ImplementationIssue 已从 smart_false_positive_filter 导入


class UnimplementedMethodAnalyzer(BaseAnalyzer):
    """基于AST深度分析的未实现方法和简化功能分析器"""
    
    def __init__(self, python_files: List[str]):
        super().__init__(python_files)
        
        # 基于AST分析的复杂度阈值 - 调整为更合理的标准
        self.method_complexity_thresholds = {
            'min_lines': 3,  # 最小行数（提高要求，避免误报）
            'min_statements': 2,  # 最小语句数（提高要求）
            'min_complexity': 2,  # 最小复杂度
            'min_parameters': 0,  # 最小参数数
            'min_local_variables': 0,  # 最小局部变量数
        }
        
        # 初始化智能误报过滤器
        self.false_positive_filter = SmartFalsePositiveFilter()
    
    def analyze_file(self, file_path: str) -> List[ImplementationIssue]:
        """分析单个文件"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return issues
        
        # 基于AST分析
        try:
            tree = ast.parse(content)
            ast_issues = self._analyze_ast_deep(tree, file_path, content)
            issues.extend(ast_issues)
        except SyntaxError as e:
            self.logger.warning(f"Syntax error in {file_path}: {e}")
        
        # 应用智能误报过滤器
        filtered_issues = self.false_positive_filter.filter_issues(issues, content)
        
        return filtered_issues
    
    def _analyze_ast_deep(self, tree: ast.AST, file_path: str, content: str) -> List[ImplementationIssue]:
        """使用AST深度分析代码"""
        issues = []
        lines = content.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                method_issues = self._analyze_method_deep(node, file_path, lines, content)
                issues.extend(method_issues)
            elif isinstance(node, ast.ClassDef):
                class_issues = self._analyze_class_deep(node, file_path, lines, content)
                issues.extend(class_issues)
        
        return issues
    
    def _analyze_method_deep(self, method_node: ast.FunctionDef, file_path: str, 
                           lines: List[str], content: str) -> List[ImplementationIssue]:
        """深度分析方法实现"""
        issues = []
        line_number = method_node.lineno
        method_name = method_node.name
        method_content = self._get_method_content(method_node, lines)
        
        # 1. 检查空方法
        if self._is_empty_method(method_node):
            issues.append(ImplementationIssue(
                file_path=file_path,
                line_number=line_number,
                issue_type=ImplementationIssueType.EMPTY_FUNCTION,
                severity='high',
                description=f'方法 {method_name} 为空实现',
                suggestion='实现方法的具体逻辑或添加文档说明',
                code_snippet=method_content,
                confidence=1.0
            ))
        
        # 2. 检查简化实现
        elif self._is_simplified_implementation(method_node):
            issues.append(ImplementationIssue(
                file_path=file_path,
                line_number=line_number,
                issue_type=ImplementationIssueType.SIMPLIFIED_IMPLEMENTATION,
                severity='medium',
                description=f'方法 {method_name} 实现过于简化',
                suggestion='实现完整的方法逻辑',
                code_snippet=method_content,
                confidence=0.9
            ))
        
        # 3. 检查占位符代码
        elif self._has_placeholder_code(method_node, content):
            issues.append(ImplementationIssue(
                file_path=file_path,
                line_number=line_number,
                issue_type=ImplementationIssueType.PLACEHOLDER_CODE,
                severity='medium',
                description=f'方法 {method_name} 包含占位符代码',
                suggestion='替换占位符为实际实现',
                code_snippet=method_content,
                confidence=0.8
            ))
        
        # 4. 检查缺失逻辑
        elif self._has_missing_logic(method_node):
            issues.append(ImplementationIssue(
                file_path=file_path,
                line_number=line_number,
                issue_type=ImplementationIssueType.MISSING_LOGIC,
                severity='low',
                description=f'方法 {method_name} 可能缺少重要逻辑',
                suggestion='检查并完善方法实现',
                code_snippet=method_content,
                confidence=0.7
            ))
        
        # 5. 检查虚拟返回
        elif self._has_dummy_return(method_node):
            issues.append(ImplementationIssue(
                file_path=file_path,
                line_number=line_number,
                issue_type=ImplementationIssueType.DUMMY_RETURN,
                severity='medium',
                description=f'方法 {method_name} 包含虚拟返回值',
                suggestion='实现真实的返回值逻辑',
                code_snippet=method_content,
                confidence=0.8
            ))
        
        # 6. 检查不完整实现（只对核心业务方法）
        elif self._is_core_business_method(method_node) and self._is_incomplete_implementation(method_node):
            issues.append(ImplementationIssue(
                file_path=file_path,
                line_number=line_number,
                issue_type=ImplementationIssueType.INCOMPLETE_IMPLEMENTATION,
                severity='medium',
                description=f'核心业务方法 {method_name} 实现不完整',
                suggestion='完善方法实现',
                code_snippet=method_content,
                confidence=0.8
            ))
        
        return issues
    
    def _analyze_class_deep(self, class_node: ast.ClassDef, file_path: str, 
                          lines: List[str], content: str) -> List[ImplementationIssue]:
        """深度分析类实现"""
        issues = []
        
        # 检查类中的方法
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                method_issues = self._analyze_method_deep(node, file_path, lines, content)
                issues.extend(method_issues)
        
        return issues
    
    def _is_empty_method(self, method_node: ast.FunctionDef) -> bool:
        """检查方法是否为空"""
        # 检查方法体是否为空
        if not method_node.body:
            return True
        
        # 检查方法体是否只包含pass
        if len(method_node.body) == 1 and isinstance(method_node.body[0], ast.Pass):
            return True
        
        # 检查方法体是否只包含省略号
        if len(method_node.body) == 1 and isinstance(method_node.body[0], ast.Expr):
            if isinstance(method_node.body[0].value, ast.Constant) and method_node.body[0].value.value is Ellipsis:
                return True
        
        return False
    
    def _is_simplified_implementation(self, method_node: ast.FunctionDef) -> bool:
        """检查方法实现是否过于简化 - 基于功能实现而非结构特征"""
        if not method_node.body:
            return True
        
        # 检查是否只有pass语句
        if len(method_node.body) == 1 and isinstance(method_node.body[0], ast.Pass):
            return True
        
        # 检查是否只有NotImplementedError
        if len(method_node.body) == 1 and isinstance(method_node.body[0], ast.Raise):
            if isinstance(method_node.body[0].exc, ast.Name) and method_node.body[0].exc.id == 'NotImplementedError':
                return True
        
        # 如果是合理的简单方法，不标记为简化实现
        if self._is_reasonable_simple_method(method_node):
            return False
        
        # 检查是否有完整的try-except-return结构
        if self._has_complete_try_except_return(method_node):
            return False
        
        # 检查是否是简单的工具方法
        if self._is_simple_utility_method(method_node):
            return False
        
        # 检查是否是内部函数（如dfs, bfs等算法函数）
        if self._is_internal_algorithm_function(method_node):
            return False
        
        # 检查语句数量，如果已经有足够的语句，不算简化实现
        statement_count = self._count_statements(method_node)
        if statement_count >= 6:  # 降低阈值，因为有些方法虽然简单但完整
            return False
        
        # 检查是否有循环、条件、异常处理等复杂结构
        if self._has_complex_structures(method_node):
            return False
        
        # 基于功能实现判断，而非行数
        return self._has_incomplete_functionality(method_node)
    
    def _is_internal_algorithm_function(self, method_node: ast.FunctionDef) -> bool:
        """检查是否是内部算法函数"""
        method_name = method_node.name.lower()
        
        # 常见的算法函数名
        algorithm_functions = [
            'dfs', 'bfs', 'dijkstra', 'floyd', 'kruskal', 'prim',
            'quicksort', 'mergesort', 'heapsort', 'bubblesort',
            'binary_search', 'linear_search', 'hash_function',
            'topological_sort', 'cycle_detection', 'path_finding',
            'visit', 'traverse', 'walk', 'explore', 'search'
        ]
        
        if method_name in algorithm_functions:
            return True
        
        # 检查是否是内部函数（嵌套在类方法中）
        # 这通常意味着它是一个辅助函数，实现可能相对简单但完整
        # 注意：AST节点没有parent属性，这里通过其他方式判断
        
        # 检查函数是否在类方法内部定义
        # 通过检查缩进级别来判断
        if hasattr(method_node, 'col_offset') and method_node.col_offset > 8:
            return True
        
        # 检查是否是递归函数（如dfs, bfs等）
        if self._is_recursive_function(method_node):
            return True
        
        return False
    
    def _is_recursive_function(self, method_node: ast.FunctionDef) -> bool:
        """检查是否是递归函数"""
        method_name = method_node.name
        
        # 检查函数是否调用自己
        for node in ast.walk(method_node):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == method_name:
                    return True
                elif isinstance(node.func, ast.Attribute) and node.func.attr == method_name:
                    return True
        
        return False
    
    def _has_complex_structures(self, method_node: ast.FunctionDef) -> bool:
        """检查是否有复杂结构"""
        has_loop = False
        has_condition = False
        has_exception = False
        has_nested_call = False
        
        for node in ast.walk(method_node):
            if isinstance(node, (ast.For, ast.While)):
                has_loop = True
            elif isinstance(node, ast.If):
                has_condition = True
            elif isinstance(node, (ast.Try, ast.ExceptHandler)):
                has_exception = True
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Call):
                has_nested_call = True
        
        # 如果有循环、条件、异常处理或嵌套调用，认为是复杂结构
        return has_loop or has_condition or has_exception or has_nested_call
    
    def _has_incomplete_functionality(self, method_node: ast.FunctionDef) -> bool:
        """检查方法是否有不完整的功能实现"""
        method_name = method_node.name.lower()
        
        # 检查是否只是返回硬编码值
        if self._only_returns_hardcoded_values(method_node):
            return True
        
        # 检查是否只是记录日志而没有实际处理
        if self._only_logs_without_processing(method_node):
            return True
        
        # 检查是否只是抛出异常而没有处理逻辑
        if self._only_raises_exceptions(method_node):
            return True
        
        # 检查是否只是返回None或空值
        if self._only_returns_none_or_empty(method_node):
            return True
        
        # 检查是否只是调用其他方法而没有自己的逻辑
        if self._only_delegates_without_logic(method_node):
            return True
        
        return False
    
    def _only_returns_hardcoded_values(self, method_node: ast.FunctionDef) -> bool:
        """检查是否只返回硬编码值"""
        # 检查方法是否有计算逻辑
        has_calculation = False
        for node in ast.walk(method_node):
            if isinstance(node, (ast.Assign, ast.For, ast.While, ast.If, ast.Call)):
                has_calculation = True
                break
        
        # 如果方法有计算逻辑，即使返回常量值也不算硬编码
        if has_calculation:
            return False
        
        # 检查是否只返回简单的常量值
        for node in ast.walk(method_node):
            if isinstance(node, ast.Return):
                if node.value is not None:
                    # 检查是否返回常量值
                    if isinstance(node.value, ast.Constant):
                        return True
                    # 检查是否返回硬编码的字符串、数字等
                    if isinstance(node.value, (ast.Str, ast.Num)):
                        return True
        return False
    
    def _only_logs_without_processing(self, method_node: ast.FunctionDef) -> bool:
        """检查是否只记录日志而没有实际处理"""
        has_logging = False
        has_processing = False
        
        for node in ast.walk(method_node):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ['info', 'debug', 'warning', 'error', 'critical']:
                        has_logging = True
                elif isinstance(node.func, ast.Name):
                    if node.func.id in ['print', 'log']:
                        has_logging = True
            elif isinstance(node, (ast.Assign, ast.For, ast.While, ast.If)):
                has_processing = True
        
        return has_logging and not has_processing
    
    def _only_raises_exceptions(self, method_node: ast.FunctionDef) -> bool:
        """检查是否只抛出异常"""
        has_raise = False
        has_other_logic = False
        
        for node in ast.walk(method_node):
            if isinstance(node, ast.Raise):
                has_raise = True
            elif isinstance(node, (ast.Assign, ast.Return, ast.For, ast.While, ast.If)):
                has_other_logic = True
        
        return has_raise and not has_other_logic
    
    def _only_returns_none_or_empty(self, method_node: ast.FunctionDef) -> bool:
        """检查是否只返回None或空值"""
        for node in ast.walk(method_node):
            if isinstance(node, ast.Return):
                if node.value is None:
                    return True
                if isinstance(node.value, ast.Constant):
                    if node.value.value in [None, "", [], {}, 0, False]:
                        return True
        return False
    
    def _only_delegates_without_logic(self, method_node: ast.FunctionDef) -> bool:
        """检查是否只是委托给其他方法而没有自己的逻辑"""
        # 如果方法体有多个语句，肯定不是简单委托
        if len(method_node.body) > 1:
            return False
        
        # 检查方法体是否只有一个return语句
        if len(method_node.body) == 1:
            node = method_node.body[0]
            if isinstance(node, ast.Return):
                if isinstance(node.value, ast.Call):
                    # 检查是否有参数处理、条件判断或其他逻辑
                    has_logic = False
                    for child in ast.walk(method_node):
                        if isinstance(child, (ast.Assign, ast.If, ast.For, ast.While, ast.Try)):
                            has_logic = True
                            break
                        # 检查是否有变量引用（不是简单的参数传递）
                        if isinstance(child, ast.Name) and child.id not in [arg.arg for arg in method_node.args.args]:
                            has_logic = True
                            break
                    return not has_logic
        return False
    
    def _is_only_try_except_wrapper(self, method_node: ast.FunctionDef) -> bool:
        """检查是否只是try-except包装的简单逻辑"""
        if len(method_node.body) != 1:
            return False
        
        try_node = method_node.body[0]
        if not isinstance(try_node, ast.Try):
            return False
        
        # 检查try块是否只有简单的逻辑
        try_body = try_node.body
        if len(try_body) == 1:
            # 如果try块只有一个语句，可能是简化实现
            if isinstance(try_body[0], (ast.Return, ast.Assign, ast.Expr)):
                return True
        
        # 检查except块是否只是记录日志或返回默认值
        for handler in try_node.handlers:
            if len(handler.body) == 1:
                if isinstance(handler.body[0], (ast.Return, ast.Expr)):
                    return True
        
        return False
    
    def _is_reasonable_simple_method(self, method_node: ast.FunctionDef) -> bool:
        """检查是否是合理的简单方法"""
        method_name = method_node.name.lower()
        
        # getter/setter方法
        if method_name.startswith(('get_', 'set_', 'is_', 'has_', 'can_', 'should_', 'will_', 'would_')):
            return True
        
        # 配置相关方法
        if any(keyword in method_name for keyword in ['config', 'option', 'setting', 'default', 'value', 'param', 'arg']):
            return True
        
        # 状态检查方法
        if any(keyword in method_name for keyword in ['status', 'state', 'ready', 'valid', 'empty', 'null', 'none']):
            return True
        
        # 工具方法
        if any(keyword in method_name for keyword in ['util', 'helper', 'format', 'parse', 'convert', 'transform', 'normalize']):
            return True
        
        # 初始化方法
        if method_name in ['__init__', '__new__', '__del__', '__enter__', '__exit__']:
            return True
        
        # 属性访问方法
        if method_name.startswith('__') and method_name.endswith('__'):
            return True
        
        # 工厂方法
        if any(keyword in method_name for keyword in ['create', 'make', 'build', 'new', 'factory']):
            return True
        
        # 时间戳和ID相关方法
        if any(keyword in method_name for keyword in ['timestamp', 'id', 'uuid', 'guid', 'hash', 'key']):
            return True
        
        # 权限和验证方法
        if any(keyword in method_name for keyword in ['permission', 'auth', 'check', 'verify', 'validate']):
            return True
        
        # 日志和调试方法
        if any(keyword in method_name for keyword in ['log', 'debug', 'trace', 'print', 'output']):
            return True
        
        # 如果方法有完整的try-except-return结构，认为是合理的
        if self._has_complete_try_except_return(method_node):
            return True
        
        # 如果方法有足够的语句数量，认为是合理的
        statement_count = self._count_statements(method_node)
        if statement_count >= 6:  # 提高阈值
            return True
        
        # 验证方法
        if any(keyword in method_name for keyword in ['check', 'verify', 'validate', 'test', 'assert']):
            return True
        
        # 清理方法
        if any(keyword in method_name for keyword in ['clean', 'clear', 'reset', 'close', 'destroy']):
            return True
        
        return False
    
    def _is_expected_to_be_complex(self, method_node: ast.FunctionDef) -> bool:
        """检查方法是否应该复杂"""
        method_name = method_node.name.lower()
        
        # 这些方法名暗示应该复杂（更严格的标准）
        complex_keywords = ['process', 'analyze', 'calculate', 'compute', 'generate', 'create', 'build', 'train', 'learn', 'optimize']
        
        # 只对明显需要复杂实现的方法应用严格检查
        if any(keyword in method_name for keyword in complex_keywords):
            # 检查方法是否已经有足够的实现
            if len(method_node.body) > 10:  # 如果已经有10行以上，可能已经足够复杂
                return False
            return True
        
        # 如果方法有很多参数，可能应该复杂
        if len(method_node.args.args) > 5:  # 提高参数数量要求
            return True
        
        # 检查是否是核心业务方法
        if self._is_core_business_method(method_node):
            return True
        
        return False
    
    def _count_statements(self, method_node: ast.FunctionDef) -> int:
        """计算方法中的语句数量"""
        count = 0
        for node in ast.walk(method_node):
            if isinstance(node, (ast.Assign, ast.Return, ast.If, ast.For, ast.While, 
                               ast.Try, ast.With, ast.Raise, ast.Assert)):
                count += 1
        return count
    
    def _has_only_simple_returns(self, method_node: ast.FunctionDef) -> bool:
        """检查是否只包含简单的返回语句"""
        return_statements = []
        
        for node in ast.walk(method_node):
            if isinstance(node, ast.Return):
                return_statements.append(node)
        
        if not return_statements:
            return False
        
        # 检查所有返回语句是否都是简单的字面量
        for return_node in return_statements:
            if return_node.value is not None:
                if not isinstance(return_node.value, (ast.Constant, ast.Name, ast.NameConstant)):
                    return False
                # 检查是否是简单的字面量
                if isinstance(return_node.value, ast.Constant):
                    if return_node.value.value in [True, False, None, 0, 1, "", []]:
                        continue
                    else:
                        return False
        
        return True
    
    def _has_placeholder_code(self, method_node: ast.FunctionDef, content: str) -> bool:
        """检查方法是否包含占位符代码"""
        # 检查方法体中是否有NotImplementedError
        for node in ast.walk(method_node):
            if isinstance(node, ast.Raise):
                if isinstance(node.exc, ast.Name) and node.exc.id == 'NotImplementedError':
                    return True
                elif isinstance(node.exc, ast.Call):
                    if isinstance(node.exc.func, ast.Name) and node.exc.func.id == 'NotImplementedError':
                        return True
        
        # 检查方法体中是否有TODO、FIXME等注释（但排除检测这些注释的方法）
        method_name = method_node.name.lower()
        if 'detect' in method_name or 'check' in method_name or 'analyze' in method_name:
            # 如果是检测方法，不将TODO检测视为占位符
            return False
        
        method_lines = self._get_method_lines(method_node, content)
        for line in method_lines:
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in ['todo', 'fixme', 'xxx', '待实现', '未实现']):
                return True
        
        return False
    
    def _has_missing_logic(self, method_node: ast.FunctionDef) -> bool:
        """检查方法是否缺少重要逻辑"""
        method_name = method_node.name.lower()
        
        # 跳过一些明显不需要复杂逻辑的方法
        if self._is_simple_utility_method(method_node):
            return False
        
        # 检查是否是内部算法函数
        if self._is_internal_algorithm_function(method_node):
            return False
        
        # 检查是否有完整的try-except-return结构
        if self._has_complete_try_except_return(method_node):
            return False
        
        # 检查是否有足够的语句数量（至少5个语句）
        statement_count = self._count_statements(method_node)
        if statement_count >= 5:
            return False
        
        # 检查是否有复杂结构
        if self._has_complex_structures(method_node):
            return False
        
        # 检查是否有参数但没有使用
        if method_node.args.args and not self._uses_parameters(method_node):
            # 但如果是简单的getter/setter方法，不算缺失逻辑
            if not self._is_simple_getter_setter(method_node):
                return True
        
        # 检查是否有复杂的条件但没有相应的处理
        if self._has_complex_conditions_without_logic(method_node):
            return True
        
        # 检查是否有异常处理但没有具体的处理逻辑
        if self._has_empty_except_blocks(method_node):
            return True
        
        return False
    
    def _is_simple_utility_method(self, method_node: ast.FunctionDef) -> bool:
        """检查是否是简单的工具方法"""
        method_name = method_node.name.lower()
        
        # 简单的工具方法模式
        utility_patterns = [
            'get_', 'set_', 'is_', 'has_', 'can_', 'should_',
            'get_current_', 'get_timestamp', 'get_fallback_',
            'check_', 'validate_', 'format_', 'parse_',
            'to_string', 'to_dict', 'to_json', 'from_json'
        ]
        
        # 如果方法名匹配工具方法模式
        if any(method_name.startswith(pattern) for pattern in utility_patterns):
            return True
        
        # 如果方法体只有简单的返回语句
        if len(method_node.body) <= 3:
            return True
        
        return False
    
    def _has_complete_try_except_return(self, method_node: ast.FunctionDef) -> bool:
        """检查是否有完整的try-except-return结构"""
        has_try = False
        has_except = False
        has_return = False
        
        for node in ast.walk(method_node):
            if isinstance(node, ast.Try):
                has_try = True
                if node.handlers:  # 有except块
                    has_except = True
            elif isinstance(node, ast.Return):
                has_return = True
        
        return has_try and has_except and has_return
    
    def _is_simple_getter_setter(self, method_node: ast.FunctionDef) -> bool:
        """检查是否是简单的getter/setter方法"""
        method_name = method_node.name.lower()
        
        # getter方法模式
        if method_name.startswith('get_') or method_name.startswith('is_') or method_name.startswith('has_'):
            return True
        
        # setter方法模式
        if method_name.startswith('set_'):
            return True
        
        # 如果方法体很简单（只有赋值或返回）
        if len(method_node.body) <= 2:
            return True
        
        return False
    
    def _uses_parameters(self, method_node: ast.FunctionDef) -> bool:
        """检查方法是否使用了参数"""
        if not method_node.args.args:
            return True
        
        param_names = {arg.arg for arg in method_node.args.args}
        
        # 检查方法体中是否使用了参数
        for node in ast.walk(method_node):
            if isinstance(node, ast.Name):
                if node.id in param_names:
                    return True
            # 检查属性访问，如 self.param
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name) and node.value.id in param_names:
                    return True
            # 检查函数调用中的参数使用
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in param_names:
                    return True
        
        return False
    
    def _has_complex_conditions_without_logic(self, method_node: ast.FunctionDef) -> bool:
        """检查是否有复杂条件但没有相应逻辑"""
        for node in ast.walk(method_node):
            if isinstance(node, ast.If):
                # 检查条件是否复杂但处理逻辑简单
                if self._is_complex_condition(node.test) and self._is_simple_body(node.body):
                    return True
        
        return False
    
    def _is_complex_condition(self, test_node: ast.expr) -> bool:
        """检查条件是否复杂"""
        # 检查是否是复合条件
        if isinstance(test_node, (ast.BoolOp, ast.Compare)):
            return True
        
        # 检查是否包含函数调用
        if isinstance(test_node, ast.Call):
            return True
        
        return False
    
    def _is_simple_body(self, body: List[ast.stmt]) -> bool:
        """检查方法体是否简单"""
        if not body:
            return True
        
        if len(body) == 1:
            if isinstance(body[0], ast.Pass):
                return True
            if isinstance(body[0], ast.Return):
                return True
        
        return False
    
    def _has_empty_except_blocks(self, method_node: ast.FunctionDef) -> bool:
        """检查是否有空的异常处理块"""
        for node in ast.walk(method_node):
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    if not handler.body or len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
                        return True
        
        return False
    
    def _has_dummy_return(self, method_node: ast.FunctionDef) -> bool:
        """检查是否有虚拟返回"""
        # 如果是合理的简单方法，不检查虚拟返回
        if self._is_reasonable_simple_method(method_node):
            return False
        
        # 只对应该复杂的方法检查虚拟返回
        if not self._is_expected_to_be_complex(method_node):
            return False
        
        # 检查方法是否有计算逻辑
        has_calculation = False
        for node in ast.walk(method_node):
            if isinstance(node, (ast.Assign, ast.For, ast.While, ast.If, ast.Call)):
                has_calculation = True
                break
        
        # 如果方法有计算逻辑，即使返回常量值也不算虚拟返回
        if has_calculation:
            return False
        
        for node in ast.walk(method_node):
            if isinstance(node, ast.Return):
                if node.value is not None:
                    # 检查是否是硬编码的返回值（更严格的标准）
                    if isinstance(node.value, ast.Constant):
                        if node.value.value in [True, False, None, "", []]:
                            return True
                    elif isinstance(node.value, ast.Name):
                        if node.value.id in ['True', 'False', 'None']:
                            return True
        
        return False
    
    def _is_core_business_method(self, method_node: ast.FunctionDef) -> bool:
        """检查是否是核心业务方法"""
        method_name = method_node.name.lower()
        
        # 核心业务方法的关键词
        core_keywords = [
            'process', 'analyze', 'execute', 'run', 'handle', 'manage',
            'coordinate', 'integrate', 'synthesize', 'generate', 'create',
            'train', 'learn', 'optimize', 'evaluate', 'assess', 'calculate',
            'compute', 'solve', 'resolve', 'implement', 'realize'
        ]
        
        # 检查方法名是否包含核心业务关键词
        if any(keyword in method_name for keyword in core_keywords):
            return True
        
        # 检查是否是公共方法（非私有方法）
        if not method_name.startswith('_'):
            return True
        
        # 检查方法参数数量（核心业务方法通常有更多参数）
        if len(method_node.args.args) > 2:
            return True
        
        return False
    
    def _is_incomplete_implementation(self, method_node: ast.FunctionDef) -> bool:
        """检查是否是不完整实现"""
        if not method_node.body:
            return True
        
        # 检查是否只有pass语句
        if len(method_node.body) == 1 and isinstance(method_node.body[0], ast.Pass):
            return True
        
        # 检查是否只有NotImplementedError
        if len(method_node.body) == 1 and isinstance(method_node.body[0], ast.Raise):
            if isinstance(method_node.body[0].exc, ast.Name) and method_node.body[0].exc.id == 'NotImplementedError':
                return True
        
        # 检查是否只有省略号
        if len(method_node.body) == 1 and isinstance(method_node.body[0], ast.Expr):
            if isinstance(method_node.body[0].value, ast.Constant) and method_node.body[0].value.value is Ellipsis:
                return True
        
        # 检查是否只有简单的return语句（没有计算逻辑）
        if len(method_node.body) == 1 and isinstance(method_node.body[0], ast.Return):
            # 检查是否有计算逻辑
            has_calculation = False
            for node in ast.walk(method_node):
                if isinstance(node, (ast.Assign, ast.For, ast.While, ast.If, ast.Call)):
                    has_calculation = True
                    break
            if not has_calculation:
                return True
        
        return False
    
    def _get_method_content(self, method_node: ast.FunctionDef, lines: List[str]) -> str:
        """获取方法内容"""
        start_line = method_node.lineno - 1
        end_line = method_node.end_lineno if hasattr(method_node, 'end_lineno') else start_line + 1
        return '\n'.join(lines[start_line:end_line])
    
    def _get_method_lines(self, method_node: ast.FunctionDef, content: str) -> List[str]:
        """获取方法的所有行"""
        lines = content.split('\n')
        start_line = method_node.lineno - 1
        end_line = method_node.end_lineno if hasattr(method_node, 'end_lineno') else start_line + 1
        return lines[start_line:end_line]
    
    def analyze(self) -> Dict[str, Any]:
        """执行分析"""
        all_issues = []
        
        # 分析所有Python文件
        for file_path in self.python_files:
            file_issues = self.analyze_file(file_path)
            all_issues.extend(file_issues)
        
        # 输出所有问题到文件
        self._save_issues_to_file(all_issues)
        
        return {
            'has_unimplemented_methods': len(all_issues) > 0,
            'unimplemented_count': len(all_issues),
            'issues': all_issues[:20],  # 限制返回数量
            'score': max(0, 1.0 - len(all_issues) * 0.05)
        }
    
    def _save_issues_to_file(self, issues: List[ImplementationIssue]) -> None:
        """保存问题列表到文件"""
        try:
            import json
            output_file = 'unimplemented_methods_details.json'
            
            issues_data = []
            for issue in issues:
                issues_data.append({
                    'file_path': issue.file_path,
                    'line_number': issue.line_number,
                    'issue_type': issue.issue_type.value,
                    'severity': issue.severity,
                    'description': issue.description,
                    'suggestion': issue.suggestion,
                    'code_snippet': issue.code_snippet[:200] if len(issue.code_snippet) > 200 else issue.code_snippet,
                    'confidence': issue.confidence
                })
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'total_issues': len(issues),
                    'issues': issues_data
                }, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"已保存{len(issues)}个未实现方法详情到文件: {output_file}")
            
        except Exception as e:
            self.logger.error(f"保存问题列表失败: {e}")
    
    def analyze_core_system(self) -> Dict[str, Any]:
        """分析核心系统 - 兼容性方法"""
        return self.analyze()