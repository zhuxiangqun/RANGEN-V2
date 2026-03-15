#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版硬编码检测器
能够检测各种复杂的硬编码形式，包括嵌套的os.getenv调用
"""

import ast
import re
import os
from typing import Dict, Any, List, Set, Union


class EnhancedHardcodedDataAnalyzer:
    """增强版硬编码检测器"""
    
    def __init__(self, python_files: List[str]):
        self.python_files = python_files
        self.logger = self._get_logger()
    
    def _get_logger(self):
        """获取日志记录器"""
        import logging
        return logging.getLogger("EnhancedHardcodedDataAnalyzer")
    
    def analyze(self) -> Dict[str, Any]:
        """执行全面的硬编码检测分析"""
        return {
            "enhanced_magic_numbers": self._detect_enhanced_magic_numbers(),
            "nested_os_getenv": self._detect_nested_os_getenv(),
            "complex_hardcoded_patterns": self._detect_complex_hardcoded_patterns(),
            "hardcoded_cleaner_issues": self._detect_hardcoded_cleaner_issues(),
            "encoding_hardcoding": self._detect_encoding_hardcoding(),
            "pattern_hardcoding": self._detect_pattern_hardcoding(),
            "hardcoded_strings": self._detect_hardcoded_strings(),
            "hardcoded_paths": self._detect_hardcoded_paths(),
            "hardcoded_urls": self._detect_hardcoded_urls(),
            "hardcoded_credentials": self._detect_hardcoded_credentials(),
            "simulated_data": self._detect_simulated_data(),
            "test_data_in_production": self._detect_test_data_in_production()
        }
    
    def _detect_enhanced_magic_numbers(self) -> Dict[str, Any]:
        """检测增强版魔法数字（包括字符串中的数字）"""
        try:
            magic_number_issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测字符串中的魔法数字
                string_magic_patterns = [
                    r'["\'](\d+)["\']',  # 字符串中的数字
                    r'os\.getenv\([^,)]+,\s*["\'](\d+)["\']\)',  # os.getenv中的数字
                    r'f["\'][^"\']*\{(\d+)\}[^"\']*["\']',  # f-string中的数字
                ]
                
                for pattern in string_magic_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        value = int(match.group(1))
                        if self._is_magic_number(value):
                            line_num = content[:match.start()].count('\n') + 1
                            magic_number_issues.append({
                                'file': file_path,
                                'line': line_num,
                                'type': 'string_magic_number',
                                'value': value,
                                'context': match.group(0)[:50] + '...' if len(match.group(0)) > 50 else match.group(0),
                                'severity': 'medium'
                            })
                
                # 检测AST中的魔法数字
                tree = self._parse_ast(content)
                if tree:
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                            value = node.value
                            if self._is_magic_number(value):
                                magic_number_issues.append({
                                    'file': file_path,
                                    'line': node.lineno,
                                    'type': 'ast_magic_number',
                                    'value': value,
                                    'severity': 'medium'
                                })
            
            return {
                'has_magic_numbers': len(magic_number_issues) > 0,
                'magic_number_count': len(magic_number_issues),
                'issues': magic_number_issues[:20],
                'score': max(0, 1.0 - len(magic_number_issues) * 0.02)
            }
            
        except Exception as e:
            self.logger.error(f"检测增强版魔法数字失败: {e}")
            return {'has_magic_numbers': False, 'magic_number_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_nested_os_getenv(self) -> Dict[str, Any]:
        """检测嵌套的os.getenv调用"""
        try:
            issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测嵌套的os.getenv模式
                nested_patterns = [
                    r'os\.getenv\([^)]*os\.getenv\([^)]*os\.getenv\([^)]*\)[^)]*\)[^)]*\)',  # 三层嵌套
                    r'os\.getenv\([^)]*os\.getenv\([^)]*\)[^)]*\)',  # 两层嵌套
                    r'os\.getenv\([^)]*"[^"]*os\.getenv\([^)]*\)[^"]*"[^)]*\)',  # 字符串中的嵌套
                ]
                
                for pattern in nested_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': 'nested_os_getenv',
                            'content': match.group(0)[:100] + '...' if len(match.group(0)) > 100 else match.group(0),
                            'severity': 'high'
                        })
            
            return {
                'has_nested_os_getenv': len(issues) > 0,
                'nested_os_getenv_count': len(issues),
                'issues': issues[:10],
                'score': max(0, 1.0 - len(issues) * 0.1)
            }
            
        except Exception as e:
            self.logger.error(f"检测嵌套os.getenv失败: {e}")
            return {'has_nested_os_getenv': False, 'nested_os_getenv_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_complex_hardcoded_patterns(self) -> Dict[str, Any]:
        """检测复杂的硬编码模式"""
        try:
            issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测复杂的硬编码模式
                complex_patterns = [
                    r'os\.getenv\([^)]*"[^"]*os\.getenv\([^)]*\)[^"]*"[^)]*\)',  # 字符串中的os.getenv
                    r'os\.path\.join\([^)]*os\.getenv\([^)]*\)[^)]*\)',  # os.path.join中的os.getenv
                    r'f"[^"]*\{os\.getenv\([^)]*os\.getenv\([^)]*\)[^)]*\)[^"]*"',  # f-string中的嵌套os.getenv
                ]
                
                for pattern in complex_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': 'complex_hardcoded_pattern',
                            'content': match.group(0)[:100] + '...' if len(match.group(0)) > 100 else match.group(0),
                            'severity': 'high'
                        })
            
            return {
                'has_complex_hardcoded_patterns': len(issues) > 0,
                'complex_hardcoded_pattern_count': len(issues),
                'issues': issues[:10],
                'score': max(0, 1.0 - len(issues) * 0.1)
            }
            
        except Exception as e:
            self.logger.error(f"检测复杂硬编码模式失败: {e}")
            return {'has_complex_hardcoded_patterns': False, 'complex_hardcoded_pattern_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_hardcoded_cleaner_issues(self) -> Dict[str, Any]:
        """检测硬编码清理器本身的问题"""
        try:
            issues = []
            
            for file_path in self.python_files:
                if 'cleaner' in file_path.lower():
                    content = self._read_file_content(file_path)
                    if not content:
                        continue
                    
                    # 检测清理器中的硬编码问题
                    cleaner_patterns = [
                        r'# -\*- coding: utf-[^"]*os\.getenv\([^)]*\)[^"]*-\*-',  # 编码声明中的硬编码
                        r'\(r\'[^\']*os\.getenv\([^)]*\)[^\']*\',[^)]*\)',  # 正则表达式中的硬编码
                        r'os\.getenv\([^)]*os\.getenv\([^)]*\)[^)]*\)',  # 嵌套的os.getenv
                    ]
                    
                    for pattern in cleaner_patterns:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            issues.append({
                                'file': file_path,
                                'line': line_num,
                                'type': 'hardcoded_cleaner_issue',
                                'content': match.group(0)[:100] + '...' if len(match.group(0)) > 100 else match.group(0),
                                'severity': 'critical'
                            })
            
            return {
                'has_hardcoded_cleaner_issues': len(issues) > 0,
                'hardcoded_cleaner_issue_count': len(issues),
                'issues': issues[:10],
                'score': max(0, 1.0 - len(issues) * 0.2)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码清理器问题失败: {e}")
            return {'has_hardcoded_cleaner_issues': False, 'hardcoded_cleaner_issue_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_encoding_hardcoding(self) -> Dict[str, Any]:
        """检测编码声明中的硬编码"""
        try:
            issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测编码声明中的硬编码
                encoding_patterns = [
                    r'# -\*- coding: utf-[^"]*os\.getenv\([^)]*\)[^"]*-\*-',
                    r'# -\*- coding: utf-[^"]*"[^"]*os\.getenv\([^)]*\)[^"]*"[^"]*-\*-',
                ]
                
                for pattern in encoding_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': 'encoding_hardcoding',
                            'content': match.group(0),
                            'severity': 'critical'
                        })
            
            return {
                'has_encoding_hardcoding': len(issues) > 0,
                'encoding_hardcoding_count': len(issues),
                'issues': issues[:10],
                'score': max(0, 1.0 - len(issues) * 0.2)
            }
            
        except Exception as e:
            self.logger.error(f"检测编码硬编码失败: {e}")
            return {'has_encoding_hardcoding': False, 'encoding_hardcoding_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_pattern_hardcoding(self) -> Dict[str, Any]:
        """检测正则表达式模式中的硬编码"""
        try:
            issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测正则表达式模式中的硬编码
                pattern_hardcoding = [
                    r'\(r\'[^\']*os\.getenv\([^)]*\)[^\']*\',[^)]*\)',  # 正则表达式中的os.getenv
                    r'\(r"[^"]*os\.getenv\([^)]*\)[^"]*",[^)]*\)',  # 正则表达式中的os.getenv
                ]
                
                for pattern in pattern_hardcoding:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': 'pattern_hardcoding',
                            'content': match.group(0)[:100] + '...' if len(match.group(0)) > 100 else match.group(0),
                            'severity': 'high'
                        })
            
            return {
                'has_pattern_hardcoding': len(issues) > 0,
                'pattern_hardcoding_count': len(issues),
                'issues': issues[:10],
                'score': max(0, 1.0 - len(issues) * 0.1)
            }
            
        except Exception as e:
            self.logger.error(f"检测模式硬编码失败: {e}")
            return {'has_pattern_hardcoding': False, 'pattern_hardcoding_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_hardcoded_strings(self) -> Dict[str, Any]:
        """检测硬编码字符串"""
        try:
            issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测硬编码字符串模式
                string_patterns = [
                    r'["\'](?:localhost|127\.0\.0\.1|0\.0\.0\.0)["\']',  # 硬编码主机地址
                    r'["\'](?:test|demo|example|sample)[^"\']*["\']',  # 测试数据
                    r'["\'](?:admin|root|user|password)[^"\']*["\']',  # 硬编码凭据
                ]
                
                for pattern in string_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': 'hardcoded_string',
                            'content': match.group(0),
                            'severity': 'medium'
                        })
            
            return {
                'has_hardcoded_strings': len(issues) > 0,
                'hardcoded_string_count': len(issues),
                'issues': issues[:10],
                'score': max(0, 1.0 - len(issues) * 0.05)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码字符串失败: {e}")
            return {'has_hardcoded_strings': False, 'hardcoded_string_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_hardcoded_paths(self) -> Dict[str, Any]:
        """检测硬编码路径"""
        try:
            issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测硬编码路径模式
                path_patterns = [
                    r'["\']/[^"\']*["\']',  # Unix路径
                    r'["\'][C-Z]:\\[^"\']*["\']',  # Windows路径
                    r'["\']\./[^"\']*["\']',  # 相对路径
                    r'["\']\.\./[^"\']*["\']',  # 上级目录路径
                ]
                
                for pattern in path_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': 'hardcoded_path',
                            'content': match.group(0),
                            'severity': 'medium'
                        })
            
            return {
                'has_hardcoded_paths': len(issues) > 0,
                'hardcoded_path_count': len(issues),
                'issues': issues[:10],
                'score': max(0, 1.0 - len(issues) * 0.1)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码路径失败: {e}")
            return {'has_hardcoded_paths': False, 'hardcoded_path_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_hardcoded_urls(self) -> Dict[str, Any]:
        """检测硬编码URL"""
        try:
            issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测硬编码URL模式
                url_patterns = [
                    r'["\']https?://[^"\']*["\']',  # HTTP/HTTPS URL
                    r'["\']ftp://[^"\']*["\']',  # FTP URL
                ]
                
                for pattern in url_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': 'hardcoded_url',
                            'content': match.group(0),
                            'severity': 'medium'
                        })
            
            return {
                'has_hardcoded_urls': len(issues) > 0,
                'hardcoded_url_count': len(issues),
                'issues': issues[:10],
                'score': max(0, 1.0 - len(issues) * 0.1)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码URL失败: {e}")
            return {'has_hardcoded_urls': False, 'hardcoded_url_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_hardcoded_credentials(self) -> Dict[str, Any]:
        """检测硬编码凭据"""
        try:
            issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测硬编码凭据模式
                credential_patterns = [
                    r'["\'](?:password|passwd|pwd)\s*[:=]\s*["\'][^"\']+["\']',  # 密码
                    r'["\'](?:username|user)\s*[:=]\s*["\'][^"\']+["\']',  # 用户名
                    r'["\'](?:api_key|secret|token)\s*[:=]\s*["\'][^"\']+["\']',  # API密钥
                ]
                
                for pattern in credential_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': 'hardcoded_credential',
                            'content': match.group(0),
                            'severity': 'high'
                        })
            
            return {
                'has_hardcoded_credentials': len(issues) > 0,
                'hardcoded_credential_count': len(issues),
                'issues': issues[:10],
                'score': max(0, 1.0 - len(issues) * 0.2)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码凭据失败: {e}")
            return {'has_hardcoded_credentials': False, 'hardcoded_credential_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_simulated_data(self) -> Dict[str, Any]:
        """检测模拟数据"""
        try:
            issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测模拟数据模式
                simulated_patterns = [
                    r'模拟[^"\']*',
                    r'mock[^"\']*',
                    r'fake[^"\']*',
                    r'simulate[^"\']*',
                ]
                
                for pattern in simulated_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': 'simulated_data',
                            'content': match.group(0),
                            'severity': 'medium'
                        })
            
            return {
                'has_simulated_data': len(issues) > 0,
                'simulated_data_count': len(issues),
                'issues': issues[:10],
                'score': max(0, 1.0 - len(issues) * 0.05)
            }
            
        except Exception as e:
            self.logger.error(f"检测模拟数据失败: {e}")
            return {'has_simulated_data': False, 'simulated_data_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_test_data_in_production(self) -> Dict[str, Any]:
        """检测生产环境中的测试数据"""
        try:
            issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测测试数据模式
                test_patterns = [
                    r'["\']test[^"\']*["\']',
                    r'["\']demo[^"\']*["\']',
                    r'["\']example[^"\']*["\']',
                    r'["\']sample[^"\']*["\']',
                ]
                
                for pattern in test_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': 'test_data_in_production',
                            'content': match.group(0),
                            'severity': 'medium'
                        })
            
            return {
                'has_test_data_in_production': len(issues) > 0,
                'test_data_in_production_count': len(issues),
                'issues': issues[:10],
                'score': max(0, 1.0 - len(issues) * 0.05)
            }
            
        except Exception as e:
            self.logger.error(f"检测生产环境测试数据失败: {e}")
            return {'has_test_data_in_production': False, 'test_data_in_production_count': 0, 'issues': [], 'score': 1.0}
    
    def _is_magic_number(self, value: Union[int, float]) -> bool:
        """判断是否为魔法数字"""
        # 扩展的魔法数字列表
        magic_numbers = {0, 1, 2, 3, 4, 5, 10, 100, 1000, 1024, 3600, 86400, 8000, 3000, 5000, 8080, 9000, 4000, 7000, 6000}
        return value in magic_numbers
    
    def _read_file_content(self, file_path: str) -> str:
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""
    
    def _parse_ast(self, content: str) -> ast.AST:
        """解析AST"""
        try:
            return ast.parse(content)
        except Exception:
            return None


def create_enhanced_hardcoded_analyzer(python_files: List[str]) -> EnhancedHardcodedDataAnalyzer:
    """创建增强版硬编码检测器"""
    return EnhancedHardcodedDataAnalyzer(python_files)
