"""
Security Control Service - Outbound confirmation, whitelist, account protection
"""
import os
import hashlib
import time
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class SecurityLevel(str, Enum):
    """安全级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ConfirmationStatus(str, Enum):
    """确认状态"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


# 敏感关键词
SENSITIVE_KEYWORDS = [
    "password", "secret", "token", "api_key", "apikey",
    "auth", "credential", "private_key", "ssh-rsa",
    "Bearer ", "Basic ", "token=", "key=",
    "信用卡", "银行卡", "身份证", "密码", "密钥"
]

# 允许的外发目的地类型
ALLOWED_DESTINATION_TYPES = [
    "api",      # API调用
    "webhook",  # Webhook
    "email",   # 邮件
    "sms",     # 短信
]


@dataclass
class OutboundRequest:
    """外发请求"""
    request_id: str
    destination: str
    destination_type: str
    content_preview: str
    contains_sensitive: bool
    sensitive_keywords_found: List[str] = field(default_factory=list)
    status: ConfirmationStatus = ConfirmationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None


@dataclass
class WhitelistEntry:
    """白名单条目"""
    id: str
    pattern: str  # 支持通配符
    pattern_type: str  # domain, ip, url
    description: str
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)


class SecurityController:
    """安全控制器 - 外发确认、白名单、账户保护"""
    
    def __init__(self):
        self._outbound_requests: Dict[str, OutboundRequest] = {}
        self._whitelist: Dict[str, WhitelistEntry] = {}
        self._security_level = SecurityLevel.MEDIUM
        self._confirmation_timeout = 300  # 5分钟超时
        self._api_key_hash: Optional[str] = None
        
        # 默认白名单
        self._init_default_whitelist()
    
    def _init_default_whitelist(self):
        """初始化默认白名单"""
        default_entries = [
            WhitelistEntry(
                id="wl_1",
                pattern="*.openai.com",
                pattern_type="domain",
                description="OpenAI API"
            ),
            WhitelistEntry(
                id="wl_2",
                pattern="*.deepseek.com",
                pattern_type="domain",
                description="DeepSeek API"
            ),
            WhitelistEntry(
                id="wl_3",
                pattern="*.anthropic.com",
                pattern_type="domain",
                description="Anthropic API"
            ),
        ]
        
        for entry in default_entries:
            self._whitelist[entry.id] = entry
    
    def set_security_level(self, level: str):
        """设置安全级别"""
        try:
            self._security_level = SecurityLevel(level)
            logger.info(f"Security level set to: {self._security_level.value}")
        except ValueError:
            logger.warning(f"Invalid security level: {level}")
    
    def check_sensitive_content(self, content: str) -> tuple[bool, List[str]]:
        """检查敏感内容"""
        content_lower = content.lower()
        found_keywords = []
        
        for keyword in SENSITIVE_KEYWORDS:
            if keyword.lower() in content_lower:
                found_keywords.append(keyword)
        
        return len(found_keywords) > 0, found_keywords
    
    def check_whitelist(self, destination: str) -> tuple[bool, str]:
        """检查目标是否在白名单中"""
        # 简单实现：检查域名匹配
        for entry in self._whitelist.values():
            if not entry.enabled:
                continue
            
            if entry.pattern_type == "domain":
                # 支持通配符
                pattern = entry.pattern.replace("*", "")
                if pattern in destination:
                    return True, entry.description
        
        return False, "Not in whitelist"
    
    def create_outbound_request(
        self,
        destination: str,
        destination_type: str,
        content: str
    ) -> OutboundRequest:
        """创建外发请求"""
        # 检查敏感内容
        contains_sensitive, keywords = self.check_sensitive_content(content)
        
        # 检查白名单
        in_whitelist, whitelist_info = self.check_whitelist(destination)
        
        # 生成请求ID
        request_id = f"out_{hashlib.md5(f'{destination}{time.time()}'.encode()).hexdigest()[:12]}"
        
        request = OutboundRequest(
            request_id=request_id,
            destination=destination,
            destination_type=destination_type,
            content_preview=content[:100] + "..." if len(content) > 100 else content,
            contains_sensitive=contains_sensitive,
            sensitive_keywords_found=keywords,
            expires_at=datetime.fromtimestamp(time.time() + self._confirmation_timeout)
        )
        
        # 如果安全级别为LOW且不在白名单，直接拒绝
        if self._security_level == SecurityLevel.LOW and not in_whitelist:
            request.status = ConfirmationStatus.REJECTED
        
        # 如果包含敏感内容，需要确认
        if contains_sensitive and self._security_level != SecurityLevel.LOW:
            request.status = ConfirmationStatus.PENDING
        elif not in_whitelist:
            request.status = ConfirmationStatus.PENDING
        
        self._outbound_requests[request_id] = request
        
        logger.info(f"Outbound request created: {request_id}, "
                   f"sensitive={contains_sensitive}, whitelist={in_whitelist}")
        
        return request
    
    def confirm_outbound(self, request_id: str, approved: bool, confirmed_by: str = "admin") -> bool:
        """确认外发请求"""
        if request_id not in self._outbound_requests:
            logger.warning(f"Outbound request not found: {request_id}")
            return False
        
        request = self._outbound_requests[request_id]
        
        # 检查是否过期
        if request.expires_at and datetime.now() > request.expires_at:
            request.status = ConfirmationStatus.EXPIRED
            logger.warning(f"Outbound request expired: {request_id}")
            return False
        
        if approved:
            request.status = ConfirmationStatus.APPROVED
            request.confirmed_by = confirmed_by
            request.confirmed_at = datetime.now()
            logger.info(f"Outbound request approved: {request_id} by {confirmed_by}")
        else:
            request.status = ConfirmationStatus.REJECTED
            logger.info(f"Outbound request rejected: {request_id} by {confirmed_by}")
        
        return True
    
    def get_outbound_status(self, request_id: str) -> Optional[OutboundRequest]:
        """获取外发请求状态"""
        return self._outbound_requests.get(request_id)
    
    def can_proceed(self, destination: str, content: str) -> tuple[bool, Optional[str]]:
        """快速检查是否可以继续（不创建请求）"""
        # 检查敏感内容
        contains_sensitive, keywords = self.check_sensitive_content(content)
        
        # 检查白名单
        in_whitelist, whitelist_info = self.check_whitelist(destination)
        
        # 根据安全级别决定
        if self._security_level == SecurityLevel.LOW:
            if not in_whitelist:
                return False, f"Not in whitelist: {whitelist_info}"
        
        if self._security_level == SecurityLevel.HIGH:
            if contains_sensitive:
                return False, f"Contains sensitive keywords: {', '.join(keywords)}"
            if not in_whitelist:
                return False, f"Not in whitelist: {whitelist_info}"
        
        if contains_sensitive and not in_whitelist:
            return False, "Requires confirmation"
        
        return True, None
    
    # ========== Whitelist Management ==========
    
    def add_whitelist(self, pattern: str, pattern_type: str, description: str) -> WhitelistEntry:
        """添加白名单"""
        entry_id = f"wl_{hashlib.md5(pattern.encode()).hexdigest()[:8]}"
        
        entry = WhitelistEntry(
            id=entry_id,
            pattern=pattern,
            pattern_type=pattern_type,
            description=description
        )
        
        self._whitelist[entry_id] = entry
        logger.info(f"Whitelist entry added: {pattern}")
        
        return entry
    
    def remove_whitelist(self, entry_id: str) -> bool:
        """移除白名单"""
        if entry_id in self._whitelist:
            del self._whitelist[entry_id]
            logger.info(f"Whitelist entry removed: {entry_id}")
            return True
        return False
    
    def get_whitelist(self) -> List[WhitelistEntry]:
        """获取白名单"""
        return list(self._whitelist.values())
    
    # ========== Account Protection ==========
    
    def protect_api_key(self, api_key: str) -> str:
        """保护API密钥（存储哈希）"""
        self._api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        logger.info("API key hash stored")
        return self._api_key_hash[:8] + "..."  # 返回掩码版本
    
    def verify_api_key(self, api_key: str) -> bool:
        """验证API密钥"""
        if not self._api_key_hash:
            return True  # 未设置则通过
        
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        return key_hash == self._api_key_hash
    
    def get_security_status(self) -> Dict[str, Any]:
        """获取安全状态"""
        pending_requests = [
            r for r in self._outbound_requests.values()
            if r.status == ConfirmationStatus.PENDING
        ]
        
        return {
            "security_level": self._security_level.value,
            "pending_requests": len(pending_requests),
            "whitelist_entries": len(self._whitelist),
            "api_key_protected": self._api_key_hash is not None
        }


# Global instance
_security_controller: Optional[SecurityController] = None


def get_security_controller() -> SecurityController:
    """获取安全控制器实例"""
    global _security_controller
    if _security_controller is None:
        _security_controller = SecurityController()
    return _security_controller
