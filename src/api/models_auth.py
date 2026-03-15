"""
Authentication Database Models
SQLAlchemy models for user authentication and authorization
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Try to import SQLAlchemy, fallback to file-based storage
try:
    from sqlalchemy import (
        create_engine, Column, Integer, String, Text, Boolean, 
        DateTime, ForeignKey, JSON, UniqueConstraint, Index
    )
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship, Session
    from sqlalchemy.exc import SQLAlchemyError
    
    SQLALCHEMY_AVAILABLE = True
    Base = declarative_base()
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Base = None

# Define database path
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "auth.db")
os.makedirs(DB_DIR, exist_ok=True)


@dataclass
class UserData:
    """User data class for file-based storage"""
    user_id: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    created_at: str = None
    updated_at: str = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow().isoformat()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ApiKeyData:
    """API key data class for file-based storage"""
    api_key: str
    hashed_key: str
    name: str
    user_id: Optional[str] = None
    permissions: List[str] = None
    is_active: bool = True
    expires_at: Optional[str] = None
    created_at: str = None
    last_used_at: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.permissions is None:
            self.permissions = ["read", "write"]
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SessionData:
    """Session data class for file-based storage"""
    session_id: str
    user_id: str
    token: str
    token_type: str = "jwt"
    device_info: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: str = None
    created_at: str = None
    last_activity_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.last_activity_at is None:
            self.last_activity_at = datetime.utcnow().isoformat()
        if self.expires_at is None:
            # Default: 24 hours from creation
            expires = datetime.utcnow() + timedelta(hours=24)
            self.expires_at = expires.isoformat()


# SQLAlchemy models (only created if SQLAlchemy is available)
if SQLALCHEMY_AVAILABLE:
    class User(Base):
        """User model for SQLAlchemy"""
        __tablename__ = "users"
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        user_id = Column(String(64), unique=True, nullable=False, index=True)
        username = Column(String(64), unique=True, nullable=False, index=True)
        email = Column(String(255), unique=True, nullable=True, index=True)
        full_name = Column(String(255), nullable=True)
        
        # Authentication fields
        password_hash = Column(String(255), nullable=True)  # For password-based auth
        salt = Column(String(64), nullable=True)
        
        # Status flags
        is_active = Column(Boolean, default=True, nullable=False)
        is_admin = Column(Boolean, default=False, nullable=False)
        is_verified = Column(Boolean, default=False, nullable=False)
        
        # Timestamps
        created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
        last_login_at = Column(DateTime, nullable=True)
        
        # Extra data
        extra_data = Column(JSON, default=dict, nullable=False)
        
        # Relationships
        api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
        sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
        
        def __repr__(self):
            return f"<User(user_id='{self.user_id}', username='{self.username}')>"
        
        def to_dict(self) -> Dict[str, Any]:
            """Convert to dictionary"""
            return {
                "user_id": self.user_id,
                "username": self.username,
                "email": self.email,
                "full_name": self.full_name,
                "is_active": self.is_active,
                "is_admin": self.is_admin,
                "is_verified": self.is_verified,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None,
                "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
                "metadata": self.metadata
            }


    class ApiKey(Base):
        """API Key model for SQLAlchemy"""
        __tablename__ = "api_keys"
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        api_key = Column(String(128), unique=True, nullable=False, index=True)  # The actual API key
        hashed_key = Column(String(128), nullable=False)  # Hashed version for verification
        name = Column(String(128), nullable=False)
        
        # Foreign key to user
        user_id = Column(String(64), ForeignKey("users.user_id"), nullable=True, index=True)
        
        # Permissions and status
        permissions = Column(JSON, default=list, nullable=False)  # List of permissions
        is_active = Column(Boolean, default=True, nullable=False)
        
        # Expiration
        expires_at = Column(DateTime, nullable=True)
        
        # Timestamps
        created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
        last_used_at = Column(DateTime, nullable=True)
        
        # Extra data
        extra_data = Column(JSON, default=dict, nullable=False)
        
        # Relationships
        user = relationship("User", back_populates="api_keys")
        
        def __repr__(self):
            return f"<ApiKey(name='{self.name}', key='{self.api_key[:10]}...')>"
        
        def to_dict(self) -> Dict[str, Any]:
            """Convert to dictionary"""
            return {
                "api_key": self.api_key,
                "hashed_key": self.hashed_key,
                "name": self.name,
                "user_id": self.user_id,
                "permissions": self.permissions,
                "is_active": self.is_active,
                "expires_at": self.expires_at.isoformat() if self.expires_at else None,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
                "metadata": self.metadata
            }


    class Session(Base):
        """Session model for SQLAlchemy"""
        __tablename__ = "sessions"
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        session_id = Column(String(128), unique=True, nullable=False, index=True)
        
        # Foreign key to user
        user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
        
        # Token information
        token = Column(String(512), nullable=False, index=True)  # JWT or other token
        token_type = Column(String(32), default="jwt", nullable=False)  # jwt, oauth2, etc
        
        # Device and location info
        device_info = Column(JSON, default=dict, nullable=False)
        ip_address = Column(String(64), nullable=True)
        user_agent = Column(Text, nullable=True)
        
        # Expiration
        expires_at = Column(DateTime, nullable=False, index=True)
        
        # Timestamps
        created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
        last_activity_at = Column(DateTime, default=datetime.utcnow, nullable=False)
        
        # Relationships
        user = relationship("User", back_populates="sessions")
        
        def __repr__(self):
            return f"<Session(session_id='{self.session_id}', user_id='{self.user_id}')>"
        
        def to_dict(self) -> Dict[str, Any]:
            """Convert to dictionary"""
            return {
                "session_id": self.session_id,
                "user_id": self.user_id,
                "token": self.token,
                "token_type": self.token_type,
                "device_info": self.device_info,
                "ip_address": self.ip_address,
                "user_agent": self.user_agent,
                "expires_at": self.expires_at.isoformat() if self.expires_at else None,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "last_activity_at": self.last_activity_at.isoformat() if self.last_activity_at else None
            }
    
    # Create indexes for performance
    __table_args__ = (
        Index("idx_api_keys_user_id", ApiKey.user_id),
        Index("idx_sessions_user_id", Session.user_id),
        Index("idx_sessions_expires_at", Session.expires_at),
    )


class AuthDatabase:
    """Unified authentication database manager"""
    
    def __init__(self, db_path: str = DB_PATH):
        """Initialize database connection"""
        self.db_path = db_path
        self.engine = None
        self.SessionLocal = None
        
        if SQLALCHEMY_AVAILABLE:
            self._init_sqlalchemy()
        else:
            self._init_file_storage()
    
    def _init_sqlalchemy(self):
        """Initialize SQLAlchemy database"""
        try:
            # Create SQLite engine
            self.engine = create_engine(f"sqlite:///{self.db_path}", echo=False)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            
            print(f"SQLAlchemy database initialized at {self.db_path}")
        except Exception as e:
            print(f"Failed to initialize SQLAlchemy database: {e}")
            self._init_file_storage()
    
    def _init_file_storage(self):
        """Initialize file-based storage"""
        try:
            import json
            import pickle
            
            self.storage_dir = os.path.join(DB_DIR, "auth_storage")
            os.makedirs(self.storage_dir, exist_ok=True)
            
            self.users_file = os.path.join(self.storage_dir, "users.json")
            self.api_keys_file = os.path.join(self.storage_dir, "api_keys.json")
            self.sessions_file = os.path.join(self.storage_dir, "sessions.json")
            
            # Initialize empty files if they don't exist
            for file_path in [self.users_file, self.api_keys_file, self.sessions_file]:
                if not os.path.exists(file_path):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump({}, f, ensure_ascii=False, indent=2)
            
            print(f"File-based storage initialized at {self.storage_dir}")
        except Exception as e:
            print(f"Failed to initialize file-based storage: {e}")
            raise
    
    def get_session(self):
        """Get database session (SQLAlchemy) or file storage handler"""
        if SQLALCHEMY_AVAILABLE and self.SessionLocal:
            return self.SessionLocal()
        else:
            return self
    
    def close_session(self, session):
        """Close database session"""
        if SQLALCHEMY_AVAILABLE and self.SessionLocal and hasattr(session, 'close'):
            session.close()
    
    # User management methods
    def create_user(self, username: str, email: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Create a new user"""
        if SQLALCHEMY_AVAILABLE:
            return self._create_user_sqlalchemy(username, email, **kwargs)
        else:
            return self._create_user_file(username, email, **kwargs)
    
    def _create_user_sqlalchemy(self, username: str, email: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Create user using SQLAlchemy"""
        from uuid import uuid4
        
        db = self.SessionLocal()
        try:
            user_id = str(uuid4())
            user = User(
                user_id=user_id,
                username=username,
                email=email,
                full_name=kwargs.get('full_name'),
                is_active=kwargs.get('is_active', True),
                is_admin=kwargs.get('is_admin', False),
                extra_data=kwargs.get('extra_data', {})
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            return user.to_dict()
        except SQLAlchemyError as e:
            db.rollback()
            raise Exception(f"Failed to create user: {e}")
        finally:
            db.close()
    
    def _create_user_file(self, username: str, email: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Create user using file storage"""
        import json
        from uuid import uuid4
        
        try:
            user_id = str(uuid4())
            user_data = UserData(
                user_id=user_id,
                username=username,
                email=email,
                full_name=kwargs.get('full_name'),
                is_active=kwargs.get('is_active', True),
                is_admin=kwargs.get('is_admin', False),
                metadata=kwargs.get('metadata', {})
            )
            
            # Load existing users
            with open(self.users_file, 'r', encoding='utf-8') as f:
                users = json.load(f)
            
            # Add new user
            users[user_id] = user_data.__dict__
            
            # Save back
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
            
            return user_data.__dict__
        except Exception as e:
            raise Exception(f"Failed to create user: {e}")
    
    # API Key management methods
    def create_api_key(self, name: str, permissions: List[str] = None, user_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Create a new API key"""
        if SQLALCHEMY_AVAILABLE:
            return self._create_api_key_sqlalchemy(name, permissions, user_id, **kwargs)
        else:
            return self._create_api_key_file(name, permissions, user_id, **kwargs)
    
    def _create_api_key_sqlalchemy(self, name: str, permissions: List[str] = None, user_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Create API key using SQLAlchemy"""
        import hashlib
        import secrets
        
        db = self.SessionLocal()
        try:
            # Generate API key
            api_key = f"rang_{secrets.token_urlsafe(32)}"
            hashed_key = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Calculate expiration if provided
            expires_at = None
            if kwargs.get('expires_in_days'):
                expires_at = datetime.utcnow() + timedelta(days=kwargs['expires_in_days'])
            
            api_key_obj = ApiKey(
                api_key=api_key,
                hashed_key=hashed_key,
                name=name,
                user_id=user_id,
                permissions=permissions or ["read", "write"],
                is_active=kwargs.get('is_active', True),
                expires_at=expires_at,
                extra_data=kwargs.get('extra_data', {})
            )
            
            db.add(api_key_obj)
            db.commit()
            db.refresh(api_key_obj)
            
            result = api_key_obj.to_dict()
            result['api_key_plain'] = api_key  # Include plain text key only once
            return result
        except SQLAlchemyError as e:
            db.rollback()
            raise Exception(f"Failed to create API key: {e}")
        finally:
            db.close()
    
    def _create_api_key_file(self, name: str, permissions: List[str] = None, user_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Create API key using file storage"""
        import json
        import hashlib
        import secrets
        
        try:
            # Generate API key
            api_key = f"rang_{secrets.token_urlsafe(32)}"
            hashed_key = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Calculate expiration if provided
            expires_at = None
            if kwargs.get('expires_in_days'):
                expires_at = datetime.utcnow() + timedelta(days=kwargs['expires_in_days'])
                expires_at = expires_at.isoformat()
            
            api_key_data = ApiKeyData(
                api_key=api_key,
                hashed_key=hashed_key,
                name=name,
                user_id=user_id,
                permissions=permissions or ["read", "write"],
                is_active=kwargs.get('is_active', True),
                expires_at=expires_at,
                metadata=kwargs.get('metadata', {})
            )
            
            # Load existing API keys
            with open(self.api_keys_file, 'r', encoding='utf-8') as f:
                api_keys = json.load(f)
            
            # Add new API key
            api_keys[api_key] = api_key_data.__dict__
            
            # Save back
            with open(self.api_keys_file, 'w', encoding='utf-8') as f:
                json.dump(api_keys, f, ensure_ascii=False, indent=2)
            
            result = api_key_data.__dict__
            result['api_key_plain'] = api_key  # Include plain text key only once
            return result
        except Exception as e:
            raise Exception(f"Failed to create API key: {e}")

    def _get_api_key_file(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get API key from file storage"""
        import json

        try:
            if not os.path.exists(self.api_keys_file):
                return None

            with open(self.api_keys_file, 'r', encoding='utf-8') as f:
                api_keys = json.load(f)

            # Check if the API key exists (direct lookup)
            if api_key in api_keys:
                return api_keys[api_key]

            return None
        except Exception as e:
            return None

    def _get_api_key_sqlalchemy(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get API key using SQLAlchemy"""
        db = self.SessionLocal()
        try:
            api_key_obj = db.query(ApiKey).filter(ApiKey.api_key == api_key).first()
            if not api_key_obj:
                return None
            return api_key_obj.to_dict()
        except SQLAlchemyError as e:
            return None
        finally:
            db.close()

#KB|    # Session management methods
    # Session management methods
    def create_session(self, user_id: str, token: str, **kwargs) -> Dict[str, Any]:
        """Create a new session"""
        if SQLALCHEMY_AVAILABLE:
            return self._create_session_sqlalchemy(user_id, token, **kwargs)
        else:
            return self._create_session_file(user_id, token, **kwargs)
    
    def _create_session_sqlalchemy(self, user_id: str, token: str, **kwargs) -> Dict[str, Any]:
        """Create session using SQLAlchemy"""
        from uuid import uuid4
        
        db = self.SessionLocal()
        try:
            session_id = str(uuid4())
            
            # Calculate expiration
            expires_hours = kwargs.get('expires_hours', 24)
            expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
            
            session = Session(
                session_id=session_id,
                user_id=user_id,
                token=token,
                token_type=kwargs.get('token_type', 'jwt'),
                device_info=kwargs.get('device_info', {}),
                ip_address=kwargs.get('ip_address'),
                user_agent=kwargs.get('user_agent'),
                expires_at=expires_at
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            return session.to_dict()
        except SQLAlchemyError as e:
            db.rollback()
            raise Exception(f"Failed to create session: {e}")
        finally:
            db.close()
    
    def _create_session_file(self, user_id: str, token: str, **kwargs) -> Dict[str, Any]:
        """Create session using file storage"""
        import json
        from uuid import uuid4
        
        try:
            session_id = str(uuid4())
            
            # Calculate expiration
            expires_hours = kwargs.get('expires_hours', 24)
            expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
            
            session_data = SessionData(
                session_id=session_id,
                user_id=user_id,
                token=token,
                token_type=kwargs.get('token_type', 'jwt'),
                device_info=kwargs.get('device_info', {}),
                ip_address=kwargs.get('ip_address'),
                user_agent=kwargs.get('user_agent'),
                expires_at=expires_at.isoformat()
            )
            
            # Load existing sessions
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                sessions = json.load(f)
            
            # Add new session
            sessions[session_id] = session_data.__dict__
            
            # Save back
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(sessions, f, ensure_ascii=False, indent=2)
            
            return session_data.__dict__
        except Exception as e:
            raise Exception(f"Failed to create session: {e}")
    
    # Query methods
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        if SQLALCHEMY_AVAILABLE:
            return self._get_user_by_username_sqlalchemy(username)
        else:
            return self._get_user_by_username_file(username)
    
    def get_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get API key by plain text key"""
        if SQLALCHEMY_AVAILABLE:
            return self._get_api_key_sqlalchemy(api_key)
        else:
            return self._get_api_key_file(api_key)
    
    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify API key and return key info if valid"""
        import hashlib
        
        key_info = self.get_api_key(api_key)
        if not key_info:
            return None
        
        # Check if key is active
        if not key_info.get('is_active', True):
            return None
        
        # Check expiration
        expires_at = key_info.get('expires_at')
        if expires_at:
            if isinstance(expires_at, str):
                expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            else:
                # Assume it's already a datetime
                expires_dt = expires_at
            
            if datetime.utcnow() > expires_dt:
                return None
        
        # Update last used timestamp
        self.update_api_key_last_used(api_key)
        
        return key_info
    
    def update_api_key_last_used(self, api_key: str):
        """Update API key last used timestamp"""
        if SQLALCHEMY_AVAILABLE:
            self._update_api_key_last_used_sqlalchemy(api_key)
        else:
            self._update_api_key_last_used_file(api_key)


# Global database instance
_auth_db_instance = None

def get_auth_database() -> AuthDatabase:
    """Get global authentication database instance"""
    global _auth_db_instance
    if _auth_db_instance is None:
        _auth_db_instance = AuthDatabase()
    return _auth_db_instance