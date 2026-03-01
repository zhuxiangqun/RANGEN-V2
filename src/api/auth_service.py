"""
Unified Authentication Service
整合JWT/OAuth2身份验证系统，支持数据库存储和统一安全中心
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from fastapi import HTTPException, Security, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from src.api.models_auth import get_auth_database, AuthDatabase
from src.services.logging_service import get_logger
from src.utils.security_utils import SecurityUtils
from src.services.audit_log_service import (
    AuditEventType, AuditSeverity, AuditSource, 
    get_audit_logger, log_auth_event, log_security_alert
)

logger = get_logger("auth_service")

# Configuration
SECRET_KEY = os.getenv("RANGEN_SECRET_KEY")
if not SECRET_KEY:
    logger.warning("RANGEN_SECRET_KEY not set, generating temporary key")
    SECRET_KEY = secrets.token_urlsafe(32)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours default
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

# Security contexts
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

# Global instances
security_utils = SecurityUtils()
auth_db = get_auth_database()


class AuthService:
    """统一认证服务"""
    
    def __init__(self):
        self.db = auth_db
    
    # JWT Token Methods
    def create_access_token(
        self, 
        data: dict, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建JWT访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(
        self, 
        data: dict, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建JWT刷新令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """验证JWT令牌并返回载荷"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            logger.warning(f"JWT验证失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌无效或已过期",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # User Management
    def create_user(
        self, 
        username: str, 
        password: Optional[str] = None,
        email: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """创建新用户"""
        # 验证用户名
        if not username or len(username) < 3:
            raise ValueError("用户名必须至少3个字符")
        
        # 如果提供密码，进行哈希处理
        password_hash = None
        salt = None
        if password:
            salt = secrets.token_bytes(32)
            password_hash = self.hash_password(password, salt)
        
        # 创建用户
        user_data = self.db.create_user(
            username=username,
            email=email,
            password_hash=password_hash.hex() if password_hash else None,
            salt=salt.hex() if salt else None,
            **kwargs
        )
        
        logger.info(f"用户创建成功: {username}")
        return user_data
    
    def authenticate_user(
        self, 
        username: str, 
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """验证用户凭据"""
        user = self.db.get_user_by_username(username)
        if not user:
            # 记录登录失败事件（用户不存在）
            log_auth_event(
                event_type=AuditEventType.LOGIN_FAILURE,
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                error_message="用户不存在",
                context={"username": username}
            )
            return None
        
        # 检查用户是否活跃
        if not user.get('is_active', True):
            # 记录登录失败事件（用户不活跃）
            log_auth_event(
                event_type=AuditEventType.LOGIN_FAILURE,
                user_id=user.get('user_id'),
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                error_message="用户账户已停用",
                context={"username": username, "user_id": user.get('user_id')}
            )
            return None
        
        # 验证密码
        password_hash = user.get('password_hash')
        salt = user.get('salt')
        
        if not password_hash or not salt:
            # 用户没有设置密码（例如使用API密钥认证）
            # 记录登录失败事件（无密码设置）
            log_auth_event(
                event_type=AuditEventType.LOGIN_FAILURE,
                user_id=user.get('user_id'),
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                error_message="用户未设置密码",
                context={"username": username, "user_id": user.get('user_id')}
            )
            return None
        
        try:
            salt_bytes = bytes.fromhex(salt)
            input_hash = self.hash_password(password, salt_bytes)
            
            if input_hash.hex() == password_hash:
                # 更新最后登录时间
                self.db.update_user_last_login(user['user_id'])
                
                # 记录登录成功事件
                log_auth_event(
                    event_type=AuditEventType.LOGIN_SUCCESS,
                    user_id=user.get('user_id'),
                    username=username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=True,
                    context={"username": username, "user_id": user.get('user_id')}
                )
                
                return user
            else:
                # 密码不匹配
                log_auth_event(
                    event_type=AuditEventType.LOGIN_FAILURE,
                    user_id=user.get('user_id'),
                    username=username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    error_message="密码错误",
                    context={"username": username, "user_id": user.get('user_id')}
                )
        except Exception as e:
            logger.error(f"密码验证失败: {e}")
            # 记录登录失败事件（验证异常）
            log_auth_event(
                event_type=AuditEventType.LOGIN_FAILURE,
                user_id=user.get('user_id'),
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                error_message=f"密码验证异常: {str(e)}",
                context={"username": username, "user_id": user.get('user_id'), "error": str(e)}
            )
        
        return None
    
    # API Key Management
    def generate_api_key(self) -> str:
        """生成新的API密钥"""
        return f"rang_{secrets.token_urlsafe(32)}"
    
    def hash_api_key(self, api_key: str) -> str:
        """哈希API密钥用于存储"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def create_api_key(
        self, 
        name: str, 
        user_id: Optional[str] = None,
        permissions: List[str] = None,
        expires_in_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """创建新的API密钥"""
        api_key_data = self.db.create_api_key(
            name=name,
            user_id=user_id,
            permissions=permissions,
            expires_in_days=expires_in_days
        )
        
        logger.info(f"API密钥创建成功: {name}")
        return api_key_data
    
    def verify_api_key(self, api_key: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """验证API密钥并返回密钥信息"""
        key_info = self.db.verify_api_key(api_key)
        
        if key_info:
            # 记录API密钥使用成功事件
            audit_logger = get_audit_logger()
            audit_logger.log_api_key_event(
                event_type=AuditEventType.API_KEY_USAGE,
                api_key_id=api_key,
                user_id=key_info.get('user_id'),
                ip_address=ip_address,
                success=True,
                context={
                    "api_key": api_key[:8] + "...",
                    "name": key_info.get('name'),
                    "permissions": key_info.get('permissions'),
                    "ip_address": ip_address,
                    "user_agent": user_agent
                }
            )
        else:
            # 记录API密钥验证失败事件
            log_security_alert(
                message=f"无效的API密钥尝试: {api_key[:8]}...",
                severity=AuditSeverity.WARNING,
                ip_address=ip_address,
                context={
                    "api_key_attempt": api_key[:8] + "...",
                    "ip_address": ip_address,
                    "user_agent": user_agent
                }
            )
        
        return key_info
    
    # Session Management
    def create_session(
        self, 
        user_id: str, 
        token: str,
        request: Optional[Request] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """创建新会话"""
        device_info = {}
        ip_address = None
        user_agent = None
        
        if request:
            # 从请求中提取设备信息
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
            
            device_info = {
                "ip_address": ip_address,
                "user_agent": user_agent,
                "method": request.method,
                "path": request.url.path
            }
        
        session_data = self.db.create_session(
            user_id=user_id,
            token=token,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
            **kwargs
        )
        
        logger.info(f"会话创建成功: {session_data['session_id'][:8]}...")
        return session_data
    
    # Password Management
    def hash_password(self, password: str, salt: bytes = None) -> bytes:
        """哈希密码"""
        if salt is None:
            salt = secrets.token_bytes(32)
        
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt,
            100000
        )
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """验证密码"""
        try:
            salt_bytes = bytes.fromhex(salt)
            input_hash = self.hash_password(password, salt_bytes)
            stored_hash = bytes.fromhex(hashed_password)
            
            return input_hash == stored_hash
        except Exception:
            return False
    
    # Token Refresh
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """使用刷新令牌获取新的访问令牌"""
        try:
            payload = self.verify_token(refresh_token)
            
            # 检查令牌类型
            if payload.get("type") != "refresh":
                logger.warning("令牌类型错误，期望刷新令牌")
                return None
            
            # 检查用户ID
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            # 创建新的访问令牌
            new_token_data = {
                "sub": user_id,
                "permissions": payload.get("permissions", ["read", "write"]),
                "type": "access"
            }
            
            return self.create_access_token(new_token_data)
            
        except HTTPException:
            return None
    
    # Permission Management
    def check_permission(
        self, 
        user_or_key_info: Dict[str, Any], 
        required_permission: str
    ) -> bool:
        """检查用户或API密钥是否具有所需权限"""
        permissions = user_or_key_info.get("permissions", [])
        
        # 管理员拥有所有权限
        if user_or_key_info.get("is_admin", False):
            return True
        
        # 检查特定权限
        return required_permission in permissions
    
    # OAuth2 Support
    def create_oauth2_token(
        self,
        client_id: str,
        user_id: str,
        scope: List[str] = None,
        expires_in: int = 3600  # 1 hour default
    ) -> Dict[str, Any]:
        """创建OAuth2令牌"""
        if scope is None:
            scope = ["read", "write"]
        
        access_token = self.create_access_token({
            "sub": user_id,
            "client_id": client_id,
            "scope": scope,
            "type": "oauth2"
        })
        
        refresh_token = self.create_refresh_token({
            "sub": user_id,
            "client_id": client_id,
            "scope": scope,
            "type": "oauth2_refresh"
        })
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "refresh_token": refresh_token,
            "scope": " ".join(scope)
        }
    
    # Utility Methods
    def get_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """从令牌中获取用户信息"""
        try:
            payload = self.verify_token(token)
            user_id = payload.get("sub")
            
            if not user_id:
                return None
            
            # 这里可以添加数据库查询获取完整用户信息
            # 目前只返回令牌中的基本信息
            return {
                "user_id": user_id,
                "permissions": payload.get("permissions", ["read", "write"]),
                "token_type": payload.get("type", "access")
            }
        except HTTPException:
            return None


# 全局服务实例
_auth_service_instance = None

def get_auth_service() -> AuthService:
    """获取全局认证服务实例"""
    global _auth_service_instance
    if _auth_service_instance is None:
        _auth_service_instance = AuthService()
    return _auth_service_instance


# FastAPI依赖项
async def verify_authentication(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    request: Optional[Request] = None
) -> Dict[str, Any]:
    """验证认证凭据（API密钥或JWT令牌）"""
    auth_service = get_auth_service()
    
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # 检查是否是API密钥（以"rang_"开头）
    if token.startswith("rang_"):
        # 提取请求信息
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
        
        key_info = auth_service.verify_api_key(token, ip_address, user_agent)
        if not key_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的API密钥",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 记录请求信息
        if request:
            auth_service.db.update_api_key_last_used(token)
        
        return {
            "type": "api_key",
            "name": key_info.get("name", "unknown"),
            "permissions": key_info.get("permissions", ["read", "write"]),
            "key": token,
            "user_id": key_info.get("user_id"),
            "ip_address": ip_address
        }
    
    # 否则视为JWT令牌
    try:
        payload = auth_service.verify_token(token)
        
        # 检查令牌类型
        token_type = payload.get("type", "access")
        if token_type not in ["access", "oauth2"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌类型",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 检查是否过期（verify_token已经检查过）
        
        return {
            "type": token_type,
            "sub": payload.get("sub"),
            "permissions": payload.get("permissions", ["read", "write"]),
            "scope": payload.get("scope", []),
            "client_id": payload.get("client_id"),
            "token": token
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"认证验证失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证凭据验证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_permission(permission: str):
    """需要特定权限的装饰器"""
    def permission_checker(auth_data: Dict[str, Any] = Depends(verify_authentication)):
        auth_service = get_auth_service()
        
        if not auth_service.check_permission(auth_data, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要 '{permission}' 权限"
            )
        return auth_data
    return permission_checker


# 常用权限依赖项
require_read = require_permission("read")
require_write = require_permission("write")
require_admin = require_permission("admin")

# OAuth2密码流依赖项
async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """获取当前用户（OAuth2密码流）"""
    auth_service = get_auth_service()
    user_info = auth_service.get_user_from_token(token)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_info


# 初始化默认API密钥（向后兼容）
def init_default_api_keys():
    """从环境变量初始化默认API密钥"""
    default_key = os.getenv("RANGEN_API_KEY")
    if default_key:
        auth_service = get_auth_service()
        
        # 检查是否已存在
        key_info = auth_service.verify_api_key(default_key)
        if not key_info:
            # 创建默认API密钥
            auth_service.create_api_key(
                name="default",
                permissions=["read", "write", "admin"]
            )
            logger.info("默认API密钥已初始化")


# 启动时初始化
init_default_api_keys()