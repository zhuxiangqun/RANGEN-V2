#!/usr/bin/env python3
"""
跨平台会话管理器 - 统一多渠道上下文
Cross-Platform Session Manager - Unified Multi-Channel Context

参考文章核心观点：
"网页端聊了一半，切到App继续问，Agent一脸茫然——换个平台就像换了个人"

核心功能：
1. 跨平台用户识别
2. 统一上下文聚合
3. 会话历史合并
4. 平台偏好学习
5. 无缝上下文切换
"""

import logging
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class Platform(Enum):
    """平台类型"""
    WEB = "web"
    WECHAT = "wechat"
    SLACK = "slack"
    TELEGRAM = "telegram"
    APP = "app"
    API = "api"
    OTHER = "other"


@dataclass
class PlatformSession:
    """平台会话"""
    session_id: str
    platform: Platform
    user_id: str
    created_at: datetime
    last_active: datetime
    message_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True


@dataclass
class UnifiedUserContext:
    """统一用户上下文"""
    user_id: str
    platforms: List[Platform]
    total_sessions: int
    merged_history: List[Dict[str, Any]]
    global_preferences: Dict[str, Any]
    recent_topics: List[str]
    knowledge_tags: List[str]
    last_activity: datetime
    platform_stats: Dict[str, int] = field(default_factory=dict)


@dataclass
class Message:
    """消息"""
    message_id: str
    session_id: str
    platform: Platform
    role: str  # user, assistant, system
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class CrossPlatformSessionManager:
    """
    跨平台会话管理器
    
    提供统一的多渠道用户上下文：
    1. 跨平台用户识别
    2. 统一上下文聚合
    3. 会话历史合并
    4. 平台偏好学习
    5. 无缝上下文切换
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 会话存储: user_id -> {platform -> session}
        self.user_sessions: Dict[str, Dict[Platform, PlatformSession]] = {}
        
        # 消息存储: session_id -> messages
        self.session_messages: Dict[str, List[Message]] = {}
        
        # 用户上下文缓存
        self.context_cache: Dict[str, UnifiedUserContext] = {}
        
        # 上下文缓存TTL（秒）
        self.cache_ttl = self.config.get("cache_ttl", 300)
        
        # 上下文缓存时间
        self.cache_time: Dict[str, datetime] = {}
        
        # 平台别名映射（如微信的小程序和公众号）
        self.platform_aliases = self.config.get("platform_aliases", {
            "wechat_mp": Platform.WECHAT,
            "wechat_pub": Platform.WECHAT,
            "wechat_mini": Platform.WECHAT,
        })
        
        logger.info("跨平台会话管理器初始化完成")
    
    def _normalize_platform(self, platform: str) -> Platform:
        """标准化平台名称"""
        platform_lower = platform.lower()
        
        # 检查别名
        if platform_lower in self.platform_aliases:
            return self.platform_aliases[platform_lower]
        
        # 直接匹配
        try:
            return Platform(platform_lower)
        except ValueError:
            return Platform.OTHER
    
    def create_session(
        self,
        user_id: str,
        platform: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PlatformSession:
        """
        创建新会话
        
        Args:
            user_id: 用户ID
            platform: 平台名称
            metadata: 元数据
            
        Returns:
            PlatformSession: 平台会话
        """
        platform = self._normalize_platform(platform)
        
        session = PlatformSession(
            session_id=str(uuid.uuid4()),
            platform=platform,
            user_id=user_id,
            created_at=datetime.now(),
            last_active=datetime.now(),
            metadata=metadata or {}
        )
        
        # 存储会话
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {}
        
        self.user_sessions[user_id][platform] = session
        
        # 初始化消息列表
        self.session_messages[session.session_id] = []
        
        logger.info(f"创建跨平台会话: user={user_id}, platform={platform.value}")
        
        return session
    
    def get_or_create_session(
        self,
        user_id: str,
        platform: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PlatformSession:
        """
        获取或创建会话
        
        Args:
            user_id: 用户ID
            platform: 平台名称
            metadata: 元数据
            
        Returns:
            PlatformSession: 平台会话
        """
        platform = self._normalize_platform(platform)
        
        # 检查现有会话
        if user_id in self.user_sessions:
            if platform in self.user_sessions[user_id]:
                session = self.user_sessions[user_id][platform]
                session.last_active = datetime.now()
                return session
        
        # 创建新会话
        return self.create_session(user_id, platform, metadata)
    
    def add_message(
        self,
        session_id: str,
        platform: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        添加消息
        
        Args:
            session_id: 会话ID
            platform: 平台名称
            role: 角色
            content: 内容
            metadata: 元数据
            
        Returns:
            Message: 消息
        """
        platform = self._normalize_platform(platform)
        
        message = Message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            platform=platform,
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        # 存储消息
        if session_id not in self.session_messages:
            self.session_messages[session_id] = []
        
        self.session_messages[session_id].append(message)
        
        # 更新会话统计
        for user_sessions in self.user_sessions.values():
            for sess in user_sessions.values():
                if sess.session_id == session_id:
                    sess.message_count += 1
                    sess.last_active = datetime.now()
        
        # 清除上下文缓存
        self._invalidate_cache_for_session(session_id)
        
        return message
    
    def get_unified_context(
        self,
        user_id: str,
        force_refresh: bool = False
    ) -> Optional[UnifiedUserContext]:
        """
        获取用户统一上下文
        
        Args:
            user_id: 用户ID
            force_refresh: 强制刷新
            
        Returns:
            UnifiedUserContext: 统一上下文
        """
        # 检查缓存
        if not force_refresh and user_id in self.context_cache:
            cache_time = self.cache_time.get(user_id)
            if cache_time:
                age = (datetime.now() - cache_time).total_seconds()
                if age < self.cache_ttl:
                    return self.context_cache[user_id]
        
        # 获取用户所有会话
        if user_id not in self.user_sessions:
            return None
        
        sessions = self.user_sessions[user_id]
        
        # 收集所有消息
        all_messages: List[Message] = []
        for session in sessions.values():
            if session.session_id in self.session_messages:
                all_messages.extend(self.session_messages[session.session_id])
        
        # 按时间排序
        all_messages.sort(key=lambda m: m.timestamp)
        
        # 提取平台列表
        platforms = [s.platform for s in sessions.values()]
        
        # 合并历史
        merged_history = self._merge_histories(all_messages)
        
        # 提取全局偏好
        global_preferences = self._extract_preferences(all_messages)
        
        # 提取最近主题
        recent_topics = self._extract_topics(merged_history)
        
        # 提取知识标签
        knowledge_tags = self._extract_tags(merged_history)
        
        # 平台统计
        platform_stats = {}
        for platform in Platform:
            count = sum(1 for s in sessions.values() if s.platform == platform)
            if count > 0:
                platform_stats[platform.value] = count
        
        # 构建统一上下文
        context = UnifiedUserContext(
            user_id=user_id,
            platforms=platforms,
            total_sessions=len(sessions),
            merged_history=merged_history,
            global_preferences=global_preferences,
            recent_topics=recent_topics,
            knowledge_tags=knowledge_tags,
            last_activity=max(
                (s.last_active for s in sessions.values()),
                default=datetime.now()
            ),
            platform_stats=platform_stats
        )
        
        # 更新缓存
        self.context_cache[user_id] = context
        self.cache_time[user_id] = datetime.now()
        
        return context
    
    def get_context_for_platform(
        self,
        user_id: str,
        platform: str
    ) -> Dict[str, Any]:
        """
        获取特定平台的上下文（包含跨平台摘要）
        
        Args:
            user_id: 用户ID
            platform: 平台名称
            
        Returns:
            平台上下文
        """
        platform = self._normalize_platform(platform)
        
        # 获取统一上下文
        unified = self.get_unified_context(user_id)
        
        # 获取当前平台会话
        session = None
        if user_id in self.user_sessions:
            session = self.user_sessions[user_id].get(platform)
        
        # 获取当前平台消息
        platform_messages = []
        if session:
            platform_messages = self.session_messages.get(session.session_id, [])
        
        return {
            "user_id": user_id,
            "current_platform": platform.value,
            "current_session_id": session.session_id if session else None,
            "current_history": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()}
                for m in platform_messages
            ],
            "unified_summary": {
                "total_sessions": unified.total_sessions if unified else 0,
                "other_platforms": [
                    p.value for p in (unified.platforms if unified else [])
                    if p != platform
                ],
                "recent_topics": unified.recent_topics[:5] if unified else [],
                "last_activity": unified.last_activity.isoformat() if unified and unified.last_activity else None
            }
        }
    
    def _merge_histories(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """合并消息历史"""
        merged = []
        
        for msg in messages:
            merged.append({
                "message_id": msg.message_id,
                "platform": msg.platform.value,
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "preview": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            })
        
        return merged
    
    def _extract_preferences(self, messages: List[Message]) -> Dict[str, Any]:
        """提取全局偏好"""
        preferences = {
            "preferred_platform": None,
            "communication_style": "neutral",
            "topics_of_interest": []
        }
        
        if not messages:
            return preferences
        
        # 统计各平台消息数量
        platform_counts: Dict[Platform, int] = {}
        for msg in messages:
            platform_counts[msg.platform] = platform_counts.get(msg.platform, 0) + 1
        
        # 找出最常用平台
        if platform_counts:
            preferences["preferred_platform"] = max(
                platform_counts.items(),
                key=lambda x: x[1]
            )[0].value
        
        return preferences
    
    def _extract_topics(self, history: List[Dict[str, Any]]) -> List[str]:
        """提取最近主题"""
        # 简化实现：取最近消息的关键词
        topics = []
        
        for item in history[-20:]:  # 最近20条
            content = item.get("content", "")
            # 简单提取：前100个字符作为预览
            if content:
                topics.append(content[:50])
        
        # 去重并返回
        return list(dict.fromkeys(topics))[:10]
    
    def _extract_tags(self, history: List[Dict[str, Any]]) -> List[str]:
        """提取知识标签"""
        # 简化实现：可以从消息内容中提取实体
        tags = []
        
        for item in history:
            content = item.get("content", "")
            # TODO: 集成实体识别
            if "?" in content or "？" in content:
                tags.append("question")
        
        return list(set(tags))[:20]
    
    def _invalidate_cache_for_session(self, session_id: str):
        """清除与会话相关的缓存"""
        # 找到session对应的user
        for user_id, sessions in self.user_sessions.items():
            for session in sessions.values():
                if session.session_id == session_id:
                    # 清除该用户的缓存
                    if user_id in self.context_cache:
                        del self.context_cache[user_id]
                    if user_id in self.cache_time:
                        del self.cache_time[user_id]
                    return
    
    def get_user_sessions(
        self,
        user_id: str,
        active_only: bool = True
    ) -> List[PlatformSession]:
        """获取用户所有会话"""
        if user_id not in self.user_sessions:
            return []
        
        sessions = list(self.user_sessions[user_id].values())
        
        if active_only:
            sessions = [s for s in sessions if s.is_active]
        
        return sessions
    
    def archive_session(self, session_id: str):
        """归档会话"""
        for user_sessions in self.user_sessions.values():
            for session in user_sessions.values():
                if session.session_id == session_id:
                    session.is_active = False
                    logger.info(f"归档会话: {session_id}")
                    return
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_users = len(self.user_sessions)
        total_sessions = sum(
            len(sessions) 
            for sessions in self.user_sessions.values()
        )
        total_messages = sum(
            len(messages)
            for messages in self.session_messages.values()
        )
        
        # 统计各平台会话数
        platform_counts = {}
        for user_sessions in self.user_sessions.values():
            for session in user_sessions.values():
                platform = session.platform.value
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        return {
            "total_users": total_users,
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "platforms": platform_counts
        }
# 全局单例
_session_manager: Optional[CrossPlatformSessionManager] = None


def get_cross_platform_session_manager(
    config: Optional[Dict[str, Any]] = None
) -> CrossPlatformSessionManager:
    """获取跨平台会话管理器单例"""
    global _session_manager
    
    if _session_manager is None:
        _session_manager = CrossPlatformSessionManager(config)
    
    return _session_manager
