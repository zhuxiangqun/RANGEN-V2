"""
业务逻辑分析器
分析代码的实际业务价值和功能实现，而不仅仅是代码结构
"""

import ast
import re
from typing import Dict, Any, List, Set
from base_analyzer import BaseAnalyzer


class BusinessLogicAnalyzer(BaseAnalyzer):
    """业务逻辑分析器 - 分析实际业务价值和功能实现"""
    
    def analyze(self) -> Dict[str, Any]:
        """执行业务逻辑分析"""
        return {
            "business_value_score": self._analyze_business_value(),
            "functional_completeness": self._analyze_functional_completeness(),
            "real_world_applicability": self._analyze_real_world_applicability(),
            "integration_readiness": self._analyze_integration_readiness(),
            "production_readiness": self._analyze_production_readiness(),
            "business_logic_quality": self._analyze_business_logic_quality()
        }
    
    def _analyze_business_value(self) -> float:
        """分析业务价值 - 检查是否有实际的业务逻辑"""
        try:
            business_indicators = 0
            total_functions = 0
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_functions += 1
                        if self._has_real_business_logic(node, content):
                            business_indicators += 1
                    elif isinstance(node, ast.ClassDef):
                        for method in node.body:
                            if isinstance(method, ast.FunctionDef):
                                total_functions += 1
                                if self._has_real_business_logic(method, content):
                                    business_indicators += 1
            
            if total_functions == 0:
                return 0.0
            
            return min(business_indicators / total_functions, 1.0)
            
        except Exception as e:
            self.logger.error(f"分析业务价值失败: {e}")
            return 0.0
    
    def _analyze_functional_completeness(self) -> float:
        """分析功能完整性 - 检查是否有完整的功能实现"""
        try:
            complete_functions = 0
            total_functions = 0
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_functions += 1
                        if self._is_function_complete(node, content):
                            complete_functions += 1
                    elif isinstance(node, ast.ClassDef):
                        for method in node.body:
                            if isinstance(method, ast.FunctionDef):
                                total_functions += 1
                                if self._is_function_complete(method, content):
                                    complete_functions += 1
            
            if total_functions == 0:
                return 0.0
            
            return min(complete_functions / total_functions, 1.0)
            
        except Exception as e:
            self.logger.error(f"分析功能完整性失败: {e}")
            return 0.0
    
    def _analyze_real_world_applicability(self) -> float:
        """分析实际应用性 - 检查是否有实际应用价值"""
        try:
            applicable_features = 0
            total_features = 0
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_features += 1
                        if self._is_real_world_applicable(node, content):
                            applicable_features += 1
                    elif isinstance(node, ast.ClassDef):
                        for method in node.body:
                            if isinstance(method, ast.FunctionDef):
                                total_features += 1
                                if self._is_real_world_applicable(method, content):
                                    applicable_features += 1
            
            if total_features == 0:
                return 0.0
            
            return min(applicable_features / total_features, 1.0)
            
        except Exception as e:
            self.logger.error(f"分析实际应用性失败: {e}")
            return 0.0
    
    def _analyze_integration_readiness(self) -> float:
        """分析集成准备度 - 检查是否准备好集成"""
        try:
            integration_ready_features = 0
            total_features = 0
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_features += 1
                        if self._is_integration_ready(node, content):
                            integration_ready_features += 1
                    elif isinstance(node, ast.ClassDef):
                        for method in node.body:
                            if isinstance(method, ast.FunctionDef):
                                total_features += 1
                                if self._is_integration_ready(method, content):
                                    integration_ready_features += 1
            
            if total_features == 0:
                return 0.0
            
            return min(integration_ready_features / total_features, 1.0)
            
        except Exception as e:
            self.logger.error(f"分析集成准备度失败: {e}")
            return 0.0
    
    def _analyze_production_readiness(self) -> float:
        """分析生产准备度 - 检查是否准备好生产部署"""
        try:
            production_ready_features = 0
            total_features = 0
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_features += 1
                        if self._is_production_ready(node, content):
                            production_ready_features += 1
                    elif isinstance(node, ast.ClassDef):
                        for method in node.body:
                            if isinstance(method, ast.FunctionDef):
                                total_features += 1
                                if self._is_production_ready(method, content):
                                    production_ready_features += 1
            
            if total_features == 0:
                return 0.0
            
            return min(production_ready_features / total_features, 1.0)
            
        except Exception as e:
            self.logger.error(f"分析生产准备度失败: {e}")
            return 0.0
    
    def _analyze_business_logic_quality(self) -> float:
        """分析业务逻辑质量 - 检查业务逻辑的质量"""
        try:
            quality_indicators = 0
            total_functions = 0
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_functions += 1
                        if self._has_quality_business_logic(node, content):
                            quality_indicators += 1
                    elif isinstance(node, ast.ClassDef):
                        for method in node.body:
                            if isinstance(method, ast.FunctionDef):
                                total_functions += 1
                                if self._has_quality_business_logic(method, content):
                                    quality_indicators += 1
            
            if total_functions == 0:
                return 0.0
            
            return min(quality_indicators / total_functions, 1.0)
            
        except Exception as e:
            self.logger.error(f"分析业务逻辑质量失败: {e}")
            return 0.0
    
    # 辅助方法
    
    def _has_real_business_logic(self, func_node: ast.FunctionDef, content: str) -> bool:
        """检查函数是否有真实的业务逻辑 - 基于业务关键词和结构特征"""
        try:
            if not func_node.body or len(func_node.body) == 0:
                return False
            
            business_features = 0
            
            # 检查业务相关关键词
            business_keywords = [
                'business', 'logic', 'process', 'validate', 'rule', 'policy',
                'workflow', 'service', 'operation', 'transaction', 'request',
                'response', 'data', 'user', 'client', 'customer', 'order',
                'payment', 'account', 'profile', 'session', 'auth', 'permission'
            ]
            
            func_content = ast.get_source_segment(content, func_node) or ""
            for keyword in business_keywords:
                if keyword in func_content.lower():
                    business_features += 1
                    break  # 找到一个关键词就够了
            
            # 检查AST结构特征
            for node in ast.walk(func_node):
                # 1. 检查是否有数据处理逻辑
                if isinstance(node, ast.Assign):
                    if self._is_data_processing(node):
                        business_features += 1
                
                # 2. 检查是否有业务规则
                elif isinstance(node, ast.If):
                    if self._is_business_rule(node):
                        business_features += 1
                
                # 3. 检查是否有业务计算
                elif isinstance(node, ast.Call):
                    if self._is_business_calculation(node):
                        business_features += 1
                
                # 4. 检查是否有业务状态管理
                elif isinstance(node, ast.For):
                    if self._is_business_state_management(node):
                        business_features += 1
            
            # 降低要求：有业务关键词或1个业务特征即可
            return business_features >= 1
            
        except Exception as e:
            self.logger.error(f"分析业务逻辑失败: {e}")
            return False
    
    def _is_function_complete(self, func_node: ast.FunctionDef, content: str) -> bool:
        """检查函数是否完整实现"""
        try:
            if not func_node.body or len(func_node.body) == 0:
                return False
            
            # 检查是否有pass语句或return None
            for node in ast.walk(func_node):
                if isinstance(node, ast.Pass):
                    return False
                elif isinstance(node, ast.Return):
                    if node.value is None:
                        return False
            
            # 检查函数体长度（至少3行有效代码）
            effective_lines = 0
            for node in func_node.body:
                if not isinstance(node, (ast.Pass, ast.Expr)):
                    effective_lines += 1
            
            return effective_lines >= 3
            
        except Exception as e:
            self.logger.error(f"检查函数完整性失败: {e}")
            return False
    
    def _is_real_world_applicable(self, func_node: ast.FunctionDef, content: str) -> bool:
        """检查函数是否有实际应用价值"""
        try:
            # 检查函数名是否暗示实际功能
            func_name = func_node.name.lower()
            real_world_indicators = [
                'process', 'handle', 'execute', 'analyze', 'generate', 'create',
                'update', 'delete', 'search', 'find', 'calculate', 'compute',
                'validate', 'verify', 'transform', 'convert', 'parse', 'format'
            ]
            
            if any(indicator in func_name for indicator in real_world_indicators):
                return True
            
            # 检查是否有实际的业务逻辑
            return self._has_real_business_logic(func_node, content)
            
        except Exception as e:
            self.logger.error(f"检查实际应用性失败: {e}")
            return False
    
    def _is_integration_ready(self, func_node: ast.FunctionDef, content: str) -> bool:
        """检查函数是否准备好集成"""
        try:
            # 检查是否有错误处理
            has_error_handling = False
            # 检查是否有日志记录
            has_logging = False
            # 检查是否有返回值
            has_return_value = False
            
            for node in ast.walk(func_node):
                if isinstance(node, ast.Try):
                    has_error_handling = True
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr in ['info', 'debug', 'warning', 'error']:
                            has_logging = True
                elif isinstance(node, ast.Return):
                    if node.value is not None:
                        has_return_value = True
            
            return has_error_handling and has_logging and has_return_value
            
        except Exception as e:
            self.logger.error(f"检查集成准备度失败: {e}")
            return False
    
    def _is_production_ready(self, func_node: ast.FunctionDef, content: str) -> bool:
        """检查函数是否准备好生产部署"""
        try:
            # 检查是否有硬编码值
            has_hardcoded_values = False
            # 检查是否有模拟数据
            has_mock_data = False
            # 检查是否有测试代码
            has_test_code = False
            
            for node in ast.walk(func_node):
                if isinstance(node, ast.Constant):
                    # 检查是否是硬编码的字符串或数字
                    if isinstance(node.value, str) and len(node.value) > 10:
                        has_hardcoded_values = True
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id.lower()
                        if 'mock' in func_name or 'fake' in func_name:
                            has_mock_data = True
                        elif 'test' in func_name:
                            has_test_code = True
            
            # 生产就绪：没有硬编码值、没有模拟数据、没有测试代码
            return not has_hardcoded_values and not has_mock_data and not has_test_code
            
        except Exception as e:
            self.logger.error(f"检查生产准备度失败: {e}")
            return False
    
    def _has_quality_business_logic(self, func_node: ast.FunctionDef, content: str) -> bool:
        """检查函数是否有高质量的业务逻辑"""
        try:
            quality_features = 0
            
            # 1. 检查是否有清晰的参数验证
            if self._has_parameter_validation(func_node):
                quality_features += 1
            
            # 2. 检查是否有清晰的业务逻辑流程
            if self._has_clear_business_flow(func_node):
                quality_features += 1
            
            # 3. 检查是否有适当的错误处理
            if self._has_proper_error_handling(func_node):
                quality_features += 1
            
            # 4. 检查是否有清晰的返回值
            if self._has_clear_return_value(func_node):
                quality_features += 1
            
            # 需要至少3个质量特征
            return quality_features >= 3
            
        except Exception as e:
            self.logger.error(f"检查业务逻辑质量失败: {e}")
            return False
    
    def _is_data_processing(self, node: ast.Assign) -> bool:
        """检查是否是数据处理"""
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target_name = node.targets[0].id.lower()
            # 检查是否是数据处理相关的变量
            return any(term in target_name for term in ['data', 'result', 'output', 'processed', 'filtered'])
        return False
    
    def _is_business_rule(self, node: ast.If) -> bool:
        """检查是否是业务规则"""
        # 检查条件是否涉及业务逻辑
        if isinstance(node.test, ast.Compare):
            return True
        elif isinstance(node.test, ast.Call):
            if isinstance(node.test.func, ast.Name):
                func_name = node.test.func.id.lower()
                return any(term in func_name for term in ['validate', 'check', 'verify', 'is_valid'])
        return False
    
    def _is_business_calculation(self, node: ast.Call) -> bool:
        """检查是否是业务计算"""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id.lower()
            return any(term in func_name for term in ['calculate', 'compute', 'sum', 'avg', 'count'])
        return False
    
    def _is_business_state_management(self, node: ast.For) -> bool:
        """检查是否是业务状态管理"""
        # 检查循环是否涉及状态管理
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                if isinstance(child.targets[0], ast.Name):
                    target_name = child.targets[0].id.lower()
                    if any(term in target_name for term in ['state', 'status', 'phase', 'stage']):
                        return True
        return False
    
    def _has_parameter_validation(self, func_node: ast.FunctionDef) -> bool:
        """检查是否有参数验证"""
        for node in ast.walk(func_node):
            if isinstance(node, ast.If):
                if isinstance(node.test, ast.Call):
                    if isinstance(node.test.func, ast.Name):
                        func_name = node.test.func.id.lower()
                        if any(term in func_name for term in ['isinstance', 'is_valid', 'validate']):
                            return True
        return False
    
    def _has_clear_business_flow(self, func_node: ast.FunctionDef) -> bool:
        """检查是否有清晰的业务逻辑流程"""
        # 检查是否有多个步骤的业务逻辑
        steps = 0
        for node in func_node.body:
            if not isinstance(node, (ast.Pass, ast.Expr)):
                steps += 1
        return steps >= 3
    
    def _has_proper_error_handling(self, func_node: ast.FunctionDef) -> bool:
        """检查是否有适当的错误处理"""
        for node in ast.walk(func_node):
            if isinstance(node, ast.Try):
                return True
        return False
    
    def _has_clear_return_value(self, func_node: ast.FunctionDef) -> bool:
        """检查是否有清晰的返回值"""
        for node in ast.walk(func_node):
            if isinstance(node, ast.Return):
                if node.value is not None:
                    return True
        return False
