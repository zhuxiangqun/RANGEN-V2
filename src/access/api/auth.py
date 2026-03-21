"""
Authentication and Authorization Module
向后兼容层，使用新的统一认证服务
"""
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from src.services.logging_service import get_logger

# 导入新的统一认证服务
try:
    from src.api.auth_service import (
        get_auth_service,
        verify_authentication as new_verify_authentication,
        require_permission as new_require_permission,
        require_read as new_require_read,
        require_write as new_require_write,
        require_admin as new_require_admin,
        get_current_user
    )
    NEW_AUTH_AVAILABLE = True
except ImportError:
    NEW_AUTH_AVAILABLE = False
    logger = get_logger("auth_service")

logger = get_logger("auth_service")

# Configuration (向后兼容)
SECRET_KEY = os.getenv("RANGEN_SECRET_KEY")
if not SECRET_KEY:
    logger.warning("RANGEN_SECRET_KEY not set, generating temporary key")
    SECRET_KEY = secrets.token_urlsafe(32)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Security context (向后兼容)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# In-memory API key storage (向后兼容，生产环境应使用数据库)
API_KEYS: Dict[str, Dict[str, Any]] = {}

class AuthService:
    """Service for handling authentication and authorization (向后兼容)"""
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key for storage"""
        if NEW_AUTH_AVAILABLE:
            auth_service = get_auth_service()
            return auth_service.hash_api_key(api_key)
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def verify_api_key(api_key: str, hashed_key: str) -> bool:
        """Verify an API key against its hash"""
        if NEW_AUTH_AVAILABLE:
            auth_service = get_auth_service()
            return auth_service.hash_api_key(api_key) == hashed_key
        return AuthService.hash_api_key(api_key) == hashed_key
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a new API key"""
        if NEW_AUTH_AVAILABLE:
            auth_service = get_auth_service()
            return auth_service.generate_api_key()
        return f"rang_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create a JWT access token"""
        if NEW_AUTH_AVAILABLE:
            auth_service = get_auth_service()
            return auth_service.create_access_token(data, expires_delta)
        
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify a JWT token and return payload"""
        if NEW_AUTH_AVAILABLE:
            auth_service = get_auth_service()
            return auth_service.verify_token(token)
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

def register_api_key(api_key: str, name: str, permissions: list = None) -> bool:
    """Register a new API key"""
    if NEW_AUTH_AVAILABLE:
        try:
            auth_service = get_auth_service()
            auth_service.create_api_key(
                name=name,
                permissions=permissions or ["read", "write"]
            )
            logger.info(f"API key registered via new service for {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to register API key via new service: {e}")
            # Fallback to old method
    
    if permissions is None:
        permissions = ["read", "write"]
    
    hashed_key = AuthService.hash_api_key(api_key)
    API_KEYS[api_key] = {
        "name": name,
        "permissions": permissions,
        "created_at": datetime.utcnow().isoformat(),
        "hashed_key": hashed_key
    }
    logger.info(f"API key registered for {name} (legacy storage)")
    return True

def init_default_api_keys():
    """Initialize default API keys from environment"""
    if NEW_AUTH_AVAILABLE:
        # 新服务有自己的初始化逻辑，这里只记录
        logger.info("New auth service handles default API keys initialization")
        return
    
    # Allow setting default API key via environment (legacy)
    default_key = os.getenv("RANGEN_API_KEY")
    if default_key and default_key not in API_KEYS:
        register_api_key(default_key, "default", ["read", "write"])

# Initialize default keys (仅在新服务不可用时)
if not NEW_AUTH_AVAILABLE:
    init_default_api_keys()

async def verify_api_key_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Dict[str, Any]:
    """Verify API key authentication (向后兼容)"""
    if NEW_AUTH_AVAILABLE:
        # 使用新的认证验证函数
        return await new_verify_authentication(credentials)
    
    # 旧版本逻辑
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if it's an API key (starts with "rang_")
    if credentials.credentials.startswith("rang_"):
        if credentials.credentials in API_KEYS:
            key_info = API_KEYS[credentials.credentials]
            return {
                "type": "api_key",
                "name": key_info["name"],
                "permissions": key_info["permissions"],
                "key": credentials.credentials
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # Otherwise treat as JWT token
    try:
        payload = AuthService.verify_token(credentials.credentials)
        return {
            "type": "jwt",
            "sub": payload.get("sub"),
            "permissions": payload.get("permissions", ["read", "write"]),
            "token": credentials.credentials
        }
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_permission(permission: str):
    """Decorator to require specific permission (向后兼容)"""
    if NEW_AUTH_AVAILABLE:
        # 使用新的权限检查函数
        return new_require_permission(permission)
    
    def permission_checker(auth_data: Dict[str, Any] = Depends(verify_api_key_auth)):
        if permission not in auth_data.get("permissions", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return auth_data
    return permission_checker

# Common permission dependencies (向后兼容)
if NEW_AUTH_AVAILABLE:
    # 使用新的权限依赖项
    require_read = new_require_read
    require_write = new_require_write
    require_admin = new_require_admin
else:
    require_read = require_permission("read")
    require_write = require_permission("write")
    require_admin = require_permission("admin")