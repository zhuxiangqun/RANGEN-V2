#!/usr/bin/env python3
"""
Unified Agent Interface
=======================

统一的 Agent 接口，整合了以下设计：
- interfaces/agent.py: AgentConfig, AgentResult, ExecutionStatus
- interfaces/core_interfaces.py: agent_id, is_enabled()

使用方式：
    from src.interfaces.unified_agent import IAgent, UnifiedAgentConfig

迁移指南：
    旧: from src.interfaces.agent import IAgent
    新: from src.interfaces.unified_agent import IAgent

Created: 2026-03-20
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# Enums & Status
# =============================================================================

class ExecutionStatus(Enum):
    """执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentCapability(Enum):
    """Agent 能力枚举"""
    REASONING = "reasoning"
    TOOL_USE = "tool_use"
    RAG = "rag"
    VALIDATION = "validation"
    CITATION = "citation"
    PLANNING = "planning"
    EXECUTION = "execution"
    REFLECTION = "reflection"


# =============================================================================
# Unified Config & Result Models
# =============================================================================

class UnifiedAgentConfig(BaseModel):
    """
    统一的 Agent 配置模型
    
    整合了:
    - interfaces/agent.py: AgentConfig (name, description, version, category, metadata)
    - interfaces/core_interfaces.py: agent_id
    """
    # 核心标识
    agent_id: str
    name: str
    description: str
    
    # 版本和分类
    version: str = "1.0.0"
    category: str = "general"
    
    # 能力配置
    capabilities: List[str] = Field(default_factory=list)
    max_retries: int = 3
    timeout: int = 300
    
    # 启用控制
    enabled: bool = True
    
    # 扩展元数据
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(use_enum_values=True)


class UnifiedAgentResult(BaseModel):
    """
    统一的 Agent 执行结果模型
    
    整合了:
    - interfaces/agent.py: AgentResult
    - interfaces/core_interfaces.py: Dict[str, Any] 返回值
    """
    # 执行信息
    agent_id: str
    agent_name: str
    
    # 状态
    status: ExecutionStatus
    
    # 输出
    output: Any = None
    
    # 执行信息
    execution_time: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # 错误信息
    error: Optional[str] = None
    
    # 扩展元数据
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # 置信度和质量
    confidence: float = 1.0
    quality_score: Optional[float] = None
    
    # 引用和证据
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    
    model_config = ConfigDict(use_enum_values=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，保持与旧接口兼容"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "output": self.output,
            "execution_time": self.execution_time,
            "error": self.error,
            "metadata": self.metadata,
            "confidence": self.confidence,
            "quality_score": self.quality_score,
            "citations": self.citations,
            "evidence": self.evidence,
        }
    
    @property
    def success(self) -> bool:
        """检查是否成功"""
        status_value = self.status.value if isinstance(self.status, Enum) else self.status
        return status_value == ExecutionStatus.COMPLETED.value and self.error is None


# =============================================================================
# Unified Agent Interface (IAgent)
# =============================================================================

class IAgent(ABC):
    """
    统一的 Agent 抽象接口
    
    统一了两个原有接口:
    - interfaces/agent.py: execute(inputs, context) -> AgentResult
    - interfaces/core_interfaces.py: process(query, context) -> Dict, is_enabled()
    
    使用示例:
        class MyAgent(IAgent):
            def __init__(self, config: UnifiedAgentConfig):
                super().__init__(config)
            
            async def execute(self, query: str, context: Optional[Dict] = None) -> UnifiedAgentResult:
                # 实现逻辑
                pass
    
    Attributes:
        config: Agent 配置
        agent_id: Agent 唯一标识符
        name: Agent 名称 (alias for config.name)
    
    Methods:
        execute(query, context): 执行 Agent 任务
        process(query, context): execute() 的别名
        is_enabled(): 检查 Agent 是否启用
        get_capabilities(): 获取 Agent 能力列表
    """
    
    def __init__(self, config: UnifiedAgentConfig):
        """
        初始化 Agent
        
        Args:
            config: UnifiedAgentConfig 配置实例
        """
        self.config = config
        self._enabled = config.enabled
    
    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    
    @property
    def agent_id(self) -> str:
        """Agent 唯一标识符"""
        return self.config.agent_id
    
    @property
    def name(self) -> str:
        """Agent 名称"""
        return self.config.name
    
    @property
    def description(self) -> str:
        """Agent 描述"""
        return self.config.description
    
    @property
    def capabilities(self) -> List[str]:
        """Agent 能力列表"""
        return self.config.capabilities
    
    # -------------------------------------------------------------------------
    # Core Methods (Must Override)
    # -------------------------------------------------------------------------
    
    @abstractmethod
    async def execute(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> UnifiedAgentResult:
        """
        执行 Agent 任务
        
        Args:
            query: 查询字符串
            context: 可选的上下文字典
            
        Returns:
            UnifiedAgentResult 执行结果
            
        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        pass
    
    # -------------------------------------------------------------------------
    # Alias Methods (Backward Compatibility)
    # -------------------------------------------------------------------------
    
    async def process(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> UnifiedAgentResult:
        """
        process() 是 execute() 的别名，保持与 core_interfaces.py 兼容
        
        Args:
            query: 查询字符串
            context: 可选的上下文字典
            
        Returns:
            UnifiedAgentResult 执行结果
        """
        return await self.execute(query, context)
    
    # -------------------------------------------------------------------------
    # Utility Methods (Can Override)
    # -------------------------------------------------------------------------
    
    def is_enabled(self) -> bool:
        """
        检查 Agent 是否启用
        
        Returns:
            bool: True 如果启用，False 否则
        """
        return self._enabled
    
    def enable(self) -> None:
        """启用 Agent"""
        self._enabled = True
        if hasattr(self.config, 'enabled'):
            self.config.enabled = True
    
    def disable(self) -> None:
        """禁用 Agent"""
        self._enabled = False
        if hasattr(self.config, 'enabled'):
            self.config.enabled = False
    
    def get_capabilities(self) -> List[str]:
        """
        获取 Agent 支持的能力列表
        
        Returns:
            List[str]: 能力列表
        """
        return self.capabilities.copy()
    
    def has_capability(self, capability: str) -> bool:
        """
        检查是否具有特定能力
        
        Args:
            capability: 能力名称
            
        Returns:
            bool: True 如果具有该能力
        """
        return capability in self.capabilities
    
    def get_config(self) -> UnifiedAgentConfig:
        """
        获取 Agent 配置
        
        Returns:
            UnifiedAgentConfig: 配置对象
        """
        return self.config
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(agent_id='{self.agent_id}', name='{self.name}', enabled={self.is_enabled()})"


# =============================================================================
# Backward Compatibility Aliases
# =============================================================================

# 导出统一模型作为别名，保持向后兼容
AgentConfig = UnifiedAgentConfig
AgentResult = UnifiedAgentResult

# 导出枚举
__all__ = [
    # 核心类
    "IAgent",
    "UnifiedAgentConfig",
    "UnifiedAgentResult",
    "AgentConfig",  # Alias
    "AgentResult",  # Alias
    
    # 枚举
    "ExecutionStatus",
    "AgentCapability",
]
