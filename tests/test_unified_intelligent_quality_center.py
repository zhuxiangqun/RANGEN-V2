#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一智能质量检测中心测试
"""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from tests.test_framework import RANGENTestCase, AsyncTestCase

# 导入被测试的模块
try:
    from src.utils.unified_intelligent_quality_center import (
        UnifiedIntelligentQualityCenter,
        QualityIssue,
        IssueType
    )
except ImportError:
    print("警告: 无法导入统一智能质量检测中心模块")
    UnifiedIntelligentQualityCenter = None

class TestUnifiedIntelligentQualityCenter(RANGENTestCase):
    """统一智能质量检测中心测试"""
    
    def setUp(self):
        super().setUp()
        if UnifiedIntelligentQualityCenter:
            self.center = UnifiedIntelligentQualityCenter()
        else:
            self.skipTest("统一智能质量检测中心模块不可用")
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.center)
        self.assertTrue(hasattr(self.center, 'detect_issues'))
        self.assertTrue(hasattr(self.center, 'analyze_file'))
    
    def test_quality_issue_creation(self):
        """测试质量问题创建"""
        if not UnifiedIntelligentQualityCenter:
            self.skipTest("模块不可用")
        
        issue = QualityIssue(
            file_path="test.py",
            line_number=10,
            issue_type=IssueType.SYNTAX_ERROR,
            message="测试错误",
            severity=0.8
        )
        
        self.assertEqual(issue.file_path, "test.py")
        self.assertEqual(issue.line_number, 10)
        self.assertEqual(issue.issue_type, IssueType.SYNTAX_ERROR)
        self.assertEqual(issue.message, "测试错误")
        self.assertEqual(issue.severity, 0.8)
    
    def test_analyze_python_file(self):
        """测试Python文件分析"""
        # 创建测试Python文件
        test_content = '''
def test_function():
    """测试函数"""
    return "Hello, World!"

class TestClass:
    def __init__(self):
        self.value = 42
'''
        test_file = self.create_test_file("test_module.py", test_content)
        
        # 分析文件
        issues = self.center.analyze_file(test_file)
        
        # 验证结果
        self.assertIsInstance(issues, list)
        # 这个文件应该没有质量问题
        self.assertEqual(len(issues), 0)
    
    def test_analyze_file_with_syntax_error(self):
        """测试语法错误文件分析"""
        # 创建有语法错误的测试文件
        test_content = '''
def test_function(
    # 缺少闭合括号
    return "Hello, World!"
'''
        test_file = self.create_test_file("syntax_error.py", test_content)
        
        # 分析文件
        issues = self.center.analyze_file(test_file)
        
        # 验证结果
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0)
        
        # 检查是否有语法错误
        syntax_errors = [issue for issue in issues if issue.issue_type == IssueType.SYNTAX_ERROR]
        self.assertGreater(len(syntax_errors), 0)
    
    def test_detect_hardcoded_values(self):
        """测试硬编码值检测"""
        # 创建包含硬编码值的测试文件
        test_content = '''
def process_data():
    # 硬编码值
    threshold = 100
    max_retries = 3
    timeout = 30
    
    # 硬编码字符串
    error_message = "处理失败"
    
    return threshold, max_retries, timeout, error_message
'''
        test_file = self.create_test_file("hardcoded.py", test_content)
        
        # 分析文件
        issues = self.center.analyze_file(test_file)
        
        # 验证结果
        self.assertIsInstance(issues, list)
        # 应该检测到硬编码值
        hardcoded_issues = [issue for issue in issues if "硬编码" in issue.message]
        self.assertGreater(len(hardcoded_issues), 0)
    
    def test_detect_pseudo_intelligence(self):
        """测试伪智能检测"""
        # 创建包含伪智能的测试文件
        test_content = '''
def intelligent_analysis():
    """智能分析函数"""
    # 伪智能：简单的if-else
    if condition == "good":
        return "excellent"
    else:
        return "poor"

def smart_processing():
    """智能处理函数"""
    # 伪智能：硬编码逻辑
    return "processed" if data else "failed"
'''
        test_file = self.create_test_file("pseudo_intelligence.py", test_content)
        
        # 分析文件
        issues = self.center.analyze_file(test_file)
        
        # 验证结果
        self.assertIsInstance(issues, list)
        # 应该检测到伪智能问题
        pseudo_issues = [issue for issue in issues if "伪智能" in issue.message]
        self.assertGreater(len(pseudo_issues), 0)
    
    def test_detect_security_vulnerabilities(self):
        """测试安全漏洞检测"""
        # 创建包含安全漏洞的测试文件
        test_content = '''
import os
import subprocess

def unsafe_function(user_input):
    # 命令注入漏洞
    os.system(f"echo {user_input}")
    
    # 代码注入漏洞 (注释掉以避免实际执行)
    # eval(user_input)  # This would be detected as a security vulnerability
    
    # 路径遍历漏洞
    with open(f"../{user_input}", "r") as f:
        return f.read()
'''
        test_file = self.create_test_file("security_issues.py", test_content)
        
        # 分析文件
        issues = self.center.analyze_file(test_file)
        
        # 验证结果
        self.assertIsInstance(issues, list)
        # 应该检测到安全漏洞
        security_issues = [issue for issue in issues if "安全" in issue.message or "漏洞" in issue.message]
        self.assertGreater(len(security_issues), 0)
    
    def test_analyze_directory(self):
        """测试目录分析"""
        # 创建多个测试文件
        files_content = [
            ("good_file.py", '''
def good_function():
    """好的函数"""
    return "good"
'''),
            ("bad_file.py", '''
def bad_function(
    # 语法错误
    return "bad"
''')
        ]
        
        for filename, content in files_content:
            self.create_test_file(filename, content)
        
        # 分析目录
        all_issues = []
        for filename in ["good_file.py", "bad_file.py"]:
            file_path = os.path.join(self.test_data_dir, filename)
            issues = self.center.analyze_file(file_path)
            all_issues.extend(issues)
        
        # 验证结果
        self.assertIsInstance(all_issues, list)
        # 应该检测到语法错误
        syntax_errors = [issue for issue in all_issues if issue.issue_type == IssueType.SYNTAX_ERROR]
        self.assertGreater(len(syntax_errors), 0)
    
    def test_issue_severity_scoring(self):
        """测试问题严重性评分"""
        # 创建包含不同严重性问题的测试文件
        test_content = '''
def test_function():
    # 高严重性：安全漏洞
    # eval(user_input)  # This would be detected as a security vulnerability
    
    # 中严重性：硬编码值
    threshold = 100
    
    # 低严重性：代码风格
    x=1+2  # 缺少空格
'''
        test_file = self.create_test_file("severity_test.py", test_content)
        
        # 分析文件
        issues = self.center.analyze_file(test_file)
        
        # 验证结果
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0)
        
        # 检查严重性评分
        for issue in issues:
            self.assertGreaterEqual(issue.severity, 0.0)
            self.assertLessEqual(issue.severity, 1.0)
    
    def test_empty_file_analysis(self):
        """测试空文件分析"""
        # 创建空文件
        test_file = self.create_test_file("empty.py", "")
        
        # 分析文件
        issues = self.center.analyze_file(test_file)
        
        # 验证结果
        self.assertIsInstance(issues, list)
        # 空文件应该没有质量问题
        self.assertEqual(len(issues), 0)
    
    def test_invalid_file_analysis(self):
        """测试无效文件分析"""
        # 创建不存在的文件路径
        invalid_file = os.path.join(self.test_data_dir, "nonexistent.py")
        
        # 分析文件
        issues = self.center.analyze_file(invalid_file)
        
        # 验证结果
        self.assertIsInstance(issues, list)
        # 不存在的文件应该返回空列表或错误
        self.assertEqual(len(issues), 0)

class TestQualityIssue(RANGENTestCase):
    """质量问题测试"""
    
    def test_quality_issue_creation(self):
        """测试质量问题创建"""
        if not UnifiedIntelligentQualityCenter:
            self.skipTest("模块不可用")
        
        issue = QualityIssue(
            file_path="test.py",
            line_number=5,
            issue_type=IssueType.SYNTAX_ERROR,
            message="语法错误",
            severity=0.9
        )
        
        self.assertEqual(issue.file_path, "test.py")
        self.assertEqual(issue.line_number, 5)
        self.assertEqual(issue.issue_type, IssueType.SYNTAX_ERROR)
        self.assertEqual(issue.message, "语法错误")
        self.assertEqual(issue.severity, 0.9)
    
    def test_quality_issue_str_representation(self):
        """测试质量问题字符串表示"""
        if not UnifiedIntelligentQualityCenter:
            self.skipTest("模块不可用")
        
        issue = QualityIssue(
            file_path="test.py",
            line_number=10,
            issue_type=IssueType.SYNTAX_ERROR,
            message="测试错误",
            severity=0.8
        )
        
        str_repr = str(issue)
        self.assertIn("test.py", str_repr)
        self.assertIn("10", str_repr)
        self.assertIn("测试错误", str_repr)

if __name__ == "__main__":
    unittest.main()
