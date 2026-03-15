"""
Account Service - User authentication with bcrypt password encryption
"""
import os
import uuid
import secrets
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from src.services.logging_service import get_logger

logger = get_logger(__name__)

# 尝试导入bcrypt
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    logger.warning("bcrypt not available, using fallback password hashing")


class UserRole(str, Enum):
    """用户角色"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class LoginResult(str, Enum):
    """登录结果"""
    SUCCESS = "success"
    INVALID_PASSWORD = "invalid_password"
    USER_NOT_FOUND = "user_not_found"
    ACCOUNT_LOCKED = "account_locked"


@dataclass
class User:
    """用户"""
    id: str
    username: str
    password_hash: str
    role: UserRole = UserRole.USER
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    login_attempts: int = 0
    locked_until: Optional[datetime] = None
    is_active: bool = True


@dataclass
class LoginLog:
    """登录日志"""
    log_id: str
    user_id: str
    username: str
    ip_address: str
    user_agent: str
    result: LoginResult
    timestamp: datetime = field(default_factory=datetime.now)


class AccountService:
    """账户服务 - 用户认证和密码管理"""
    
    def __init__(self):
        self._users: Dict[str, User] = {}
        self._login_logs: List[LoginLog] = []
        self._max_login_attempts = 5
        self._lockout_duration = 15  # 分钟
        
        # 初始化默认管理员
        self._init_default_admin()
    
    def _init_default_admin(self):
        """初始化默认管理员"""
        # 检查是否已有管理员
        admin_exists = any(u.role == UserRole.ADMIN for u in self._users.values())
        if not admin_exists:
            # 创建默认管理员账户
            self.create_user(
                username="admin",
                password="admin123",  # 首次登录后应修改
                role=UserRole.ADMIN,
                email="admin@example.com"
            )
            logger.info("Default admin user created")
    
    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        if BCRYPT_AVAILABLE:
            salt = bcrypt.gensalt()
            return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        else:
            # 简单fallback（不推荐生产使用）
            import hashlib
            return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        if BCRYPT_AVAILABLE:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        else:
            import hashlib
            return hashlib.sha256(password.encode()).hexdigest() == password_hash
    
    def create_user(
        self,
        username: str,
        password: str,
        role: UserRole = UserRole.USER,
        email: Optional[str] = None,
        phone: Optional[str] = None
    ) -> User:
        """创建用户"""
        # 检查用户名是否已存在
        if any(u.username == username for u in self._users.values()):
            raise ValueError(f"Username already exists: {username}")
        
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        
        user = User(
            id=user_id,
            username=username,
            password_hash=self._hash_password(password),
            role=role,
            email=self._mask_sensitive(email) if email else None,
            phone=self._mask_sensitive(phone) if phone else None
        )
        
        self._users[user_id] = user
        
        logger.info(f"User created: {username}")
        
        return user
    
    def _mask_sensitive(self, value: str) -> str:
        """脱敏处理"""
        if not value:
            return value
        
        if '@' in value:  # 邮箱
            parts = value.split('@')
            if len(parts[0]) > 2:
                return parts[0][:2] + '***@' + parts[1]
            return '***@' + parts[1]
        
        # 手机号
        if len(value) >= 7:
            return value[:3] + '****' + value[-4:]
        
        return '***'
    
    def authenticate(
        self,
        username: str,
        password: str,
        ip_address: str = "unknown",
        user_agent: str = "unknown"
    ) -> tuple[Optional[User], LoginResult]:
        """验证登录"""
        # 查找用户
        user = None
        for u in self._users.values():
            if u.username == username:
                user = u
                break
        
        if not user:
            self._log_login("", username, ip_address, user_agent, LoginResult.USER_NOT_FOUND)
            return None, LoginResult.USER_NOT_FOUND
        
        # 检查账户是否被锁定
        if user.locked_until and datetime.now() < user.locked_until:
            self._log_login(user.id, username, ip_address, user_agent, LoginResult.ACCOUNT_LOCKED)
            return None, LoginResult.ACCOUNT_LOCKED
        
        # 验证密码
        if not self._verify_password(password, user.password_hash):
            user.login_attempts += 1
            
            # 锁定账户
            if user.login_attempts >= self._max_login_attempts:
                user.locked_until = datetime.now() + timedelta(minutes=self._lockout_duration)
                logger.warning(f"Account locked: {username}")
            
            self._log_login(user.id, username, ip_address, user_agent, LoginResult.INVALID_PASSWORD)
            return None, LoginResult.INVALID_PASSWORD
        
        # 登录成功
        user.login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now()
        
        self._log_login(user.id, username, ip_address, user_agent, LoginResult.SUCCESS)
        
        logger.info(f"User logged in: {username}")
        
        return user, LoginResult.SUCCESS
    
    def _log_login(
        self,
        user_id: str,
        username: str,
        ip_address: str,
        user_agent: str,
        result: LoginResult
    ):
        """记录登录日志"""
        log = LoginLog(
            log_id=f"log_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            result=result
        )
        self._login_logs.append(log)
    
    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户"""
        return self._users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        for user in self._users.values():
            if user.username == username:
                return user
        return None
    
    def update_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """更新密码"""
        user = self._users.get(user_id)
        if not user:
            return False
        
        # 验证旧密码
        if not self._verify_password(old_password, user.password_hash):
            return False
        
        # 更新密码
        user.password_hash = self._hash_password(new_password)
        
        logger.info(f"Password updated for user: {user.username}")
        
        return True
    
    def reset_password(self, user_id: str, new_password: str) -> bool:
        """重置密码（管理员操作）"""
        user = self._users.get(user_id)
        if not user:
            return False
        
        user.password_hash = self._hash_password(new_password)
        
        logger.info(f"Password reset for user: {user.username}")
        
        return True
    
    def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        if user_id in self._users:
            username = self._users[user_id].username
            del self._users[user_id]
            logger.info(f"User deleted: {username}")
            return True
        return False
    
    def get_login_logs(self, user_id: Optional[str] = None, limit: int = 50) -> List[LoginLog]:
        """获取登录日志"""
        logs = self._login_logs
        
        if user_id:
            logs = [l for l in logs if l.user_id == user_id]
        
        return sorted(logs, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """获取所有用户（脱敏）"""
        return [
            {
                "id": u.id,
                "username": u.username,
                "role": u.role.value,
                "email": u.email,
                "phone": u.phone,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
                "last_login": u.last_login.isoformat() if u.last_login else None,
                "login_attempts": u.login_attempts
            }
            for u in self._users.values()
        ]


# Global instance
_account_service: Optional[AccountService] = None


def get_account_service() -> AccountService:
    """获取账户服务实例"""
    global _account_service
    if _account_service is None:
        _account_service = AccountService()
    return _account_service
