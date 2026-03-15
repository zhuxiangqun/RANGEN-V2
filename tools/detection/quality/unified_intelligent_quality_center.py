#!/usr/bin/env python3
"""
统一智能质量检测中心 - 修复版本
提供全面的代码质量检测和分析功能
"""

import os
import re
import logging
import subprocess
import sys
import json
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

# 导入统一中心系统
from src.utils.unified_centers import get_unified_center

# 设置日志
logger = logging.getLogger(__name__)

class UnifiedErrorHandler:
    """统一错误处理器"""
    
    @staticmethod
    def handle_error(error: Exception, context: str = "") -> None:
        """处理错误"""
        logger.error(f"Error in {context}: {str(error)}")
    
    @staticmethod
    def safe_execute(func, *args, **kwargs):
        """安全执行函数"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            UnifiedErrorHandler.handle_error(e, func.__name__)
            return None

class BaseInterface:
    """统一接口基类"""
    
    def __init__(self) -> None:
        self.initialized = True
    
    def validate_input(self, data: Any) -> bool:
        """验证输入数据"""
        return data is not None

class Severity(Enum):
    """严重程度枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IssueType(Enum):
    """问题类型枚举"""
    # 基础代码质量问题
    SYNTAX_ERROR = "syntax_error"
    LOGIC_ERROR = "logic_error"
    PERFORMANCE_ISSUE = "performance_issue"
    SECURITY_VULNERABILITY = "security_vulnerability"
    STRUCTURE_ISSUE = "structure_issue"
    
    # 智能质量问题
    HARDCODED_VALUE = "hardcoded_value"
    MOCK_RESPONSE = "mock_response"
    SIMPLIFIED_LOGIC = "simplified_logic"
    PSEUDO_INTELLIGENCE = "pseudo_intelligence"
    MISSING_ERROR_HANDLING = "missing_error_handling"
    
    # 静态分析问题
    STATIC_ANALYSIS_ERROR = "static_analysis_error"

@dataclass
class QualityIssue:
    """质量问题数据类"""
    file_path: str
    line_number: int
    issue_type: IssueType
    severity: Severity
    description: str
    suggestion: str
    code_snippet: str
    confidence: float

class UnifiedIntelligentQualityCenter:
    """统一智能质量检测中心"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.context = {}
        
        # 检测模式配置
        self.detection_modes = {
            "basic": ["syntax", "logic", "performance"],
            "comprehensive": ["syntax", "logic", "performance", "security", "structure"],
            "intelligent": ["syntax", "logic", "performance", "security", "structure", "intelligence"],
            "full": ["syntax", "logic", "performance", "security", "structure", "intelligence", "linter"]
        }
    
    def _is_test_file(self, file_path: str) -> bool:
        """判断是否为测试文件"""
        test_patterns = [
            r'test_.*\.py$',
            r'.*_test\.py$',
            r'.*test.*\.py$'
        ]
        
        for pattern in test_patterns:
            if re.match(pattern, os.path.basename(file_path)):
                return True
        return False
    
    def detect_hardcoded_values(self, file_path: str, content: str) -> List[QualityIssue]:
        """检测硬编码值"""
        issues = []
        lines = content.split('\n')
        
        # 硬编码模式 - 更智能的检测
        hardcoded_patterns = [
            (r'"[^"]{15,}"', "长字符串硬编码"),  # 提高长度阈值
            (r"'[^']{15,}'", "长字符串硬编码"),  # 提高长度阈值
            (r'\b\d{5,}\b', "大数字硬编码"),  # 提高数字阈值
            (r'localhost|127\.0\.0\.1', "本地地址硬编码"),
            (r'http://[^\s"\']+', "URL硬编码"),
            (r'password\s*=\s*["\'][^"\']+["\']', "密码硬编码"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "API密钥硬编码")
        ]
        
        # 排除配置常量的模式
        config_patterns = [
            r'[A-Z_]+_CONFIG\s*=',
            r'[A-Z_]+_KEYS\s*=',
            r'[A-Z_]+_MESSAGES\s*=',
            r'[A-Z_]+_PATTERNS\s*=',
            r'CONSTANTS\s*=',
            r'DEFAULT_\w+\s*='
        ]
        
        for line_num, line in enumerate(lines, 1):
            # 检查是否是配置常量定义行
            is_config_line = any(re.search(pattern, line) for pattern in config_patterns)
            
            for pattern, description in hardcoded_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    # 跳过配置常量定义行
                    if is_config_line:
                        continue
                    
                    issues.append(QualityIssue(
                        file_path=file_path,
                        line_number=line_num,
                        issue_type=IssueType.HARDCODED_VALUE,
                        severity=Severity.MEDIUM,
                        description=f"{description}: {match.group()}",
                        suggestion="将硬编码值提取到配置文件或环境变量中",
                        code_snippet=line.strip(),
                        confidence=0.8
                    ))
        
        return issues
    
    def detect_mock_responses(self, file_path: str, content: str) -> List[QualityIssue]:
        """检测模拟响应"""
        issues = []
        lines = content.split('\n')
        
        # 模拟响应模式
        mock_patterns = [
            (r'return\s+["\'].*mock.*["\']', "返回模拟数据"),
            (r'return\s+["\'].*test.*["\']', "返回测试数据"),
            (r'return\s+["\'].*dummy.*["\']', "返回虚拟数据"),
            (r'return\s+["\'].*placeholder.*["\']', "返回占位符数据"),
            (r'# TODO.*模拟', "TODO模拟注释"),
            (r'# 模拟.*响应', "模拟响应注释")
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description in mock_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(QualityIssue(
                        file_path=file_path,
                        line_number=line_num,
                        issue_type=IssueType.MOCK_RESPONSE,
                        severity=Severity.HIGH,
                        description=f"{description}",
                        suggestion="实现真实的业务逻辑，避免返回模拟数据",
                        code_snippet=line.strip(),
                        confidence=0.9
                    ))
        
        return issues
    
    def detect_simplified_logic(self, file_path: str, content: str) -> List[QualityIssue]:
        """检测简化逻辑"""
        issues = []
        lines = content.split('\n')
        
        # 简化逻辑模式
        simplified_patterns = [
            (r'if\s+True:', "总是为真的条件"),
            (r'if\s+False:', "总是为假的条件"),
            (r'return\s+True\s*$', "简单返回True"),
            (r'return\s+False\s*$', "简单返回False"),
            (r'return\s+None\s*$', "简单返回None"),
            (r'pass\s*$', "空实现"),
            (r'# TODO.*实现', "TODO实现注释")
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description in simplified_patterns:
                if re.search(pattern, line.strip()):
                    issues.append(QualityIssue(
                        file_path=file_path,
                        line_number=line_num,
                        issue_type=IssueType.SIMPLIFIED_LOGIC,
                        severity=Severity.MEDIUM,
                        description=f"{description}",
                        suggestion="实现完整的业务逻辑",
                        code_snippet=line.strip(),
                        confidence=0.7
                    ))
        
        return issues
    
    def detect_pseudo_intelligence(self, file_path: str, content: str) -> List[QualityIssue]:
        """检测伪智能"""
        issues = []
        lines = content.split('\n')
        
        # 伪智能模式
        pseudo_patterns = [
            (r'智能.*分析.*结果', "伪智能分析"),
            (r'基于.*查询.*生成', "伪智能生成"),
            (r'模拟.*智能', "模拟智能"),
            (r'# 智能.*处理', "智能处理注释"),
            (r'def.*intelligent.*\(', "智能函数定义")
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description in pseudo_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(QualityIssue(
                        file_path=file_path,
                        line_number=line_num,
                        issue_type=IssueType.PSEUDO_INTELLIGENCE,
                        severity=Severity.HIGH,
                        description=f"{description}",
                        suggestion="实现真正的智能算法，避免伪智能",
                        code_snippet=line.strip(),
                        confidence=0.8
                    ))
        
        return issues
    
    def detect_missing_error_handling(self, file_path: str, content: str) -> List[QualityIssue]:
        """检测缺失的错误处理"""
        issues = []
        lines = content.split('\n')
        
        # 需要错误处理的模式
        error_prone_patterns = [
            (r'open\([^)]+\)', "文件操作"),
            (r'requests\.', "网络请求"),
            (r'json\.loads\(', "JSON解析"),
            (r'\.split\(', "字符串分割"),
            (r'\.index\(', "列表索引"),
            (r'\.get\(', "字典获取")
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description in error_prone_patterns:
                if re.search(pattern, line):
                    # 检查是否有try-except
                    has_try_except = False
                    for check_line in lines[max(0, line_num-10):line_num+10]:
                        if 'try:' in check_line or 'except' in check_line:
                            has_try_except = True
                            break
                    
                    if not has_try_except:
                        issues.append(QualityIssue(
                            file_path=file_path,
                            line_number=line_num,
                            issue_type=IssueType.MISSING_ERROR_HANDLING,
                            severity=Severity.MEDIUM,
                            description=f"缺失错误处理: {description}",
                            suggestion="添加try-except块处理可能的异常",
                            code_snippet=line.strip(),
                            confidence=0.6
                        ))
        
        return issues
    
    def run_static_analysis(self, file_path: str) -> List[QualityIssue]:
        """运行静态分析"""
        issues = []
        
        try:
            # 使用pylint进行静态分析
            result = subprocess.run(
                ['pylint', '--output-format=json', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                try:
                    pylint_results = json.loads(result.stdout)
                    for issue in pylint_results:
                        issues.append(QualityIssue(
                            file_path=file_path,
                            line_number=issue.get('line', 0),
                            issue_type=IssueType.STATIC_ANALYSIS_ERROR,
                            severity=Severity.LOW if issue.get('type') == 'convention' else Severity.MEDIUM,
                            description=issue.get('message', ''),
                            suggestion=issue.get('message', ''),
                            code_snippet='',
                            confidence=0.9
                        ))
                except json.JSONDecodeError:
                    pass
                    
        except subprocess.TimeoutExpired:
            logger.warning(f"Pylint timeout for {file_path}")
        except FileNotFoundError:
            logger.warning("Pylint not found, skipping static analysis")
        except Exception as e:
            logger.error(f"Static analysis error for {file_path}: {e}")
        
        return issues
    
    def analyze_file(self, file_path: str, mode: str = "comprehensive") -> List[QualityIssue]:
        """分析单个文件"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return issues
        
        # 跳过测试文件
        if self._is_test_file(file_path):
            return issues
        
        # 根据模式进行检测
        detection_types = self.detection_modes.get(mode, self.detection_modes["comprehensive"])
        
        if "intelligence" in detection_types:
            issues.extend(self.detect_hardcoded_values(file_path, content))
            issues.extend(self.detect_mock_responses(file_path, content))
            issues.extend(self.detect_simplified_logic(file_path, content))
            issues.extend(self.detect_pseudo_intelligence(file_path, content))
            issues.extend(self.detect_missing_error_handling(file_path, content))
        
        if "linter" in detection_types:
            issues.extend(self.run_static_analysis(file_path))
        
        return issues
    
    def analyze_directory(self, directory: str, mode: str = "comprehensive") -> Dict[str, List[QualityIssue]]:
        """分析目录"""
        results = {}
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    issues = self.analyze_file(file_path, mode)
                    if issues:
                        results[file_path] = issues
        
        return results
    
    def generate_report(self, results: Dict[str, List[QualityIssue]]) -> Dict[str, Any]:
        """生成质量报告"""
        total_issues = sum(len(issues) for issues in results.values())
        
        # 按类型统计
        type_stats = {}
        severity_stats = {}
        
        for file_path, issues in results.items():
            for issue in issues:
                # 类型统计
                issue_type = issue.issue_type.value
                type_stats[issue_type] = type_stats.get(issue_type, 0) + 1
                
                # 严重程度统计
                severity = issue.severity.value
                severity_stats[severity] = severity_stats.get(severity, 0) + 1
        
        # 计算质量分数
        quality_score = max(0, 100 - total_issues * 2)
        
        return {
            "total_files": len(results),
            "total_issues": total_issues,
            "quality_score": quality_score,
            "type_statistics": type_stats,
            "severity_statistics": severity_stats,
            "files_with_issues": list(results.keys()),
            "detailed_results": results
        }

# 便捷函数
def get_unified_intelligent_quality_center() -> UnifiedIntelligentQualityCenter:
    """获取统一智能质量检测中心实例"""
    return UnifiedIntelligentQualityCenter()

def analyze_code_quality(file_path: str, mode: str = "comprehensive") -> List[QualityIssue]:
    """分析代码质量"""
    center = get_unified_intelligent_quality_center()
    return center.analyze_file(file_path, mode)

def analyze_directory_quality(directory: str, mode: str = "comprehensive") -> Dict[str, Any]:
    """分析目录质量"""
    center = get_unified_intelligent_quality_center()
    results = center.analyze_directory(directory, mode)
    return center.generate_report(results)