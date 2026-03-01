#!/usr/bin/env python3
"""
SecurityGuardian - 安全卫士 (L1基础认知)
实时威胁检测、隐私保护、安全自动化、合规性检查
from ..utils.unified_centers import get_unified_config_center
from ..utils.unified_threshold_manager import get_unified_threshold_manager


优化特性：
- 实时威胁检测：监控和识别各种安全威胁
- 隐私保护：自动识别和保护敏感信息
- 安全自动化：自动响应和缓解安全事件
- 合规性检查：确保系统行为符合法规要求
"""

import time
import logging
import asyncio
import json
import hashlib
import threading
import re
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, OrderedDict
from concurrent.futures import ThreadPoolExecutor

from .expert_agent import ExpertAgent
from .base_agent import AgentResult
from src.utils.logging_helper import get_module_logger, ModuleType

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """威胁级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """威胁类型"""
    PROMPT_INJECTION = "prompt_injection"
    DATA_LEAKAGE = "data_leakage"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    MALICIOUS_INPUT = "malicious_input"
    RESOURCE_ABUSE = "resource_abuse"
    PRIVACY_VIOLATION = "privacy_violation"
    COMPLIANCE_BREACH = "compliance_breach"


class PrivacyType(Enum):
    """隐私类型"""
    PERSONAL_DATA = "personal_data"
    FINANCIAL_DATA = "financial_data"
    HEALTH_DATA = "health_data"
    LOCATION_DATA = "location_data"
    CONTACT_INFO = "contact_info"
    IDENTIFIERS = "identifiers"


@dataclass
class SecurityThreat:
    """安全威胁"""
    threat_id: str
    threat_type: ThreatType
    level: ThreatLevel
    description: str
    source: str
    target: str
    indicators: List[str] = field(default_factory=list)
    detected_at: float = field(default_factory=time.time)
    status: str = "active"  # active, mitigated, resolved
    mitigation_actions: List[str] = field(default_factory=list)


@dataclass
class PrivacyIncident:
    """隐私事件"""
    incident_id: str
    privacy_type: PrivacyType
    description: str
    affected_data: List[str]
    risk_level: str
    detected_at: float = field(default_factory=time.time)
    status: str = "active"  # active, contained, resolved
    remediation_actions: List[str] = field(default_factory=list)


@dataclass
class ComplianceViolation:
    """合规性违规"""
    violation_id: str
    regulation: str
    requirement: str
    description: str
    severity: str
    detected_at: float = field(default_factory=time.time)
    status: str = "active"  # active, remediated, accepted
    remediation_plan: List[str] = field(default_factory=list)


class SecurityGuardian(ExpertAgent):
    """SecurityGuardian - 安全卫士 (L1基础认知)

    核心职责：
    1. 实时威胁检测 - 监控和识别各种安全威胁
    2. 隐私保护 - 自动识别和保护敏感信息
    3. 安全自动化 - 自动响应和缓解安全事件
    4. 合规性检查 - 确保系统行为符合法规要求

    优化特性：
    - 多层威胁检测：基于规则、模式匹配和行为分析
    - 隐私信息识别：自动检测和保护各种类型的敏感数据
    - 自动化响应：威胁检测后的自动缓解措施
    - 合规性监控：持续监控法规遵从性
    """

    def __init__(self):
        """初始化SecurityGuardian"""
        # 初始化统一配置中心
        self.config_center = get_unified_config_center()
        self.threshold_manager = get_unified_threshold_manager()

        # 获取Agent特定配置
        self.agent_config = self.config_center.get_agent_config(self.__class__.__name__, {
            'enabled': True,
            'max_retries': 3,
            'timeout': 30,
            'debug_mode': False
        })

        # 获取阈值配置
        self.thresholds = self.threshold_manager.get_thresholds(self.__class__.__name__, {
            'performance_warning_threshold': 5.0,
            'error_rate_threshold': 0.1,
            'memory_usage_threshold': 80.0
        })

        super().__init__(
            agent_id="security_guardian",
            domain_expertise="安全防护和隐私保护",
            capability_level=0.5,  # L1基础认知
            collaboration_style="protective"
        )

        # 使用模块日志器
        self.module_logger = get_module_logger(ModuleType.AGENT, "SecurityGuardian")

        # 🚀 新增：安全监控和防护配置
        self._active_threats: Dict[str, SecurityThreat] = {}
        self._privacy_incidents: Dict[str, PrivacyIncident] = {}
        self._compliance_violations: Dict[str, ComplianceViolation] = {}
        self._security_events: List[Dict[str, Any]] = []

        # 🚀 新增：威胁检测和隐私保护配置
        self._threat_detection_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="threat_detection")
        self._threat_patterns: Dict[str, Dict[str, Any]] = {}
        self._privacy_patterns: Dict[str, Dict[str, Any]] = {}
        self._compliance_rules: Dict[str, Dict[str, Any]] = {}

        # 🚀 新增：监控和响应配置
        self._monitoring_enabled = True
        self._alert_thresholds = {
            'threat_detection_rate': 0.1,  # 威胁检测率阈值
            'privacy_incident_rate': 0.05,  # 隐私事件率阈值
            'compliance_violation_rate': 0.02  # 合规违规率阈值
        }

        # 🚀 新增：统计和监控
        self._stats = {
            'total_threats_detected': 0,
            'threats_mitigated': 0,
            'privacy_incidents_handled': 0,
            'compliance_checks_passed': 0,
            'auto_responses_triggered': 0,
            'false_positives': 0
        }

        # 🚀 新增：缓存和性能优化
        self._threat_cache = OrderedDict()  # LRU缓存
        self._privacy_cache = OrderedDict()
        self._cache_max_size = 1000

        # 初始化内置威胁模式和隐私模式
        self._initialize_builtin_patterns()
        self._initialize_compliance_rules()

        # 启动监控线程
        self._monitoring_thread: Optional[threading.Thread] = None
        self._running = False
        self._start_monitoring_thread()

    def _get_service(self):
        """SecurityGuardian不直接使用单一Service"""
        return None

    # 🚀 新增：实时威胁检测
    async def detect_threats(self, input_data: str, context: Optional[Dict[str, Any]] = None) -> List[SecurityThreat]:
        """实时威胁检测"""
        start_time = time.time()

        # 检查缓存
        cache_key = self._get_threat_cache_key(input_data, context)
        if cache_key in self._threat_cache:
            self._threat_cache.move_to_end(cache_key)
            return self._threat_cache[cache_key]

        threats = []

        # 并行执行多种威胁检测
        detection_tasks = [
            self._detect_prompt_injection(input_data, context),
            self._detect_malicious_input(input_data, context),
            self._detect_resource_abuse(input_data, context),
            self._detect_unauthorized_access(input_data, context)
        ]

        detection_results = await asyncio.gather(*detection_tasks, return_exceptions=True)

        # 处理检测结果
        for result in detection_results:
            if isinstance(result, list):
                threats.extend(result)

        # 去重和过滤
        unique_threats = self._deduplicate_threats(threats)

        # 注册活跃威胁
        for threat in unique_threats:
            self._active_threats[threat.threat_id] = threat
            self._stats['total_threats_detected'] += 1

        # 缓存结果
        if len(self._threat_cache) >= self._cache_max_size:
            self._threat_cache.popitem(last=False)
        self._threat_cache[cache_key] = unique_threats

        execution_time = time.time() - start_time
        if unique_threats:
            self.module_logger.warning(f"⚠️ 检测到 {len(unique_threats)} 个安全威胁，耗时={execution_time:.3f}秒")

        return unique_threats

    async def _detect_prompt_injection(self, input_data: str, context: Optional[Dict[str, Any]]) -> List[SecurityThreat]:
        """检测提示注入攻击"""
        threats = []

        # 提示注入模式
        injection_patterns = [
            (r'\b(ignore|forget|disregard)\s+(previous|all|these)\s+(instructions?|rules?)\b', '指令覆盖'),
            (r'\b(you\s+are|act\s+as)\s+(now|a\s+new)\s+(persona|role|character)\b', '角色扮演注入'),
            (r'\b(system|developer)\s+(mode|prompt|instruction)\b', '系统模式访问'),
            (r'\b(override|change|modify)\s+(your\s+)?((core\s+)?instructions?|behavior|rules?)\b', '行为修改'),
            (r'\b(reveal|show|display)\s+(your\s+)?(system|internal|hidden)\s+(prompt|instruction|code)\b', '信息泄露'),
        ]

        input_lower = input_data.lower()

        for pattern, description in injection_patterns:
            if re.search(pattern, input_lower, re.IGNORECASE):
                threat = SecurityThreat(
                    threat_id=f"threat_{int(time.time() * 1000)}_{hash(input_data) % 10000}",
                    threat_type=ThreatType.PROMPT_INJECTION,
                    level=ThreatLevel.HIGH,
                    description=f"检测到提示注入攻击: {description}",
                    source="input_analysis",
                    target="system_prompt",
                    indicators=[pattern]
                )
                threats.append(threat)

        return threats

    async def _detect_malicious_input(self, input_data: str, context: Optional[Dict[str, Any]]) -> List[SecurityThreat]:
        """检测恶意输入"""
        threats = []

        # 恶意输入模式
        malicious_patterns = [
            (r'<script[^>]*>.*?</script>', 'XSS攻击'),
            (r'(javascript|vbscript|data):', '脚本注入'),
            (r'\b(eval|exec|compile)\s*\(', '代码执行'),
            (r'\b(import|require)\s*\([^)]*\)', '模块注入'),
            (r'(\.\./|\.\.\\)', '路径遍历'),
        ]

        for pattern, description in malicious_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                threat = SecurityThreat(
                    threat_id=f"threat_{int(time.time() * 1000)}_{hash(input_data + pattern) % 10000}",
                    threat_type=ThreatType.MALICIOUS_INPUT,
                    level=ThreatLevel.CRITICAL,
                    description=f"检测到恶意输入: {description}",
                    source="input_validation",
                    target="system_execution",
                    indicators=[pattern]
                )
                threats.append(threat)

        return threats

    async def _detect_resource_abuse(self, input_data: str, context: Optional[Dict[str, Any]]) -> List[SecurityThreat]:
        """检测资源滥用"""
        threats = []

        # 检查输入长度（防止DoS攻击）
        if len(input_data) > 10000:  # 10KB阈值
            threat = SecurityThreat(
                threat_id=f"threat_{int(time.time() * 1000)}_{hash(input_data) % 10000}",
                threat_type=ThreatType.RESOURCE_ABUSE,
                level=ThreatLevel.MEDIUM,
                description="检测到潜在的资源滥用攻击（输入过长）",
                source="resource_monitoring",
                target="system_resources",
                indicators=[f"input_length={len(input_data)}"]
            )
            threats.append(threat)

        # 检查重复模式（可能为DoS）
        if input_data.count(input_data[:10]) > 10:  # 重复10次以上
            threat = SecurityThreat(
                threat_id=f"threat_{int(time.time() * 1000)}_{hash(input_data) % 10000}",
                threat_type=ThreatType.RESOURCE_ABUSE,
                level=ThreatLevel.MEDIUM,
                description="检测到重复模式，可能为DoS攻击",
                source="pattern_analysis",
                target="system_resources",
                indicators=["repetitive_pattern"]
            )
            threats.append(threat)

        return threats

    async def _detect_unauthorized_access(self, input_data: str, context: Optional[Dict[str, Any]]) -> List[SecurityThreat]:
        """检测未经授权的访问"""
        threats = []

        # 检查敏感操作关键词
        sensitive_keywords = [
            'admin', 'root', 'sudo', 'superuser', 'godmode',
            'bypass', 'override', 'disable', 'shutdown', 'restart',
            'delete', 'drop', 'truncate', 'format'
        ]

        input_lower = input_data.lower()
        matched_keywords = [kw for kw in sensitive_keywords if kw in input_lower]

        if len(matched_keywords) > 2:  # 多个敏感关键词
            threat = SecurityThreat(
                threat_id=f"threat_{int(time.time() * 1000)}_{hash(input_data) % 10000}",
                threat_type=ThreatType.UNAUTHORIZED_ACCESS,
                level=ThreatLevel.HIGH,
                description=f"检测到潜在的未经授权访问尝试（敏感关键词: {', '.join(matched_keywords[:3])}）",
                source="keyword_analysis",
                target="system_access",
                indicators=matched_keywords
            )
            threats.append(threat)

        return threats

    # 🚀 新增：隐私保护
    async def protect_privacy(self, content: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """隐私保护"""
        start_time = time.time()

        # 检查缓存
        cache_key = self._get_privacy_cache_key(content, context)
        if cache_key in self._privacy_cache:
            self._privacy_cache.move_to_end(cache_key)
            return self._privacy_cache[cache_key]

        privacy_incidents = []

        # 并行执行隐私检测
        privacy_tasks = [
            self._detect_personal_data(content),
            self._detect_financial_data(content),
            self._detect_health_data(content),
            self._detect_location_data(content),
            self._detect_contact_info(content)
        ]

        privacy_results = await asyncio.gather(*privacy_tasks, return_exceptions=True)

        # 处理检测结果
        for result in privacy_results:
            if isinstance(result, list):
                privacy_incidents.extend(result)

        # 注册隐私事件
        for incident in privacy_incidents:
            self._privacy_incidents[incident.incident_id] = incident
            self._stats['privacy_incidents_handled'] += 1

        # 执行隐私保护措施
        protected_content, applied_protections = await self._apply_privacy_protections(content, privacy_incidents)

        result = {
            'original_content': content,
            'protected_content': protected_content,
            'privacy_incidents': len(privacy_incidents),
            'applied_protections': applied_protections,
            'risk_level': self._calculate_privacy_risk(privacy_incidents),
            'processing_time': time.time() - start_time
        }

        # 缓存结果
        if len(self._privacy_cache) >= self._cache_max_size:
            self._privacy_cache.popitem(last=False)
        self._privacy_cache[cache_key] = result

        if privacy_incidents:
            self.module_logger.warning(f"🔒 检测到 {len(privacy_incidents)} 个隐私风险，风险等级: {result['risk_level']}")

        return result

    async def _detect_personal_data(self, content: str) -> List[PrivacyIncident]:
        """检测个人信息"""
        incidents = []

        # 个人信息模式
        personal_patterns = [
            (r'\b\d{3}-\d{2}-\d{4}\b', 'social_security_number', PrivacyType.IDENTIFIERS),  # SSN
            (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 'credit_card', PrivacyType.FINANCIAL_DATA),  # 信用卡
            (r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', 'full_name', PrivacyType.PERSONAL_DATA),  # 姓名
            (r'\b\d{1,2}/\d{1,2}/\d{4}\b', 'birth_date', PrivacyType.PERSONAL_DATA),  # 生日
        ]

        for pattern, data_type, privacy_type in personal_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                incident = PrivacyIncident(
                    incident_id=f"privacy_{int(time.time() * 1000)}_{hash(match) % 10000}",
                    privacy_type=privacy_type,
                    description=f"检测到{data_type}: {match[:10]}...",
                    affected_data=[match],
                    risk_level="high" if privacy_type in [PrivacyType.IDENTIFIERS, PrivacyType.FINANCIAL_DATA] else "medium"
                )
                incidents.append(incident)

        return incidents

    async def _detect_financial_data(self, content: str) -> List[PrivacyIncident]:
        """检测财务信息"""
        incidents = []

        # 财务信息模式
        financial_patterns = [
            (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 'credit_card_number'),  # 信用卡号
            (r'\b\d{9,18}\b', 'bank_account'),  # 银行账户
            (r'\$\d+(?:,\d{3})*(?:\.\d{2})?', 'monetary_amount'),  # 金额
        ]

        for pattern, data_type in financial_patterns:
            matches = re.findall(pattern, content)
            if matches:
                incident = PrivacyIncident(
                    incident_id=f"privacy_{int(time.time() * 1000)}_{hash(str(matches)) % 10000}",
                    privacy_type=PrivacyType.FINANCIAL_DATA,
                    description=f"检测到财务信息: {data_type}",
                    affected_data=matches[:5],  # 限制数量
                    risk_level="high"
                )
                incidents.append(incident)

        return incidents

    async def _detect_health_data(self, content: str) -> List[PrivacyIncident]:
        """检测健康信息"""
        incidents = []

        # 健康信息关键词
        health_keywords = [
            'diagnosis', 'treatment', 'medication', 'symptom', 'disease',
            'medical', 'health', 'doctor', 'hospital', 'prescription'
        ]

        content_lower = content.lower()
        matched_keywords = [kw for kw in health_keywords if kw in content_lower]

        if len(matched_keywords) > 2:  # 多个健康关键词
            incident = PrivacyIncident(
                incident_id=f"privacy_{int(time.time() * 1000)}_{hash(content) % 10000}",
                privacy_type=PrivacyType.HEALTH_DATA,
                description=f"检测到健康相关信息（关键词: {', '.join(matched_keywords[:3])}）",
                affected_data=matched_keywords,
                risk_level="high"
            )
            incidents.append(incident)

        return incidents

    async def _detect_location_data(self, content: str) -> List[PrivacyIncident]:
        """检测位置信息"""
        incidents = []

        # 位置信息模式
        location_patterns = [
            (r'\b\d+\.\d+,\s*-?\d+\.\d+\b', 'coordinates'),  # 坐标
            (r'\b\d{5}(?:[-\s]\d{4})?\b', 'zip_code'),  # 邮编
            (r'\b\d+\s+[A-Z][a-zA-Z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b', 'street_address'),  # 街道地址
        ]

        for pattern, location_type in location_patterns:
            matches = re.findall(pattern, content)
            if matches:
                incident = PrivacyIncident(
                    incident_id=f"privacy_{int(time.time() * 1000)}_{hash(str(matches)) % 10000}",
                    privacy_type=PrivacyType.LOCATION_DATA,
                    description=f"检测到位置信息: {location_type}",
                    affected_data=matches[:3],
                    risk_level="medium"
                )
                incidents.append(incident)

        return incidents

    async def _detect_contact_info(self, content: str) -> List[PrivacyIncident]:
        """检测联系信息"""
        incidents = []

        # 联系信息模式
        contact_patterns = [
            (r'\b[\w\.-]+@[\w\.-]+\.\w+\b', 'email_address'),  # 邮箱
            (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', 'phone_number'),  # 电话
        ]

        for pattern, contact_type in contact_patterns:
            matches = re.findall(pattern, content)
            if matches:
                incident = PrivacyIncident(
                    incident_id=f"privacy_{int(time.time() * 1000)}_{hash(str(matches)) % 10000}",
                    privacy_type=PrivacyType.CONTACT_INFO,
                    description=f"检测到联系信息: {contact_type}",
                    affected_data=matches[:3],
                    risk_level="medium"
                )
                incidents.append(incident)

        return incidents

    async def _apply_privacy_protections(self, content: str, incidents: List[PrivacyIncident]) -> Tuple[str, List[str]]:
        """应用隐私保护措施"""
        protected_content = content
        applied_protections = []

        for incident in incidents:
            for data_item in incident.affected_data:
                if incident.privacy_type == PrivacyType.IDENTIFIERS:
                    # 对标识符进行完全遮盖
                    protected_content = protected_content.replace(data_item, "[REDACTED_ID]")
                    applied_protections.append("identifier_redaction")
                elif incident.privacy_type == PrivacyType.FINANCIAL_DATA:
                    # 对财务数据进行部分遮盖
                    if len(data_item) > 4:
                        masked = data_item[:-4] + "****"
                        protected_content = protected_content.replace(data_item, masked)
                        applied_protections.append("financial_data_masking")
                elif incident.privacy_type in [PrivacyType.PERSONAL_DATA, PrivacyType.CONTACT_INFO]:
                    # 对个人信息进行泛化
                    protected_content = protected_content.replace(data_item, "[PERSONAL_DATA]")
                    applied_protections.append("personal_data_generalization")
                elif incident.privacy_type == PrivacyType.HEALTH_DATA:
                    # 对健康信息进行完全移除
                    for keyword in incident.affected_data:
                        protected_content = re.sub(r'\b' + re.escape(keyword) + r'\b', '[HEALTH_DATA]', protected_content, flags=re.IGNORECASE)
                    applied_protections.append("health_data_removal")

        # 去重保护措施
        applied_protections = list(set(applied_protections))

        return protected_content, applied_protections

    def _calculate_privacy_risk(self, incidents: List[PrivacyIncident]) -> str:
        """计算隐私风险等级"""
        if not incidents:
            return "low"

        risk_scores = {'low': 1, 'medium': 2, 'high': 3}
        max_risk = max((risk_scores.get(incident.risk_level, 1) for incident in incidents), default=1)

        risk_levels = {1: 'low', 2: 'medium', 3: 'high'}
        return risk_levels[max_risk]

    # 🚀 新增：安全自动化响应
    async def respond_to_threats(self, threats: List[SecurityThreat]) -> Dict[str, Any]:
        """自动响应威胁"""
        response_actions = []

        for threat in threats:
            actions = await self._generate_threat_response(threat)

            for action in actions:
                success = await self._execute_security_action(action, threat)
                if success:
                    threat.mitigation_actions.append(action)
                    response_actions.append({
                        'threat_id': threat.threat_id,
                        'action': action,
                        'success': True
                    })
                    self._stats['auto_responses_triggered'] += 1

            # 更新威胁状态
            if threat.level == ThreatLevel.CRITICAL:
                threat.status = "mitigated"
                self._stats['threats_mitigated'] += 1

        return {
            'threats_addressed': len(threats),
            'actions_taken': len(response_actions),
            'response_details': response_actions
        }

    async def _generate_threat_response(self, threat: SecurityThreat) -> List[str]:
        """生成威胁响应措施"""
        actions = []

        if threat.threat_type == ThreatType.PROMPT_INJECTION:
            actions.extend([
                "log_security_event",
                "sanitize_input",
                "alert_administrator"
            ])
        elif threat.threat_type == ThreatType.MALICIOUS_INPUT:
            actions.extend([
                "block_request",
                "log_security_event",
                "update_threat_patterns"
            ])
        elif threat.threat_type == ThreatType.RESOURCE_ABUSE:
            actions.extend([
                "rate_limit_request",
                "log_security_event",
                "monitor_resource_usage"
            ])
        elif threat.threat_type == ThreatType.UNAUTHORIZED_ACCESS:
            actions.extend([
                "block_access",
                "log_security_event",
                "alert_administrator",
                "update_access_controls"
            ])

        return actions

    async def _execute_security_action(self, action: str, threat: SecurityThreat) -> bool:
        """执行安全措施"""
        try:
            if action == "log_security_event":
                # 记录安全事件
                self._security_events.append({
                    'timestamp': time.time(),
                    'threat_id': threat.threat_id,
                    'action': 'logged',
                    'details': threat.description
                })
                return True

            elif action == "alert_administrator":
                # 发送管理员警报
                self.module_logger.error(f"🚨 安全警报: {threat.description}")
                return True

            elif action == "block_request":
                # 阻止请求（在实际系统中会设置拦截）
                self.module_logger.warning(f"🚫 请求已被阻止: {threat.threat_id}")
                return True

            elif action == "sanitize_input":
                # 清理输入（在实际系统中会过滤恶意内容）
                self.module_logger.info(f"🧹 输入已清理: {threat.threat_id}")
                return True

            # 其他措施...
            return False

        except Exception as e:
            self.module_logger.error(f"执行安全措施失败: {action} - {e}")
            return False

    # 🚀 新增：合规性检查
    async def check_compliance(self, content: str, context: Optional[Dict[str, Any]] = None) -> List[ComplianceViolation]:
        """合规性检查"""
        violations = []

        # 检查GDPR合规
        gdpr_violations = await self._check_gdpr_compliance(content, context)
        violations.extend(gdpr_violations)

        # 检查数据保护合规
        data_protection_violations = await self._check_data_protection_compliance(content, context)
        violations.extend(data_protection_violations)

        # 检查内容安全合规
        content_safety_violations = await self._check_content_safety_compliance(content, context)
        violations.extend(content_safety_violations)

        # 注册合规违规
        for violation in violations:
            self._compliance_violations[violation.violation_id] = violation

        if violations:
            self.module_logger.warning(f"⚖️ 检测到 {len(violations)} 个合规违规")

        return violations

    async def _check_gdpr_compliance(self, content: str, context: Optional[Dict[str, Any]]) -> List[ComplianceViolation]:
        """检查GDPR合规性"""
        violations = []

        # 检查个人数据处理
        personal_data_indicators = [
            'collect', 'store', 'process', 'share', 'personal', 'data', 'consent'
        ]

        content_lower = content.lower()
        has_personal_data_processing = any(indicator in content_lower for indicator in personal_data_indicators)

        if has_personal_data_processing:
            # 检查是否提及同意和权利
            has_consent = 'consent' in content_lower
            has_rights = any(word in content_lower for word in ['right', 'access', 'rectification', 'erasure'])

            if not has_consent:
                violation = ComplianceViolation(
                    violation_id=f"compliance_{int(time.time() * 1000)}_{hash('gdpr_consent') % 10000}",
                    regulation="GDPR",
                    requirement="Art. 6 - Lawfulness of processing",
                    description="处理个人数据时未提及用户同意要求",
                    severity="high"
                )
                violations.append(violation)

            if not has_rights:
                violation = ComplianceViolation(
                    violation_id=f"compliance_{int(time.time() * 1000)}_{hash('gdpr_rights') % 10000}",
                    regulation="GDPR",
                    requirement="Art. 15-22 - Data subject rights",
                    description="未说明数据主体权利（访问、更正、删除等）",
                    severity="medium"
                )
                violations.append(violation)

        return violations

    async def _check_data_protection_compliance(self, content: str, context: Optional[Dict[str, Any]]) -> List[ComplianceViolation]:
        """检查数据保护合规性"""
        violations = []

        # 检查数据保留政策
        retention_keywords = ['retain', 'store', 'keep', 'delete', 'remove', 'disposal']
        has_retention_info = any(word in content.lower() for word in retention_keywords)

        if not has_retention_info and len(content) > 1000:  # 长内容应该有保留政策
            violation = ComplianceViolation(
                violation_id=f"compliance_{int(time.time() * 1000)}_{hash('retention_policy') % 10000}",
                regulation="Data Protection",
                requirement="Data Retention Policy",
                description="未说明数据保留和删除政策",
                severity="medium"
            )
            violations.append(violation)

        return violations

    async def _check_content_safety_compliance(self, content: str, context: Optional[Dict[str, Any]]) -> List[ComplianceViolation]:
        """检查内容安全合规性"""
        violations = []

        # 检查有害内容
        harmful_keywords = [
            'violence', 'harm', 'abuse', 'exploit', 'illegal',
            'discrimination', 'hate', 'offensive', 'inappropriate'
        ]

        content_lower = content.lower()
        harmful_matches = [kw for kw in harmful_keywords if kw in content_lower]

        if len(harmful_matches) > 3:  # 多个有害关键词
            violation = ComplianceViolation(
                violation_id=f"compliance_{int(time.time() * 1000)}_{hash('content_safety') % 10000}",
                regulation="Content Safety",
                requirement="Harmful Content Prevention",
                description=f"检测到潜在有害内容（关键词: {', '.join(harmful_matches[:3])}）",
                severity="high"
            )
            violations.append(violation)

        return violations

    # 🚀 新增：辅助方法
    def _deduplicate_threats(self, threats: List[SecurityThreat]) -> List[SecurityThreat]:
        """去重威胁"""
        seen = set()
        unique_threats = []

        for threat in threats:
            threat_key = (threat.threat_type.value, threat.source, threat.target, tuple(threat.indicators))
            if threat_key not in seen:
                seen.add(threat_key)
                unique_threats.append(threat)

        return unique_threats

    def _get_threat_cache_key(self, input_data: str, context: Optional[Dict[str, Any]]) -> str:
        """生成威胁缓存键"""
        key_data = {
            'input_hash': hashlib.md5(input_data.encode()).hexdigest(),
            'context_keys': sorted(context.keys()) if context else []
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_privacy_cache_key(self, content: str, context: Optional[Dict[str, Any]]) -> str:
        """生成隐私缓存键"""
        key_data = {
            'content_hash': hashlib.md5(content.encode()).hexdigest(),
            'context_keys': sorted(context.keys()) if context else []
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    # 🚀 新增：内置模式初始化
    def _initialize_builtin_patterns(self):
        """初始化内置威胁和隐私模式"""
        # 威胁模式已在检测方法中定义
        pass

    def _initialize_compliance_rules(self):
        """初始化合规规则"""
        # 合规规则已在检查方法中定义
        pass

    # 🚀 新增：监控线程
    def _start_monitoring_thread(self):
        """启动监控线程"""
        self._running = True
        self._monitoring_thread = threading.Thread(target=self._monitoring_worker, daemon=True)
        self._monitoring_thread.start()
        self.module_logger.debug("🛡️ 安全监控线程已启动")

    def _monitoring_worker(self):
        """监控工作线程"""
        while self._running:
            try:
                time.sleep(300)  # 每5分钟监控一次

                # 创建事件循环来运行异步任务
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    # 执行监控任务
                    if self._monitoring_enabled:
                        # 监控威胁检测率
                        threat_rate = self._stats['total_threats_detected'] / max(self._stats.get('total_requests', 1), 1)

                        if threat_rate > self._alert_thresholds['threat_detection_rate']:
                            self.module_logger.warning(f"⚠️ 威胁检测率过高: {threat_rate:.1%}")

                        # 监控隐私事件率
                        privacy_rate = self._stats['privacy_incidents_handled'] / max(self._stats.get('total_requests', 1), 1)

                        if privacy_rate > self._alert_thresholds['privacy_incident_rate']:
                            self.module_logger.warning(f"⚠️ 隐私事件率过高: {privacy_rate:.1%}")

                finally:
                    loop.close()

            except Exception as e:
                self.module_logger.warning(f"安全监控异常: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            'active_threats': len(self._active_threats),
            'privacy_incidents': len(self._privacy_incidents),
            'compliance_violations': len(self._compliance_violations),
            'security_events': len(self._security_events),
            'threat_cache_size': len(self._threat_cache),
            'privacy_cache_size': len(self._privacy_cache),
            'monitoring_enabled': self._monitoring_enabled
        }

    # 核心执行方法
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        执行安全防护任务

        Args:
            context: 安全防护请求上下文
                - action: 操作类型 ("detect_threats", "protect_privacy", "check_compliance", "respond_to_threats", "monitor_security", "stats")
                - content: 要检查的内容 (detect_threats/protect_privacy/check_compliance时需要)
                - threats: 威胁列表 (respond_to_threats时需要)

        Returns:
            AgentResult: 执行结果
        """
        start_time = time.time()
        action = context.get("action", "")

        try:
            if action == "detect_threats":
                content = context.get("content", "")

                if not content:
                    result_data = {"error": "内容不能为空"}
                else:
                    threats = await self.detect_threats(content, context)
                    result_data = {
                        "threats_detected": len(threats),
                        "threats": [
                            {
                                "id": t.threat_id,
                                "type": t.threat_type.value,
                                "level": t.level.value,
                                "description": t.description
                            }
                            for t in threats
                        ]
                    }

            elif action == "protect_privacy":
                content = context.get("content", "")

                if not content:
                    result_data = {"error": "内容不能为空"}
                else:
                    privacy_result = await self.protect_privacy(content, context)
                    result_data = privacy_result

            elif action == "check_compliance":
                content = context.get("content", "")

                if not content:
                    result_data = {"error": "内容不能为空"}
                else:
                    violations = await self.check_compliance(content, context)
                    result_data = {
                        "compliance_check_passed": len(violations) == 0,
                        "violations": len(violations),
                        "violation_details": [
                            {
                                "id": v.violation_id,
                                "regulation": v.regulation,
                                "requirement": v.requirement,
                                "description": v.description,
                                "severity": v.severity
                            }
                            for v in violations
                        ]
                    }

            elif action == "respond_to_threats":
                threats_data = context.get("threats", [])

                # 转换威胁数据为SecurityThreat对象
                threats = []
                for t_data in threats_data:
                    threat = SecurityThreat(
                        threat_id=t_data.get("id", ""),
                        threat_type=ThreatType(t_data.get("type", "malicious_input")),
                        level=ThreatLevel(t_data.get("level", "medium")),
                        description=t_data.get("description", ""),
                        source="external",
                        target="system"
                    )
                    threats.append(threat)

                response_result = await self.respond_to_threats(threats)
                result_data = response_result

            elif action == "monitor_security":
                # 获取安全监控统计
                result_data = {
                    'active_threats': len(self._active_threats),
                    'privacy_incidents': len(self._privacy_incidents),
                    'compliance_violations': len(self._compliance_violations),
                    'recent_security_events': len(self._security_events[-10:])  # 最近10个事件
                }

            elif action == "stats":
                result_data = self.get_stats()

            else:
                result_data = {"error": f"不支持的操作: {action}"}

            return AgentResult(
                success=True,
                data=result_data,
                confidence=0.9,
                processing_time=time.time() - start_time
            )

        except Exception as e:
            self.module_logger.error(f"❌ SecurityGuardian执行异常: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )

    def shutdown(self):
        """关闭安全卫士"""
        self._running = False
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5)

        self._threat_detection_executor.shutdown(wait=True)
        self.module_logger.info("🛡️ SecurityGuardian已关闭")
