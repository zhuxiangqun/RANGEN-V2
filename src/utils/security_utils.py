#!/usr/bin/env python3
"""
Security Utils - 增强版本
提供全面的安全工具功能
"""

import os
import re
import html
import json
import hashlib
import secrets
import logging
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    sanitized_value: Any
    error_message: Optional[str] = None
    warnings: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


@dataclass
class SecurityResult:
    """安全检查结果"""
    has_issues: bool
    issues: List[str]
    warnings: List[str]
    confidence: float


class SecurityUtils:
    """SecurityUtils类 - 增强版本"""
    
    def __init__(self) -> None:
        """初始化"""
        self.initialized = True
        self.dangerous_patterns = [
            # SQL注入模式
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(--|\#|\/\*|\*\/)",
            r"(\bOR\b|\bAND\b).*?(\bOR\b|\bAND\b)",
            r"(\bUNION\b.*?\bSELECT\b)",
            
            # XSS模式
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            
            # 命令注入模式
            r"[;&|`$]",
            r"(\bcat\b|\bls\b|\bpwd\b|\bwhoami\b)",
            r"(\brm\b|\bmkdir\b|\bchmod\b)",
            r"(\bcurl\b|\bwget\b|\bping\b)",
            r"(\bpython\b|\bperl\b|\bruby\b)",
        ]
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.dangerous_patterns]
    
    def process_data(self, data: Any) -> Any:
        """处理数据 - 增强版本"""
        try:
            # 验证输入数据
            if not self._validate_input_data(data):
                return self._create_security_error("Invalid input data")
            
            # 执行安全检查
            security_result = self._perform_security_check(data)
            
            # 如果发现安全问题，记录并处理
            if security_result.has_issues:
                self._handle_security_issues(security_result)
                return self._create_security_error("Security issues detected")
            
            # 清理数据
            cleaned_data = self._clean_data(data)
            
            # 记录处理历史
            self._record_processing(data, cleaned_data, security_result)
            
            return cleaned_data
            
        except Exception as e:
            return self._create_security_error(f"Data processing failed: {e}")
    
    def _validate_input_data(self, data: Any) -> bool:
        """验证输入数据"""
        return data is not None
    
    def _perform_security_check(self, data: Any) -> SecurityResult:
        """执行安全检查"""
        try:
            issues = []
            warnings = []
            
            # 检查SQL注入
            sql_issues = self._check_sql_injection(data)
            issues.extend(sql_issues)
            
            # 检查XSS
            xss_issues = self._check_xss(data)
            issues.extend(xss_issues)
            
            # 检查命令注入
            cmd_issues = self._check_command_injection(data)
            issues.extend(cmd_issues)
            
            # 检查路径遍历
            path_issues = self._check_path_traversal(data)
            issues.extend(path_issues)
            
            # 检查敏感信息泄露
            sensitive_issues = self._check_sensitive_data(data)
            issues.extend(sensitive_issues)
            
            return SecurityResult(
                has_issues=len(issues) > 0,
                issues=issues,
                warnings=warnings,
                confidence=0.9 if len(issues) == 0 else 0.3
            )
            
        except Exception as e:
            return SecurityResult(
                has_issues=True,
                issues=[f"Security check failed: {e}"],
                warnings=[],
                confidence=0.0
            )
    
    def _check_sql_injection(self, data: Any) -> List[str]:
        """检查SQL注入"""
        issues = []
        data_str = str(data).lower()
        
        for pattern in self.dangerous_patterns[:4]:  # SQL注入模式
            if re.search(pattern, data_str, re.IGNORECASE):
                issues.append(f"Potential SQL injection detected: {pattern}")
        
        return issues
    
    def _check_xss(self, data: Any) -> List[str]:
        """检查XSS"""
        issues = []
        data_str = str(data)
        
        for pattern in self.dangerous_patterns[4:10]:  # XSS模式
            if re.search(pattern, data_str, re.IGNORECASE):
                issues.append(f"Potential XSS detected: {pattern}")
        
        return issues
    
    def _check_command_injection(self, data: Any) -> List[str]:
        """检查命令注入"""
        issues = []
        data_str = str(data).lower()
        
        for pattern in self.dangerous_patterns[10:15]:  # 命令注入模式
            if re.search(pattern, data_str, re.IGNORECASE):
                issues.append(f"Potential command injection detected: {pattern}")
        
        return issues
    
    def _check_path_traversal(self, data: Any) -> List[str]:
        """检查路径遍历"""
        issues = []
        data_str = str(data)
        
        path_patterns = [r'\.\./', r'\.\.\\', r'\.\.%2f', r'\.\.%5c']
        for pattern in path_patterns:
            if re.search(pattern, data_str, re.IGNORECASE):
                issues.append(f"Potential path traversal detected: {pattern}")
        
        return issues
    
    def _check_sensitive_data(self, data: Any) -> List[str]:
        """检查敏感信息泄露"""
        issues = []
        data_str = str(data)
        
        sensitive_patterns = [
            r'password\s*[:=]\s*\w+',
            r'api[_-]?key\s*[:=]\s*\w+',
            r'token\s*[:=]\s*\w+',
            r'secret\s*[:=]\s*\w+'
        ]
        
        for pattern in sensitive_patterns:
            if re.search(pattern, data_str, re.IGNORECASE):
                issues.append(f"Potential sensitive data exposure: {pattern}")
        
        return issues
    
    def _clean_data(self, data: Any) -> Any:
        """清理数据"""
        try:
            if isinstance(data, str):
                # 移除危险字符
                cleaned = data
                for pattern in self.dangerous_patterns:
                    cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
                return cleaned
            elif isinstance(data, dict):
                # 递归清理字典
                return {k: self._clean_data(v) for k, v in data.items()}
            elif isinstance(data, list):
                # 递归清理列表
                return [self._clean_data(item) for item in data]
            else:
                return data
        except Exception:
            return data
    
    def _handle_security_issues(self, security_result: SecurityResult):
        """处理安全问题"""
        if not hasattr(self, 'security_incidents'):
            self.security_incidents = []
        
        self.security_incidents.append({
            'issues': security_result.issues,
            'warnings': security_result.warnings,
            'timestamp': time.time()
        })
    
    def _record_processing(self, original_data: Any, cleaned_data: Any, security_result: SecurityResult):
        """记录处理历史"""
        if not hasattr(self, 'processing_history'):
            self.processing_history = []
        
        self.processing_history.append({
            'original': original_data,
            'cleaned': cleaned_data,
            'security_result': security_result,
            'timestamp': time.time()
        })
    
    def _create_security_error(self, message: str) -> Any:
        """创建安全错误"""
        return {
            'error': True,
            'message': message,
            'timestamp': time.time()
        }
    
    def validate(self, data: Any) -> bool:
        """验证数据 - 增强版本"""
        if isinstance(data, str):
            return self.validate_input(data)
        return data is not None
    
    def validate_input(self, data: str) -> bool:
        """验证输入数据"""
        if not isinstance(data, str):
            return False
        
        # 基本检查
        if len(data) > 1000 or len(data.strip()) == 0:
            return False
        
        # 危险模式检查
        for pattern in self.compiled_patterns:
            if pattern.search(data):
                return False
        
        return True
    
    def validate_string(self, value: str, max_length: int = 100, allow_html: bool = False) -> ValidationResult:
        """验证字符串输入"""
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                sanitized_value="",
                error_message="输入必须是字符串类型"
            )
        
        # 长度检查
        if len(value) > max_length:
            return ValidationResult(
                is_valid=False,
                sanitized_value=value[:max_length],
                error_message=f"输入长度超过限制 ({max_length} 字符)"
            )
        
        # 空值检查
        if not value.strip():
            return ValidationResult(
                is_valid=True,
                sanitized_value="",
                warnings=["输入为空"]
            )
        
        # 危险模式检查
        for pattern in self.compiled_patterns:
            if pattern.search(value):
                return ValidationResult(
                    is_valid=False,
                    sanitized_value="",
                    error_message="输入包含危险模式"
                )
        
        # HTML转义（如果不允许HTML）
        if not allow_html:
            sanitized_value = html.escape(value)
        else:
            sanitized_value = value
        
        # 增强安全检查：检测编码攻击
        if self._detect_encoding_attacks(value):
            return ValidationResult(
                is_valid=False,
                sanitized_value="",
                error_message="检测到编码攻击尝试"
            )
        
        # 增强安全检查：检测路径遍历
        if self._detect_path_traversal(value):
            return ValidationResult(
                is_valid=False,
                sanitized_value="",
                error_message="检测到路径遍历攻击"
            )
        
        # 增强安全检查：检测命令注入
        if self._detect_command_injection(value):
            return ValidationResult(
                is_valid=False,
                sanitized_value="",
                error_message="检测到命令注入攻击"
            )
        
        return ValidationResult(
            is_valid=True,
            sanitized_value=sanitized_value
        )
    
    def _detect_encoding_attacks(self, value: str) -> bool:
        """检测编码攻击"""
        # 检测URL编码攻击
        if '%' in value and len([c for c in value if c == '%']) > len(value) * 0.1:
            return True
        
        # 检测Unicode编码攻击
        if '\\u' in value or '\\x' in value:
            return True
        
        # 检测Base64编码攻击
        import base64
        try:
            if len(value) > 10 and value.replace('=', '').replace('+', '').replace('/', '').isalnum():
                decoded = base64.b64decode(value)
                if b'<' in decoded or b'>' in decoded or b'script' in decoded.lower():
                    return True
        except:
            pass
        
        return False
    
    def _detect_path_traversal(self, value: str) -> bool:
        """检测路径遍历攻击"""
        dangerous_patterns = [
            '../', '..\\', '..%2f', '..%5c', '%2e%2e%2f', '%2e%2e%5c',
            '....//', '....\\\\', '..%252f', '..%255c'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in value.lower():
                return True
        
        return False
    
    def _detect_command_injection(self, value: str) -> bool:
        """检测命令注入攻击"""
        command_patterns = [
            r';\s*(rm|del|mkdir|chmod|chown|kill|ps|netstat)',
            r'\|\s*(cat|ls|dir|type|more|less)',
            r'`[^`]*`',
            r'\$\([^)]*\)',
            r'&&\s*\w+',
            r'\|\|\s*\w+'
        ]
        
        for pattern in command_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        
        return False
    
    def sanitize_input(self, data: str) -> str:
        """清理输入数据"""
        if not isinstance(data, str):
            return ""
        dangerous_chars = ["<", ">", "'", "\"", "&", ";", "|", "`", "\\", ".."]
        for char in dangerous_chars:
            data = data.replace(char, "")
        
        return data.strip()
    
    def hash_password(self, password: str) -> str:
        """哈希密码"""
        salt = os.urandom(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return f"{salt}:{password_hash.hex()}"
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """验证密码"""
        try:
            salt, stored_hash = hashed_password.split(':')
            salt = bytes.fromhex(salt)
            stored_hash = bytes.fromhex(stored_hash)
            password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
            return password_hash == stored_hash
        except Exception:
            return False
    
    def generate_token(self, length: int = 32) -> str:
        """生成安全令牌"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return ''.join(secrets.choice(alphabet) for _ in range(length))


# 便捷函数
def get_security_utils() -> SecurityUtils:
    """获取实例"""
    return SecurityUtils()


# 全局实例
security_utils = SecurityUtils()
