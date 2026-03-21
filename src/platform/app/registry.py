"""
应用注册表 - 纯新增，不影响现有系统

功能:
- 应用注册与认证
- API Key 管理
- 应用状态管理

使用单例模式，确保全局唯一实例
"""

import secrets
import hashlib
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime


class AppStatus(Enum):
    """应用状态"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


@dataclass
class App:
    """应用实体"""
    app_id: str
    name: str
    description: str
    owner_id: str
    status: AppStatus = AppStatus.ACTIVE
    quota_config: Dict = field(default_factory=dict)
    enabled_agents: List[str] = field(default_factory=list)
    namespace_id: Optional[str] = None
    api_key_hash: Optional[str] = None  # 存储密钥哈希而非明文
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class AppRegistry:
    """
    应用注册表 - 单例模式
    
    功能:
    - 注册新应用，生成 API Key
    - 认证应用 (通过 API Key)
    - 管理应用状态
    
    使用内存存储，Phase 1 不涉及数据库
    """
    
    _instance: Optional['AppRegistry'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._apps: Dict[str, App] = {}  # app_id -> App
        self._api_key_hashes: Dict[str, str] = {}  # hash -> app_id
        self._app_names: Dict[str, str] = {}  # name -> app_id
        self._initialized = True
    
    def register(
        self,
        name: str,
        description: str,
        owner_id: str,
        quota_config: Optional[Dict] = None
    ) -> App:
        """
        注册新应用
        
        Args:
            name: 应用名称
            description: 应用描述
            owner_id: 所有者ID
            quota_config: 配额配置
            
        Returns:
            App: 创建的应用实例
        """
        # 检查名称是否已存在
        if name in self._app_names:
            raise ValueError(f"应用名称已存在: {name}")
        
        # 生成唯一 ID 和 API Key
        app_id = f"app_{uuid.uuid4().hex[:12]}"
        api_key = f"sk_{secrets.token_urlsafe(24)}"
        
        # 创建应用实例
        app = App(
            app_id=app_id,
            name=name,
            description=description,
            owner_id=owner_id,
            quota_config=quota_config or {},
            api_key_hash=self._hash_key(api_key)
        )
        
        # 存储
        self._apps[app_id] = app
        self._api_key_hashes[app.api_key_hash] = app_id
        self._app_names[name] = app_id
        
        return app
    
    def register_with_key(self, app: App) -> str:
        """
        注册应用并返回 API Key (用于内部创建时)
        
        Args:
            app: 应用实例
            
        Returns:
            str: 生成的 API Key
        """
        api_key = f"sk_{secrets.token_urlsafe(24)}"
        app.api_key_hash = self._hash_key(api_key)
        
        self._apps[app.app_id] = app
        self._api_key_hashes[app.api_key_hash] = app.app_id
        self._app_names[app.name] = app.app_id
        
        return api_key
    
    def authenticate(self, api_key: str) -> Optional[App]:
        """
        通过 API Key 认证应用
        
        Args:
            api_key: API Key
            
        Returns:
            Optional[App]: 认证成功返回 App，否则返回 None
        """
        if not api_key:
            return None
        
        key_hash = self._hash_key(api_key)
        app_id = self._api_key_hashes.get(key_hash)
        
        if not app_id:
            return None
        
        app = self._apps.get(app_id)
        if not app or app.status != AppStatus.ACTIVE:
            return None
        
        return app
    
    def get_by_id(self, app_id: str) -> Optional[App]:
        """通过 ID 获取应用"""
        return self._apps.get(app_id)
    
    def get_by_name(self, name: str) -> Optional[App]:
        """通过名称获取应用"""
        app_id = self._app_names.get(name)
        if not app_id:
            return None
        return self._apps.get(app_id)
    
    def list_apps(self, owner_id: Optional[str] = None, 
                  status: Optional[AppStatus] = None) -> List[App]:
        """
        列出应用
        
        Args:
            owner_id: 按所有者过滤
            status: 按状态过滤
            
        Returns:
            List[App]: 应用列表
        """
        apps = list(self._apps.values())
        
        if owner_id:
            apps = [a for a in apps if a.owner_id == owner_id]
        
        if status:
            apps = [a for a in apps if a.status == status]
        
        return apps
    
    def update_status(self, app_id: str, status: AppStatus) -> bool:
        """更新应用状态"""
        app = self._apps.get(app_id)
        if not app:
            return False
        
        app.status = status
        app.updated_at = datetime.now()
        return True
    
    def delete(self, app_id: str) -> bool:
        """删除应用 (软删除)"""
        app = self._apps.get(app_id)
        if not app:
            return False
        
        app.status = AppStatus.DELETED
        app.updated_at = datetime.now()
        return True
    
    def _hash_key(self, api_key: str) -> str:
        """对 API Key 进行哈希"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def __len__(self) -> int:
        """获取应用数量"""
        return len([a for a in self._apps.values() if a.status != AppStatus.DELETED])


# 全局单例
_app_registry: Optional[AppRegistry] = None


def get_app_registry() -> AppRegistry:
    """获取应用注册表实例"""
    global _app_registry
    if _app_registry is None:
        _app_registry = AppRegistry()
    return _app_registry
