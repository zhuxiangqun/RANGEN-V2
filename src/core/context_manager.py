"""
Unified Context Manager Implementation with Backend Abstraction
"""
from typing import Dict, Any, Optional, List, Tuple
import time
import asyncio
import json
from abc import ABC, abstractmethod
from src.interfaces.context import IContext
from src.services.logging_service import get_logger
from src.core.neural.factory import NeuralServiceFactory
from src.services.context_engineering.summarizer import ContextSummarizer
from src.core.llm_integration import LLMIntegration

logger = get_logger(__name__)

# --- Backend Abstraction ---

class IContextBackend(ABC):
    @abstractmethod
    async def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        pass
        
    @abstractmethod
    async def save(self, session_id: str, data: Dict[str, Any]):
        pass
        
    @abstractmethod
    async def delete(self, session_id: str):
        pass

class MemoryBackend(IContextBackend):
    def __init__(self):
        self._store = {}
        
    async def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._store.get(session_id)
        
    async def save(self, session_id: str, data: Dict[str, Any]):
        self._store[session_id] = data
        
    async def delete(self, session_id: str):
        if session_id in self._store:
            del self._store[session_id]

class RedisBackend(IContextBackend):
    def __init__(self, redis_url: str):
        try:
            import redis.asyncio as redis
            self.client = redis.from_url(redis_url)
            self.enabled = True
        except ImportError:
            logger.warning("redis-py not installed. Falling back to MemoryBackend.")
            self.enabled = False
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.enabled = False

    async def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        if not self.enabled: return None
        data = await self.client.get(f"session:{session_id}")
        return json.loads(data) if data else None
        
    async def save(self, session_id: str, data: Dict[str, Any]):
        if not self.enabled: return
        await self.client.set(f"session:{session_id}", json.dumps(data))
        
    async def delete(self, session_id: str):
        if not self.enabled: return
        await self.client.delete(f"session:{session_id}")

# --- Core Implementation ---

class SessionContext(IContext):
    """
    Represents the context for a single user session.
    Now syncs with backend on changes.
    """
    def __init__(self, session_id: str, initial_data: Dict[str, Any], backend: IContextBackend, beta_threshold: float = 0.2, llm_service: Optional[LLMIntegration] = None):
        self.session_id = session_id
        self._memory = initial_data
        self._backend = backend
        self._lock = asyncio.Lock()
        
        # Neural Component for Smart Forgetting
        self.reranker = NeuralServiceFactory.get_reranker()
        
        # Context Summarizer (requires LLM)
        # Now uses injected LLM service or None
        if llm_service:
            self.summarizer = ContextSummarizer(llm_service)
        else:
            self.summarizer = None
            # Only log debug, not warning, as this might be intended in tests
            logger.debug("ContextSummarizer disabled (No LLM service provided)")
        
        # DDL Parameter: β≈1 threshold
        # Can be adjusted dynamically via update_config() in future
        self.beta_threshold = beta_threshold
        
        # Initialize topic switch counter if not exists
        if "topic_switch_count" not in self._memory:
            self._memory["topic_switch_count"] = 0

    def get(self, key: str, default: Any = None) -> Any:
        return self._memory.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._memory[key] = value
        self._memory["last_updated"] = time.time()
        # Fire and forget save (or await if strict consistency needed)
        # For simplicity in this async context, we might need an explicit save method
        # or just assume the manager handles it. 
        # But here we can't easily await inside a sync set method if interface is sync.
        # Ideally IContext should be async, but for now we update memory.
        
    def update(self, data: Dict[str, Any]) -> None:
        self._memory.update(data)
        self._memory["last_updated"] = time.time()

    async def save(self):
        """Explicitly persist state"""
        await self._backend.save(self.session_id, self._memory)

    def clear(self) -> None:
        created_at = self._memory.get("created_at", time.time())
        self._memory = {
            "session_id": self.session_id,
            "created_at": created_at,
            "last_updated": time.time(),
            "history": []
        }

    def to_dict(self) -> Dict[str, Any]:
        return self._memory.copy()
        
    async def add_message(self, role: str, content: str, smart_forget: bool = True):
        """
        Add a message to history with optional Smart Forgetting (DDL β≈1).
        If new message is irrelevant to recent history, compress/archive old context.
        """
        history = self._memory["history"]
        
        # Smart Forgetting Logic
        if smart_forget and len(history) > 3 and role == "user":
            # Check relevance with last few messages
            last_msgs = [m["content"] for m in history[-3:] if m["role"] == "user"]
            if last_msgs:
                # Use Cross-Encoder to check similarity/relevance
                # We check if new query is related to ANY of the recent queries
                # If max score < threshold, it's a topic switch
                try:
                    scores = await self.reranker.rerank(content, last_msgs)
                    max_score = scores[0][1] if scores else 0.0
                    
                    if max_score < self.beta_threshold: # Use parameterized threshold
                        logger.info(f"Topic switch detected (score={max_score:.2f} < {self.beta_threshold}). Enhanced Smart Forgetting triggered.")
                        
                        # Increment topic switch counter
                        self._memory["topic_switch_count"] = self._memory.get("topic_switch_count", 0) + 1
                        
                        # Determine what to archive (all but last message)
                        if len(history) > 1:
                            archive_candidates = history[:-1]  # Archive all but the most recent message
                            try:
                                # Perform smart archiving
                                archive_id = await self.smart_archive(archive_candidates, reason="topic_switch")
                                logger.info(f"Archived {len(archive_candidates)} messages with ID: {archive_id}")
                            except Exception as e:
                                logger.error(f"Smart archiving failed: {e}")
                        
                        # Generate Summary before compressing
                        if self.summarizer:
                            summary_result = await self.summarizer.summarize(history, level="standard")
                            # Store multi-layer summary
                            self._memory["summary"] = summary_result["summary"]  # Main abstractive summary for backward compatibility
                            self._memory["full_summary"] = summary_result  # Full multi-layer summary
                        
                        # Compress history - keep only the last message as context transition
                        self._memory["history"] = history[-1:] # Keep only the very last message as context transition
                        # 🚀 P0修复：更新本地变量history，确保后续追加消息时基于截断后的历史
                        history = self._memory["history"]
                        
                        # Perform adaptive threshold adjustment
                        try:
                            await self.adaptive_threshold_adjustment()
                        except Exception as e:
                            logger.warning(f"Adaptive threshold adjustment failed: {e}")
                        
                        # Analyze topic clusters for better understanding
                        try:
                            await self.analyze_topic_clusters()
                        except Exception as e:
                            logger.debug(f"Topic cluster analysis skipped: {e}")
                except Exception as e:
                    logger.warning(f"Smart forgetting failed: {e}")

        history.append({
            "role": role, 
            "content": content,
            "timestamp": time.time()
        })
        self._memory["last_updated"] = time.time()
        await self.save()
    
    async def adaptive_threshold_adjustment(self):
        """自适应调整β阈值基于对话历史特性"""
        history = self._memory.get("history", [])
        if len(history) < 5:
            return  # 历史太短，不调整
        
        # 分析话题切换频率
        topic_switch_count = self._memory.get("topic_switch_count", 0)
        total_messages = len(history)
        
        # 计算话题切换率
        switch_rate = topic_switch_count / total_messages if total_messages > 0 else 0
        
        # 调整阈值：高切换率时降低阈值（更宽松），低切换率时提高阈值（更严格）
        if switch_rate > 0.5:  # 高频切换
            new_threshold = max(0.1, self.beta_threshold * 0.8)  # 降低阈值
        elif switch_rate < 0.1:  # 低频切换
            new_threshold = min(0.5, self.beta_threshold * 1.2)  # 提高阈值
        else:
            new_threshold = self.beta_threshold  # 保持不变
        
        if new_threshold != self.beta_threshold:
            old_threshold = self.beta_threshold
            self.beta_threshold = new_threshold
            logger.info(f"自适应β阈值调整: {old_threshold:.3f} → {new_threshold:.3f} (切换率: {switch_rate:.3f})")
    
    async def analyze_topic_clusters(self, history: List[Dict] = None) -> List[Dict[str, Any]]:
        """分析历史消息的话题聚类"""
        if history is None:
            history = self._memory.get("history", [])
        
        if len(history) < 2:
            return []
        
        user_messages = [msg["content"] for msg in history if msg.get("role") == "user"]
        if len(user_messages) < 2:
            return []
        
        try:
            # 使用重排器计算消息之间的相似度
            clusters = []
            current_cluster = {
                "messages": [user_messages[0]],
                "start_index": 0,
                "end_index": 0
            }
            
            for i in range(1, len(user_messages)):
                current_msg = user_messages[i]
                last_msg_in_cluster = current_cluster["messages"][-1]
                
                # 计算相似度
                scores = await self.reranker.rerank(current_msg, [last_msg_in_cluster])
                similarity = scores[0][1] if scores else 0.0
                
                if similarity >= self.beta_threshold:
                    # 属于同一话题
                    current_cluster["messages"].append(current_msg)
                    current_cluster["end_index"] = i
                else:
                    # 新话题开始
                    clusters.append(current_cluster.copy())
                    current_cluster = {
                        "messages": [current_msg],
                        "start_index": i,
                        "end_index": i
                    }
            
            # 添加最后一个聚类
            if current_cluster["messages"]:
                clusters.append(current_cluster)
            
            # 增强聚类信息
            enhanced_clusters = []
            for i, cluster in enumerate(clusters):
                topic_text = " ".join(cluster["messages"])
                keywords = []
                if self.summarizer:
                    # 使用summarizer的关键词提取功能
                    keywords = self.summarizer._extract_keywords(topic_text, max_keywords=5)
                
                enhanced_clusters.append({
                    "cluster_id": i,
                    "topic_summary": f"话题{i+1}: {keywords[0] if keywords else '未命名'}",
                    "message_count": len(cluster["messages"]),
                    "start_index": cluster["start_index"],
                    "end_index": cluster["end_index"],
                    "keywords": keywords,
                    "sample_messages": cluster["messages"][:2]  # 前两条消息作为样本
                })
            
            # 存储聚类结果
            self._memory["topic_clusters"] = enhanced_clusters
            return enhanced_clusters
            
        except Exception as e:
            logger.warning(f"话题聚类分析失败: {e}")
            return []
    
    async def smart_archive(self, history_to_archive: List[Dict], reason: str = "topic_switch"):
        """智能归档历史消息"""
        if not history_to_archive:
            return
        
        # 创建归档记录
        archive_id = f"archive_{int(time.time())}"
        archive_record = {
            "archive_id": archive_id,
            "timestamp": time.time(),
            "reason": reason,
            "message_count": len(history_to_archive),
            "messages": history_to_archive
        }
        
        # 如果有总结器，生成总结
        if self.summarizer:
            summary_result = await self.summarizer.summarize(history_to_archive, level="brief")
            archive_record["summary"] = summary_result["summary"]
            archive_record["keywords"] = summary_result["keywords"]
        
        # 存储归档记录
        if "archives" not in self._memory:
            self._memory["archives"] = []
        
        self._memory["archives"].append(archive_record)
        
        # 限制归档数量
        max_archives = 10
        if len(self._memory["archives"]) > max_archives:
            self._memory["archives"] = self._memory["archives"][-max_archives:]
        
        logger.info(f"智能归档完成: {archive_id}, {len(history_to_archive)}条消息, 原因: {reason}")
        
        return archive_id
    
    def update_config(self, config: Dict[str, Any]):
        """更新会话配置"""
        if "beta_threshold" in config:
            old_value = self.beta_threshold
            self.beta_threshold = config["beta_threshold"]
            logger.info(f"β阈值更新: {old_value} → {self.beta_threshold}")
        
        # 可以添加其他配置更新逻辑
        self._memory["last_config_update"] = time.time()

class ContextManager:
    """
    Manages multiple SessionContexts with pluggable backend.
    """
    
    def __init__(self, backend_type: str = "memory", redis_url: str = None, llm_service: Optional[LLMIntegration] = None):
        if backend_type == "redis" and redis_url:
            self.backend = RedisBackend(redis_url)
            if not getattr(self.backend, 'enabled', True):
                self.backend = MemoryBackend()
        else:
            self.backend = MemoryBackend()
            
        self.llm_service = llm_service
        self._active_sessions: Dict[str, SessionContext] = {}
        logger.info(f"ContextManager initialized with {type(self.backend).__name__}")

    async def get_session(self, session_id: str) -> SessionContext:
        """Get or create a session context (async to allow DB load)"""
        if session_id in self._active_sessions:
            return self._active_sessions[session_id]
            
        # Try load from backend
        data = await self.backend.load(session_id)
        
        if not data:
            logger.debug(f"Creating new session context: {session_id}")
            data = {
                "session_id": session_id,
                "created_at": time.time(),
                "last_updated": time.time(),
                "history": []
            }
        else:
            logger.debug(f"Loaded session context from backend: {session_id}")
            
        session = SessionContext(session_id, data, self.backend, llm_service=self.llm_service)
        self._active_sessions[session_id] = session
        return session

    async def save_session(self, session_id: str):
        """Persist a specific session"""
        if session_id in self._active_sessions:
            await self._active_sessions[session_id].save()

    async def delete_session(self, session_id: str):
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
        await self.backend.delete(session_id)
        logger.info(f"Session deleted: {session_id}")
            
    def get_active_sessions_count(self) -> int:
        return len(self._active_sessions)



# ============================================================================
# Workspace-Aware Session Context
# ============================================================================

class WorkspaceAwareSessionContext(SessionContext):
    """
    Session context with Workspace isolation support.
    
    Extends SessionContext to optionally link to a Workspace,
    enabling cross-session state sharing within a workspace.
    """
    
    def __init__(
        self,
        session_id: str,
        initial_data: Dict[str, Any],
        backend: IContextBackend,
        workspace=None,
        beta_threshold: float = 0.2,
        llm_service: Optional[LLMIntegration] = None
    ):
        super().__init__(
            session_id=session_id,
            initial_data=initial_data,
            backend=backend,
            beta_threshold=beta_threshold,
            llm_service=llm_service
        )
        
        self._workspace = workspace
        
        if workspace is not None:
            self._initialize_from_workspace()
    
    def _initialize_from_workspace(self):
        if self._workspace and hasattr(self._workspace, 'memory'):
            workspace_memory = self._workspace.memory
            if workspace_memory:
                self._memory["workspace_context"] = {
                    "workspace_id": self._workspace.workspace_id,
                    "memory_count": len(workspace_memory)
                }
    
    @property
    def workspace(self):
        return self._workspace
    
    def get_workspace_state(self, key: str, default: Any = None) -> Any:
        if self._workspace:
            return self._workspace.get_state(key, default)
        return default
    
    def set_workspace_state(self, key: str, value: Any):
        if self._workspace:
            self._workspace.set_state(key, value)
    
    def add_workspace_memory(self, memory_item: Dict[str, Any]):
        if self._workspace:
            self._workspace.add_memory(memory_item)
    
    def get_shared_history(self, limit: int = 10) -> list:
        if self._workspace:
            return self._workspace.memory[-limit:]
        return []


WorkspaceContext = WorkspaceAwareSessionContext