#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能安全验证系统 - 增强系统安全性的智能解决方案

本模块提供智能安全验证功能，包括：
- 输入验证和清理
- 安全漏洞检测
- 恶意代码识别
- 安全策略管理

作者: RANGEN开发团队
版本: 1.0.0
更新时间: 2024
"""

import logging
import re
import html
import json
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import secrets

from src.utils.unified_centers import get_unified_center

logger = logging.getLogger(__name__)

@dataclass
class SecurityThreat:
    """安全威胁信息"""
    threat_type: str
    severity: str
    description: str
    affected_input: str
    mitigation: str
    confidence: float

@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    cleaned_input: str
    threats_detected: List[SecurityThreat]
    validation_score: float
    recommendations: List[str]

class IntelligentSecurityValidator:
    """智能安全验证系统"""
    
    def __init__(self):
        """初始化智能安全验证系统"""
        self.context = {"query_type": "security_validator"}
        
        # 安全模式定义
        self.security_patterns = self._initialize_security_patterns()
        self.validation_rules = self._initialize_validation_rules()
        self.threat_database = self._initialize_threat_database()
        
        # 初始化智能组件
        self._initialize_intelligent_components()
        
        logger.info("智能安全验证系统初始化完成")

    def _initialize_security_patterns(self) -> Dict[str, List[str]]:
        """初始化安全模式"""
        return {
            'sql_injection': [
                r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
                r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
                r"(\b(OR|AND)\s+'.*'\s*=\s*'.*')",
                r"(\b(OR|AND)\s+\".*\"\s*=\s*\".*\")",
                r"(\b(OR|AND)\s+\w+\s*=\s*\w+)",
                r"(\b(OR|AND)\s+\w+\s*LIKE\s+'.*')",
                r"(\b(OR|AND)\s+\w+\s*IN\s*\(.*\))",
                r"(\b(OR|AND)\s+\w+\s*BETWEEN\s+.*\s+AND\s+.*)",
                r"(\b(OR|AND)\s+\w+\s*IS\s+NULL)",
                r"(\b(OR|AND)\s+\w+\s*IS\s+NOT\s+NULL)"
            ],
            'xss_attack': [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe[^>]*>.*?</iframe>",
                r"<object[^>]*>.*?</object>",
                r"<embed[^>]*>.*?</embed>",
                r"<link[^>]*>.*?</link>",
                r"<meta[^>]*>.*?</meta>",
                r"<style[^>]*>.*?</style>",
                r"<form[^>]*>.*?</form>"
            ],
            'path_traversal': [
                r"\.\./",
                r"\.\.\\",
                r"\.\.%2f",
                r"\.\.%5c",
                r"\.\.%252f",
                r"\.\.%255c",
                r"\.\.%c0%af",
                r"\.\.%c1%9c",
                r"\.\.%c0%2f",
                r"\.\.%c1%9c"
            ],
            'command_injection': [
                r"[;&|`$]",
                r"\b(cat|ls|pwd|whoami|id|uname|ps|netstat|ifconfig|ping|nslookup)\b",
                r"\b(rm|del|mkdir|rmdir|copy|move|rename)\b",
                r"\b(type|more|less|head|tail|grep|find|locate)\b",
                r"\b(chmod|chown|chgrp|sudo|su)\b",
                r"\b(wget|curl|nc|telnet|ssh|ftp|scp)\b",
                r"\b(echo|printf|print|puts)\b",
                r"\b(exec|eval|system|shell_exec|passthru)\b"
            ],
            'code_injection': [
                r"\b(eval|exec|compile|__import__|getattr|setattr|delattr)\b",
                r"\b(globals|locals|vars|dir|hasattr)\b",
                r"\b(open|file|input|raw_input)\b",
                r"\b(execfile|reload|__builtins__)\b",
                r"\b(apply|callable|isinstance|issubclass)\b",
                r"\b(getitem|setitem|delitem|getslice|setslice|delslice)\b",
                r"\b(__getattribute__|__setattr__|__delattr__)\b",
                r"\b(__getitem__|__setitem__|__delitem__)\b"
            ]
        }

    def _initialize_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """初始化验证规则"""
        return {
            'string_input': {
                'max_length': 1000,
                'min_length': 1,
                'allowed_chars': r'[a-zA-Z0-9\s\-_.,!?@#$%^&*()+={}[\]|\\:";\'<>?/~`]',
                'forbidden_patterns': ['<script', 'javascript:', 'onload=', 'onerror=']
            },
            'numeric_input': {
                'max_value': 999999999,
                'min_value': -999999999,
                'decimal_places': 2,
                'forbidden_patterns': ['e', 'E', 'inf', 'nan']
            },
            'file_path': {
                'max_length': 255,
                'allowed_extensions': ['.py', '.txt', '.json', '.csv', '.md'],
                'forbidden_patterns': ['..', '~', '$', '`']
            },
            'url_input': {
                'max_length': 2048,
                'allowed_protocols': ['http', 'https', 'ftp'],
                'forbidden_patterns': ['javascript:', 'data:', 'vbscript:']
            }
        }

    def _initialize_threat_database(self) -> Dict[str, Dict[str, Any]]:
        """初始化威胁数据库"""
        return {
            'sql_injection': {
                'severity': 'high',
                'description': 'SQL注入攻击尝试',
                'mitigation': '使用参数化查询和输入验证',
                'confidence_threshold': 0.8
            },
            'xss_attack': {
                'severity': 'high',
                'description': '跨站脚本攻击尝试',
                'mitigation': '输出编码和内容安全策略',
                'confidence_threshold': 0.8
            },
            'path_traversal': {
                'severity': 'high',
                'description': '路径遍历攻击尝试',
                'mitigation': '路径验证和访问控制',
                'confidence_threshold': 0.9
            },
            'command_injection': {
                'severity': 'critical',
                'description': '命令注入攻击尝试',
                'mitigation': '避免执行用户输入的命令',
                'confidence_threshold': 0.9
            },
            'code_injection': {
                'severity': 'critical',
                'description': '代码注入攻击尝试',
                'mitigation': '避免执行用户输入的代码',
                'confidence_threshold': 0.9
            }
        }

    def _initialize_intelligent_components(self):
        """初始化智能组件"""
        try:
            # 使用统一中心系统获取智能威胁检测器
            self.threat_detector = get_unified_center('threat_detector')
            if not self.threat_detector:
                self.threat_detector = self._create_basic_threat_detector()
            
            # 初始化智能输入清理器
            self.input_cleaner = get_unified_center('input_cleaner')
            if not self.input_cleaner:
                self.input_cleaner = self._create_basic_input_cleaner()
                
        except Exception as e:
            logger.error(f"智能组件初始化失败: {e}")
            self.threat_detector = self._create_basic_threat_detector()
            self.input_cleaner = self._create_basic_input_cleaner()

    def _create_basic_threat_detector(self):
        """创建基础威胁检测器"""
        class BasicThreatDetector:
            def detect_threats(self, input_data: str) -> List[SecurityThreat]:
                """检测安全威胁"""
                threats = []
                
                for threat_type, patterns in self.security_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, input_data, re.IGNORECASE):
                            threat_info = self.threat_database.get(threat_type, {})
                            confidence = self._calculate_confidence(pattern, input_data)
                            
                            if confidence >= threat_info.get('confidence_threshold', 0.8):
                                threat = SecurityThreat(
                                    threat_type=threat_type,
                                    severity=threat_info.get('severity', 'medium'),
                                    description=threat_info.get('description', '未知威胁'),
                                    affected_input=input_data[:100] + '...' if len(input_data) > 100 else input_data,
                                    mitigation=threat_info.get('mitigation', '请检查输入'),
                                    confidence=confidence
                                )
                                threats.append(threat)
                
                return threats
            
            def _calculate_confidence(self, pattern: str, input_data: str) -> float:
                """计算威胁置信度"""
                matches = re.findall(pattern, input_data, re.IGNORECASE)
                if not matches:
                    return 0.0
                
                # 基于匹配数量和模式复杂度计算置信度
                match_count = len(matches)
                pattern_complexity = len(pattern)
                
                confidence = min(1.0, (match_count * 0.3 + pattern_complexity * 0.01))
                return confidence
        
        return BasicThreatDetector()

    def _create_basic_input_cleaner(self):
        """创建基础输入清理器"""
        class BasicInputCleaner:
            def clean_input(self, input_data: str, input_type: str = 'string') -> str:
                """清理输入数据"""
                try:
                    if input_type == 'string':
                        return self._clean_string_input(input_data)
                    elif input_type == 'numeric':
                        return self._clean_numeric_input(input_data)
                    elif input_type == 'file_path':
                        return self._clean_file_path_input(input_data)
                    elif input_type == 'url':
                        return self._clean_url_input(input_data)
                    else:
                        return self._clean_string_input(input_data)
                        
                except Exception as e:
                    logger.error(f"输入清理失败: {e}")
                    return ""
            
            def _clean_string_input(self, input_data: str) -> str:
                """清理字符串输入"""
                # HTML编码
                cleaned = html.escape(input_data)
                
                # 移除危险字符
                dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`', '$']
                for char in dangerous_chars:
                    cleaned = cleaned.replace(char, '')
                
                # 限制长度
                max_length = 1000
                if len(cleaned) > max_length:
                    cleaned = cleaned[:max_length]
                
                return cleaned.strip()
            
            def _clean_numeric_input(self, input_data: str) -> str:
                """清理数字输入"""
                # 只保留数字、小数点和负号
                cleaned = re.sub(r'[^0-9.\-]', '', input_data)
                
                # 验证数字格式
                try:
                    float(cleaned)
                    return cleaned
                except ValueError:
                    return "0"
            
            def _clean_file_path_input(self, input_data: str) -> str:
                """清理文件路径输入"""
                # 移除危险路径模式
                cleaned = input_data.replace('..', '')
                cleaned = cleaned.replace('~', '')
                cleaned = cleaned.replace('$', '')
                cleaned = cleaned.replace('`', '')
                
                # 限制长度
                max_length = 255
                if len(cleaned) > max_length:
                    cleaned = cleaned[:max_length]
                
                return cleaned.strip()
            
            def _clean_url_input(self, input_data: str) -> str:
                """清理URL输入"""
                # 移除危险协议
                dangerous_protocols = ['javascript:', 'data:', 'vbscript:']
                for protocol in dangerous_protocols:
                    if input_data.lower().startswith(protocol):
                        input_data = input_data[len(protocol):]
                
                # 限制长度
                max_length = 2048
                if len(input_data) > max_length:
                    input_data = input_data[:max_length]
                
                return input_data.strip()
        
        return BasicInputCleaner()

    def validate_input(self, input_data: Union[str, int, float], input_type: str = 'string') -> ValidationResult:
        """验证输入数据"""
        try:
            # 转换为字符串进行处理
            input_str = str(input_data)
            
            # 检测安全威胁
            threats = self.threat_detector.detect_threats(input_str)
            
            # 清理输入
            cleaned_input = self.input_cleaner.clean_input(input_str, input_type)
            
            # 计算验证分数
            validation_score = self._calculate_validation_score(input_str, threats)
            
            # 生成建议
            recommendations = self._generate_recommendations(threats, input_type)
            
            # 判断是否有效
            is_valid = len(threats) == 0 and validation_score > 0.5
            
            return ValidationResult(
                is_valid=is_valid,
                cleaned_input=cleaned_input,
                threats_detected=threats,
                validation_score=validation_score,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"输入验证失败: {e}")
            return ValidationResult(
                is_valid=False,
                cleaned_input="",
                threats_detected=[],
                validation_score=0.0,
                recommendations=["验证过程出现错误"]
            )

    def _calculate_validation_score(self, input_data: str, threats: List[SecurityThreat]) -> float:
        """计算验证分数"""
        try:
            base_score = 1.0
            
            # 基于威胁数量扣分
            threat_penalty = len(threats) * 0.2
            
            # 基于威胁严重程度扣分
            severity_penalty = 0.0
            for threat in threats:
                if threat.severity == 'critical':
                    severity_penalty += 0.3
                elif threat.severity == 'high':
                    severity_penalty += 0.2
                elif threat.severity == 'medium':
                    severity_penalty += 0.1
                elif threat.severity == 'low':
                    severity_penalty += 0.05
            
            # 基于输入长度调整
            length_factor = 1.0
            if len(input_data) > 1000:
                length_factor = 0.9
            elif len(input_data) < 10:
                length_factor = 0.8
            
            final_score = max(0.0, (base_score - threat_penalty - severity_penalty) * length_factor)
            return min(1.0, final_score)
            
        except Exception as e:
            logger.error(f"验证分数计算失败: {e}")
            return 0.0

    def _generate_recommendations(self, threats: List[SecurityThreat], input_type: str) -> List[str]:
        """生成安全建议"""
        try:
            recommendations = []
            
            if not threats:
                recommendations.append("输入验证通过，未发现安全威胁")
                return recommendations
            
            # 基于威胁类型生成建议
            threat_types = set(threat.threat_type for threat in threats)
            
            if 'sql_injection' in threat_types:
                recommendations.append("检测到SQL注入威胁，建议使用参数化查询")
            
            if 'xss_attack' in threat_types:
                recommendations.append("检测到XSS攻击威胁，建议对输出进行HTML编码")
            
            if 'path_traversal' in threat_types:
                recommendations.append("检测到路径遍历威胁，建议验证文件路径")
            
            if 'command_injection' in threat_types:
                recommendations.append("检测到命令注入威胁，建议避免执行用户输入的命令")
            
            if 'code_injection' in threat_types:
                recommendations.append("检测到代码注入威胁，建议避免执行用户输入的代码")
            
            # 通用建议
            recommendations.append("建议对所有用户输入进行严格验证和清理")
            recommendations.append("建议实施内容安全策略(CSP)")
            recommendations.append("建议定期更新安全规则和威胁数据库")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"建议生成失败: {e}")
            return ["建议检查输入安全性"]

    def get_security_statistics(self) -> Dict[str, Any]:
        """获取安全统计信息"""
        try:
            return {
                'threat_patterns_count': sum(len(patterns) for patterns in self.security_patterns.values()),
                'validation_rules_count': len(self.validation_rules),
                'threat_types_count': len(self.threat_database),
                'system_status': 'active',
                'last_update': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取安全统计失败: {e}")
            return {}

    def update_security_patterns(self, new_patterns: Dict[str, List[str]]):
        """更新安全模式"""
        try:
            self.security_patterns.update(new_patterns)
            logger.info(f"安全模式已更新，新增 {len(new_patterns)} 个模式组")
        except Exception as e:
            logger.error(f"安全模式更新失败: {e}")

# 全局实例
_security_validator_instance = None

def get_intelligent_security_validator() -> IntelligentSecurityValidator:
    """获取智能安全验证系统实例"""
    global _security_validator_instance
    if _security_validator_instance is None:
        _security_validator_instance = IntelligentSecurityValidator()
    return _security_validator_instance

def validate_input(input_data: Union[str, int, float], input_type: str = 'string') -> ValidationResult:
    """便捷函数: 验证输入数据"""
    validator = get_intelligent_security_validator()
    return validator.validate_input(input_data, input_type)

if __name__ == "__main__":
    # 测试智能安全验证系统
    print("测试智能安全验证系统...")
    
    validator = IntelligentSecurityValidator()
    
    # 测试各种输入
    test_inputs = [
        "Hello World",
        "SELECT * FROM users WHERE id = 1",
        "<script>alert('XSS')</script>",
        "../../../etc/passwd",
        "rm -rf /",
        "eval('malicious_code')",
        "https://example.com",
        "normal_file.txt"
    ]
    
    for test_input in test_inputs:
        result = validator.validate_input(test_input)
        print(f"输入: {test_input}")
        print(f"有效: {result.is_valid}")
        print(f"清理后: {result.cleaned_input}")
        print(f"验证分数: {result.validation_score:.3f}")
        print(f"威胁数量: {len(result.threats_detected)}")
        if result.threats_detected:
            for threat in result.threats_detected:
                print(f"  威胁: {threat.threat_type} ({threat.severity})")
        print("-" * 50)
    
    # 显示统计信息
    stats = validator.get_security_statistics()
    print(f"安全统计: {stats}")
    
    print("智能安全验证系统测试完成！")
