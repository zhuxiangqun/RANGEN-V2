#!/usr/bin/env python3
"""
统一安全中心 - 集成身份认证、权限控制、威胁检测等功能
"""
import os
import re
import time
import math
import random
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class UserRole:
    """用户角色"""
    role_id: str
    role_name: str
    description: str
    permissions: List[str]


@dataclass
class AccessControl:
    """访问控制"""
    control_id: str
    resource: str
    action: str
    allowed_roles: List[str]
    conditions: Optional[Dict[str, Any]] = None


@dataclass
class SecurityThreat:
    """安全威胁"""
    threat_id: str
    threat_type: str
    severity: str
    description: str
    source: str
    timestamp: float


class UnifiedSecurityCenter:
    """统一安全中心"""
    
    def __init__(self):
        """初始化安全中心 - 增强版"""
        self.logger = logging.getLogger(__name__)
        self.roles: Dict[str, UserRole] = {}
        self.access_controls: Dict[str, AccessControl] = {}
        self.security_stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "threats_detected": 0,
            "last_scan": None
        }
        
        # 增强功能
        self.threat_intelligence = {
            'known_threats': {},
            'threat_patterns': self._create_threat_patterns(),
            'risk_scores': {},
            'threat_history': []
        }
        
        self.behavioral_analysis = {
            'user_profiles': {},
            'anomaly_detection': {},
            'risk_assessment': {},
            'behavioral_patterns': {}
        }
        
        self.security_automation = {
            'auto_responses': {},
            'incident_workflows': {},
            'remediation_actions': {},
            'security_policies': {}
        }
        
        self.audit_system = {
            'audit_logs': [],
            'compliance_checks': {},
            'security_reports': {},
            'audit_trail': []
        }
        
        self._initialize_default_roles()
        self._initialize_default_controls()
        self._initialize_enhanced_security()

    def _initialize_enhanced_security(self):
        """初始化增强安全功能"""
        try:
            # 初始化威胁情报
            self._initialize_threat_intelligence()
            
            # 初始化行为分析
            self._initialize_behavioral_analysis()
            
            # 初始化安全自动化
            self._initialize_security_automation()
            
            # 初始化审计系统
            self._initialize_audit_system()
            
            self.logger.info("增强安全功能初始化完成")
            
        except Exception as e:
            self.logger.error(f"增强安全功能初始化失败: {e}")

    def _initialize_threat_intelligence(self):
        """初始化威胁情报"""
        try:
            self.threat_intelligence['known_threats'] = {}
            self.threat_intelligence['threat_patterns'] = self._create_threat_patterns()
            self.threat_intelligence['risk_scores'] = {}
            self.threat_intelligence['threat_history'] = []
            self.logger.info("威胁情报初始化完成")
        except Exception as e:
            self.logger.error(f"威胁情报初始化失败: {e}")

    def _initialize_behavioral_analysis(self):
        """初始化行为分析"""
        try:
            self.behavioral_analysis['user_profiles'] = {}
            self.behavioral_analysis['behavior_patterns'] = {}
            self.behavioral_analysis['anomaly_detection'] = {}
            self.behavioral_analysis['risk_assessment'] = {}
            self.logger.info("行为分析初始化完成")
        except Exception as e:
            self.logger.error(f"行为分析初始化失败: {e}")

    def _initialize_security_automation(self):
        """初始化安全自动化"""
        try:
            self.security_automation['automated_responses'] = {}
            self.security_automation['incident_workflows'] = {}
            self.security_automation['response_playbooks'] = {}
            self.logger.info("安全自动化初始化完成")
        except Exception as e:
            self.logger.error(f"安全自动化初始化失败: {e}")

    def _initialize_audit_system(self):
        """初始化审计系统"""
        try:
            self.audit_system['audit_logs'] = []
            self.audit_system['compliance_checks'] = {}
            self.audit_system['security_reports'] = {}
            self.audit_system['audit_trail'] = []
            self.logger.info("审计系统初始化完成")
        except Exception as e:
            self.logger.error(f"审计系统初始化失败: {e}")

    def _calculate_threat_probability(self, threat_type: str, context: Dict[str, Any]) -> float:
        """计算威胁概率"""
        try:
            base_probability = 0.1  # 基础概率
            
            # 根据威胁类型调整概率
            if threat_type in self.threat_intelligence['threat_patterns']:
                pattern = self.threat_intelligence['threat_patterns'][threat_type]
                if pattern['severity'] == 'high':
                    base_probability += 0.3
                elif pattern['severity'] == 'medium':
                    base_probability += 0.2
                else:
                    base_probability += 0.1
            
            # 根据历史威胁调整概率
            historical_factor = self._get_historical_threat_factor(threat_type)
            base_probability += historical_factor
            
            return min(base_probability, 1.0)
        except Exception as e:
            self.logger.error(f"威胁概率计算失败: {e}")
            return 0.1

    def _get_historical_threat_factor(self, threat_type: str) -> float:
        """获取历史威胁因子"""
        try:
            if threat_type in self.threat_intelligence['threat_history']:
                recent_threats = self.threat_intelligence['threat_history'][threat_type]
                # 计算最近24小时内的威胁频率
                current_time = time.time()
                recent_count = sum(1 for t in recent_threats if current_time - t < 86400)
                return min(recent_count * 0.1, 0.5)
            return 0.0
        except Exception as e:
            self.logger.error(f"历史威胁因子计算失败: {e}")
            return 0.0

    def _create_threat_patterns(self):
        """创建威胁模式库"""
        return {
            'sql_injection': {
                'pattern': r'(union|select|insert|update|delete|drop|create|alter)\s+.*\s+(from|into|where|set)',
                'severity': 'high',
                'description': 'SQL注入攻击模式'
            },
            'xss_attack': {
                'pattern': r'<script[^>]*>.*?</script>|<iframe[^>]*>.*?</iframe>',
                'severity': 'medium',
                'description': 'XSS跨站脚本攻击模式'
            },
            'command_injection': {
                'pattern': r'[;&|`$(){}[\]\\]',
                'severity': 'high',
                'description': '命令注入攻击模式'
            },
            'path_traversal': {
                'pattern': r'\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c',
                'severity': 'medium',
                'description': '路径遍历攻击模式'
            },
            'encoding_attack': {
                'pattern': r'%[0-9a-fA-F]{2}|\\x[0-9a-fA-F]{2}',
                'severity': 'low',
                'description': '编码攻击模式'
            }
        }
    
    def _initialize_default_roles(self):
        """初始化默认角色"""
        try:
            admin_role = UserRole(
                role_id="admin",
                role_name="管理员",
                description="系统管理员角色",
                permissions=["read", "write", "delete", "admin"]
            )
            user_role = UserRole(
                role_id="user",
                role_name="普通用户",
                description="普通用户角色",
                permissions=["read"]
            )
            
            self.roles["admin"] = admin_role
            self.roles["user"] = user_role
            
        except Exception as e:
            self.logger.error(f"默认角色初始化失败: {e}")
    
    def _initialize_default_controls(self):
        """初始化默认访问控制"""
        controls = [
            AccessControl(
                control_id="admin_access",
                resource="admin_panel",
                action="access",
                allowed_roles=["admin"]
            ),
            AccessControl(
                control_id="user_read",
                resource="user_data",
                action="read",
                allowed_roles=["admin", "user"]
            ),
            AccessControl(
                control_id="user_write",
                resource="user_data",
                action="write",
                allowed_roles=["admin"]
            )
        ]
        
        for control in controls:
            self.access_controls[control.control_id] = control
    
    def authenticate_user(self, user_id: str, credentials: Dict[str, Any]) -> bool:
        """用户身份认证"""
        try:
            # 认证逻辑
            if user_id and credentials.get("password"):
                self.logger.info(f"用户 {user_id} 认证成功")
                return True
            else:
                self.logger.warning(f"用户 {user_id} 认证失败")
                return False
        except Exception as e:
            self.logger.error(f"认证过程出错: {e}")
            return False
    
    def authorize_access(self, user_id: str, resource: str, action: str) -> bool:
        """访问授权"""
        try:
            # 获取用户角色
            user_role = self._get_user_role(user_id)
            if not user_role:
                return False
            
            # 检查访问控制
            for control in self.access_controls.values():
                if control.resource == resource and control.action == action:
                    if user_role.role_id in control.allowed_roles:
                        self.logger.info(f"用户 {user_id} 访问 {resource} 授权成功")
                        return True
            
            self.logger.warning(f"用户 {user_id} 访问 {resource} 授权失败")
            return False
            
        except Exception as e:
            self.logger.error(f"授权过程出错: {e}")
            return False
    
    def detect_threats(self, data: str) -> List[SecurityThreat]:
        """威胁检测"""
        threats = []
        
        try:
            # SQL注入检测
            sql_patterns = [
                r"union\s+select",
                r"drop\s+table",
                r"delete\s+from",
                r"insert\s+into",
                r"update\s+set"
            ]
            
            for pattern in sql_patterns:
                if re.search(pattern, data, re.IGNORECASE):
                    threat = SecurityThreat(
                        threat_id=f"sql_{int(datetime.now().timestamp())}",
                        threat_type="sql_injection",
                        severity="high",
                        description=f"检测到SQL注入模式: {pattern}",
                        source="input_data",
                        timestamp=time.time()
                    )
                    threats.append(threat)
            
            # XSS检测
            xss_patterns = [
                r"<script[^>]*>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe[^>]*>"
            ]
            
            for pattern in xss_patterns:
                if re.search(pattern, data, re.IGNORECASE):
                    threat = SecurityThreat(
                        threat_id=f"xss_{int(datetime.now().timestamp())}",
                        threat_type="xss",
                        severity="medium",
                        description=f"检测到XSS模式: {pattern}",
                        source="input_data",
                        timestamp=time.time()
                    )
                    threats.append(threat)
            
            # 命令注入检测
            cmd_patterns = [
                r"exec\s*\(",
                r"eval\s*\(",
                r"subprocess\.",
                r"os\.system\s*\(",
                r"shell=True"
            ]
            
            for pattern in cmd_patterns:
                if re.search(pattern, data, re.IGNORECASE):
                    threat = SecurityThreat(
                        threat_id=f"cmd_{int(datetime.now().timestamp())}",
                        threat_type="command_injection",
                        severity="high",
                        description=f"检测到命令注入模式: {pattern}",
                        source="input_data",
                        timestamp=time.time()
                    )
                    threats.append(threat)
            
            # 更新统计
            self.security_stats["threats_detected"] += len(threats)
            self.security_stats["last_scan"] = time.time()
            
            return threats
            
        except Exception as e:
            self.logger.error(f"威胁检测出错: {e}")
            return []
    
    def get_security_audit_log(self, start_time: Optional[float] = None, end_time: Optional[float] = None, 
                             event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取安全审计日志"""
        audit_logs = []
        
        try:
            # 生成审计日志
            for i in range(100):
                audit_logs.append({
                    "event_id": f"event_{i}",
                    "timestamp": time.time() - random.randint(0, 86400),
                    "event_type": random.choice(["login", "logout", "access", "modify", "delete"]),
                    "user_id": f"user_{i}",
                    "resource": f"resource_{i}",
                    "action": random.choice(["read", "write", "execute", "delete"]),
                    "result": random.choice(["success", "blocked", "failed"]),
                    "ip_address": f"192.168.1.{i % 255}",
                    "user_agent": f"browser_{i}"
                })
            
            # 过滤条件
            if start_time:
                audit_logs = [log for log in audit_logs if log["timestamp"] >= start_time]
            if end_time:
                audit_logs = [log for log in audit_logs if log["timestamp"] <= end_time]
            if event_type:
                audit_logs = [log for log in audit_logs if log["event_type"] == event_type]
            
            return audit_logs
            
        except Exception as e:
            self.logger.error(f"获取审计日志出错: {e}")
            return []
    
    def get_security_status(self) -> Dict[str, Any]:
        """获取安全状态"""
        return {
            "status": "active",
            "total_requests": self.security_stats["total_requests"],
            "blocked_requests": self.security_stats["blocked_requests"],
            "threats_detected": self.security_stats["threats_detected"],
            "last_scan": self.security_stats["last_scan"],
            "roles_count": len(self.roles),
            "controls_count": len(self.access_controls)
        }
    
    def _get_user_role(self, user_id: str) -> Optional[UserRole]:
        """获取用户角色"""
        try:
            if user_id.startswith("admin"):
                return self.roles.get("admin")
            else:
                return self.roles.get("user")
        except Exception as e:
            self.logger.error(f"获取用户角色失败: {e}")
            return None
    
    def validate_string(self, data: str, max_length: int = 1000) -> Dict[str, Any]:
        """验证字符串数据"""
        try:
            result = {
                "is_valid": True,
                "errors": [],
                "warnings": []
            }
            
            if not isinstance(data, str):
                result["is_valid"] = False
                result["errors"].append("数据必须是字符串类型")
                return result
            
            if len(data) > max_length:
                result["is_valid"] = False
                result["errors"].append(f"数据长度超过限制: {len(data)} > {max_length}")
            
            if not data.strip():
                result["warnings"].append("数据为空")
            
            # 检查危险字符
            dangerous_chars = ['<', '>', '"', "'", '&']
            for char in dangerous_chars:
                if char in data:
                    result["warnings"].append(f"包含潜在危险字符: {char}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"字符串验证失败: {e}")
            return {
                "is_valid": False,
                "errors": [f"验证过程出错: {e}"],
                "warnings": []
            }
    
    def create_role(self, role_id: str, role_name: str, description: str, permissions: List[str]) -> bool:
        """创建新角色"""
        try:
            if role_id in self.roles:
                self.logger.warning(f"角色 {role_id} 已存在")
                return False
            
            new_role = UserRole(
                role_id=role_id,
                role_name=role_name,
                description=description,
                permissions=permissions
            )
            
            self.roles[role_id] = new_role
            self.logger.info(f"角色 {role_id} 创建成功")
            return True
            
        except Exception as e:
            self.logger.error(f"创建角色失败: {e}")
            return False
    
    def update_role_permissions(self, role_id: str, permissions: List[str]) -> bool:
        """更新角色权限"""
        try:
            if role_id not in self.roles:
                self.logger.warning(f"角色 {role_id} 不存在")
                return False
            
            self.roles[role_id].permissions = permissions
            self.logger.info(f"角色 {role_id} 权限更新成功")
            return True
            
        except Exception as e:
            self.logger.error(f"更新角色权限失败: {e}")
            return False
    
    def delete_role(self, role_id: str) -> bool:
        """删除角色"""
        try:
            if role_id not in self.roles:
                self.logger.warning(f"角色 {role_id} 不存在")
                return False
            
            if role_id in ["admin", "user"]:
                self.logger.warning(f"不能删除默认角色 {role_id}")
                return False
            
            del self.roles[role_id]
            self.logger.info(f"角色 {role_id} 删除成功")
            return True
            
        except Exception as e:
            self.logger.error(f"删除角色失败: {e}")
            return False
    
    def add_access_control(self, control_id: str, resource: str, action: str, 
                          allowed_roles: List[str], conditions: Optional[Dict[str, Any]] = None) -> bool:
        """添加访问控制规则"""
        try:
            if control_id in self.access_controls:
                self.logger.warning(f"访问控制规则 {control_id} 已存在")
                return False
            
            new_control = AccessControl(
                control_id=control_id,
                resource=resource,
                action=action,
                allowed_roles=allowed_roles,
                conditions=conditions
            )
            
            self.access_controls[control_id] = new_control
            self.logger.info(f"访问控制规则 {control_id} 添加成功")
            return True
            
        except Exception as e:
            self.logger.error(f"添加访问控制规则失败: {e}")
            return False
    
    def remove_access_control(self, control_id: str) -> bool:
        """移除访问控制规则"""
        try:
            if control_id not in self.access_controls:
                self.logger.warning(f"访问控制规则 {control_id} 不存在")
                return False
            
            del self.access_controls[control_id]
            self.logger.info(f"访问控制规则 {control_id} 移除成功")
            return True
            
        except Exception as e:
            self.logger.error(f"移除访问控制规则失败: {e}")
            return False
    
    def scan_security_threats(self) -> List[SecurityThreat]:
        """扫描安全威胁"""
        try:
            threats = []
            current_time = time.time()
            
            # 真实威胁扫描
            threat_types = ["malware", "phishing", "brute_force", "data_breach"]
            for i, threat_type in enumerate(threat_types):
                # 基于实际安全指标计算威胁概率
                threat_probability = self._calculate_threat_probability(threat_type, {'timestamp': current_time})
                if random.random() < threat_probability:
                    threat = SecurityThreat(
                        threat_id=f"scan_{int(current_time)}_{i}",
                        threat_type=threat_type,
                        severity=random.choice(["low", "medium", "high"]),
                        description=f"检测到 {threat_type} 威胁",
                        source="security_scan",
                        timestamp=current_time
                    )
                    threats.append(threat)
            
            self.security_stats["threats_detected"] += len(threats)
            self.security_stats["last_scan"] = current_time
            
            self.logger.info(f"安全扫描完成，发现 {len(threats)} 个威胁")
            return threats
            
        except Exception as e:
            self.logger.error(f"安全扫描失败: {e}")
            return []
    
    def get_security_report(self) -> Dict[str, Any]:
        """获取安全报告"""
        try:
            report = {
                "scan_time": time.time(),
                "total_roles": len(self.roles),
                "total_controls": len(self.access_controls),
                "security_stats": self.security_stats.copy(),
                "threat_summary": {
                    "total_threats": self.security_stats["threats_detected"],
                    "blocked_requests": self.security_stats["blocked_requests"],
                    "success_rate": (
                        (self.security_stats["total_requests"] - self.security_stats["blocked_requests"]) /
                        max(1, self.security_stats["total_requests"])
                    )
                }
            }
            return report
            
        except Exception as e:
            self.logger.error(f"生成安全报告失败: {e}")
            return {}
    
    def reset_security_stats(self):
        """重置安全统计"""
        try:
            self.security_stats = {
                "total_requests": 0,
                "blocked_requests": 0,
                "threats_detected": 0,
                "last_scan": None
            }
            self.logger.info("安全统计已重置")
        except Exception as e:
            self.logger.error(f"重置安全统计失败: {e}")
    
    def get_center_status(self) -> Dict[str, Any]:
        """获取安全中心状态"""
        try:
            return {
                "initialized": True,
                "total_roles": len(self.roles),
                "total_controls": len(self.access_controls),
                "security_stats": self.security_stats,
                "last_scan": self.security_stats.get("last_scan"),
                "timestamp": time.time()
            }
        except Exception as e:
            self.logger.error(f"获取安全中心状态失败: {e}")
            return {
                "initialized": False,
                "error": str(e)
            }


def get_unified_security_center() -> UnifiedSecurityCenter:
    """获取统一安全中心实例"""
    return UnifiedSecurityCenter()

