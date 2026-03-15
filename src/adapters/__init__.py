"""
适配器模块

包含两种类型的适配器：
1. Agent迁移适配器 - 用于Agent迁移
2. LLM模型适配器 - 用于多模型架构统一接口
"""

from .base_adapter import MigrationAdapter
from .citation_agent_adapter import CitationAgentAdapter
from .react_agent_adapter import ReActAgentAdapter
from .knowledge_retrieval_agent_adapter import KnowledgeRetrievalAgentAdapter
from .rag_agent_adapter import RAGAgentAdapter
from .chief_agent_adapter import ChiefAgentAdapter
from .answer_generation_agent_adapter import AnswerGenerationAgentAdapter
from .prompt_engineering_agent_adapter import PromptEngineeringAgentAdapter
from .context_engineering_agent_adapter import ContextEngineeringAgentAdapter
from .memory_agent_adapter import MemoryAgentAdapter
from .optimized_knowledge_retrieval_agent_adapter import OptimizedKnowledgeRetrievalAgentAdapter
from .enhanced_analysis_agent_adapter import EnhancedAnalysisAgentAdapter
from .learning_system_adapter import LearningSystemAdapter
from .intelligent_strategy_agent_adapter import IntelligentStrategyAgentAdapter
from .fact_verification_agent_adapter import FactVerificationAgentAdapter
from .intelligent_coordinator_agent_adapter import IntelligentCoordinatorAgentAdapter
from .strategic_chief_agent_adapter import StrategicChiefAgentAdapter

# LLM模型适配器
from .llm_adapter_base import (
    LLMProvider,
    AdapterCapability,
    LLMResponse,
    LLMRequest,
    AdapterConfig,
    BaseLLMAdapter,
)

# 具体LLM适配器实现
try:
    from .local_llm_adapter import LocalLLMAdapter
except ImportError:
    LocalLLMAdapter = None  # 如果依赖不满足，设置为None

# LLM适配器工厂
from .llm_adapter_factory import (
    LLMAdapterFactory,
)

__all__ = [
    # Agent迁移适配器
    "MigrationAdapter",
    "CitationAgentAdapter",
    "ReActAgentAdapter",
    "KnowledgeRetrievalAgentAdapter",
    "RAGAgentAdapter",
    "ChiefAgentAdapter",
    "AnswerGenerationAgentAdapter",
    "PromptEngineeringAgentAdapter",
    "ContextEngineeringAgentAdapter",
    "MemoryAgentAdapter",
    "OptimizedKnowledgeRetrievalAgentAdapter",
    "EnhancedAnalysisAgentAdapter",
    "LearningSystemAdapter",
    "IntelligentStrategyAgentAdapter",
    "FactVerificationAgentAdapter",
    "IntelligentCoordinatorAgentAdapter",
    "StrategicChiefAgentAdapter",
    
    # LLM模型适配器
    "LLMProvider",
    "AdapterCapability",
    "LLMResponse",
    "LLMRequest",
    "AdapterConfig",
    "BaseLLMAdapter",
    "LocalLLMAdapter",
    
    # LLM适配器工厂
    "LLMAdapterFactory",
]

