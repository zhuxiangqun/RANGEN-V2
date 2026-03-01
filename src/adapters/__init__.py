"""
迁移适配器模块

提供Agent迁移的适配器实现，支持平滑迁移。
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

__all__ = [
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
]

