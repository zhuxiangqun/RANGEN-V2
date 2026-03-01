#!/usr/bin/env python3
"""
Agent能力模块 (Agent Capabilities)
为Agent提供增强的核心能力

包含:
1. 结构化推理 - 透明可追溯的推理过程
2. 记忆系统 - 短期/工作/长期记忆
3. 反思机制 - 自我监控与修正
4. 工具选择 - 基于语义和效用的智能选择
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


# ==================== 结构化推理 ====================

class ReasoningType(Enum):
    """推理类型"""
    DEDUCTIVE = "deductive"  # 演绎推理
    INDUCTIVE = "inductive"  # 归纳推理
    ABDUCTIVE = "abductive"  # 溯因推理
    ANALOGICAL = "analogical"  # 类比推理
    CAUSAL = "causal"  # 因果推理


class ConfidenceLevel(Enum):
    """置信度级别"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


@dataclass
class ReasoningStep:
    """推理步骤"""
    step_id: str
    step_number: int
    reasoning_type: ReasoningType
    description: str
    premise: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    inference: str = ""
    confidence: float = 0.5
    alternatives: List[str] = field(default_factory=list)
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ReasoningChain:
    """完整推理链"""
    chain_id: str
    query: str
    steps: List[ReasoningStep] = field(default_factory=list)
    final_conclusion: str = ""
    overall_confidence: float = 0.0
    
    def add_step(self, step: ReasoningStep):
        self.steps.append(step)
        self._recalculate_confidence()
    
    def _recalculate_confidence(self):
        if not self.steps:
            self.overall_confidence = 0.0
            return
        confidences = [step.confidence for step in self.steps]
        weights = [i + 1 for i in range(len(confidences))]
        total_weight = sum(weights)
        self.overall_confidence = sum(c * w for c, w in zip(confidences, weights)) / total_weight


class StructuredReasoningEngine:
    """结构化推理引擎"""
    
    def __init__(self, llm_service: Optional[Any] = None):
        self.logger = logger
        self.llm_service = llm_service
        self.reasoning_chains: Dict[str, ReasoningChain] = {}
        self._chain_counter = 0
        self._step_counter = 0
    
    def create_chain(self, query: str) -> ReasoningChain:
        self._chain_counter += 1
        chain = ReasoningChain(
            chain_id=f"chain_{self._chain_counter:06d}",
            query=query
        )
        self.reasoning_chains[chain.chain_id] = chain
        return chain
    
    def add_step(self, chain: ReasoningChain, reasoning_type: ReasoningType,
                 description: str, premise=None, evidence=None,
                 inference: str = "", confidence: float = 0.5,
                 alternatives=None) -> ReasoningStep:
        self._step_counter += 1
        step = ReasoningStep(
            step_id=f"step_{self._step_counter:06d}",
            step_number=len(chain.steps) + 1,
            reasoning_type=reasoning_type,
            description=description,
            premise=premise or [],
            evidence=evidence or [],
            inference=inference,
            confidence=confidence,
            alternatives=alternatives or []
        )
        chain.add_step(step)
        return step
    
    def reason_automatically(self, chain: ReasoningChain, observation: str, query: str) -> ReasoningStep:
        """自动推理"""
        inference = observation[:200] if observation and len(observation) > 10 else "需要更多信息"
        confidence = 0.7 if inference != "需要更多信息" else 0.3
        
        return self.add_step(
            chain=chain,
            reasoning_type=ReasoningType.DEDUCTIVE,
            description=f"基于观察: {observation[:100]}...",
            evidence=[observation],
            inference=inference,
            confidence=confidence
        )


# ==================== 记忆系统 ====================

class MemoryType(Enum):
    SHORT_TERM = "short_term"
    WORKING = "working"
    LONG_TERM = "long_term"


class MemoryPriority(Enum):
    CRITICAL = 3
    HIGH = 2
    NORMAL = 1
    LOW = 0


@dataclass
class MemoryItem:
    memory_id: str
    content: str
    memory_type: MemoryType
    priority: MemoryPriority
    created_at: str
    importance_score: float = 0.5
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class ShortTermMemory:
    """短期记忆"""
    def __init__(self, max_size: int = 10, decay_factor: float = 0.9):
        self.max_size = max_size
        self.decay_factor = decay_factor
        self._memories: List[MemoryItem] = []
        self._counter = 0
    
    def add(self, content: str, priority: MemoryPriority = MemoryPriority.NORMAL) -> MemoryItem:
        self._counter += 1
        # 简单衰减
        for m in self._memories:
            m.importance_score *= self.decay_factor
        
        memory = MemoryItem(
            memory_id=f"stm_{self._counter:08d}",
            content=content,
            memory_type=MemoryType.SHORT_TERM,
            priority=priority,
            created_at=datetime.now().isoformat(),
            importance_score=priority.value / 3.0
        )
        
        self._memories.append(memory)
        if len(self._memories) > self.max_size:
            self._memories.pop(0)
        return memory
    
    def get_all(self) -> List[MemoryItem]:
        return sorted(self._memories, key=lambda m: m.importance_score, reverse=True)


class WorkingMemory:
    """工作记忆"""
    def __init__(self):
        self._memory: Dict[str, Any] = {}
    
    def set(self, key: str, value: Any):
        self._memory[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._memory.get(key, default)
    
    def has(self, key: str) -> bool:
        return key in self._memory
    
    def clear(self):
        self._memory.clear()
    
    def __len__(self):
        return len(self._memory)


class AgentMemorySystem:
    """Agent统一记忆系统"""
    
    def __init__(self, embedding_service: Optional[Any] = None):
        self.logger = logger
        self.short_term = ShortTermMemory()
        self.working = WorkingMemory()
        # 长期记忆简化实现
        self._long_term: List[MemoryItem] = []
    
    def add_short_term(self, content: str, priority: MemoryPriority = MemoryPriority.NORMAL) -> MemoryItem:
        return self.short_term.add(content, priority)
    
    def add_working(self, key: str, value: Any):
        self.working.set(key, value)
    
    def get_working(self, key: str, default: Any = None) -> Any:
        return self.working.get(key, default)
    
    def get_context_for_query(self, query: str, max_length: int = 2000) -> str:
        """获取用于查询的上下文"""
        parts = []
        
        # 添加短期记忆
        for m in self.short_term.get_all()[:3]:
            parts.append(f"[短期记忆] {m.content}")
        
        # 添加工作记忆
        for k, v in self.working._memory.items():
            parts.append(f"[工作记忆] {k}: {v}")
        
        return "\n\n".join(parts)[:max_length]
    
    def get_stats(self) -> Dict[str, int]:
        return {
            "short_term": len(self.short_term),
            "working": len(self.working),
            "long_term": len(self._long_term)
        }


# ==================== 反思机制 ====================

class ReflectionType(Enum):
    PRE_EXECUTION = "pre_execution"
    ONGOING = "ongoing"
    POST_EXECUTION = "post_execution"
    ERROR = "error"


class IssueSeverity(Enum):
    CRITICAL = 3
    HIGH = 2
    MEDIUM = 1
    LOW = 0


@dataclass
class IdentifiedIssue:
    issue_id: str
    issue_type: str
    description: str
    severity: IssueSeverity
    location: str
    suggestion: str


@dataclass
class ReflectionResult:
    reflection_type: ReflectionType
    issues_found: List[IdentifiedIssue]
    confidence_adjustment: float
    should_retry: bool = False
    should_abort: bool = False
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class ReflectionMechanism:
    """反思机制"""
    
    def __init__(self, llm_service: Optional[Any] = None):
        self.logger = logger
        self.llm_service = llm_service
        self.reflection_history: List[ReflectionResult] = []
        self._issue_counter = 0
    
    async def reflect_pre_execution(self, query: str, planned_actions: List) -> ReflectionResult:
        """执行前反思"""
        issues = []
        
        if not planned_actions:
            self._issue_counter += 1
            issues.append(IdentifiedIssue(
                issue_id=f"issue_{self._issue_counter:06d}",
                issue_type="empty_plan",
                description="行动计划为空",
                severity=IssueSeverity.HIGH,
                location="planned_actions",
                suggestion="需要制定具体的行动计划"
            ))
        
        result = ReflectionResult(
            reflection_type=ReflectionType.PRE_EXECUTION,
            issues_found=issues,
            confidence_adjustment=-0.3 if issues else 0.1,
            should_abort=any(i.severity == IssueSeverity.CRITICAL for i in issues)
        )
        
        self.reflection_history.append(result)
        return result
    
    async def reflect_ongoing(self, current_step: int, observations: List) -> ReflectionResult:
        """执行中反思"""
        issues = []
        
        # 检测循环
        if len(observations) >= 3:
            recent = observations[-3:]
            contents = [str(o.get("data", ""))[:100] for o in recent]
            if len(set(contents)) == 1:
                self._issue_counter += 1
                issues.append(IdentifiedIssue(
                    issue_id=f"issue_{self._issue_counter:06d}",
                    issue_type="circular_loop",
                    description="检测到循环",
                    severity=IssueSeverity.CRITICAL,
                    location=f"step {current_step}",
                    suggestion="需要跳出循环，尝试新方法"
                ))
        
        result = ReflectionResult(
            reflection_type=ReflectionType.ONGOING,
            issues_found=issues,
            confidence_adjustment=-0.2 if issues else 0,
            should_retry=any(i.severity == IssueSeverity.HIGH for i in issues)
        )
        
        self.reflection_history.append(result)
        return result
    
    async def reflect_error(self, error: Exception, context: Dict) -> ReflectionResult:
        """错误反思"""
        self._issue_counter += 1
        issue = IdentifiedIssue(
            issue_id=f"issue_{self._issue_counter:06d}",
            issue_type=type(error).__name__,
            description=str(error)[:100],
            severity=IssueSeverity.CRITICAL,
            location=context.get("location", "unknown"),
            suggestion="需要分析错误原因"
        )
        
        result = ReflectionResult(
            reflection_type=ReflectionType.ERROR,
            issues_found=[issue],
            confidence_adjustment=-0.3,
            should_retry=True
        )
        
        self.reflection_history.append(result)
        return result
    
    def get_history(self) -> List[ReflectionResult]:
        return self.reflection_history


# ==================== 工具选择 ====================

@dataclass
class ToolDescription:
    name: str
    description: str
    category: str = "general"
    success_rate: float = 0.5


@dataclass
class ToolSelectionScore:
    tool_name: str
    semantic_score: float = 0.0
    utility_score: float = 0.0
    total_score: float = 0.0


class EnhancedToolSelector:
    """增强工具选择器"""
    
    def __init__(self, embedding_service: Optional[Any] = None, llm_service: Optional[Any] = None):
        self.logger = logger
        self.embedding_service = embedding_service
        self.llm_service = llm_service
        self.tools: Dict[str, ToolDescription] = {}
        self.tool_stats: Dict[str, Dict] = {}
    
    def register_tool(self, tool: ToolDescription):
        self.tools[tool.name] = tool
        if tool.name not in self.tool_stats:
            self.tool_stats[tool.name] = {"success_count": 0, "total_calls": 0}
    
    def select_tools(self, query: str, context: Optional[Dict] = None, top_k: int = 3) -> List[ToolSelectionScore]:
        """选择最合适的工具"""
        if not self.tools:
            return []
        
        scores = []
        for tool_name, tool in self.tools.items():
            # 简单关键词匹配
            score = 0.5
            query_lower = query.lower()
            tool_lower = tool.description.lower()
            
            for word in query_lower.split():
                if word in tool_lower:
                    score += 0.1
            
            scores.append(ToolSelectionScore(
                tool_name=tool_name,
                semantic_score=min(1.0, score),
                utility_score=0.5,
                total_score=min(1.0, score)
            ))
        
        scores.sort(key=lambda x: x.total_score, reverse=True)
        return scores[:top_k]
    
    def record_result(self, tool_name: str, success: bool):
        if tool_name in self.tool_stats:
            stats = self.tool_stats[tool_name]
            stats["total_calls"] += 1
            if success:
                stats["success_count"] += 1


# ==================== 单例访问 ====================

_reasoning_engine: Optional[StructuredReasoningEngine] = None
_memory_system: Optional[AgentMemorySystem] = None
_reflection_mechanism: Optional[ReflectionMechanism] = None
_tool_selector: Optional[EnhancedToolSelector] = None


def get_structured_reasoning_engine(llm_service: Any = None) -> StructuredReasoningEngine:
    global _reasoning_engine
    if _reasoning_engine is None:
        _reasoning_engine = StructuredReasoningEngine(llm_service)
    return _reasoning_engine


def get_agent_memory_system(embedding_service: Any = None) -> AgentMemorySystem:
    global _memory_system
    if _memory_system is None:
        _memory_system = AgentMemorySystem(embedding_service)
    return _memory_system


def get_reflection_mechanism(llm_service: Any = None) -> ReflectionMechanism:
    global _reflection_mechanism
    if _reflection_mechanism is None:
        _reflection_mechanism = ReflectionMechanism(llm_service)
    return _reflection_mechanism


def get_enhanced_tool_selector(embedding_service: Any = None, llm_service: Any = None) -> EnhancedToolSelector:
    global _tool_selector
    if _tool_selector is None:
        _tool_selector = EnhancedToolSelector(embedding_service, llm_service)
    return _tool_selector
