"""
硬编码和模拟数据检测分析器
专门检测系统中的硬编码数据、模拟数据、虚假数据等问题
"""

import ast
import re
from typing import Dict, Any, List
from base_analyzer import BaseAnalyzer


class HardcodedDataAnalyzer(BaseAnalyzer):
    """硬编码和模拟数据检测分析器"""
    
    def analyze(self) -> Dict[str, Any]:
        """执行硬编码和模拟数据检测分析"""
        # 收集所有问题
        all_issues = []
        
        # 检测各种硬编码数据问题
        hardcoded_strings = self._detect_hardcoded_strings()
        simulated_data = self._detect_simulated_data()
        mock_fake_data = self._detect_mock_fake_data()
        test_data_in_production = self._detect_test_data_in_production()
        magic_numbers = self._detect_magic_numbers()
        hardcoded_paths = self._detect_hardcoded_paths()
        hardcoded_urls = self._detect_hardcoded_urls()
        hardcoded_credentials = self._detect_hardcoded_credentials()
        data_quality_issues = self._detect_data_quality_issues()
        
        # 合并所有问题
        all_issues.extend(hardcoded_strings.get('issues', []))
        all_issues.extend(simulated_data.get('issues', []))
        all_issues.extend(mock_fake_data.get('issues', []))
        all_issues.extend(test_data_in_production.get('issues', []))
        all_issues.extend(magic_numbers.get('issues', []))
        all_issues.extend(hardcoded_paths.get('issues', []))
        all_issues.extend(hardcoded_urls.get('issues', []))
        all_issues.extend(hardcoded_credentials.get('issues', []))
        all_issues.extend(data_quality_issues.get('issues', []))
        
        # 计算分数
        total_issues = len(all_issues)
        score = max(0, 1.0 - (total_issues / 100.0))  # 每100个问题扣1分
        
        return {
            "score": score,
            "total_issues": total_issues,
            "issues": all_issues,
            "hardcoded_strings": hardcoded_strings,
            "simulated_data": simulated_data,
            "mock_fake_data": mock_fake_data,
            "test_data_in_production": test_data_in_production,
            "magic_numbers": magic_numbers,
            "hardcoded_paths": hardcoded_paths,
            "hardcoded_urls": hardcoded_urls,
            "hardcoded_credentials": hardcoded_credentials,
            "data_quality_issues": data_quality_issues
        }
    
    def _detect_hardcoded_strings(self) -> Dict[str, Any]:
        """检测硬编码字符串"""
        try:
            hardcoded_issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Constant) and isinstance(node.value, str):
                        string_value = node.value
                        
                        # 检测硬编码的业务数据
                        if self._is_hardcoded_business_data(string_value):
                            hardcoded_issues.append({
                                'file': file_path,
                                'line': node.lineno,
                                'type': 'hardcoded_business_data',
                                'value': string_value[:50] + '...' if len(string_value) > 50 else string_value,
                                'severity': 'high'
                            })
                        
                        # 检测硬编码的配置值
                        elif self._is_hardcoded_config(string_value):
                            hardcoded_issues.append({
                                'file': file_path,
                                'line': node.lineno,
                                'type': 'hardcoded_config',
                                'value': string_value[:50] + '...' if len(string_value) > 50 else string_value,
                                'severity': 'medium'
                            })
            
            return {
                'has_hardcoded_strings': len(hardcoded_issues) > 0,
                'hardcoded_count': len(hardcoded_issues),
                'issues': hardcoded_issues[:10],  # 只显示前10个问题
                'score': max(0, 1.0 - len(hardcoded_issues) * 0.1)  # 每个问题扣0.1分
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码字符串失败: {e}")
            return {'has_hardcoded_strings': False, 'hardcoded_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_simulated_data(self) -> Dict[str, Any]:
        """检测模拟数据"""
        try:
            simulated_issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测模拟数据相关的关键词和模式
                simulated_patterns = [
                    r'simulated.*data',
                    r'mock.*data',
                    r'fake.*data',
                    r'dummy.*data',
                    r'test.*data',
                    r'sample.*data',
                    r'placeholder.*data',
                    r'# 模拟',
                    r'# 虚假',
                    r'# 测试数据',
                    r'模拟.*数据',
                    r'虚假.*数据',
                    r'测试.*数据'
                ]
                
                for pattern in simulated_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        context = self._get_line_context(content, line_num)
                        
                        # 过滤掉注释中的模拟数据（误报）
                        if self._is_comment_only_simulation(context, pattern):
                            continue
                        
                        # 过滤掉测试文件中的模拟数据
                        if self._is_test_file_simulation(file_path, context):
                            continue
                        
                        simulated_issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': 'simulated_data',
                            'pattern': pattern,
                            'context': context,
                            'severity': 'high'
                        })
            
            # 输出具体的模拟数据位置用于调试
            if simulated_issues:
                self.logger.info(f"发现 {len(simulated_issues)} 个模拟数据问题:")
                for issue in simulated_issues[:10]:  # 只显示前10个
                    self.logger.info(f"  {issue['file']}:{issue['line']} - {issue['pattern']} - {issue['context'].strip()}")
            
            return {
                'has_simulated_data': len(simulated_issues) > 0,
                'simulated_count': len(simulated_issues),
                'issues': simulated_issues[:10],
                'score': max(0, 1.0 - len(simulated_issues) * 0.2)  # 每个问题扣0.2分
            }
            
        except Exception as e:
            self.logger.error(f"检测模拟数据失败: {e}")
            return {'has_simulated_data': False, 'simulated_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_mock_fake_data(self) -> Dict[str, Any]:
        """检测Mock和虚假数据"""
        try:
            mock_issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                for node in ast.walk(tree):
                    # 检测函数定义中的mock/fake数据
                    if isinstance(node, ast.FunctionDef):
                        func_name = node.name.lower()
                        if any(keyword in func_name for keyword in ['mock', 'fake', 'dummy', 'test', 'simulate']):
                            mock_issues.append({
                                'file': file_path,
                                'line': node.lineno,
                                'type': 'mock_function',
                                'function_name': node.name,
                                'severity': 'medium'
                            })
                    
                    # 检测变量赋值中的mock/fake数据
                    elif isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                var_name = target.id.lower()
                                if any(keyword in var_name for keyword in ['mock', 'fake', 'dummy', 'test', 'simulate']):
                                    mock_issues.append({
                                        'file': file_path,
                                        'line': node.lineno,
                                        'type': 'mock_variable',
                                        'variable_name': target.id,
                                        'severity': 'medium'
                                    })
            
            return {
                'has_mock_fake_data': len(mock_issues) > 0,
                'mock_count': len(mock_issues),
                'issues': mock_issues[:10],
                'score': max(0, 1.0 - len(mock_issues) * 0.15)
            }
            
        except Exception as e:
            self.logger.error(f"检测Mock虚假数据失败: {e}")
            return {'has_mock_fake_data': False, 'mock_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_test_data_in_production(self) -> Dict[str, Any]:
        """检测生产环境中的测试数据"""
        try:
            test_data_issues = []
            
            for file_path in self.python_files:
                # 跳过测试文件
                if 'test' in file_path.lower() or 'spec' in file_path.lower():
                    continue
                
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测测试数据模式
                test_data_patterns = [
                    r'test.*user',
                    r'test.*password',
                    r'test.*email',
                    r'test.*data',
                    r'sample.*user',
                    r'demo.*data',
                    r'example.*data',
                    r'测试.*用户',
                    r'测试.*密码',
                    r'示例.*数据'
                ]
                
                for pattern in test_data_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        test_data_issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': 'test_data_in_production',
                            'pattern': pattern,
                            'context': self._get_line_context(content, line_num),
                            'severity': 'high'
                        })
            
            return {
                'has_test_data_in_production': len(test_data_issues) > 0,
                'test_data_count': len(test_data_issues),
                'issues': test_data_issues[:10],
                'score': max(0, 1.0 - len(test_data_issues) * 0.3)  # 生产环境中的测试数据问题更严重
            }
            
        except Exception as e:
            self.logger.error(f"检测生产环境测试数据失败: {e}")
            return {'has_test_data_in_production': False, 'test_data_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_magic_numbers(self) -> Dict[str, Any]:
        """检测魔法数字"""
        try:
            magic_number_issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                        value = node.value
                        
                        # 检测魔法数字
                        if self._is_magic_number(value):
                            magic_number_issues.append({
                                'file': file_path,
                                'line': node.lineno,
                                'type': 'magic_number',
                                'value': value,
                                'severity': 'medium'
                            })
            
            return {
                'has_magic_numbers': len(magic_number_issues) > 0,
                'magic_number_count': len(magic_number_issues),
                'issues': magic_number_issues[:10],
                'score': max(0, 1.0 - len(magic_number_issues) * 0.05)  # 魔法数字问题相对较轻
            }
            
        except Exception as e:
            self.logger.error(f"检测魔法数字失败: {e}")
            return {'has_magic_numbers': False, 'magic_number_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_hardcoded_paths(self) -> Dict[str, Any]:
        """检测硬编码路径"""
        try:
            path_issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测硬编码路径模式
                path_patterns = [
                    r'["\']/[^"\']*["\']',  # Unix路径
                    r'["\']C:\\[^"\']*["\']',  # Windows路径
                    r'["\']D:\\[^"\']*["\']',  # Windows路径
                    r'["\']E:\\[^"\']*["\']',  # Windows路径
                    r'["\']/home/[^"\']*["\']',  # 用户目录
                    r'["\']/usr/[^"\']*["\']',  # 系统目录
                    r'["\']/var/[^"\']*["\']',  # 系统目录
                ]
                
                for pattern in path_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        path_issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': 'hardcoded_path',
                            'path': match.group(),
                            'severity': 'high'
                        })
            
            return {
                'has_hardcoded_paths': len(path_issues) > 0,
                'path_count': len(path_issues),
                'issues': path_issues[:10],
                'score': max(0, 1.0 - len(path_issues) * 0.2)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码路径失败: {e}")
            return {'has_hardcoded_paths': False, 'path_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_hardcoded_urls(self) -> Dict[str, Any]:
        """检测硬编码URL"""
        try:
            url_issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测硬编码URL模式
                url_patterns = [
                    r'["\']https?://[^"\']*["\']',
                    r'["\']ftp://[^"\']*["\']',
                    r'["\']file://[^"\']*["\']'
                ]
                
                for pattern in url_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        url_issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': 'hardcoded_url',
                            'url': match.group(),
                            'severity': 'medium'
                        })
            
            return {
                'has_hardcoded_urls': len(url_issues) > 0,
                'url_count': len(url_issues),
                'issues': url_issues[:10],
                'score': max(0, 1.0 - len(url_issues) * 0.15)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码URL失败: {e}")
            return {'has_hardcoded_urls': False, 'url_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_hardcoded_credentials(self) -> Dict[str, Any]:
        """检测硬编码凭据"""
        try:
            credential_issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测硬编码凭据模式
                credential_patterns = [
                    r'password\s*=\s*["\'][^"\']*["\']',
                    r'passwd\s*=\s*["\'][^"\']*["\']',
                    r'pwd\s*=\s*["\'][^"\']*["\']',
                    r'secret\s*=\s*["\'][^"\']*["\']',
                    r'key\s*=\s*["\'][^"\']*["\']',
                    r'token\s*=\s*["\'][^"\']*["\']',
                    r'api_key\s*=\s*["\'][^"\']*["\']',
                    r'access_token\s*=\s*["\'][^"\']*["\']'
                ]
                
                for pattern in credential_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        credential_issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': 'hardcoded_credential',
                            'pattern': pattern,
                            'context': self._get_line_context(content, line_num),
                            'severity': 'critical'
                        })
            
            return {
                'has_hardcoded_credentials': len(credential_issues) > 0,
                'credential_count': len(credential_issues),
                'issues': credential_issues[:10],
                'score': max(0, 1.0 - len(credential_issues) * 0.5)  # 凭据泄露问题最严重
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码凭据失败: {e}")
            return {'has_hardcoded_credentials': False, 'credential_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_data_quality_issues(self) -> Dict[str, Any]:
        """检测数据质量问题"""
        try:
            quality_issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测数据质量问题模式
                quality_patterns = [
                    r'return\s*\{\}',  # 返回空字典
                    r'return\s*\[\]',  # 返回空列表
                    r'return\s*None',  # 返回None
                    r'return\s*""',  # 返回空字符串
                    r'return\s*0',  # 返回0
                    r'return\s*False',  # 返回False
                    r'# TODO.*数据',
                    r'# FIXME.*数据',
                    r'# 临时.*数据',
                    r'# 测试.*数据'
                ]
                
                for pattern in quality_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        quality_issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': 'data_quality_issue',
                            'pattern': pattern,
                            'context': self._get_line_context(content, line_num),
                            'severity': 'low'
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
    
    def _is_hardcoded_business_data(self, string_value: str) -> bool:
        """基于字符串特征判断是否为硬编码的业务数据"""
        if not string_value or len(string_value) < 2:
            return False
        
        # 基于字符串结构特征分析，不依赖正则表达式
        return self._analyze_string_business_patterns(string_value)
    
    def _analyze_string_business_patterns(self, s: str) -> bool:
        """分析字符串的业务模式特征"""
        # 1. 检查人名模式（首字母大写，空格分隔）
        if self._is_name_pattern(s):
            return True
        
        # 2. 检查地名模式
        if self._is_location_pattern(s):
            return True
        
        # 3. 检查特定业务术语
        if self._contains_business_terms(s):
            return True
        
        # 4. 检查历史/文化相关术语
        if self._contains_historical_terms(s):
            return True
        
        return False
    
    def _is_name_pattern(self, s: str) -> bool:
        """检查是否是人名模式"""
        words = s.split()
        if len(words) < 2 or len(words) > 5:
            return False
        
        # 检查每个词是否以大写字母开头
        for word in words:
            if not word or not word[0].isupper():
                return False
        
        return True
    
    def _is_location_pattern(self, s: str) -> bool:
        """检查是否是地名模式"""
        location_indicators = [
            'park', 'building', 'tower', 'center', 'central', 'world',
            'trade', 'city', 'street', 'avenue', 'road', 'place'
        ]
        
        s_lower = s.lower()
        return any(indicator in s_lower for indicator in location_indicators)
    
    def _contains_business_terms(self, s: str) -> bool:
        """检查是否包含业务术语"""
        business_terms = [
            'president', 'assassinated', 'first lady', 'classification',
            'library', 'dewey', 'fifa', 'uefa', 'champions'
        ]
        
        s_lower = s.lower()
        return any(term in s_lower for term in business_terms)
    
    def _contains_historical_terms(self, s: str) -> bool:
        """检查是否包含历史/文化术语"""
        historical_terms = [
            'monroe', 'madison', 'jefferson', 'lincoln', 'ballou',
            'bronte', 'charlotte', 'jane', 'eyre', 'london', 'france'
        ]
        
        s_lower = s.lower()
        return any(term in s_lower for term in historical_terms)
    
    def _is_hardcoded_config(self, string_value: str) -> bool:
        """判断是否为硬编码的配置值"""
        config_patterns = [
            r'^\d+$',  # 纯数字
            r'^[A-Z_]+$',  # 全大写常量
            r'^[a-z]+_[a-z]+$',  # 下划线分隔的小写字符串
            r'^[a-z]+$'  # 简单小写字符串
        ]
        
        for pattern in config_patterns:
            if re.match(pattern, string_value):
                return True
        
        return False
    
    def _is_magic_number(self, value: float) -> bool:
        """判断是否为魔法数字"""
        # 常见的魔法数字
        magic_numbers = [0, 1, 2, 3, 4, 5, 10, 100, 1000, 1024, 3600, 86400]
        
        if isinstance(value, int):
            return value in magic_numbers
        
        if isinstance(value, float):
            return any(abs(value - magic) < 0.001 for magic in magic_numbers)
        
        return False
    
    def _get_line_context(self, content: str, line_num: int) -> str:
        """获取指定行的上下文"""
        lines = content.split('\n')
        if 0 <= line_num - 1 < len(lines):
            return lines[line_num - 1].strip()
        return ""
    
    def _is_comment_only_simulation(self, context: str, pattern: str) -> bool:
        """检查是否是注释中的模拟数据（误报）"""
        context = context.strip()
        
        # 如果是注释行，且只是说明性文字，认为是误报
        if context.startswith('#'):
            # 检查是否是纯注释说明
            if any(keyword in context for keyword in ['# 模拟', '# 测试数据', '# 示例']):
                return True
        
        # 如果包含"模拟"但只是注释说明
        if '模拟' in context and context.startswith('#'):
            return True
        
        return False
    
    def _is_test_file_simulation(self, file_path: str, context: str) -> bool:
        """检查是否是测试文件中的模拟数据"""
        # 检查文件路径是否包含测试相关目录
        test_dirs = ['test', 'tests', 'testing', 'spec', 'specs']
        if any(test_dir in file_path.lower() for test_dir in test_dirs):
            return True
        
        # 检查文件名是否包含测试相关关键词
        import os
        filename = os.path.basename(file_path).lower()
        if any(keyword in filename for keyword in ['test', 'spec', 'mock', 'fake']):
            return True
        
        return False
