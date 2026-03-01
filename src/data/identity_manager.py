#!/usr/bin/env python3
"""
身份管理器 - 实现模糊匹配用户认证和数据集成
"""

import os
import logging
import time
import hashlib
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import difflib
import re


class IdentityType(Enum):
    """身份类型"""
    USER = "user"
    SYSTEM = "system"
    API = "api"
    BOT = "bot"
    GUEST = "guest"


class AuthMethod(Enum):
    """认证方法"""
    PASSWORD = "password"
    TOKEN = "token"
    BIOMETRIC = "biometric"
    SSO = "sso"
    OAUTH = "oauth"
    API_KEY = "api_key"


@dataclass
class UserIdentity:
    """用户身份"""
    identity_id: str
    username: str
    email: str
    phone: Optional[str]
    identity_type: IdentityType
    auth_methods: List[AuthMethod]
    created_at: float
    last_login: float
    is_active: bool
    metadata: Dict[str, Any]
    aliases: List[str]
    fuzzy_identifiers: List[str]


@dataclass
class AuthSession:
    """认证会话"""
    session_id: str
    identity_id: str
    auth_method: AuthMethod
    created_at: float
    expires_at: float
    is_valid: bool
    ip_address: str
    user_agent: str
    metadata: Dict[str, Any]


class IdentityManager:
    """身份管理器"""
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.identities = {}
        self.default_token = "default_token_123"
        self.fuzzy_index = {}
        self.active_sessions = {}
        self._init_default_identity()
    
    def _init_default_identity(self):
        """初始化默认身份"""
        try:
            # 系统身份
            system_identity = UserIdentity(
                identity_id="system_001",
                username="system",
                email="system@rangen.ai",
                phone=None,
                identity_type=IdentityType.SYSTEM,
                auth_methods=[AuthMethod.API_KEY],
                created_at=time.time(),
                last_login=time.time(),
                is_active=True,
                metadata={"role": "system", "permissions": ["all"]},
                aliases=["sys", "admin"],
                fuzzy_identifiers=["system", "sys", "admin", "root"]
            )
            
            self.identities["system_001"] = system_identity
            self._update_fuzzy_index(system_identity)
            
            # 匿名用户身份
            anonymous_identity = UserIdentity(
                identity_id="anonymous_001",
                username="anonymous",
                email=None,
                phone=None,
                identity_type=IdentityType.ANONYMOUS,
                auth_methods=[AuthMethod.SESSION],
                created_at=time.time(),
                last_login=time.time(),
                is_active=True,
                metadata={"role": "guest", "permissions": ["read"]},
                aliases=["guest", "visitor"],
                fuzzy_identifiers=["anonymous", "guest", "visitor"]
            )
            
            self.identities["anonymous_001"] = anonymous_identity
            self._update_fuzzy_index(anonymous_identity)
            
            self.logger.info("默认身份初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化默认身份失败: {e}")
    
    def create_identity(self, username: str, email: str = None, phone: str = None, 
                       identity_type: IdentityType = IdentityType.USER) -> Optional[str]:
        """创建新身份"""
        try:
            # 验证输入
            if not self._validate_identity_input(username, email, phone):
                return None
            
            # 生成身份ID
            identity_id = self._generate_identity_id(username)
            
            # 检查是否已存在
            if identity_id in self.identities:
                self.logger.warning(f"身份已存在: {identity_id}")
                return None
            
            # 创建身份
            identity = UserIdentity(
                identity_id=identity_id,
                username=username,
                email=email,
                phone=phone,
                identity_type=identity_type,
                auth_methods=[AuthMethod.PASSWORD],
                created_at=time.time(),
                last_login=time.time(),
                is_active=True,
                metadata={"role": "user", "permissions": ["read", "write"]},
                aliases=[],
                fuzzy_identifiers=self._generate_fuzzy_identifiers(username, email, phone)
            )
            
            # 保存身份
            self.identities[identity_id] = identity
            self._update_fuzzy_index(identity)
            
            self.logger.info(f"创建身份成功: {identity_id}")
            return identity_id
            
        except Exception as e:
            self.logger.error(f"创建身份失败: {e}")
            return None
    
    def _validate_identity_input(self, username: str, email: str = None, phone: str = None) -> bool:
        """验证身份输入"""
        if not username or not username.strip():
            return False
        
        if email and not self._is_valid_email(email):
            return False
        
        if phone and not self._is_valid_phone(phone):
            return False
        
        return True
    
    def _is_valid_email(self, email: str) -> bool:
        """验证邮箱格式"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_valid_phone(self, phone: str) -> bool:
        """验证手机号格式"""
        import re
        pattern = r'^\+?1?\d{9,15}$'
        return re.match(pattern, phone) is not None
    
    def _generate_identity_id(self, username: str) -> str:
        """生成身份ID"""
        import hashlib
        timestamp = str(int(time.time()))
        data = f"{username}_{timestamp}"
        return hashlib.md5(data.encode()).hexdigest()[:12]
    
    def register_identity(self, username: str, email: str, identity_type: IdentityType,
                         phone: Optional[str] = None, auth_methods: Optional[List[AuthMethod]] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """注册身份"""
        try:
            identity_id = f"value"
            
            # 生成模糊标识符
            fuzzy_identifiers = self._generate_fuzzy_identifiers(username, email, phone or "")
            
            identity = UserIdentity(
                identity_id=identity_id,
                username=username,
                email=email,
                phone=phone,
                identity_type=identity_type,
                auth_methods=auth_methods or [AuthMethod.PASSWORD],
                created_at=time.time(),
                last_login=0.0,
                is_active=True,
                metadata=metadata or {},
                aliases=[],
                fuzzy_identifiers=fuzzy_identifiers
            )
            
            self.identities[identity_id] = identity
            self._update_fuzzy_index(identity)
            
            self.logger.info(f"注册身份: {identity_id} - {username}")
            return identity_id
            
        except Exception as e:
            self.logger.error(f"注册身份失败: {e}")
            return ""
    
    def _generate_fuzzy_identifiers(self, username: str, email: str, phone: str) -> List[str]:
        """生成模糊标识符"""
        identifiers = []
        
        # 用户名变体
        identifiers.append(username.lower())
        identifiers.append(username.replace("_", ""))
        identifiers.append(username.replace("-", ""))
        identifiers.append(username.replace(".", ""))
        
        # 邮箱变体
        if email:
            local_part = email.split("@")[0]
            identifiers.append(local_part.lower())
            identifiers.append(local_part.replace("_", ""))
            identifiers.append(local_part.replace("-", ""))
            identifiers.append(local_part.replace(".", ""))
        
        # 电话号码变体
        if phone:
            clean_phone = re.sub(r"[^\d]", "", phone)
            identifiers.append(clean_phone)
            if len(clean_phone) > 4:
                identifiers.append(clean_phone[-4:])  # 后4位
                identifiers.append(clean_phone[-8:])  # 后8位
        
        # 去重并过滤空值
        identifiers = list(set([id for id in identifiers if id]))
        
        return identifiers
    
    def fuzzy_match_identity(self, query: str, threshold: float = 0.6) -> List[Tuple[str, float]]:
        """模糊匹配身份"""
        matches = []
        
        # 清理查询
        clean_query = query.lower().strip()
        
        # 在模糊索引中搜索
        for identifier, identity_ids in self.fuzzy_index.items():
            similarity = difflib.SequenceMatcher(None, clean_query, identifier).ratio()
            if similarity >= threshold:
                for identity_id in identity_ids:
                    matches.append((identity_id, similarity))
        
        # 按相似度排序
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches
    
    def authenticate(self, identifier: str, auth_method: AuthMethod, 
                    credentials: Dict[str, Any]) -> Optional[str]:
        """认证用户"""
        try:
            # 模糊匹配身份
            matches = self.fuzzy_match_identity(identifier)
            if not matches:
                self.logger.warning(f"未找到匹配的身份: {identifier}")
                return None
            
            # 选择最佳匹配
            identity_id, similarity = matches[0]
            identity = self.identities.get(identity_id)
            
            if not identity or not identity.is_active:
                self.logger.warning(f"身份无效或已禁用: {identity_id}")
                return None
            
            # 检查认证方法
            if auth_method not in identity.auth_methods:
                self.logger.warning(f"不支持的认证方法: {auth_method.value}")
                return None
            
            # 执行认证
            if self._perform_authentication(identity, auth_method, credentials):
                # 创建会话
                session_id = self._create_session(identity_id, auth_method, credentials)
                
                # 更新最后登录时间
                identity.last_login = time.time()
                
                self.logger.info(f"认证成功: {identity_id} - {auth_method.value}")
                return session_id
            else:
                self.logger.warning(f"认证失败: {identity_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"认证失败: {e}")
            return None
    
    def _perform_authentication(self, identity: UserIdentity, auth_method: AuthMethod,
                              credentials: Dict[str, Any]) -> bool:
        """执行认证"""
        if auth_method == AuthMethod.PASSWORD:
            return self._authenticate_password(identity, credentials)
        elif auth_method == AuthMethod.TOKEN:
            return self._authenticate_token(identity, credentials)
        elif auth_method == AuthMethod.API_KEY:
            return self._authenticate_api_key(identity, credentials)
        elif auth_method == AuthMethod.SSO:
            return self._authenticate_sso(identity, credentials)
        else:
            return False
    
    def _authenticate_password(self, identity: UserIdentity, credentials: Dict[str, Any]) -> bool:
        """密码认证"""
        password = credentials.get("password", "")
        stored_hash = identity.metadata.get("password_hash", "")
        salt = identity.metadata.get("password_salt", "")
        
        if not stored_hash or not salt:
            return False
        
        # 使用PBKDF2进行密码哈希验证
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 迭代次数
        ).hex()
        
        return password_hash == stored_hash
    
    def _authenticate_token(self, identity: UserIdentity, credentials: Dict[str, Any]) -> bool:
        """令牌认证"""
        token = credentials.get("token", "")
        valid_tokens = identity.metadata.get("valid_tokens", [])
        
        return token in valid_tokens
    
    def _authenticate_api_key(self, identity: UserIdentity, credentials: Dict[str, Any]) -> bool:
        """API密钥认证"""
        api_key = credentials.get("api_key", "")
        valid_keys = identity.metadata.get("valid_api_keys", [])
        
        return api_key in valid_keys
    
    def _authenticate_sso(self, identity: UserIdentity, credentials: Dict[str, Any]) -> bool:
        """SSO认证"""
        sso_token = credentials.get("sso_token", "")
        sso_provider = credentials.get("provider", "")
        
        if not sso_token or not sso_provider:
            return False
        
        # 验证SSO令牌
        return self._verify_sso_token(sso_token, sso_provider, identity)
    
    def _verify_sso_token(self, token: str, provider: str, identity: UserIdentity) -> bool:
        """验证SSO令牌"""
        try:
            # 这里应该与实际的SSO提供商集成
            # 简化实现，实际应用中需要调用相应的API
            if provider == "google":
                return self._verify_google_token(token)
            elif provider == "microsoft":
                return self._verify_microsoft_token(token)
            elif provider == "github":
                return self._verify_github_token(token)
            else:
                return False
        except Exception as e:
            self.logger.error(f"SSO令牌验证失败: {e}")
            return False
    
    def _verify_google_token(self, token: str) -> bool:
        """验证Google令牌"""
        # 简化实现，实际应用中需要调用Google API
        return len(token) > 10
    
    def _verify_microsoft_token(self, token: str) -> bool:
        """验证Microsoft令牌"""
        # 简化实现，实际应用中需要调用Microsoft Graph API
        return len(token) > 10
    
    def _verify_github_token(self, token: str) -> bool:
        """验证GitHub令牌"""
        # 简化实现，实际应用中需要调用GitHub API
        return len(token) > 10
    
    def _create_session(self, identity_id: str, auth_method: AuthMethod,
                       credentials: Dict[str, Any]) -> str:
        """创建会话"""
        session_id = f"value"
        
        session = AuthSession(
            session_id=session_id,
            identity_id=identity_id,
            auth_method=auth_method,
            created_at=time.time(),
            expires_at=time.time() + 3600,  # 1小时过期
            is_valid=True,
            ip_address=credentials.get("ip_address", ""),
            user_agent=credentials.get("user_agent", ""),
            metadata=credentials.get("metadata", {})
        )
        
        self.active_sessions[session_id] = session
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[UserIdentity]:
        """验证会话"""
        session = self.active_sessions.get(session_id)
        
        if not session or not session.is_valid:
            return None
        
        if time.time() > session.expires_at:
            session.is_valid = False
            return None
        
        return self.identities.get(session.identity_id)
    
    def invalidate_session(self, session_id: str) -> bool:
        """使会话失效"""
        session = self.active_sessions.get(session_id)
        if session:
            session.is_valid = False
            self.logger.info(f"会话失效: {session_id}")
            return True
        return False
    
    def add_alias(self, identity_id: str, alias: str) -> bool:
        """添加别名"""
        identity = self.identities.get(identity_id)
        if not identity:
            return False
        
        if alias not in identity.aliases:
            identity.aliases.append(alias)
            identity.fuzzy_identifiers.append(alias.lower())
            self._update_fuzzy_index(identity)
            
            self.logger.info(f"添加别名: {identity_id} - {alias}")
            return True
        
        return False
    
    def _update_fuzzy_index(self, identity: UserIdentity):
        """更新模糊索引"""
        for identifier in identity.fuzzy_identifiers:
            if identifier not in self.fuzzy_index:
                self.fuzzy_index[identifier] = []
            if identity.identity_id not in self.fuzzy_index[identifier]:
                self.fuzzy_index[identifier].append(identity.identity_id)
    
    def get_identity(self, identity_id: str) -> Optional[Dict[str, Any]]:
        """获取身份信息"""
        identity = self.identities.get(identity_id)
        if not identity:
            return None
        
        return {
            "identity_id": identity.identity_id,
            "username": identity.username,
            "email": identity.email,
            "phone": identity.phone,
            "identity_type": identity.identity_type.value,
            "auth_methods": [method.value for method in identity.auth_methods],
            "created_at": identity.created_at,
            "last_login": identity.last_login,
            "is_active": identity.is_active,
            "aliases": identity.aliases,
            "metadata": identity.metadata
        }
    
    def search_identities(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索身份"""
        matches = self.fuzzy_match_identity(query)
        
        results = []
        for identity_id, similarity in matches[:limit]:
            identity = self.identities.get(identity_id)
            if identity:
                result = self.get_identity(identity_id)
                if result:
                    result["similarity"] = similarity
                    results.append(result)
        
        return results
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """获取活跃会话"""
        sessions = []
        for session in self.active_sessions.values():
            if session.is_valid and time.time() <= session.expires_at:
                sessions.append({
                    "session_id": session.session_id,
                    "identity_id": session.identity_id,
                    "auth_method": session.auth_method.value,
                    "created_at": session.created_at,
                    "expires_at": session.expires_at,
                    "ip_address": session.ip_address,
                    "user_agent": session.user_agent
                })
        
        return sessions
    
    def export_identities(self, file_path: str) -> bool:
        """导出身份数据"""
        try:
            data = {
                "identities": [identity.__dict__ for identity in self.identities.values()],
                "active_sessions": [session.__dict__ for session in self.active_sessions.values()],
                "exported_at": time.time()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"身份数据已导出到: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出身份数据失败: {e}")
            return False


# 全局实例
identity_manager = IdentityManager()


def get_identity_manager():
    """获取身份管理器实例"""
    return identity_manager