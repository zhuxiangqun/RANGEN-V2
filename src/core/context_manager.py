"""
Unified Context Manager Implementation with Backend Abstraction
"""
from typing import Dict, Any, Optional
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
                        logger.info(f"Topic switch detected (score={max_score:.2f} < {self.beta_threshold}). Smart Forgetting triggered.")
                        
                        # Generate Summary before forgetting
                        if self.summarizer:
                            summary = await self.summarizer.summarize(history)
                            self._memory["summary"] = summary # Store summary in session
                        
                        # Archive/Compress history
                        self._memory["history"] = history[-1:] # Keep only the very last message as context transition
                        # 🚀 P0修复：更新本地变量history，确保后续追加消息时基于截断后的历史
                        history = self._memory["history"]
                except Exception as e:
                    logger.warning(f"Smart forgetting failed: {e}")

        history.append({
            "role": role, 
            "content": content,
            "timestamp": time.time()
        })
        self._memory["last_updated"] = time.time()
        await self.save()

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