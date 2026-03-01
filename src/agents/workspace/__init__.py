"""
Agent Workspace System
=====================
Provides isolation for agents through workspace concept.

Inspired by OpenCLAW's workspace design.
"""

import uuid
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
import os


@dataclass
class WorkspaceConfig:
    """Workspace configuration"""
    workspace_id: str = ""
    root_path: str = "./workspace"
    enable_isolation: bool = True
    max_memory_mb: int = 1024
    auto_cleanup: bool = True


class AgentWorkspace:
    """
    Agent Workspace - Provides isolation for agent execution.
    
    Each workspace contains:
    - Isolated state
    - Isolated memory
    - Isolated tool cache
    - Isolated file storage
    - Session history
    """
    
    def __init__(
        self,
        workspace_id: Optional[str] = None,
        root_path: str = "./workspace",
        enable_isolation: bool = True,
        config: Optional[WorkspaceConfig] = None
    ):
        self.workspace_id = workspace_id or str(uuid.uuid4())[:8]
        self.root_path = Path(root_path) / self.workspace_id
        self.enable_isolation = enable_isolation
        self.config = config or WorkspaceConfig(
            workspace_id=self.workspace_id,
            root_path=root_path
        )
        
        # Isolated resources
        self._state: Dict[str, Any] = {}
        self._memory: List[Dict[str, Any]] = []
        self._tool_cache: Dict[str, Any] = {}
        self._session_history: List[Dict[str, Any]] = []
        
        # Create workspace directory
        self._init_workspace()
    
    def _init_workspace(self):
        """Initialize workspace directory structure"""
        if self.enable_isolation:
            self.root_path.mkdir(parents=True, exist_ok=True)
            (self.root_path / "state").mkdir(exist_ok=True)
            (self.root_path / "memory").mkdir(exist_ok=True)
            (self.root_path / "cache").mkdir(exist_ok=True)
            (self.root_path / "sessions").mkdir(exist_ok=True)
    
    @property
    def state(self) -> Dict[str, Any]:
        """Get workspace state"""
        return self._state
    
    @property
    def memory(self) -> List[Dict[str, Any]]:
        """Get workspace memory"""
        return self._memory
    
    @property
    def tool_cache(self) -> Dict[str, Any]:
        """Get tool cache"""
        return self._tool_cache
    
    def set_state(self, key: str, value: Any):
        """Set state value"""
        self._state[key] = value
        if self.enable_isolation:
            self._persist_state(key, value)
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get state value"""
        return self._state.get(key, default)
    
    def add_memory(self, memory_item: Dict[str, Any]):
        """Add memory item"""
        memory_item["timestamp"] = datetime.now().isoformat()
        self._memory.append(memory_item)
        
        if self.enable_isolation and len(self._memory) % 10 == 0:
            self._persist_memory()
    
    def add_session(self, session_data: Dict[str, Any]):
        """Add session record"""
        session_data["timestamp"] = datetime.now().isoformat()
        self._session_history.append(session_data)
        
        if self.enable_isolation:
            self._persist_session(session_data)
    
    def cache_tool_result(self, tool_name: str, params: Dict, result: Any):
        """Cache tool execution result"""
        cache_key = f"{tool_name}:{json.dumps(params, sort_keys=True)}"
        self._tool_cache[cache_key] = {
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_cached_tool_result(self, tool_name: str, params: Dict) -> Optional[Any]:
        """Get cached tool result"""
        cache_key = f"{tool_name}:{json.dumps(params, sort_keys=True)}"
        cached = self._tool_cache.get(cache_key)
        return cached["result"] if cached else None
    
    def _persist_state(self, key: str, value: Any):
        """Persist state to disk"""
        state_file = self.root_path / "state" / f"{key}.json"
        try:
            with open(state_file, 'w') as f:
                json.dump(value, f, indent=2, default=str)
        except Exception:
            pass
    
    def _persist_memory(self):
        """Persist memory to disk"""
        memory_file = self.root_path / "memory" / "memory.jsonl"
        try:
            with open(memory_file, 'a') as f:
                for item in self._memory[-10:]:
                    f.write(json.dumps(item, default=str) + "\n")
        except Exception:
            pass
    
    def _persist_session(self, session_data: Dict[str, Any]):
        """Persist session to disk"""
        session_id = session_data.get("session_id", "unknown")
        session_file = self.root_path / "sessions" / f"{session_id}.json"
        try:
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2, default=str)
        except Exception:
            pass
    
    def isolate(self) -> "AgentWorkspace":
        """
        Create a new isolated workspace based on this one.
        
        The new workspace has:
        - New workspace_id
        - Empty state
        - Empty memory (optionally inherit)
        - Empty tool cache
        """
        new_workspace = AgentWorkspace(
            workspace_id=str(uuid.uuid4())[:8],
            root_path=str(self.root_path.parent),
            enable_isolation=self.enable_isolation
        )
        return new_workspace
    
    def clone(self, include_memory: bool = False) -> "AgentWorkspace":
        """
        Clone this workspace with optionally including memory.
        
        Unlike isolate(), clone() can inherit memory from parent.
        """
        new_workspace = AgentWorkspace(
            workspace_id=str(uuid.uuid4())[:8],
            root_path=str(self.root_path.parent),
            enable_isolation=self.enable_isolation
        )
        
        if include_memory:
            new_workspace._memory = self._memory.copy()
        
        return new_workspace
    
    def cleanup(self):
        """Clean up workspace resources"""
        if self.enable_isolation and self.root_path.exists():
            import shutil
            try:
                shutil.rmtree(self.root_path)
            except Exception:
                pass
    
    def __repr__(self) -> str:
        return f"AgentWorkspace(id={self.workspace_id}, path={self.root_path})"


class WorkspaceManager:
    """
    Manager for multiple agent workspaces.
    
    Handles workspace lifecycle and resource management.
    """
    
    def __init__(self, root_path: str = "./workspace"):
        self.root_path = Path(root_path)
        self.workspaces: Dict[str, AgentWorkspace] = {}
        self._init_manager()
    
    def _init_manager(self):
        """Initialize workspace manager"""
        self.root_path.mkdir(parents=True, exist_ok=True)
    
    def create_workspace(
        self,
        workspace_id: Optional[str] = None,
        enable_isolation: bool = True
    ) -> AgentWorkspace:
        """Create a new workspace"""
        workspace = AgentWorkspace(
            workspace_id=workspace_id,
            root_path=str(self.root_path),
            enable_isolation=enable_isolation
        )
        self.workspaces[workspace.workspace_id] = workspace
        return workspace
    
    def get_workspace(self, workspace_id: str) -> Optional[AgentWorkspace]:
        """Get workspace by ID"""
        return self.workspaces.get(workspace_id)
    
    def delete_workspace(self, workspace_id: str) -> bool:
        """Delete workspace"""
        workspace = self.workspaces.get(workspace_id)
        if workspace:
            workspace.cleanup()
            del self.workspaces[workspace_id]
            return True
        return False
    
    def list_workspaces(self) -> List[AgentWorkspace]:
        """List all workspaces"""
        return list(self.workspaces.values())
    
    def cleanup_all(self):
        """Clean up all workspaces"""
        for workspace in self.workspaces.values():
            workspace.cleanup()
        self.workspaces.clear()


# Global workspace manager
_workspace_manager: Optional[WorkspaceManager] = None


def get_workspace_manager(root_path: str = "./workspace") -> WorkspaceManager:
    """Get global workspace manager"""
    global _workspace_manager
    if _workspace_manager is None:
        _workspace_manager = WorkspaceManager(root_path)
    return _workspace_manager
