#!/usr/bin/env python3
"""
高级安全检测服务
提供智能安全威胁检测，包括行为分析、异常检测、威胁情报集成
"""

import asyncio
import logging
import time
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import statistics
import ipaddress

# 导入审计日志服务
from .audit_log_service import AuditEvent, AuditEventType, AuditSeverity, AuditSource

logger = logging.getLogger(__name__)


class ThreatType(Enum):
    """威胁类型"""
    BRUTE_FORCE_ATTACK = "brute_force_attack"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    INSIDER_THREAT = "insider_threat"
    API_ABUSE = "api_abuse"
    ACCOUNT_TAKEOVER = "account_takeover"
    MALICIOUS_SCRIPT = "malicious_script"
    RATE_LIMIT_VIOLATION = "rate_limit_violation"
    SUSPICIOUS_PATTERN = "suspicious_pattern"


class DetectionRuleType(Enum):
    """检测规则类型"""
    THRESHOLD_BASED = "threshold_based"          # 基于阈值
    BEHAVIORAL_BASED = "behavioral_based"        # 基于行为
    STATISTICAL_ANOMALY = "statistical_anomaly"  # 统计异常
    PATTERN_MATCHING = "pattern_matching"        # 模式匹配
    MACHINE_LEARNING = "machine_learning"        # 机器学习
    HYBRID = "hybrid"                            # 混合规则


@dataclass
class ThreatIndicator:
    """威胁指标"""
    indicator_id: str
    threat_type: ThreatType
    confidence: float  # 0.0-1.0
    severity: AuditSeverity
    description: str
    detection_time: datetime
    related_events: List[AuditEvent]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityDetectionRule:
    """安全检测规则"""
    rule_id: str
    name: str
    description: str
    rule_type: DetectionRuleType
    enabled: bool = True
    threshold: Optional[float] = None
    time_window_seconds: int = 300  # 5分钟
    min_events: int = 1
    severity: AuditSeverity = AuditSeverity.WARNING
    actions: List[str] = field(default_factory=lambda: ["alert", "log"])
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserBehaviorProfile:
    """用户行为画像"""
    user_id: str
    login_times: List[datetime] = field(default_factory=list)
    ip_addresses: Set[str] = field(default_factory=set)
    user_agents: Set[str] = field(default_factory=set)
    accessed_resources: Set[str] = field(default_factory=set)
    api_call_patterns: Dict[str, int] = field(default_factory=dict)  # API端点 -> 调用次数
    last_login: Optional[datetime] = None
    last_ip: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class GeoLocation:
    """地理位置信息"""
    ip_address: str
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    isp: Optional[str] = None


class AdvancedSecurityDetectionService:
    """高级安全检测服务"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化高级安全检测服务"""
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 检测规则
        self.detection_rules: List[SecurityDetectionRule] = self._create_default_rules()
        
        # 用户行为画像缓存
        self.user_profiles: Dict[str, UserBehaviorProfile] = {}
        self.max_user_profiles = self.config.get("max_user_profiles", 1000)
        
        # 事件历史（用于时间窗口分析）
        self.event_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self.config.get("max_events_per_key", 1000))
        )
        
        # IP地理位置缓存
        self.geo_cache: Dict[str, GeoLocation] = {}
        self.geo_cache_ttl = self.config.get("geo_cache_ttl", 3600)  # 1小时
        
        # 威胁情报（可以扩展为从外部API获取）
        self.threat_intelligence = {
            "malicious_ips": set(),
            "suspicious_user_agents": set(),
            "known_attack_patterns": set()
        }
        
        # 统计信息
        self.stats = {
            "events_processed": 0,
            "threats_detected": 0,
            "false_positives": 0,
            "rules_triggered": defaultdict(int)
        }
        
        # 告警历史
        self.alert_history: List[ThreatIndicator] = []
        self.max_alert_history = self.config.get("max_alert_history", 500)
        
        self.logger.info("高级安全检测服务初始化完成")
    
    def _parse_timestamp(self, timestamp) -> datetime:
        """解析时间戳，支持datetime对象或ISO格式字符串"""
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, str):
            return datetime.fromisoformat(timestamp)
        else:
            # 默认为当前时间
            self.logger.warning(f"无法解析时间戳类型: {type(timestamp)}，使用当前时间")
            return datetime.now()
    
    def _create_default_rules(self) -> List[SecurityDetectionRule]:
        """创建默认检测规则"""
        return [
            # 1. 暴力破解攻击检测
            SecurityDetectionRule(
                rule_id="rule_brute_force",
                name="暴力破解攻击检测",
                description="检测短时间内多次登录失败",
                rule_type=DetectionRuleType.THRESHOLD_BASED,
                threshold=5,  # 5次失败登录
                time_window_seconds=300,  # 5分钟
                min_events=5,
                severity=AuditSeverity.CRITICAL,
                actions=["alert", "block_ip", "notify_admin"],
                metadata={"attack_type": "brute_force"}
            ),
            
            # 2. 地理位置异常检测
            SecurityDetectionRule(
                rule_id="rule_geo_anomaly",
                name="地理位置异常检测",
                description="检测用户从异常地理位置登录",
                rule_type=DetectionRuleType.BEHAVIORAL_BASED,
                time_window_seconds=86400,  # 24小时
                min_events=1,
                severity=AuditSeverity.WARNING,
                actions=["alert", "require_mfa"],
                metadata={"anomaly_type": "geographic"}
            ),
            
            # 3. 权限提升检测
            SecurityDetectionRule(
                rule_id="rule_privilege_escalation",
                name="权限提升检测",
                description="检测用户权限异常提升",
                rule_type=DetectionRuleType.PATTERN_MATCHING,
                time_window_seconds=3600,  # 1小时
                min_events=1,
                severity=AuditSeverity.ERROR,
                actions=["alert", "suspend_user", "notify_admin"],
                metadata={"pattern": "privilege_change"}
            ),
            
            # 4. 数据泄露检测
            SecurityDetectionRule(
                rule_id="rule_data_exfiltration",
                name="数据泄露检测",
                description="检测异常数据导出模式",
                rule_type=DetectionRuleType.STATISTICAL_ANOMALY,
                threshold=3.0,  # 3倍标准差
                time_window_seconds=3600,  # 1小时
                min_events=5,
                severity=AuditSeverity.CRITICAL,
                actions=["alert", "block_user", "notify_admin"],
                metadata={"data_type": "export"}
            ),
            
            # 5. API滥用检测
            SecurityDetectionRule(
                rule_id="rule_api_abuse",
                name="API滥用检测",
                description="检测异常API调用频率",
                rule_type=DetectionRuleType.THRESHOLD_BASED,
                threshold=100,  # 100次/分钟
                time_window_seconds=60,  # 1分钟
                min_events=100,
                severity=AuditSeverity.WARNING,
                actions=["alert", "throttle", "log"],
                metadata={"api_endpoint": "all"}
            ),
            
            # 6. 内部威胁检测
            SecurityDetectionRule(
                rule_id="rule_insider_threat",
                name="内部威胁检测",
                description="检测员工异常行为模式",
                rule_type=DetectionRuleType.BEHAVIORAL_BASED,
                time_window_seconds=604800,  # 7天
                min_events=3,
                severity=AuditSeverity.ERROR,
                actions=["alert", "investigate", "notify_hr"],
                metadata={"user_type": "employee"}
            ),
            
            # 7. 账户劫持检测
            SecurityDetectionRule(
                rule_id="rule_account_takeover",
                name="账户劫持检测",
                description="检测账户异常活动",
                rule_type=DetectionRuleType.HYBRID,
                time_window_seconds=1800,  # 30分钟
                min_events=2,
                severity=AuditSeverity.CRITICAL,
                actions=["alert", "lock_account", "notify_user"],
                metadata={"risk_level": "high"}
            ),
        ]
    
    def _update_user_profile(self, event: AuditEvent) -> None:
        """更新用户行为画像"""
        user_id = event.user_id
        if not user_id:
            return
        
        if user_id not in self.user_profiles:
            if len(self.user_profiles) >= self.max_user_profiles:
                # 简单的LRU策略：删除最久未更新的用户
                oldest_user = min(self.user_profiles.items(), 
                                 key=lambda x: x[1].updated_at)[0]
                del self.user_profiles[oldest_user]
            
            self.user_profiles[user_id] = UserBehaviorProfile(user_id=user_id)
        
        profile = self.user_profiles[user_id]
        
        # 更新登录时间
        if event.event_type in [AuditEventType.LOGIN_SUCCESS, AuditEventType.LOGIN_FAILURE]:
            profile.login_times.append(self._parse_timestamp(event.timestamp))
            profile.last_login = self._parse_timestamp(event.timestamp)
            
            if event.ip_address:
                profile.ip_addresses.add(event.ip_address)
                profile.last_ip = event.ip_address
            
            if event.user_agent:
                profile.user_agents.add(event.user_agent)
        
        # 更新API调用模式
        if event.event_type == AuditEventType.API_KEY_USAGE:
            # 从metadata中提取API端点
            api_endpoint = event.metadata.get("endpoint", "unknown") if hasattr(event, 'metadata') else "unknown"
            profile.api_call_patterns[api_endpoint] = profile.api_call_patterns.get(api_endpoint, 0) + 1
        
        # 更新资源访问记录
        if event.event_type in [AuditEventType.DATA_ACCESS, AuditEventType.DATA_MODIFY]:
            resource = event.metadata.get("resource", "unknown") if hasattr(event, 'metadata') else "unknown"
            profile.accessed_resources.add(resource)
        
        profile.updated_at = datetime.now()
    
    def _get_geo_location(self, ip_address: str) -> Optional[GeoLocation]:
        """获取IP地理位置（简化版，实际应使用外部API）"""
        if not ip_address:
            return None
        
        # 检查缓存
        if ip_address in self.geo_cache:
            cached = self.geo_cache[ip_address]
            # 简单的TTL检查
            if hasattr(cached, 'cached_at'):
                if (datetime.now() - cached.cached_at).total_seconds() < self.geo_cache_ttl:
                    return cached
        
        # 简化实现：实际应使用ip-api.com或类似服务
        try:
            ip_obj = ipaddress.ip_address(ip_address)
            
            # 模拟地理位置（实际项目应集成真实的地理位置服务）
            if ip_address.startswith("192.168.") or ip_address.startswith("10.") or ip_address.startswith("172."):
                geo = GeoLocation(
                    ip_address=ip_address,
                    country="内部网络",
                    region="内部",
                    city="内部",
                    isp="内部网络"
                )
            else:
                # 简单哈希用于模拟不同地理位置
                ip_hash = int(hashlib.md5(ip_address.encode()).hexdigest()[:8], 16)
                
                countries = ["中国", "美国", "日本", "德国", "英国", "法国", "澳大利亚", "加拿大"]
                country = countries[ip_hash % len(countries)]
                
                geo = GeoLocation(
                    ip_address=ip_address,
                    country=country,
                    region=f"区域{ip_hash % 10 + 1}",
                    city=f"城市{ip_hash % 50 + 1}",
                    latitude=20.0 + (ip_hash % 50),
                    longitude=-100.0 + (ip_hash % 120),
                    isp=f"ISP{(ip_hash % 5) + 1}"
                )
            
            # 添加缓存时间
            geo.cached_at = datetime.now()
            self.geo_cache[ip_address] = geo
            
            return geo
            
        except Exception as e:
            self.logger.warning(f"获取地理位置失败 {ip_address}: {e}")
            return None
    
    def _detect_brute_force(self, events: List[AuditEvent]) -> Optional[ThreatIndicator]:
        """检测暴力破解攻击"""
        rule = next((r for r in self.detection_rules if r.rule_id == "rule_brute_force"), None)
        if not rule or not rule.enabled:
            return None
        
        # 按IP地址分组失败登录
        ip_failures = defaultdict(int)
        recent_events = []
        
        for event in events:
            if (event.event_type == AuditEventType.LOGIN_FAILURE and 
                event.ip_address and
                event.timestamp):
                event_time = self._parse_timestamp(event.timestamp)
                time_diff = (datetime.now() - event_time).total_seconds()
                
                if time_diff <= rule.time_window_seconds:
                    ip_failures[event.ip_address] += 1
                    recent_events.append(event)
        
        # 检查是否超过阈值
        for ip, count in ip_failures.items():
            if count >= rule.threshold:
                # 计算置信度
                confidence = min(1.0, count / (rule.threshold * 2))
                
                indicator = ThreatIndicator(
                    indicator_id=f"brute_force_{int(time.time())}_{hash(ip) % 10000}",
                    threat_type=ThreatType.BRUTE_FORCE_ATTACK,
                    confidence=confidence,
                    severity=rule.severity,
                    description=f"IP地址 {ip} 在 {rule.time_window_seconds} 秒内 {count} 次登录失败，疑似暴力破解攻击",
                    detection_time=datetime.now(),
                    related_events=recent_events[:10],  # 最多10个相关事件
                    metadata={
                        "ip_address": ip,
                        "failure_count": count,
                        "time_window": rule.time_window_seconds,
                        "threshold": rule.threshold
                    }
                )
                
                self.stats["threats_detected"] += 1
                self.stats["rules_triggered"]["brute_force"] += 1
                
                return indicator
        
        return None
    
    def _detect_geographic_anomaly(self, events: List[AuditEvent]) -> Optional[ThreatIndicator]:
        """检测地理位置异常"""
        rule = next((r for r in self.detection_rules if r.rule_id == "rule_geo_anomaly"), None)
        if not rule or not rule.enabled:
            return None
        
        for event in events:
            if (event.event_type == AuditEventType.LOGIN_SUCCESS and 
                event.user_id and 
                event.ip_address and
                event.timestamp):
                
                # 获取用户画像
                user_profile = self.user_profiles.get(event.user_id)
                if not user_profile or len(user_profile.ip_addresses) < 3:
                    # 数据不足，跳过
                    continue
                
                # 获取当前登录的地理位置
                current_geo = self._get_geo_location(event.ip_address)
                if not current_geo or not current_geo.country:
                    continue
                
                # 分析历史地理位置
                historical_countries = set()
                for ip in user_profile.ip_addresses:
                    geo = self._get_geo_location(ip)
                    if geo and geo.country:
                        historical_countries.add(geo.country)
                
                # 如果当前国家不在历史国家列表中，标记为异常
                if (current_geo.country not in historical_countries and 
                    len(historical_countries) > 0):
                    
                    confidence = 0.7  # 基础置信度
                    
                    # 如果距离上次登录时间很短，增加置信度
                    if user_profile.last_login:
                        last_login_time = user_profile.last_login
                        current_time = self._parse_timestamp(event.timestamp)
                        hours_diff = (current_time - last_login_time).total_seconds() / 3600
                        
                        if hours_diff < 2:  # 2小时内从不同国家登录
                            confidence = 0.9
                    
                    indicator = ThreatIndicator(
                        indicator_id=f"geo_anomaly_{int(time.time())}_{hash(event.user_id) % 10000}",
                        threat_type=ThreatType.GEOGRAPHIC_ANOMALY,
                        confidence=confidence,
                        severity=rule.severity,
                        description=f"用户 {event.user_id} 从异常地理位置登录: {current_geo.country} (历史: {', '.join(historical_countries)})",
                        detection_time=datetime.now(),
                        related_events=[event],
                        metadata={
                            "user_id": event.user_id,
                            "current_country": current_geo.country,
                            "historical_countries": list(historical_countries),
                            "ip_address": event.ip_address
                        }
                    )
                    
                    self.stats["threats_detected"] += 1
                    self.stats["rules_triggered"]["geo_anomaly"] += 1
                    
                    return indicator
        
        return None
    
    def _detect_privilege_escalation(self, events: List[AuditEvent]) -> Optional[ThreatIndicator]:
        """检测权限提升"""
        rule = next((r for r in self.detection_rules if r.rule_id == "rule_privilege_escalation"), None)
        if not rule or not rule.enabled:
            return None
        
        for event in events:
            if event.event_type == AuditEventType.USER_PERMISSION_CHANGE:
                # 检查是否为自我权限提升
                if hasattr(event, 'metadata') and event.metadata:
                    target_user = event.metadata.get("target_user")
                    changed_by = event.metadata.get("changed_by")
                    
                    if target_user and changed_by and target_user == changed_by:
                        # 自我权限提升，高风险
                        indicator = ThreatIndicator(
                            indicator_id=f"priv_esc_{int(time.time())}_{hash(target_user) % 10000}",
                            threat_type=ThreatType.PRIVILEGE_ESCALATION,
                            confidence=0.95,
                            severity=rule.severity,
                            description=f"用户 {target_user} 尝试自我权限提升",
                            detection_time=datetime.now(),
                            related_events=[event],
                            metadata={
                                "user_id": target_user,
                                "action": "self_privilege_escalation",
                                "permissions": event.metadata.get("permissions", [])
                            }
                        )
                        
                        self.stats["threats_detected"] += 1
                        self.stats["rules_triggered"]["privilege_escalation"] += 1
                        
                        return indicator
        
        return None
    
    def _detect_api_abuse(self, events: List[AuditEvent]) -> Optional[ThreatIndicator]:
        """检测API滥用"""
        rule = next((r for r in self.detection_rules if r.rule_id == "rule_api_abuse"), None)
        if not rule or not rule.enabled:
            return None
        
        # 按API端点和IP地址统计调用频率
        endpoint_stats = defaultdict(lambda: defaultdict(int))
        recent_events = []
        
        for event in events:
            if (event.event_type == AuditEventType.API_KEY_USAGE and 
                event.ip_address and
                event.timestamp):
                
                event_time = self._parse_timestamp(event.timestamp)
                time_diff = (datetime.now() - event_time).total_seconds()
                
                if time_diff <= rule.time_window_seconds:
                    api_endpoint = event.metadata.get("endpoint", "unknown") if hasattr(event, 'metadata') else "unknown"
                    endpoint_stats[api_endpoint][event.ip_address] += 1
                    recent_events.append(event)
        
        # 检查是否超过阈值
        for endpoint, ip_counts in endpoint_stats.items():
            for ip, count in ip_counts.items():
                if count >= rule.threshold:
                    confidence = min(1.0, count / (rule.threshold * 1.5))
                    
                    indicator = ThreatIndicator(
                        indicator_id=f"api_abuse_{int(time.time())}_{hash(ip) % 10000}",
                        threat_type=ThreatType.API_ABUSE,
                        confidence=confidence,
                        severity=rule.severity,
                        description=f"IP地址 {ip} 对端点 {endpoint} 在 {rule.time_window_seconds} 秒内调用 {count} 次，疑似API滥用",
                        detection_time=datetime.now(),
                        related_events=[e for e in recent_events if e.ip_address == ip][:10],
                        metadata={
                            "ip_address": ip,
                            "api_endpoint": endpoint,
                            "call_count": count,
                            "time_window": rule.time_window_seconds,
                            "threshold": rule.threshold
                        }
                    )
                    
                    self.stats["threats_detected"] += 1
                    self.stats["rules_triggered"]["api_abuse"] += 1
                    
                    return indicator
        
        return None
    
    def _detect_insider_threat(self, events: List[AuditEvent]) -> Optional[ThreatIndicator]:
        """检测内部威胁"""
        rule = next((r for r in self.detection_rules if r.rule_id == "rule_insider_threat"), None)
        if not rule or not rule.enabled:
            return None
        
        # 检测异常数据访问模式
        user_data_access = defaultdict(list)
        
        for event in events:
            if event.event_type in [AuditEventType.DATA_ACCESS, AuditEventType.DATA_EXPORT]:
                if event.user_id and event.timestamp:
                    event_time = self._parse_timestamp(event.timestamp)
                    time_diff = (datetime.now() - event_time).total_seconds()
                    
                    if time_diff <= rule.time_window_seconds:
                        user_data_access[event.user_id].append({
                            "time": event_time,
                            "resource": event.metadata.get("resource", "unknown") if hasattr(event, 'metadata') else "unknown",
                            "action": event.event_type.value
                        })
        
        # 分析用户行为
        for user_id, accesses in user_data_access.items():
            if len(accesses) >= rule.min_events:
                # 检查是否访问了敏感资源
                sensitive_resources = {"user_data", "payment_info", "config", "admin"}
                accessed_resources = {access["resource"] for access in accesses}
                sensitive_accessed = sensitive_resources.intersection(accessed_resources)
                
                if sensitive_accessed:
                    # 检查访问时间模式（例如非工作时间）
                    non_work_hours_access = 0
                    for access in accesses:
                        hour = access["time"].hour
                        if hour < 9 or hour > 17:  # 非工作时间
                            non_work_hours_access += 1
                    
                    confidence = 0.6
                    if non_work_hours_access > 0:
                        confidence = 0.8
                    
                    indicator = ThreatIndicator(
                        indicator_id=f"insider_{int(time.time())}_{hash(user_id) % 10000}",
                        threat_type=ThreatType.INSIDER_THREAT,
                        confidence=confidence,
                        severity=rule.severity,
                        description=f"用户 {user_id} 在 {rule.time_window_seconds} 秒内访问了 {len(accesses)} 次敏感资源: {', '.join(sensitive_accessed)}",
                        detection_time=datetime.now(),
                        related_events=events[:5],  # 相关事件
                        metadata={
                            "user_id": user_id,
                            "access_count": len(accesses),
                            "sensitive_resources": list(sensitive_accessed),
                            "non_work_hours_access": non_work_hours_access,
                            "time_window": rule.time_window_seconds
                        }
                    )
                    
                    self.stats["threats_detected"] += 1
                    self.stats["rules_triggered"]["insider_threat"] += 1
                    
                    return indicator
        
        return None
    
    async def analyze_events(self, events: List[AuditEvent]) -> List[ThreatIndicator]:
        """分析审计事件，检测安全威胁"""
        self.stats["events_processed"] += len(events)
        
        # 更新事件历史
        for event in events:
            self._update_user_profile(event)
            
            # 按事件类型和用户/IP存储历史
            if event.user_id:
                key = f"user_{event.user_id}_{event.event_type.value}"
                self.event_history[key].append(event)
            
            if event.ip_address:
                key = f"ip_{event.ip_address}_{event.event_type.value}"
                self.event_history[key].append(event)
        
        # 应用检测规则
        threats = []
        
        # 暴力破解检测
        brute_force_threat = self._detect_brute_force(events)
        if brute_force_threat:
            threats.append(brute_force_threat)
        
        # 地理位置异常检测
        geo_threat = self._detect_geographic_anomaly(events)
        if geo_threat:
            threats.append(geo_threat)
        
        # 权限提升检测
        priv_threat = self._detect_privilege_escalation(events)
        if priv_threat:
            threats.append(priv_threat)
        
        # API滥用检测
        api_threat = self._detect_api_abuse(events)
        if api_threat:
            threats.append(api_threat)
        
        # 内部威胁检测
        insider_threat = self._detect_insider_threat(events)
        if insider_threat:
            threats.append(insider_threat)
        
        # 添加到告警历史
        for threat in threats:
            self.alert_history.append(threat)
            if len(self.alert_history) > self.max_alert_history:
                self.alert_history.pop(0)
        
        return threats
    
    def process_audit_event(self, event: AuditEvent) -> List[ThreatIndicator]:
        """处理单个审计事件（同步方法，用于兼容性）"""
        import asyncio
        
        # 将单个事件包装为列表并调用异步方法
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.analyze_events([event]))
        finally:
            loop.close()
    
    async def get_user_risk_score(self, user_id: str) -> Dict[str, Any]:
        """获取用户风险评分"""
        profile = self.user_profiles.get(user_id)
        if not profile:
            return {"user_id": user_id, "risk_score": 0.0, "factors": []}
        
        risk_factors = []
        risk_score = 0.0
        
        # 因素1: 登录地理位置多样性
        if len(profile.ip_addresses) > 3:
            geo_diversity_score = min(0.3, (len(profile.ip_addresses) - 3) * 0.1)
            risk_score += geo_diversity_score
            risk_factors.append({
                "factor": "high_geo_diversity",
                "score": geo_diversity_score,
                "details": f"{len(profile.ip_addresses)} 个不同IP地址"
            })
        
        # 因素2: 非工作时间登录
        if profile.login_times:
            non_work_logins = 0
            for login_time in profile.login_times[-10:]:  # 最近10次登录
                hour = login_time.hour
                if hour < 9 or hour > 17:
                    non_work_logins += 1
            
            if non_work_logins > 0:
                non_work_score = min(0.2, non_work_logins * 0.05)
                risk_score += non_work_score
                risk_factors.append({
                    "factor": "non_work_hour_logins",
                    "score": non_work_score,
                    "details": f"{non_work_logins} 次非工作时间登录"
                })
        
        # 因素3: API调用频率异常
        if profile.api_call_patterns:
            total_calls = sum(profile.api_call_patterns.values())
            if total_calls > 1000:  # 高频率调用
                api_score = min(0.2, total_calls / 10000)
                risk_score += api_score
                risk_factors.append({
                    "factor": "high_api_usage",
                    "score": api_score,
                    "details": f"总计 {total_calls} 次API调用"
                })
        
        # 限制在0-1之间
        risk_score = min(1.0, max(0.0, risk_score))
        
        return {
            "user_id": user_id,
            "risk_score": risk_score,
            "risk_level": self._get_risk_level(risk_score),
            "factors": risk_factors,
            "profile_summary": {
                "total_logins": len(profile.login_times),
                "unique_ips": len(profile.ip_addresses),
                "unique_user_agents": len(profile.user_agents),
                "last_login": profile.last_login.isoformat() if profile.last_login else None,
                "accessed_resources_count": len(profile.accessed_resources)
            }
        }
    
    def _get_risk_level(self, score: float) -> str:
        """根据风险评分获取风险等级"""
        if score >= 0.7:
            return "critical"
        elif score >= 0.5:
            return "high"
        elif score >= 0.3:
            return "medium"
        elif score >= 0.1:
            return "low"
        else:
            return "normal"
    
    async def get_detection_stats(self) -> Dict[str, Any]:
        """获取检测统计信息"""
        return {
            "stats": dict(self.stats),
            "rules_enabled": sum(1 for r in self.detection_rules if r.enabled),
            "total_rules": len(self.detection_rules),
            "user_profiles": len(self.user_profiles),
            "recent_threats": len([t for t in self.alert_history 
                                  if (datetime.now() - t.detection_time).total_seconds() < 3600]),
            "geo_cache_size": len(self.geo_cache)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息（同步方法，用于兼容性）"""
        return self.stats.copy()
    
    async def enable_rule(self, rule_id: str, enabled: bool = True) -> bool:
        """启用或禁用检测规则"""
        for rule in self.detection_rules:
            if rule.rule_id == rule_id:
                rule.enabled = enabled
                self.logger.info(f"规则 {rule_id} {'启用' if enabled else '禁用'}")
                return True
        return False
    
    async def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """更新检测规则"""
        for rule in self.detection_rules:
            if rule.rule_id == rule_id:
                for key, value in updates.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                
                self.logger.info(f"规则 {rule_id} 已更新: {updates}")
                return True
        return False
    
    async def add_custom_rule(self, rule: SecurityDetectionRule) -> bool:
        """添加自定义检测规则"""
        # 检查规则ID是否已存在
        if any(r.rule_id == rule.rule_id for r in self.detection_rules):
            self.logger.error(f"规则ID已存在: {rule.rule_id}")
            return False
        
        self.detection_rules.append(rule)
        self.logger.info(f"添加自定义规则: {rule.name}")
        return True


# 创建服务的工厂函数
def create_advanced_security_detection_service(config: Optional[Dict[str, Any]] = None) -> AdvancedSecurityDetectionService:
    """创建高级安全检测服务实例"""
    return AdvancedSecurityDetectionService(config or {})