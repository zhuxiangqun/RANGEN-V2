#!/usr/bin/env python3
"""
基础安全检测服务
提供基本的安全事件检测和日志记录功能
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque

# 导入审计日志服务
from .audit_log_service import AuditEvent, AuditEventType, AuditSeverity, AuditSource

logger = logging.getLogger(__name__)


class ThreatType(Enum):
    """威胁类型（基础版本）"""
    BRUTE_FORCE_ATTACK = "brute_force_attack"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


class DetectionRuleType(Enum):
    """检测规则类型（基础版本）"""
    THRESHOLD_BASED = "threshold_based"          # 基于阈值


@dataclass
class ThreatIndicator:
    """威胁指标（基础版本）"""
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
    """安全检测规则（基础版本）"""
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


class SecurityDetectionService:
    """基础安全检测服务"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化基础安全检测服务"""
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 检测规则
        self.detection_rules: List[SecurityDetectionRule] = self._create_default_rules()
        
        # 事件历史（用于时间窗口分析）
        self.event_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self.config.get("max_events_per_key", 1000))
        )
        
        # 统计信息
        self.stats = {
            "events_processed": 0,
            "threats_detected": 0,
            "false_positives": 0,
            "rules_triggered": defaultdict(int)
        }
        
        # 告警历史
        self.alert_history: List[ThreatIndicator] = []
        self.max_alert_history = self.config.get("max_alert_history", 100)
        
        self.logger.info("基础安全检测服务初始化完成")
    
    def _create_default_rules(self) -> List[SecurityDetectionRule]:
        """创建默认检测规则"""
        return [
            SecurityDetectionRule(
                rule_id="brute_force_detection",
                name="暴力破解检测",
                description="检测短时间内多次失败的登录尝试",
                rule_type=DetectionRuleType.THRESHOLD_BASED,
                threshold=5,  # 5次失败尝试
                time_window_seconds=300,  # 5分钟
                min_events=3,
                severity=AuditSeverity.ERROR,
                actions=["alert", "block_ip", "log"]
            ),
            SecurityDetectionRule(
                rule_id="suspicious_activity",
                name="可疑活动检测",
                description="检测异常的用户行为模式",
                rule_type=DetectionRuleType.THRESHOLD_BASED,
                threshold=10,  # 10次异常活动
                time_window_seconds=3600,  # 1小时
                min_events=5,
                severity=AuditSeverity.WARNING,
                actions=["alert", "log"]
            )
        ]
    
    def process_audit_event(self, event: AuditEvent) -> List[ThreatIndicator]:
        """处理审计事件，检测安全威胁"""
        self.stats["events_processed"] += 1
        
        # 记录事件到历史
        event_key = self._get_event_key(event)
        self.event_history[event_key].append(event)
        
        # 应用检测规则
        detected_threats: List[ThreatIndicator] = []
        
        for rule in self.detection_rules:
            if not rule.enabled:
                continue
                
            if rule.rule_type == DetectionRuleType.THRESHOLD_BASED:
                threats = self._apply_threshold_rule(event, rule)
                detected_threats.extend(threats)
        
        # 记录检测到的威胁
        for threat in detected_threats:
            self._record_threat(threat)
        
        return detected_threats
    
    def _get_event_key(self, event: AuditEvent) -> str:
        """获取事件分类键"""
        if event.event_type in [AuditEventType.LOGIN_ATTEMPT, AuditEventType.LOGIN_SUCCESS, AuditEventType.LOGIN_FAILURE]:
            return f"login:{event.user_id or event.ip_address}"
        elif event.event_type in [AuditEventType.API_CALL, AuditEventType.DATA_ACCESS]:
            return f"api:{event.user_id or event.ip_address}:{event.resource}"
        else:
            return f"other:{event.event_type.value}"
    
    def _apply_threshold_rule(self, event: AuditEvent, rule: SecurityDetectionRule) -> List[ThreatIndicator]:
        """应用基于阈值的检测规则"""
        if rule.threshold is None:
            return []
        
        event_key = self._get_event_key(event)
        events_in_window = self._get_events_in_window(event_key, rule.time_window_seconds)
        
        # 计算相关事件数量
        relevant_events = self._filter_relevant_events(events_in_window, event, rule)
        
        if len(relevant_events) >= rule.threshold and len(relevant_events) >= rule.min_events:
            threat = self._create_threat_indicator(
                threat_type=self._map_event_to_threat_type(event),
                description=f"检测到阈值触发: {rule.name} (阈值: {rule.threshold}, 实际: {len(relevant_events)})",
                severity=rule.severity,
                confidence=min(0.9, len(relevant_events) / (rule.threshold * 2)),  # 简单的置信度计算
                related_events=relevant_events
            )
            self.stats["rules_triggered"][rule.rule_id] += 1
            return [threat]
        
        return []
    
    def _get_events_in_window(self, event_key: str, time_window_seconds: int) -> List[AuditEvent]:
        """获取时间窗口内的事件"""
        now = datetime.now()
        window_start = now - timedelta(seconds=time_window_seconds)
        
        events = list(self.event_history.get(event_key, deque()))
        return [e for e in events if e.timestamp >= window_start]
    
    def _filter_relevant_events(self, events: List[AuditEvent], current_event: AuditEvent, rule: SecurityDetectionRule) -> List[AuditEvent]:
        """过滤相关事件（基础实现：只过滤相同类型的事件）"""
        return [e for e in events if e.event_type == current_event.event_type]
    
    def _map_event_to_threat_type(self, event: AuditEvent) -> ThreatType:
        """将事件类型映射到威胁类型"""
        if event.event_type == AuditEventType.LOGIN_FAILURE:
            return ThreatType.BRUTE_FORCE_ATTACK
        elif event.severity == AuditSeverity.ERROR:
            return ThreatType.UNAUTHORIZED_ACCESS
        else:
            return ThreatType.SUSPICIOUS_ACTIVITY
    
    def _create_threat_indicator(self, threat_type: ThreatType, description: str, 
                               severity: AuditSeverity, confidence: float, 
                               related_events: List[AuditEvent]) -> ThreatIndicator:
        """创建威胁指标"""
        return ThreatIndicator(
            indicator_id=f"threat_{int(time.time())}_{hash(threat_type.value) % 10000:04d}",
            threat_type=threat_type,
            confidence=confidence,
            severity=severity,
            description=description,
            detection_time=datetime.now(),
            related_events=related_events,
            metadata={
                "detection_time": datetime.now().isoformat(),
                "related_event_count": len(related_events)
            }
        )
    
    def _record_threat(self, threat: ThreatIndicator) -> None:
        """记录检测到的威胁"""
        self.alert_history.append(threat)
        if len(self.alert_history) > self.max_alert_history:
            self.alert_history.pop(0)
        
        self.stats["threats_detected"] += 1
        
        # 执行规则动作
        self._execute_rule_actions(threat)
    
    def _execute_rule_actions(self, threat: ThreatIndicator) -> None:
        """执行规则动作（基础实现：仅日志记录）"""
        self.logger.warning(
            f"安全威胁检测: {threat.threat_type.value} - {threat.description} "
            f"(置信度: {threat.confidence:.2f}, 严重性: {threat.severity.value})"
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        return self.stats.copy()
    
    def get_recent_threats(self, limit: int = 50) -> List[ThreatIndicator]:
        """获取最近的威胁检测结果"""
        return self.alert_history[-limit:] if self.alert_history else []
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats = {
            "events_processed": 0,
            "threats_detected": 0,
            "false_positives": 0,
            "rules_triggered": defaultdict(int)
        }
        self.logger.info("统计信息已重置")


# 创建服务的工厂函数
def create_security_detection_service(config: Optional[Dict[str, Any]] = None) -> SecurityDetectionService:
    """创建基础安全检测服务实例"""
    return SecurityDetectionService(config or {})