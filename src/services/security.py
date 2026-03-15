"""
统一安全服务模块

合并以下服务:
- SecurityController (security_control.py)
- SecurityDetectionService (security_detection_service.py)
- AdvancedSecurityDetectionService (advanced_security_detection_service.py)
- ToolSafetyInterceptor (tool_safety_interceptor.py)
- AuditLogger (audit_log_service.py)

使用示例:
```python
from src.services.security import SecurityService

security = SecurityService()
result = security.check_request(request)
security.log_event(event)
```
"""

import time
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field


# ============== Enums ==============

class SecurityLevel(str, Enum):
    """安全级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(str, Enum):
    """威胁类型"""
    INJECTION = "injection"
    XSS = "xss"
    CSRF = "csrf"
    DOS = "dos"
    DATA_LEAK = "data_leak"
    UNAUTHORIZED = "unauthorized"


class DangerLevel(str, Enum):
    """危险级别"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEventType(str, Enum):
    """审计事件类型"""
    LOGIN = "login"
    LOGOUT = "logout"
    API_CALL = "api_call"
    DATA_ACCESS = "data_access"
    CONFIG_CHANGE = "config_change"
    SECURITY_EVENT = "security_event"


class AuditSeverity(str, Enum):
    """审计严重性"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============== Data Classes ==============

@dataclass
class SecurityCheckResult:
    """安全检查结果"""
    allowed: bool
    level: SecurityLevel
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThreatIndicator:
    """威胁指标"""
    threat_type: ThreatType
    severity: AuditSeverity
    description: str
    evidence: str
    timestamp: float


@dataclass
class AuditEvent:
    """审计事件"""
    event_type: AuditEventType
    severity: AuditSeverity
    source: str
    user: str
    action: str
    result: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============== Main Class ==============

class SecurityService:
    """
    统一安全服务
    
    提供:
    - 访问控制 (Access Control)
    - 威胁检测 (Threat Detection)
    - 工具安全 (Tool Safety)
    - 审计日志 (Audit Logging)
    """
    
    def __init__(self):
        self._whitelist: List[str] = []
        self._blacklist: List[str] = []
        self._audit_log: List[AuditEvent] = []
        self._threats: List[ThreatIndicator] = []
        self._max_log_size = 10000
    
    # ============== Access Control ==============
    
    def add_to_whitelist(self, pattern: str) -> None:
        """添加到白名单"""
        if pattern not in self._whitelist:
            self._whitelist.append(pattern)
    
    def add_to_blacklist(self, pattern: str) -> None:
        """添加到黑名单"""
        if pattern not in self._blacklist:
            self._blacklist.append(pattern)
    
    def check_request(
        self,
        user: str,
        action: str,
        resource: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SecurityCheckResult:
        """检查请求是否允许"""
        # Check blacklist first
        for pattern in self._blacklist:
            if pattern in user or pattern in action:
                self._log_audit(
                    event_type=AuditEventType.SECURITY_EVENT,
                    severity=AuditSeverity.WARNING,
                    source="access_control",
                    user=user,
                    action=action,
                    result="blocked",
                    metadata={"reason": "blacklist", "pattern": pattern}
                )
                return SecurityCheckResult(
                    allowed=False,
                    level=SecurityLevel.CRITICAL,
                    reason=f"Blocked by blacklist pattern: {pattern}",
                    details={"pattern": pattern}
                )
        
        # Check whitelist (if non-empty)
        if self._whitelist:
            allowed = any(pattern in user or pattern in action for pattern in self._whitelist)
            if not allowed:
                return SecurityCheckResult(
                    allowed=False,
                    level=SecurityLevel.MEDIUM,
                    reason="Not in whitelist",
                    details={}
                )
        
        # Default allow
        self._log_audit(
            event_type=AuditEventType.API_CALL,
            severity=AuditSeverity.INFO,
            source="access_control",
            user=user,
            action=action,
            result="allowed",
            metadata=metadata or {}
        )
        
        return SecurityCheckResult(
            allowed=True,
            level=SecurityLevel.LOW,
            reason="Allowed",
            details={}
        )
    
    # ============== Threat Detection ==============
    
    def detect_threats(self, content: str) -> List[ThreatIndicator]:
        """检测威胁"""
        threats = []
        timestamp = time.time()
        
        # Simple pattern-based detection
        injection_patterns = ["';", "--", "DROP TABLE", "DELETE FROM"]
        xss_patterns = ["<script>", "javascript:", "onerror="]
        
        # Check for injection
        for pattern in injection_patterns:
            if pattern.lower() in content.lower():
                threats.append(ThreatIndicator(
                    threat_type=ThreatType.INJECTION,
                    severity=AuditSeverity.CRITICAL,
                    description="Potential SQL injection detected",
                    evidence=pattern,
                    timestamp=timestamp
                ))
        
        # Check for XSS
        for pattern in xss_patterns:
            if pattern.lower() in content.lower():
                threats.append(ThreatIndicator(
                    threat_type=ThreatType.XSS,
                    severity=AuditSeverity.ERROR,
                    description="Potential XSS attack detected",
                    evidence=pattern,
                    timestamp=timestamp
                ))
        
        # Store threats
        self._threats.extend(threats)
        
        return threats
    
    def get_threats(
        self,
        threat_type: Optional[ThreatType] = None,
        limit: int = 50
    ) -> List[ThreatIndicator]:
        """获取威胁列表"""
        threats = self._threats
        
        if threat_type:
            threats = [t for t in threats if t.threat_type == threat_type]
        
        return threats[-limit:]
    
    # ============== Tool Safety ==============
    
    def check_tool_safety(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> bool:
        """检查工具调用是否安全"""
        # Dangerous tool patterns
        dangerous_tools = {
            "delete": ["file", "database", "user"],
            "exec": ["system", "shell", "command"],
            "write": ["config", "password", "secret"],
        }
        
        tool_lower = tool_name.lower()
        
        for danger, keywords in dangerous_tools.items():
            if danger in tool_lower:
                for keyword in keywords:
                    if keyword in str(parameters).lower():
                        self._log_audit(
                            event_type=AuditEventType.SECURITY_EVENT,
                            severity=AuditSeverity.WARNING,
                            source="tool_safety",
                            user="system",
                            action=f"dangerous_tool:{tool_name}",
                            result="blocked",
                            metadata={"reason": f"dangerous: {keyword}"}
                        )
                        return False
        
        return True
    
    # ============== Audit Logging ==============
    
    def _log_audit(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        source: str,
        user: str,
        action: str,
        result: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录审计日志"""
        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            source=source,
            user=user,
            action=action,
            result=result,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        
        self._audit_log.append(event)
        
        # Trim if too large
        if len(self._audit_log) > self._max_log_size:
            self._audit_log = self._audit_log[-self._max_log_size:]
    
    def log_event(
        self,
        event_type: AuditEventType,
        user: str,
        action: str,
        result: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录事件"""
        self._log_audit(
            event_type=event_type,
            severity=severity,
            source="manual",
            user=user,
            action=action,
            result=result,
            metadata=metadata
        )
    
    def get_audit_log(
        self,
        user: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """获取审计日志"""
        logs = self._audit_log
        
        if user:
            logs = [e for e in logs if e.user == user]
        
        if event_type:
            logs = [e for e in logs if e.event_type == event_type]
        
        return logs[-limit:]
    
    # ============== Summary ==============
    
    def get_security_summary(self) -> Dict[str, Any]:
        """获取安全摘要"""
        return {
            "whitelist_count": len(self._whitelist),
            "blacklist_count": len(self._blacklist),
            "threats_count": len(self._threats),
            "audit_log_count": len(self._audit_log),
            "recent_threats": len([t for t in self._threats if time.time() - t.timestamp < 3600]),
            "critical_events": len([e for e in self._audit_log if e.severity == AuditSeverity.CRITICAL]),
        }


# ============== Factory ==============

def get_security_service() -> SecurityService:
    """获取安全服务实例"""
    return SecurityService()
