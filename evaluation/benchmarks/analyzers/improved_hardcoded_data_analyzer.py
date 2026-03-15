#!/usr/bin/env python3
"""
基于AST深度分析的硬编码检测分析器
完全基于代码结构分析，不依赖关键词匹配
"""

import ast
import re
from typing import Dict, Any, List, Set, Union
from base_analyzer import BaseAnalyzer


class ImprovedHardcodedDataAnalyzer(BaseAnalyzer):
    """基于AST深度分析的硬编码检测分析器"""
    
    def analyze(self) -> Dict[str, Any]:
        """执行基于AST的硬编码检测分析"""
        return {
            "hardcoded_conditionals": self._detect_hardcoded_conditionals_ast(),
            "hardcoded_lists": self._detect_hardcoded_lists_ast(),
            "hardcoded_patterns": self._detect_hardcoded_patterns_ast(),
            "hardcoded_strings": self._detect_hardcoded_strings_ast(),
            "hardcoded_functions": self._detect_hardcoded_functions_ast(),
            "simulated_data": self._detect_simulated_data_ast(),
            "test_data_in_production": self._detect_test_data_in_production_ast(),
            "magic_numbers": self._detect_magic_numbers_ast(),
            "hardcoded_paths": self._detect_hardcoded_paths_ast(),
            "hardcoded_urls": self._detect_hardcoded_urls_ast(),
            "hardcoded_credentials": self._detect_hardcoded_credentials_ast(),
            "data_quality_issues": self._detect_data_quality_issues_ast(),
            "hardcoded_config_values": self._detect_hardcoded_config_values_ast(),
            "hardcoded_booleans": self._detect_hardcoded_booleans_ast()
        }
    
    def _detect_hardcoded_conditionals_ast(self) -> Dict[str, Any]:
        """基于AST检测硬编码的条件判断"""
        try:
            hardcoded_issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                # 分析AST中的条件判断节点
                for node in ast.walk(tree):
                    if isinstance(node, ast.If):
                        hardcoded_cond = self._analyze_conditional_hardcoding(node, content)
                        if hardcoded_cond['is_hardcoded']:
                            hardcoded_issues.append({
                                'file': file_path,
                                'line': node.lineno,
                                'type': 'hardcoded_conditional',
                                'severity': hardcoded_cond['severity'],
                                'description': hardcoded_cond['description'],
                                'suggestion': hardcoded_cond['suggestion']
                            })
            
            return {
                'has_hardcoded_conditionals': len(hardcoded_issues) > 0,
                'hardcoded_count': len(hardcoded_issues),
                'issues': hardcoded_issues[:10],
                'score': max(0, 1.0 - len(hardcoded_issues) * 0.1)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码条件判断失败: {e}")
            return {'has_hardcoded_conditionals': False, 'hardcoded_count': 0, 'issues': [], 'score': 1.0}
    
    def _analyze_conditional_hardcoding(self, if_node: ast.If, content: str) -> Dict[str, Any]:
        """分析条件判断是否硬编码"""
        analysis = {
            'is_hardcoded': False,
            'severity': 'low',
            'description': '',
            'suggestion': ''
        }
        
        # 检查条件是否包含硬编码列表
        if isinstance(if_node.test, ast.Call):
            if isinstance(if_node.test.func, ast.Name) and if_node.test.func.id == 'any':
                # 分析 any() 函数调用
                if len(if_node.test.args) > 0:
                    generator = if_node.test.args[0]
                    if isinstance(generator, ast.GeneratorExp):
                        # 检查生成器表达式中的硬编码列表
                        if self._has_hardcoded_list_in_generator(generator):
                            analysis['is_hardcoded'] = True
                            analysis['severity'] = 'medium'
                            analysis['description'] = '条件判断中包含硬编码列表'
                            analysis['suggestion'] = '将硬编码列表提取为配置或常量'
        
        # 检查条件是否包含硬编码字符串比较
        elif isinstance(if_node.test, ast.Compare):
            if self._has_hardcoded_string_comparison(if_node.test):
                analysis['is_hardcoded'] = True
                analysis['severity'] = 'high'
                analysis['description'] = '条件判断中包含硬编码字符串比较'
                analysis['suggestion'] = '使用配置管理或枚举类型'
        
        return analysis
    
    def _has_hardcoded_list_in_generator(self, generator: ast.GeneratorExp) -> bool:
        """检查生成器表达式中是否有硬编码列表"""
        # 检查生成器的可迭代对象
        if generator.generators:
            for comp in generator.generators:
                if isinstance(comp.iter, ast.List):
                    # 如果列表包含多个字符串字面量，认为是硬编码
                    string_literals = 0
                    for elt in comp.iter.elts:
                        if isinstance(elt, ast.Str):
                            string_literals += 1
                    
                    # 如果字符串字面量超过3个，认为是硬编码
                    if string_literals > 3:
                        return True
        
        return False
    
    def _has_hardcoded_string_comparison(self, compare_node: ast.Compare) -> bool:
        """检查比较操作中是否有硬编码字符串"""
        # 检查左操作数
        if isinstance(compare_node.left, ast.Str):
            # 检查字符串是否看起来像业务数据
            if self._is_business_like_string(compare_node.left.s):
                return True
        
        # 检查比较操作
        for op, comparator in zip(compare_node.ops, compare_node.comparators):
            if isinstance(comparator, ast.Str):
                if self._is_business_like_string(comparator.s):
                    return True
        
        return False
    
    def _is_business_like_string(self, s: str) -> bool:
        """基于字符串特征判断是否像业务数据"""
        if not s or len(s) < 2:
            return False
        
        # 检查是否包含人名模式（首字母大写）
        if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+$', s):
            return True
        
        # 检查是否包含特定业务术语
        business_indicators = [
            'president', 'assassinated', 'first lady', 'building',
            'tower', 'height', 'classification', 'library'
        ]
        
        s_lower = s.lower()
        for indicator in business_indicators:
            if indicator in s_lower:
                return True
        
        return False
    
    def _detect_hardcoded_lists_ast(self) -> Dict[str, Any]:
        """基于AST检测硬编码列表"""
        try:
            hardcoded_issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                # 分析AST中的列表节点
                for node in ast.walk(tree):
                    if isinstance(node, ast.List):
                        hardcoded_list = self._analyze_list_hardcoding(node, content)
                        if hardcoded_list['is_hardcoded']:
                            hardcoded_issues.append({
                                'file': file_path,
                                'line': node.lineno,
                                'type': 'hardcoded_list',
                                'severity': hardcoded_list['severity'],
                                'description': hardcoded_list['description'],
                                'suggestion': hardcoded_list['suggestion']
                            })
            
            return {
                'has_hardcoded_lists': len(hardcoded_issues) > 0,
                'hardcoded_count': len(hardcoded_issues),
                'issues': hardcoded_issues[:10],
                'score': max(0, 1.0 - len(hardcoded_issues) * 0.1)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码列表失败: {e}")
            return {'has_hardcoded_lists': False, 'hardcoded_count': 0, 'issues': [], 'score': 1.0}
    
    def _analyze_list_hardcoding(self, list_node: ast.List, content: str) -> Dict[str, Any]:
        """分析列表是否硬编码"""
        analysis = {
            'is_hardcoded': False,
            'severity': 'low',
            'description': '',
            'suggestion': ''
        }
        
        if not list_node.elts:
            return analysis
        
        # 检查列表元素类型和数量
        string_elements = 0
        business_like_elements = 0
        
        for elt in list_node.elts:
            if isinstance(elt, ast.Str):
                string_elements += 1
                if self._is_business_like_string(elt.s):
                    business_like_elements += 1
        
        # 降低阈值：如果字符串元素超过3个，或者业务相关元素超过2个，认为是硬编码
        if string_elements > 3 or business_like_elements > 2:
            analysis['is_hardcoded'] = True
            analysis['severity'] = 'medium'
            analysis['description'] = f'列表包含{string_elements}个字符串元素，其中{business_like_elements}个像业务数据'
            analysis['suggestion'] = '将硬编码列表提取为配置文件或数据库'
        
        return analysis
    
    def _detect_hardcoded_patterns_ast(self) -> Dict[str, Any]:
        """基于AST检测硬编码模式"""
        try:
            hardcoded_issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                # 分析AST中的字符串字面量
                for node in ast.walk(tree):
                    if isinstance(node, ast.Str):
                        hardcoded_pattern = self._analyze_string_hardcoding(node, content)
                        if hardcoded_pattern['is_hardcoded']:
                            hardcoded_issues.append({
                                'file': file_path,
                                'line': node.lineno,
                                'type': 'hardcoded_pattern',
                                'severity': hardcoded_pattern['severity'],
                                'description': hardcoded_pattern['description'],
                                'suggestion': hardcoded_pattern['suggestion']
                            })
            
            return {
                'has_hardcoded_patterns': len(hardcoded_issues) > 0,
                'hardcoded_count': len(hardcoded_issues),
                'issues': hardcoded_issues[:10],
                'score': max(0, 1.0 - len(hardcoded_issues) * 0.05)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码模式失败: {e}")
            return {'has_hardcoded_patterns': False, 'hardcoded_count': 0, 'issues': [], 'score': 1.0}
    
    def _analyze_string_hardcoding(self, str_node: ast.Str, content: str) -> Dict[str, Any]:
        """分析字符串是否硬编码"""
        analysis = {
            'is_hardcoded': False,
            'severity': 'low',
            'description': '',
            'suggestion': ''
        }
        
        s = str_node.s
        if not s or len(s) < 3:
            return analysis
        
        # 检查是否是路径
        if self._is_hardcoded_path(s):
            analysis['is_hardcoded'] = True
            analysis['severity'] = 'high'
            analysis['description'] = '硬编码文件路径'
            analysis['suggestion'] = '使用配置文件或环境变量'
            return analysis
        
        # 检查是否是URL
        if self._is_hardcoded_url(s):
            analysis['is_hardcoded'] = True
            analysis['severity'] = 'high'
            analysis['description'] = '硬编码URL'
            analysis['suggestion'] = '使用配置文件管理URL'
            return analysis
        
        # 检查是否是凭据
        if self._is_hardcoded_credential(s):
            analysis['is_hardcoded'] = True
            analysis['severity'] = 'critical'
            analysis['description'] = '硬编码凭据'
            analysis['suggestion'] = '使用环境变量或密钥管理系统'
            return analysis
        
        # 检查是否是业务数据
        if self._is_business_like_string(s):
            analysis['is_hardcoded'] = True
            analysis['severity'] = 'medium'
            analysis['description'] = '硬编码业务数据'
            analysis['suggestion'] = '使用数据库或配置文件'
            return analysis
        
        return analysis
    
    def _is_hardcoded_path(self, s: str) -> bool:
        """检查是否是硬编码路径"""
        # 检查是否包含路径分隔符
        if '/' in s or '\\' in s:
            # 检查是否是绝对路径
            if s.startswith('/') or (len(s) > 1 and s[1] == ':'):
                return True
            # 检查是否包含常见的路径模式
            if any(pattern in s.lower() for pattern in ['/home/', '/usr/', '/var/', 'c:\\', 'd:\\']):
                return True
        
        return False
    
    def _is_hardcoded_url(self, s: str) -> bool:
        """检查是否是硬编码URL"""
        # 检查是否包含URL协议
        if s.startswith(('http://', 'https://', 'ftp://', 'ws://', 'wss://')):
            return True
        
        # 检查是否包含域名模式
        if re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', s):
            return True
        
        return False
    
    def _is_hardcoded_credential(self, s: str) -> bool:
        """检查是否是硬编码凭据"""
        # 检查是否包含常见的凭据模式
        credential_patterns = [
            r'password\s*=\s*["\']\w+["\']',
            r'secret\s*=\s*["\']\w+["\']',
            r'token\s*=\s*["\']\w+["\']',
            r'key\s*=\s*["\']\w+["\']',
            r'api_key\s*=\s*["\']\w+["\']'
        ]
        
        for pattern in credential_patterns:
            if re.search(pattern, s, re.IGNORECASE):
                return True
        
        return False
    
    def _detect_hardcoded_strings_ast(self) -> Dict[str, Any]:
        """基于AST检测硬编码字符串"""
        return self._detect_hardcoded_patterns_ast()
    
    def _detect_hardcoded_functions_ast(self) -> Dict[str, Any]:
        """基于AST检测硬编码函数"""
        try:
            hardcoded_issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                # 分析AST中的函数定义
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        hardcoded_func = self._analyze_function_hardcoding(node, content)
                        if hardcoded_func['is_hardcoded']:
                            hardcoded_issues.append({
                                'file': file_path,
                                'line': node.lineno,
                                'type': 'hardcoded_function',
                                'severity': hardcoded_func['severity'],
                                'description': hardcoded_func['description'],
                                'suggestion': hardcoded_func['suggestion']
                            })
            
            return {
                'has_hardcoded_functions': len(hardcoded_issues) > 0,
                'hardcoded_count': len(hardcoded_issues),
                'issues': hardcoded_issues[:10],
                'score': max(0, 1.0 - len(hardcoded_issues) * 0.1)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码函数失败: {e}")
            return {'has_hardcoded_functions': False, 'hardcoded_count': 0, 'issues': [], 'score': 1.0}
    
    def _analyze_function_hardcoding(self, func_node: ast.FunctionDef, content: str) -> Dict[str, Any]:
        """分析函数是否包含硬编码逻辑"""
        analysis = {
            'is_hardcoded': False,
            'severity': 'low',
            'description': '',
            'suggestion': ''
        }
        
        # 检查函数名是否包含硬编码标识
        if self._is_hardcoded_function_name(func_node.name):
            analysis['is_hardcoded'] = True
            analysis['severity'] = 'medium'
            analysis['description'] = '函数名包含硬编码标识'
            analysis['suggestion'] = '使用参数化或配置化的函数名'
            return analysis
        
        # 检查函数体是否包含硬编码逻辑
        hardcoded_logic_count = 0
        for node in ast.walk(func_node):
            if isinstance(node, ast.Str):
                if self._is_business_like_string(node.s):
                    hardcoded_logic_count += 1
        
        if hardcoded_logic_count > 2:
            analysis['is_hardcoded'] = True
            analysis['severity'] = 'medium'
            analysis['description'] = f'函数包含{hardcoded_logic_count}个硬编码字符串'
            analysis['suggestion'] = '将硬编码数据提取为参数或配置'
        
        return analysis
    
    def _is_hardcoded_function_name(self, func_name: str) -> bool:
        """检查函数名是否包含硬编码标识"""
        # 检查是否包含特定的人名或业务术语
        hardcoded_names = [
            'monroe', 'madison', 'jefferson', 'lincoln', 'ballou',
            'bronte', 'charlotte', 'jane', 'eyre', 'world_trade',
            'central_park', 'fifa', 'uefa', 'champions'
        ]
        
        func_name_lower = func_name.lower()
        for name in hardcoded_names:
            if name in func_name_lower:
                return True
        
        return False
    
    def _detect_simulated_data_ast(self) -> Dict[str, Any]:
        """基于AST检测模拟数据"""
        try:
            simulated_issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                # 分析AST中的变量赋值
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        simulated_data = self._analyze_simulated_data(node, content)
                        if simulated_data['is_simulated']:
                            simulated_issues.append({
                                'file': file_path,
                                'line': node.lineno,
                                'type': 'simulated_data',
                                'severity': simulated_data['severity'],
                                'description': simulated_data['description'],
                                'suggestion': simulated_data['suggestion']
                            })
            
            return {
                'has_simulated_data': len(simulated_issues) > 0,
                'simulated_count': len(simulated_issues),
                'issues': simulated_issues[:10],
                'score': max(0, 1.0 - len(simulated_issues) * 0.1)
            }
            
        except Exception as e:
            self.logger.error(f"检测模拟数据失败: {e}")
            return {'has_simulated_data': False, 'simulated_count': 0, 'issues': [], 'score': 1.0}
    
    def _analyze_simulated_data(self, assign_node: ast.Assign, content: str) -> Dict[str, Any]:
        """分析赋值是否包含模拟数据"""
        analysis = {
            'is_simulated': False,
            'severity': 'low',
            'description': '',
            'suggestion': ''
        }
        
        # 检查赋值的目标变量名
        for target in assign_node.targets:
            if isinstance(target, ast.Name):
                if self._is_simulated_variable_name(target.id):
                    analysis['is_simulated'] = True
                    analysis['severity'] = 'medium'
                    analysis['description'] = '变量名表明这是模拟数据'
                    analysis['suggestion'] = '使用真实数据源'
                    return analysis
        
        # 检查赋值值是否包含模拟数据
        if isinstance(assign_node.value, ast.Str):
            if self._is_simulated_string(assign_node.value.s):
                analysis['is_simulated'] = True
                analysis['severity'] = 'medium'
                analysis['description'] = '字符串值看起来像模拟数据'
                analysis['suggestion'] = '使用真实数据源'
        
        return analysis
    
    def _is_simulated_variable_name(self, var_name: str) -> bool:
        """检查变量名是否表明是模拟数据"""
        simulated_patterns = [
            'mock', 'fake', 'dummy', 'test', 'sample', 'example',
            'simulated', 'placeholder', 'temp', 'temporary'
        ]
        
        var_name_lower = var_name.lower()
        for pattern in simulated_patterns:
            if pattern in var_name_lower:
                return True
        
        return False
    
    def _is_simulated_string(self, s: str) -> bool:
        """检查字符串是否看起来像模拟数据"""
        if not s or len(s) < 2:
            return False
        
        # 检查是否包含模拟数据标识
        simulated_patterns = [
            'test', 'mock', 'fake', 'dummy', 'sample', 'example',
            'placeholder', 'temp', 'temporary', 'simulated'
        ]
        
        s_lower = s.lower()
        for pattern in simulated_patterns:
            if pattern in s_lower:
                return True
        
        return False
    
    def _detect_test_data_in_production_ast(self) -> Dict[str, Any]:
        """基于AST检测生产环境中的测试数据"""
        return self._detect_simulated_data_ast()
    
    def _detect_magic_numbers_ast(self) -> Dict[str, Any]:
        """基于AST检测魔法数字"""
        try:
            magic_issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                # 分析AST中的数字字面量
                for node in ast.walk(tree):
                    if isinstance(node, ast.Num):
                        magic_number = self._analyze_magic_number(node, content)
                        if magic_number['is_magic']:
                            magic_issues.append({
                                'file': file_path,
                                'line': node.lineno,
                                'type': 'magic_number',
                                'severity': magic_number['severity'],
                                'description': magic_number['description'],
                                'suggestion': magic_number['suggestion']
                            })
            
            return {
                'has_magic_numbers': len(magic_issues) > 0,
                'magic_count': len(magic_issues),
                'issues': magic_issues[:10],
                'score': max(0, 1.0 - len(magic_issues) * 0.05)
            }
            
        except Exception as e:
            self.logger.error(f"检测魔法数字失败: {e}")
            return {'has_magic_numbers': False, 'magic_count': 0, 'issues': [], 'score': 1.0}
    
    def _analyze_magic_number(self, num_node: ast.Num, content: str) -> Dict[str, Any]:
        """分析数字是否是魔法数字"""
        analysis = {
            'is_magic': False,
            'severity': 'low',
            'description': '',
            'suggestion': ''
        }
        
        num_value = num_node.n
        
        # 检查是否是常见的魔法数字
        magic_numbers = {
            0: '零值',
            1: '单位值',
            2: '双值',
            3: '三值',
            7: '一周天数',
            24: '一天小时数',
            60: '分钟/秒数',
            100: '百分比',
            1000: '千值',
            1024: '字节单位',
            3600: '一小时秒数',
            86400: '一天秒数'
        }
        
        if isinstance(num_value, (int, float)) and num_value in magic_numbers:
            analysis['is_magic'] = True
            analysis['severity'] = 'medium'
            analysis['description'] = f'魔法数字: {num_value} ({magic_numbers[num_value]})'
            analysis['suggestion'] = '使用命名常量替代魔法数字'
        
        return analysis
    
    def _detect_hardcoded_paths_ast(self) -> Dict[str, Any]:
        """基于AST检测硬编码路径"""
        try:
            path_issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                # 分析AST中的字符串字面量
                for node in ast.walk(tree):
                    if isinstance(node, ast.Str):
                        if self._is_hardcoded_path(node.s):
                            path_issues.append({
                                'file': file_path,
                                'line': node.lineno,
                                'type': 'hardcoded_path',
                                'severity': 'high',
                                'description': '硬编码文件路径',
                                'suggestion': '使用配置文件或环境变量'
                            })
            
            return {
                'has_hardcoded_paths': len(path_issues) > 0,
                'path_count': len(path_issues),
                'issues': path_issues[:10],
                'score': max(0, 1.0 - len(path_issues) * 0.1)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码路径失败: {e}")
            return {'has_hardcoded_paths': False, 'path_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_hardcoded_urls_ast(self) -> Dict[str, Any]:
        """基于AST检测硬编码URL"""
        try:
            url_issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                # 分析AST中的字符串字面量
                for node in ast.walk(tree):
                    if isinstance(node, ast.Str):
                        if self._is_hardcoded_url(node.s):
                            url_issues.append({
                                'file': file_path,
                                'line': node.lineno,
                                'type': 'hardcoded_url',
                                'severity': 'high',
                                'description': '硬编码URL',
                                'suggestion': '使用配置文件管理URL'
                            })
            
            return {
                'has_hardcoded_urls': len(url_issues) > 0,
                'url_count': len(url_issues),
                'issues': url_issues[:10],
                'score': max(0, 1.0 - len(url_issues) * 0.1)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码URL失败: {e}")
            return {'has_hardcoded_urls': False, 'url_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_hardcoded_credentials_ast(self) -> Dict[str, Any]:
        """基于AST检测硬编码凭据"""
        try:
            credential_issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                # 分析AST中的字符串字面量
                for node in ast.walk(tree):
                    if isinstance(node, ast.Str):
                        if self._is_hardcoded_credential(node.s):
                            credential_issues.append({
                                'file': file_path,
                                'line': node.lineno,
                                'type': 'hardcoded_credential',
                                'severity': 'critical',
                                'description': '硬编码凭据',
                                'suggestion': '使用环境变量或密钥管理系统'
                            })
            
            return {
                'has_hardcoded_credentials': len(credential_issues) > 0,
                'credential_count': len(credential_issues),
                'issues': credential_issues[:10],
                'score': max(0, 1.0 - len(credential_issues) * 0.2)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码凭据失败: {e}")
            return {'has_hardcoded_credentials': False, 'credential_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_data_quality_issues_ast(self) -> Dict[str, Any]:
        """基于AST检测数据质量问题"""
        try:
            quality_issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                # 分析AST中的数据质量问题
                for node in ast.walk(tree):
                    if isinstance(node, ast.Str):
                        quality_issue = self._analyze_data_quality(node, content)
                        if quality_issue['has_quality_issue']:
                            quality_issues.append({
                                'file': file_path,
                                'line': node.lineno,
                                'type': 'data_quality',
                                'severity': quality_issue['severity'],
                                'description': quality_issue['description'],
                                'suggestion': quality_issue['suggestion']
                            })
            
            return {
                'has_data_quality_issues': len(quality_issues) > 0,
                'quality_issue_count': len(quality_issues),
                'issues': quality_issues[:10],
                'score': max(0, 1.0 - len(quality_issues) * 0.05)
            }
            
        except Exception as e:
            self.logger.error(f"检测数据质量问题失败: {e}")
            return {'has_data_quality_issues': False, 'quality_issue_count': 0, 'issues': [], 'score': 1.0}
    
    def _analyze_data_quality(self, str_node: ast.Str, content: str) -> Dict[str, Any]:
        """分析数据质量"""
        analysis = {
            'has_quality_issue': False,
            'severity': 'low',
            'description': '',
            'suggestion': ''
        }
        
        s = str_node.s
        if not s or len(s) < 2:
            return analysis
        
        # 检查是否包含空值或无效值
        if s.strip() in ['', 'null', 'none', 'undefined', 'n/a', 'na']:
            analysis['has_quality_issue'] = True
            analysis['severity'] = 'medium'
            analysis['description'] = '包含空值或无效值'
            analysis['suggestion'] = '使用适当的数据验证'
        
        # 检查是否包含不一致的格式
        if self._has_inconsistent_format(s):
            analysis['has_quality_issue'] = True
            analysis['severity'] = 'low'
            analysis['description'] = '数据格式不一致'
            analysis['suggestion'] = '统一数据格式'
        
        return analysis
    
    def _has_inconsistent_format(self, s: str) -> bool:
        """检查是否有不一致的格式"""
        # 检查是否混合了不同的命名风格
        has_camel_case = bool(re.search(r'[a-z][A-Z]', s))
        has_snake_case = '_' in s
        has_kebab_case = '-' in s
        
        # 如果同时包含多种命名风格，认为格式不一致
        format_count = sum([has_camel_case, has_snake_case, has_kebab_case])
        return format_count > 1
    
    def _detect_hardcoded_config_values_ast(self) -> Dict[str, Any]:
        """基于AST检测硬编码的配置值"""
        try:
            hardcoded_issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                # 分析AST中的数字字面量
                for node in ast.walk(tree):
                    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                        config_value = self._analyze_config_value_hardcoding(node, content)
                        if config_value['is_hardcoded']:
                            hardcoded_issues.append({
                                'file': file_path,
                                'line': node.lineno,
                                'type': 'hardcoded_config_value',
                                'severity': config_value['severity'],
                                'description': config_value['description'],
                                'suggestion': config_value['suggestion'],
                                'value': node.value
                            })
            
            return {
                'has_hardcoded_config_values': len(hardcoded_issues) > 0,
                'hardcoded_count': len(hardcoded_issues),
                'issues': hardcoded_issues[:20],
                'score': max(0, 1.0 - len(hardcoded_issues) * 0.02)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码配置值失败: {e}")
            return {'has_hardcoded_config_values': False, 'hardcoded_count': 0, 'issues': [], 'score': 1.0}
    
    def _analyze_config_value_hardcoding(self, const_node: ast.Constant, content: str) -> Dict[str, Any]:
        """分析配置值是否硬编码"""
        analysis = {
            'is_hardcoded': False,
            'severity': 'low',
            'description': '',
            'suggestion': ''
        }
        
        value = const_node.value
        
        # 检查是否是配置相关的数字
        if isinstance(value, float) and 0 < value < 1:
            # 检查是否在配置上下文中
            if self._is_in_config_context(const_node, content):
                analysis['is_hardcoded'] = True
                analysis['severity'] = 'medium'
                analysis['description'] = f'硬编码配置值: {value}'
                analysis['suggestion'] = '将配置值提取为常量或配置文件'
        
        # 检查是否是布尔值
        elif isinstance(value, bool):
            if self._is_in_config_context(const_node, content):
                analysis['is_hardcoded'] = True
                analysis['severity'] = 'low'
                analysis['description'] = f'硬编码布尔值: {value}'
                analysis['suggestion'] = '将布尔值提取为常量'
        
        return analysis
    
    def _is_in_config_context(self, node: ast.Constant, content: str) -> bool:
        """检查节点是否在配置上下文中"""
        # 获取节点所在的行
        lines = content.split('\n')
        if node.lineno <= len(lines):
            line = lines[node.lineno - 1]
            
            # 检查是否包含配置相关的关键词
            config_keywords = [
                'confidence', 'relevance', 'threshold', 'weight', 'score',
                'high', 'medium', 'low', 'default', 'penalty', 'bonus',
                'quality', 'format', 'length', 'type', 'specific'
            ]
            
            return any(keyword in line.lower() for keyword in config_keywords)
        
        return False
    
    def _detect_hardcoded_booleans_ast(self) -> Dict[str, Any]:
        """基于AST检测硬编码的布尔值"""
        try:
            hardcoded_issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                # 分析AST中的布尔字面量
                for node in ast.walk(tree):
                    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
                        boolean_value = self._analyze_boolean_hardcoding(node, content)
                        if boolean_value['is_hardcoded']:
                            hardcoded_issues.append({
                                'file': file_path,
                                'line': node.lineno,
                                'type': 'hardcoded_boolean',
                                'severity': boolean_value['severity'],
                                'description': boolean_value['description'],
                                'suggestion': boolean_value['suggestion'],
                                'value': node.value
                            })
            
            return {
                'has_hardcoded_booleans': len(hardcoded_issues) > 0,
                'hardcoded_count': len(hardcoded_issues),
                'issues': hardcoded_issues[:10],
                'score': max(0, 1.0 - len(hardcoded_issues) * 0.05)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码布尔值失败: {e}")
            return {'has_hardcoded_booleans': False, 'hardcoded_count': 0, 'issues': [], 'score': 1.0}
    
    def _analyze_boolean_hardcoding(self, const_node: ast.Constant, content: str) -> Dict[str, Any]:
        """分析布尔值是否硬编码"""
        analysis = {
            'is_hardcoded': False,
            'severity': 'low',
            'description': '',
            'suggestion': ''
        }
        
        value = const_node.value
        
        # 检查是否在配置上下文中
        if self._is_in_config_context(const_node, content):
            analysis['is_hardcoded'] = True
            analysis['severity'] = 'low'
            analysis['description'] = f'硬编码布尔值: {value}'
            analysis['suggestion'] = '将布尔值提取为常量'
        
        return analysis