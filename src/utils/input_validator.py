"""
输入验证和安全防护模块
提供企业级输入验证，防止各种安全攻击和恶意输入
"""
import re
import json
import html
import urllib.parse
from typing import Dict, Any, List, Optional, Union, Pattern
from dataclasses import dataclass
from enum import Enum
from fastapi import HTTPException, Request, status
from src.services.logging_service import get_logger

logger = get_logger("input_validator")

class ValidationLevel(Enum):
    """验证级别"""
    STRICT = "strict"      # 严格验证，拒绝任何可疑输入
    MODERATE = "moderate"  # 中等验证，允许常见字符但检查恶意模式
    LENIENT = "lenient"    # 宽松验证，仅检查明显威胁

class ThreatType(Enum):
    """威胁类型"""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    LDAP_INJECTION = "ldap_injection"
    NO_INJECTION = "no_injection"
    SCRIPT_INJECTION = "script_injection"
    EXCESSIVE_LENGTH = "excessive_length"
    MALICIOUS_CHARS = "malicious_chars"

@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    threat_type: Optional[ThreatType] = None
    threat_details: Optional[str] = None
    sanitized_value: Optional[Any] = None
    error_message: Optional[str] = None

class InputValidator:
    """输入验证器主类"""
    
    def __init__(self, level: ValidationLevel = ValidationLevel.MODERATE):
        self.level = level
        self._init_threat_patterns()
        self._init_limits()
    
    def _init_threat_patterns(self):
        """初始化威胁检测模式"""
        # SQL注入模式
        self.sql_patterns = [
            r'(?i)(union|select|insert|update|delete|drop|create|alter|exec|execute)\s+',
            r'(?i)(\bor\b|\band\b)\s+\d+\s*=\s*\d+',
            r'(?i)(\'|").*(\bor\b|\band\b).*(\'|")',
            r'(?i)(waitfor|delay\s+|benchmark\s*\()',
            r'(?i)(information_schema|sysobjects|syscolumns)',
            r'(?i)(@@version|@@servername|user\(\))',
            r'(?i)(#|--|\/\*|\*\/)',
            r'(?i)(xp_cmdshell|sp_executesql)',
        ]
        
        # XSS模式
        self.xss_patterns = [
            r'(?i)(<script|<iframe|<object|<embed|<link|<meta)',
            r'(?i)(javascript:|vbscript:|data:|mocha:|livescript:)',
            r'(?i)(onload|onerror|onclick|onmouseover|onfocus|onblur)',
            r'(?i)(eval\(|alert\(|confirm\(|prompt\()',
            r'(?i)(document\.|window\.|location\.)',
            r'(?i)(innerHTML|outerHTML|insertAdjacentHTML)',
            r'(?i)(expression\(|url\(|@import)',
        ]
        
        # 命令注入模式 - 排除 URL 中的常见字符
        self.command_patterns = [
            # 只检查真正的命令注入模式，排除 URL
            r'(?i)(;\s*(rm|del|mkdir|chmod|chown|kill|ps|netstat))',
            r'(?i)(\|\s*(cat|ls|dir|type|more|less))',
            r'(?i)(`[^`]*`)',  # 反引号命令替换
            r'(?i)(\$\([^)]*\))',  # $() 命令替换
            r'(?i)(&&\s*(rm|del|mkdir|chmod|chown))',
            r'(?i)(\|\|\s*(rm|del|mkdir|chmod|chown))',
            r'(?i)(wget\s|curl\s)',  # wget/curl 命令
            r'(?i)(chmod\s+7|chmod\s+7|chmod\s+0)',
            r'(?i)(sudo\s|su\s)',
        ]
        
        # 路径遍历模式
        self.path_traversal_patterns = [
            r'(?i)(\.\./|\.\.\\)',
            r'(?i)(/etc/|/var/|/usr/|/home/|/root/)',
            r'(?i)(\\windows\\|\\system32\\|\\program files\\)',
            r'(?i)(%2e%2e%2f|%2e%2e%5c|%2e%2e/)',
            r'(?i)(\.\.\/\.\.\/|\.\.\\\.\.\\)',
        ]
        
        # LDAP注入模式
        self.ldap_patterns = [
            r'(?i)(\*|\(|\)|\\|\(|\))',
            r'(?i)(\&|\||\!)',
            r'(?i)(cn=|dn=|ou=|dc=|uid=)',
            r'(?i)(objectClass=|memberOf=)',
        ]
        
        # NoSQL注入模式
        self.nosql_patterns = [
            r'(?i)(\$where|\$ne|\$gt|\$lt|\$in|\$nin)',
            r'(?i)(\$regex|\$exists|\$or|\$and)',
            r'(?i)(\{.*\}.*\{.*\})',
            r'(?i)(true|false|null)\s*(\$|,)',
        ]
        
        # 脚本注入模式
        self.script_patterns = [
            r'(?i)(<%|%>|<\?|\?>)',
            r'(?i)(<script|</script>)',
            r'(?i)(<%@\s*page|<%@\s*include)',
            r'(?i)(<\?php|<\?=)',
        ]
        
        # 恶意字符模式
        self.malicious_char_patterns = [
            r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]',  # 控制字符
            r'[\uFFFE\uFFFF]',  # 无效Unicode字符
            r'[<>]',  # HTML标签字符（在严格模式下）
        ]
    
    def _init_limits(self):
        """初始化输入限制"""
        self.limits = {
            'max_string_length': 10000,
            'max_query_length': 5000,
            'max_session_id_length': 255,
            'max_name_length': 100,
            'max_context_size': 100,  # 最大context键值对数量
            'max_depth': 10,  # 最大嵌套深度
            'max_array_length': 1000,
        }
    
    def _check_pattern(self, value: str, patterns: List[str], threat_type: ThreatType) -> ValidationResult:
        """检查模式匹配"""
        for pattern in patterns:
            if re.search(pattern, value):
                logger.warning(f"检测到{threat_type.value}威胁: {pattern[:50]}...")
                return ValidationResult(
                    is_valid=False,
                    threat_type=threat_type,
                    threat_details=f"匹配到危险模式: {pattern}",
                    error_message=f"检测到潜在的{threat_type.value}攻击"
                )
        return ValidationResult(is_valid=True)
    
    def _check_length(self, value: str, max_length: int) -> ValidationResult:
        """检查长度限制"""
        if len(value) > max_length:
            return ValidationResult(
                is_valid=False,
                threat_type=ThreatType.EXCESSIVE_LENGTH,
                threat_details=f"输入长度{len(value)}超过限制{max_length}",
                error_message=f"输入长度超过最大限制{max_length}字符"
            )
        return ValidationResult(is_valid=True)
    
    def _check_depth(self, obj: Any, max_depth: int, current_depth: int = 0) -> bool:
        """检查嵌套深度"""
        if current_depth > max_depth:
            return False
        
        if isinstance(obj, dict):
            return all(self._check_depth(v, max_depth, current_depth + 1) for v in obj.values())
        elif isinstance(obj, (list, tuple)):
            return all(self._check_depth(item, max_depth, current_depth + 1) for item in obj)
        
        return True
    
    def _sanitize_string(self, value: str) -> str:
        """清理字符串"""
        # HTML转义
        sanitized = html.escape(value)
        
        # URL解码检查
        try:
            decoded = urllib.parse.unquote(sanitized)
            if decoded != sanitized:
                # 如果URL解码后不同，再次检查威胁
                if not self._check_all_patterns(decoded).is_valid:
                    sanitized = decoded  # 保留解码后的，但会在后续检查中被拒绝
        except Exception:
            pass
        
        return sanitized
    
    def _check_all_patterns(self, value: str) -> ValidationResult:
        """检查所有威胁模式"""
        # SQL注入检查
        result = self._check_pattern(value, self.sql_patterns, ThreatType.SQL_INJECTION)
        if not result.is_valid:
            return result
        
        # XSS检查
        result = self._check_pattern(value, self.xss_patterns, ThreatType.XSS)
        if not result.is_valid:
            return result
        
        # 命令注入检查
        result = self._check_pattern(value, self.command_patterns, ThreatType.COMMAND_INJECTION)
        if not result.is_valid:
            return result
        
        # 路径遍历检查
        result = self._check_pattern(value, self.path_traversal_patterns, ThreatType.PATH_TRAVERSAL)
        if not result.is_valid:
            return result
        
        # LDAP注入检查
        result = self._check_pattern(value, self.ldap_patterns, ThreatType.LDAP_INJECTION)
        if not result.is_valid:
            return result
        
        # NoSQL注入检查
        result = self._check_pattern(value, self.nosql_patterns, ThreatType.NO_INJECTION)
        if not result.is_valid:
            return result
        
        # 脚本注入检查
        result = self._check_pattern(value, self.script_patterns, ThreatType.SCRIPT_INJECTION)
        if not result.is_valid:
            return result
        
        # 恶意字符检查（仅在严格模式下）
        if self.level == ValidationLevel.STRICT:
            result = self._check_pattern(value, self.malicious_char_patterns, ThreatType.MALICIOUS_CHARS)
            if not result.is_valid:
                return result
        
        return ValidationResult(is_valid=True)
    
    def validate_string(self, value: str, max_length: Optional[int] = None, field_name: str = "string") -> ValidationResult:
        """验证字符串输入"""
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                error_message=f"{field_name}必须是字符串类型"
            )
        
        # 长度检查
        length_limit = max_length or self.limits['max_string_length']
        result = self._check_length(value, length_limit)
        if not result.is_valid:
            return result
        
        # 威胁模式检查
        result = self._check_all_patterns(value)
        if not result.is_valid:
            return result
        
        # 清理并返回
        sanitized = self._sanitize_string(value)
        return ValidationResult(
            is_valid=True,
            sanitized_value=sanitized
        )
    
    def validate_query(self, query: str) -> ValidationResult:
        """验证查询字符串"""
        return self.validate_string(query, self.limits['max_query_length'], "query")
    
    def validate_session_id(self, session_id: str) -> ValidationResult:
        """验证会话ID"""
        if not session_id:
            return ValidationResult(is_valid=True, sanitized_value=None)
        
        # 会话ID应该是字母数字和少量特殊字符
        allowed_pattern = r'^[a-zA-Z0-9_-]+$'
        if not re.match(allowed_pattern, session_id):
            return ValidationResult(
                is_valid=False,
                error_message="会话ID只能包含字母、数字、下划线和连字符"
            )
        
        return self.validate_string(session_id, self.limits['max_session_id_length'], "session_id")
    
    def validate_context(self, context: Dict[str, Any]) -> ValidationResult:
        """验证上下文数据"""
        if not isinstance(context, dict):
            return ValidationResult(
                is_valid=False,
                error_message="context必须是字典类型"
            )
        
        # 检查大小
        if len(context) > self.limits['max_context_size']:
            return ValidationResult(
                is_valid=False,
                error_message=f"context大小超过限制{self.limits['max_context_size']}"
            )
        
        # 检查嵌套深度
        if not self._check_depth(context, self.limits['max_depth']):
            return ValidationResult(
                is_valid=False,
                error_message=f"context嵌套深度超过限制{self.limits['max_depth']}"
            )
        
        # 递归验证所有值
        sanitized_context = {}
        for key, value in context.items():
            # 验证键名
            key_result = self.validate_string(str(key), 100, "context_key")
            if not key_result.is_valid:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"context键名无效: {key_result.error_message}"
                )
            
            # 验证值
            if isinstance(value, str):
                value_result = self.validate_string(value, 1000, f"context_value_{key}")
                if not value_result.is_valid:
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"context值[{key}]无效: {value_result.error_message}"
                    )
                sanitized_context[key_result.sanitized_value] = value_result.sanitized_value
            elif isinstance(value, (int, float, bool)):
                sanitized_context[key_result.sanitized_value] = value
            elif isinstance(value, dict):
                # 递归处理嵌套字典
                nested_result = self.validate_context(value)
                if not nested_result.is_valid:
                    return nested_result
                sanitized_context[key_result.sanitized_value] = nested_result.sanitized_value
            elif isinstance(value, list):
                # 验证列表
                if len(value) > self.limits['max_array_length']:
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"context列表[{key}]长度超过限制"
                    )
                sanitized_list = []
                for item in value:
                    if isinstance(item, str):
                        item_result = self.validate_string(item, 500, f"context_list_item_{key}")
                        if not item_result.is_valid:
                            return ValidationResult(
                                is_valid=False,
                                error_message=f"context列表项[{key}]无效: {item_result.error_message}"
                            )
                        sanitized_list.append(item_result.sanitized_value)
                    else:
                        sanitized_list.append(item)
                sanitized_context[key_result.sanitized_value] = sanitized_list
            else:
                # 其他类型直接拒绝
                return ValidationResult(
                    is_valid=False,
                    error_message=f"context值[{key}]类型不支持: {type(value)}"
                )
        
        return ValidationResult(
            is_valid=True,
            sanitized_value=sanitized_context
        )
    
    def validate_name(self, name: str) -> ValidationResult:
        """验证名称参数"""
        return self.validate_string(name, self.limits['max_name_length'], "name")
    
    def validate_permissions(self, permissions: str) -> ValidationResult:
        """验证权限参数"""
        if not isinstance(permissions, str):
            return ValidationResult(
                is_valid=False,
                error_message="permissions必须是字符串类型"
            )
        
        # 权限应该是逗号分隔的字母数字字符串
        permission_list = [p.strip() for p in permissions.split(",")]
        allowed_permissions = {"read", "write", "admin", "execute", "delete"}
        
        for perm in permission_list:
            if perm not in allowed_permissions:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"无效权限: {perm}。允许的权限: {', '.join(allowed_permissions)}"
                )
        
        return ValidationResult(
            is_valid=True,
            sanitized_value=",".join(permission_list)
        )
    
    def validate_request_body(self, body: Dict[str, Any], endpoint: str) -> ValidationResult:
        """验证请求体"""
        if not isinstance(body, dict):
            return ValidationResult(
                is_valid=False,
                error_message="请求体必须是JSON对象"
            )
        
        # 根据端点进行特定验证
        if endpoint == "/chat":
            return self._validate_chat_body(body)
        elif endpoint == "/auth/api-key":
            return self._validate_api_key_body(body)
        
        return ValidationResult(is_valid=True)
    
    def _validate_chat_body(self, body: Dict[str, Any]) -> ValidationResult:
        """验证聊天请求体"""
        required_fields = ["query"]
        for field in required_fields:
            if field not in body:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"缺少必需字段: {field}"
                )
        
        # 验证query
        query_result = self.validate_query(body["query"])
        if not query_result.is_valid:
            return query_result
        
        # 验证session_id（可选）
        if "session_id" in body and body["session_id"]:
            session_result = self.validate_session_id(body["session_id"])
            if not session_result.is_valid:
                return session_result
        
        # 验证context（可选）
        if "context" in body and body["context"]:
            context_result = self.validate_context(body["context"])
            if not context_result.is_valid:
                return context_result
        
        # 构建清理后的请求体
        sanitized_body = {
            "query": query_result.sanitized_value,
        }
        
        if "session_id" in body and body["session_id"]:
            sanitized_body["session_id"] = session_result.sanitized_value
        
        if "context" in body and body["context"]:
            sanitized_body["context"] = context_result.sanitized_value
        
        return ValidationResult(
            is_valid=True,
            sanitized_value=sanitized_body
        )
    
    def _validate_api_key_body(self, body: Dict[str, Any]) -> ValidationResult:
        """验证API密钥创建请求体"""
        # 这个端点使用路径参数，不是请求体
        return ValidationResult(is_valid=True)
    
    def validate_query_params(self, params: Dict[str, str], endpoint: str) -> ValidationResult:
        """验证查询参数"""
        if not isinstance(params, dict):
            return ValidationResult(
                is_valid=False,
                error_message="查询参数必须是字典"
            )
        
        sanitized_params = {}
        
        for key, value in params.items():
            # 验证参数名
            key_result = self.validate_string(str(key), 50, "param_name")
            if not key_result.is_valid:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"查询参数名无效: {key_result.error_message}"
                )
            
            # 验证参数值
            if value is not None:
                value_result = self.validate_string(str(value), 500, f"param_{key}")
                if not value_result.is_valid:
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"查询参数值[{key}]无效: {value_result.error_message}"
                    )
                sanitized_params[key_result.sanitized_value] = value_result.sanitized_value
        
        return ValidationResult(
            is_valid=True,
            sanitized_value=sanitized_params
        )

# 全局验证器实例
default_validator = InputValidator(ValidationLevel.MODERATE)
strict_validator = InputValidator(ValidationLevel.STRICT)
lenient_validator = InputValidator(ValidationLevel.LENIENT)

def get_validator(level: ValidationLevel = ValidationLevel.MODERATE) -> InputValidator:
    """获取指定级别的验证器"""
    if level == ValidationLevel.STRICT:
        return strict_validator
    elif level == ValidationLevel.LENIENT:
        return lenient_validator
    else:
        return default_validator