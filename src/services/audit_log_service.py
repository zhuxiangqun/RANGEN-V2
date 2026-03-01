"""
审计日志和安全事件监控服务
记录所有安全相关事件，监控可疑活动
"""

import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict
import logging

from src.services.logging_service import get_logger

logger = get_logger("audit_log")


class AuditEventType(Enum):
    """审计事件类型"""
    # 认证相关事件
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    SESSION_CREATE = "session_create"
    SESSION_DESTROY = "session_destroy"
    
    # API密钥相关事件
    API_KEY_CREATE = "api_key_create"
    API_KEY_REVOKE = "api_key_revoke"
    API_KEY_USAGE = "api_key_usage"
    
    # 用户管理事件
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_PERMISSION_CHANGE = "user_permission_change"
    
    # 系统操作事件
    CONFIG_CHANGE = "config_change"
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"
    
    # 安全事件
    SECURITY_ALERT = "security_alert"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    MALICIOUS_INPUT = "malicious_input"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    
    # 数据访问事件
    DATA_ACCESS = "data_access"
    DATA_MODIFY = "data_modify"
    DATA_EXPORT = "data_export"
    DATA_DELETE = "data_delete"
    
    # 管理操作事件
    ADMIN_ACTION = "admin_action"
    ROLE_CHANGE = "role_change"
    SETTINGS_CHANGE = "settings_change"


class AuditSeverity(Enum):
    """审计事件严重级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditSource(Enum):
    """审计事件来源"""
    AUTH_SERVICE = "auth_service"
    API_GATEWAY = "api_gateway"
    VALIDATION_MIDDLEWARE = "validation_middleware"
    USER_MANAGEMENT = "user_management"
    SYSTEM_ADMIN = "system_admin"
    SECURITY_SCANNER = "security_scanner"
    EXTERNAL_SYSTEM = "external_system"


@dataclass
class AuditEvent:
    """审计事件数据类"""
    event_id: str
    event_type: AuditEventType
    timestamp: str
    severity: AuditSeverity
    source: AuditSource
    
    # 事件详情
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # 资源信息
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    
    # 操作信息
    action: Optional[str] = None
    action_details: Optional[str] = None
    
    # 结果信息
    success: bool = True
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    
    # 上下文信息
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 转换枚举值为字符串
        data["event_type"] = self.event_type.value
        data["severity"] = self.severity.value
        data["source"] = self.source.value
        return data
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class AuditLogStorage:
    """审计日志存储抽象类"""
    
    def save_event(self, event: AuditEvent) -> bool:
        """保存审计事件"""
        raise NotImplementedError
    
    def get_events(
        self, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """获取审计事件"""
        raise NotImplementedError
    
    def get_event_by_id(self, event_id: str) -> Optional[AuditEvent]:
        """根据ID获取审计事件"""
        raise NotImplementedError
    
    def delete_old_events(self, older_than_days: int = 90) -> int:
        """删除旧事件"""
        raise NotImplementedError


class FileAuditLogStorage(AuditLogStorage):
    """文件存储审计日志"""
    
    def __init__(self, log_dir: str = "logs/audit"):
        import os
        
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # 按日期分文件存储
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.log_file = os.path.join(log_dir, f"audit_{self.current_date}.log")
        
        logger.info(f"文件审计日志存储初始化: {self.log_file}")
    
    def _get_today_log_file(self) -> str:
        """获取当天的日志文件"""
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self.current_date:
            self.current_date = today
            self.log_file = os.path.join(self.log_dir, f"audit_{self.current_date}.log")
        return self.log_file
    
    def save_event(self, event: AuditEvent) -> bool:
        """保存审计事件到文件"""
        import os
        
        try:
            log_file = self._get_today_log_file()
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")
            
            logger.debug(f"审计事件已保存: {event.event_id}")
            return True
        except Exception as e:
            logger.error(f"保存审计事件失败: {e}")
            return False
    
    def get_events(
        self, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """从文件获取审计事件"""
        import os
        import glob
        
        events = []
        
        try:
            # 确定要读取的文件
            log_files = []
            if start_time and end_time:
                # 读取时间范围内的所有日志文件
                current = start_time
                while current <= end_time:
                    date_str = current.strftime("%Y-%m-%d")
                    log_file = os.path.join(self.log_dir, f"audit_{date_str}.log")
                    if os.path.exists(log_file):
                        log_files.append(log_file)
                    current += timedelta(days=1)
            else:
                # 读取最近7天的文件
                for i in range(7):
                    date = datetime.now() - timedelta(days=i)
                    date_str = date.strftime("%Y-%m-%d")
                    log_file = os.path.join(self.log_dir, f"audit_{date_str}.log")
                    if os.path.exists(log_file):
                        log_files.append(log_file)
            
            # 读取并解析事件
            for log_file in log_files:
                if not os.path.exists(log_file):
                    continue
                
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        
                        try:
                            data = json.loads(line)
                            event = self._dict_to_event(data)
                            
                            # 应用过滤器
                            if start_time and event.timestamp < start_time.isoformat():
                                continue
                            if end_time and event.timestamp > end_time.isoformat():
                                continue
                            if event_type and event.event_type != event_type:
                                continue
                            if user_id and event.user_id != user_id:
                                continue
                            if severity and event.severity != severity:
                                continue
                            
                            events.append(event)
                            
                            if len(events) >= limit:
                                return events
                                
                        except json.JSONDecodeError as e:
                            logger.error(f"解析审计日志行失败: {e}, 行: {line[:100]}")
            
            return events
            
        except Exception as e:
            logger.error(f"获取审计事件失败: {e}")
            return []
    
    def _dict_to_event(self, data: Dict[str, Any]) -> AuditEvent:
        """将字典转换为AuditEvent对象"""
        # 转换字符串枚举值回枚举类型
        data["event_type"] = AuditEventType(data["event_type"])
        data["severity"] = AuditSeverity(data["severity"])
        data["source"] = AuditSource(data["source"])
        
        return AuditEvent(**data)
    
    def get_event_by_id(self, event_id: str) -> Optional[AuditEvent]:
        """根据ID获取审计事件"""
        events = self.get_events(limit=1000)  # 读取较多事件
        for event in events:
            if event.event_id == event_id:
                return event
        return None
    
    def delete_old_events(self, older_than_days: int = 90) -> int:
        """删除旧事件文件"""
        import os
        import glob
        
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        deleted_count = 0
        
        try:
            log_files = glob.glob(os.path.join(self.log_dir, "audit_*.log"))
            for log_file in log_files:
                # 从文件名提取日期
                filename = os.path.basename(log_file)
                date_str = filename[6:-4]  # 移除"audit_"和".log"
                
                try:
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")
                    if file_date < cutoff_date:
                        os.remove(log_file)
                        deleted_count += 1
                        logger.info(f"删除旧审计日志文件: {log_file}")
                except ValueError:
                    # 文件名格式错误，跳过
                    continue
            
            logger.info(f"已删除 {deleted_count} 个旧审计日志文件")
            return deleted_count
            
        except Exception as e:
            logger.error(f"删除旧审计事件失败: {e}")
            return 0


class SecurityEventMonitor:
    """安全事件监控器"""
    
    def __init__(self, audit_storage: AuditLogStorage):
        self.audit_storage = audit_storage
        self.suspicious_patterns = self._init_suspicious_patterns()
        self.alert_rules = self._init_alert_rules()
        
        logger.info("安全事件监控器已初始化")
    
    def _init_suspicious_patterns(self) -> Dict[str, Any]:
        """初始化可疑模式"""
        return {
            "brute_force": {
                "max_attempts": 5,
                "time_window": 300,  # 5分钟
                "lockout_duration": 900,  # 15分钟
            },
            "api_key_abuse": {
                "max_requests": 1000,
                "time_window": 60,  # 1分钟
            },
            "suspicious_location": {
                "country_changes": 3,  # 短时间内国家变更次数
                "time_window": 3600,  # 1小时
            },
            "data_exfiltration": {
                "max_export_size": 1000000,  # 1MB
                "time_window": 300,  # 5分钟
            },
            "privilege_escalation": {
                "permission_changes": 3,
                "time_window": 3600,  # 1小时
            }
        }
    
    def _init_alert_rules(self) -> List[Dict[str, Any]]:
        """初始化警报规则"""
        return [
            {
                "name": "暴力破解检测",
                "condition": self._check_brute_force,
                "severity": AuditSeverity.CRITICAL,
                "action": "block_ip"
            },
            {
                "name": "API密钥滥用",
                "condition": self._check_api_key_abuse,
                "severity": AuditSeverity.ERROR,
                "action": "revoke_key"
            },
            {
                "name": "可疑地理位置",
                "condition": self._check_suspicious_location,
                "severity": AuditSeverity.WARNING,
                "action": "require_2fa"
            },
            {
                "name": "数据泄露尝试",
                "condition": self._check_data_exfiltration,
                "severity": AuditSeverity.CRITICAL,
                "action": "block_user"
            },
            {
                "name": "权限提升尝试",
                "condition": self._check_privilege_escalation,
                "severity": AuditSeverity.ERROR,
                "action": "alert_admin"
            }
        ]
    
    def monitor_events(self) -> List[Dict[str, Any]]:
        """监控事件并生成警报"""
        alerts = []
        
        # 获取最近的事件进行分析
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)  # 分析最近1小时的事件
        
        events = self.audit_storage.get_events(
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )
        
        # 应用所有警报规则
        for rule in self.alert_rules:
            try:
                rule_alerts = rule["condition"](events)
                if rule_alerts:
                    alerts.extend(rule_alerts)
            except Exception as e:
                logger.error(f"执行警报规则失败 {rule['name']}: {e}")
        
        # 记录检测到的警报
        if alerts:
            logger.warning(f"检测到 {len(alerts)} 个安全警报")
            for alert in alerts:
                self._create_security_alert(alert)
        
        return alerts
    
    def _check_brute_force(self, events: List[AuditEvent]) -> List[Dict[str, Any]]:
        """检查暴力破解尝试"""
        alerts = []
        
        # 按IP地址分组登录失败事件
        failed_logins_by_ip = {}
        for event in events:
            if event.event_type == AuditEventType.LOGIN_FAILURE and event.ip_address:
                ip = event.ip_address
                if ip not in failed_logins_by_ip:
                    failed_logins_by_ip[ip] = []
                failed_logins_by_ip[ip].append(event)
        
        # 检查每个IP的失败次数
        pattern = self.suspicious_patterns["brute_force"]
        max_attempts = pattern["max_attempts"]
        time_window = pattern["time_window"]
        
        for ip, ip_events in failed_logins_by_ip.items():
            # 检查最近时间窗口内的失败次数
            recent_failures = 0
            cutoff_time = datetime.now() - timedelta(seconds=time_window)
            
            for event in ip_events:
                event_time = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
                if event_time > cutoff_time:
                    recent_failures += 1
            
            if recent_failures >= max_attempts:
                alerts.append({
                    "type": "brute_force_attempt",
                    "severity": AuditSeverity.CRITICAL.value,
                    "message": f"IP地址 {ip} 在 {time_window} 秒内登录失败 {recent_failures} 次",
                    "ip_address": ip,
                    "failure_count": recent_failures,
                    "time_window": time_window,
                    "action": "block_ip",
                    "timestamp": datetime.now().isoformat()
                })
        
        return alerts
    
    def _check_api_key_abuse(self, events: List[AuditEvent]) -> List[Dict[str, Any]]:
        """检查API密钥滥用"""
        alerts = []
        
        # 按API密钥分组使用事件
        usage_by_key = {}
        for event in events:
            if event.event_type == AuditEventType.API_KEY_USAGE and event.resource_id:
                key_id = event.resource_id
                if key_id not in usage_by_key:
                    usage_by_key[key_id] = []
                usage_by_key[key_id].append(event)
        
        # 检查每个密钥的使用频率
        pattern = self.suspicious_patterns["api_key_abuse"]
        max_requests = pattern["max_requests"]
        time_window = pattern["time_window"]
        
        for key_id, key_events in usage_by_key.items():
            # 检查最近时间窗口内的请求次数
            recent_requests = 0
            cutoff_time = datetime.now() - timedelta(seconds=time_window)
            
            for event in key_events:
                event_time = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
                if event_time > cutoff_time:
                    recent_requests += 1
            
            if recent_requests >= max_requests:
                alerts.append({
                    "type": "api_key_abuse",
                    "severity": AuditSeverity.ERROR.value,
                    "message": f"API密钥 {key_id[:8]}... 在 {time_window} 秒内使用 {recent_requests} 次",
                    "api_key_id": key_id,
                    "request_count": recent_requests,
                    "time_window": time_window,
                    "action": "revoke_key",
                    "timestamp": datetime.now().isoformat()
                })
        
        return alerts
    
    def _check_suspicious_location(self, events: List[AuditEvent]) -> List[Dict[str, Any]]:
        """检查可疑地理位置"""
        # 这里简化为检查IP地址频繁变更
        alerts = []
        
        # 按用户分组登录事件
        logins_by_user = {}
        for event in events:
            if event.event_type in [AuditEventType.LOGIN_SUCCESS, AuditEventType.SESSION_CREATE] and event.user_id:
                user_id = event.user_id
                if user_id not in logins_by_user:
                    logins_by_user[user_id] = []
                logins_by_user[user_id].append(event)
        
        # 检查每个用户的IP地址变化
        pattern = self.suspicious_patterns["suspicious_location"]
        max_country_changes = pattern["country_changes"]
        
        for user_id, user_events in logins_by_user.items():
            if len(user_events) < 2:
                continue
            
            # 提取IP地址（简化：这里假设IP地址直接可用）
            # 实际应用中需要将IP地址转换为地理位置
            ip_addresses = set()
            for event in user_events:
                if event.ip_address:
                    ip_addresses.add(event.ip_address)
            
            # 如果IP地址数量超过阈值
            if len(ip_addresses) >= max_country_changes:
                alerts.append({
                    "type": "suspicious_location",
                    "severity": AuditSeverity.WARNING.value,
                    "message": f"用户 {user_id} 从 {len(ip_addresses)} 个不同IP地址登录",
                    "user_id": user_id,
                    "ip_count": len(ip_addresses),
                    "ip_addresses": list(ip_addresses),
                    "action": "require_2fa",
                    "timestamp": datetime.now().isoformat()
                })
        
        return alerts
    
    def _check_data_exfiltration(self, events: List[AuditEvent]) -> List[Dict[str, Any]]:
        """检查数据泄露尝试"""
        alerts = []
        
        # 检查数据导出事件
        data_exports = []
        for event in events:
            if event.event_type == AuditEventType.DATA_EXPORT:
                data_exports.append(event)
        
        # 检查导出频率和大小
        pattern = self.suspicious_patterns["data_exfiltration"]
        max_export_size = pattern["max_export_size"]
        
        # 这里简化检查：如果有大量导出事件就报警
        if len(data_exports) > 10:  # 简化阈值
            total_size = 0
            # 从上下文中提取大小信息（简化）
            for event in data_exports:
                if event.context and "size" in event.context:
                    total_size += event.context["size"]
            
            if total_size > max_export_size:
                alerts.append({
                    "type": "data_exfiltration",
                    "severity": AuditSeverity.CRITICAL.value,
                    "message": f"检测到潜在数据泄露，总导出大小: {total_size} 字节",
                    "export_count": len(data_exports),
                    "total_size": total_size,
                    "max_allowed": max_export_size,
                    "action": "block_user",
                    "timestamp": datetime.now().isoformat()
                })
        
        return alerts
    
    def _check_privilege_escalation(self, events: List[AuditEvent]) -> List[Dict[str, Any]]:
        """检查权限提升尝试"""
        alerts = []
        
        # 检查权限变更事件
        permission_changes = []
        for event in events:
            if event.event_type == AuditEventType.USER_PERMISSION_CHANGE:
                permission_changes.append(event)
        
        # 检查频繁的权限变更
        pattern = self.suspicious_patterns["privilege_escalation"]
        max_changes = pattern["permission_changes"]
        
        # 按用户分组
        changes_by_user = {}
        for event in permission_changes:
            user_id = event.user_id
            if user_id not in changes_by_user:
                changes_by_user[user_id] = []
            changes_by_user[user_id].append(event)
        
        for user_id, user_changes in changes_by_user.items():
            if len(user_changes) >= max_changes:
                alerts.append({
                    "type": "privilege_escalation",
                    "severity": AuditSeverity.ERROR.value,
                    "message": f"用户 {user_id} 权限变更过于频繁: {len(user_changes)} 次",
                    "user_id": user_id,
                    "change_count": len(user_changes),
                    "max_allowed": max_changes,
                    "action": "alert_admin",
                    "timestamp": datetime.now().isoformat()
                })
        
        return alerts
    
    def _create_security_alert(self, alert_data: Dict[str, Any]):
        """创建安全警报事件"""
        try:
            from src.services.audit_log_service import AuditLogger
            
            audit_logger = AuditLogger.get_instance()
            
            event = audit_logger.create_event(
                event_type=AuditEventType.SECURITY_ALERT,
                severity=AuditSeverity(alert_data["severity"]),
                source=AuditSource.SECURITY_SCANNER,
                action_details=alert_data["message"],
                context=alert_data
            )
            
            audit_logger.log_event(event)
            logger.warning(f"安全警报已记录: {alert_data['message']}")
            
        except Exception as e:
            logger.error(f"创建安全警报失败: {e}")


class AuditLogger:
    """审计日志记录器"""
    
    _instance = None
    _storage = None
    _monitor = None
    
    def __init__(self, storage: Optional[AuditLogStorage] = None):
        if storage is None:
            storage = FileAuditLogStorage()
        
        self.storage = storage
        self.monitor = SecurityEventMonitor(storage)
        
        logger.info("审计日志记录器已初始化")
    
    @classmethod
    def get_instance(cls) -> 'AuditLogger':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def create_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity = AuditSeverity.INFO,
        source: AuditSource = AuditSource.SYSTEM_ADMIN,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        action: Optional[str] = None,
        action_details: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """创建审计事件"""
        import uuid
        
        event_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        return AuditEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=timestamp,
            severity=severity,
            source=source,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            action=action,
            action_details=action_details,
            success=success,
            error_message=error_message,
            error_code=error_code,
            context=context or {},
            metadata=metadata or {}
        )
    
    def log_event(self, event: AuditEvent):
        """记录审计事件"""
        # 保存事件
        success = self.storage.save_event(event)
        
        if success:
            logger.debug(f"审计事件已记录: {event.event_type.value} - {event.action_details}")
        else:
            logger.error(f"记录审计事件失败: {event.event_id}")
        
        # 定期运行监控检查（例如每100个事件检查一次）
        # 这里简化处理
        return success
    
    def log_auth_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """记录认证事件"""
        event = self.create_event(
            event_type=event_type,
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING,
            source=AuditSource.AUTH_SERVICE,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            action="authentication",
            action_details=f"{event_type.value}: {'成功' if success else '失败'}",
            success=success,
            error_message=error_message,
            context=context
        )
        
        return self.log_event(event)
    
    def log_api_key_event(
        self,
        event_type: AuditEventType,
        api_key_id: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        success: bool = True,
        context: Optional[Dict[str, Any]] = None
    ):
        """记录API密钥事件"""
        event = self.create_event(
            event_type=event_type,
            severity=AuditSeverity.INFO,
            source=AuditSource.API_GATEWAY,
            user_id=user_id,
            ip_address=ip_address,
            resource_type="api_key",
            resource_id=api_key_id,
            action="api_key_operation",
            action_details=f"{event_type.value}: {api_key_id[:8]}...",
            success=success,
            context=context
        )
        
        return self.log_event(event)
    
    def log_security_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        source: AuditSource,
        action_details: str,
        ip_address: Optional[str] = None,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """记录安全事件"""
        event = self.create_event(
            event_type=event_type,
            severity=severity,
            source=source,
            user_id=user_id,
            ip_address=ip_address,
            action="security_incident",
            action_details=action_details,
            success=False,
            context=context
        )
        
        return self.log_event(event)
    
    def get_recent_events(self, limit: int = 50) -> List[AuditEvent]:
        """获取最近的事件"""
        return self.storage.get_events(limit=limit)
    
    def run_security_monitoring(self) -> List[Dict[str, Any]]:
        """运行安全监控"""
        return self.monitor.monitor_events()
    
    def cleanup_old_events(self, older_than_days: int = 90) -> int:
        """清理旧事件"""
        return self.storage.delete_old_events(older_than_days)


# 便捷函数
def get_audit_logger() -> AuditLogger:
    """获取审计日志记录器实例"""
    return AuditLogger.get_instance()


def log_auth_event(
    event_type: AuditEventType,
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
):
    """记录认证事件便捷函数"""
    logger = get_audit_logger()
    return logger.log_auth_event(
        event_type=event_type,
        user_id=user_id,
        username=username,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        error_message=error_message,
        context=context
    )


def log_security_alert(
    message: str,
    severity: AuditSeverity = AuditSeverity.WARNING,
    ip_address: Optional[str] = None,
    user_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
):
    """记录安全警报便捷函数"""
    logger = get_audit_logger()
    return logger.log_security_event(
        event_type=AuditEventType.SECURITY_ALERT,
        severity=severity,
        source=AuditSource.SECURITY_SCANNER,
        action_details=message,
        ip_address=ip_address,
        user_id=user_id,
        context=context
    )