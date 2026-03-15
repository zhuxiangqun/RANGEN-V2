"""
统一推理服务模块

合并以下服务:
- ReasoningEngine (reasoning_engines.py)
- ReasoningStrategy (reasoning_strategies.py)
- ReasoningService (reasoning_service.py)
- MultiHopReasoningEngine (multi_hop_reasoning_engine.py)

使用示例:
```python
from src.services.reasoning import ReasoningService

reasoning = ReasoningService()
result = reasoning.reason("What is the cause of X?")
```
"""

from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
import re


# ============== Enums ==============

class ReasoningType(str, Enum):
    """推理类型"""
    DEDUCTIVE = "deductive"      # 演绎推理
    INDUCTIVE = "inductive"      # 归纳推理
    ABDUCTIVE = "abductive"     # 溯因推理
    CAUSAL = "causal"          # 因果推理
    ANALOGICAL = "analogical"   # 类比推理
    MULTI_HOP = "multi_hop"    # 多跳推理


class ReasoningStrategy(str, Enum):
    """推理策略"""
    LOGICAL = "logical"
    PROBABILISTIC = "probabilistic"
    CAUSAL = "causal"
    COUNTERFACTUAL = "counterfactual"


# ============== Data Classes ==============

@dataclass
class ReasoningStep:
    """推理步骤"""
    step_number: int
    reasoning_type: ReasoningType
    premise: str
    conclusion: str
    confidence: float
    evidence: List[str]


@dataclass
class ReasoningResult:
    """推理结果"""
    reasoning_type: ReasoningType
    conclusion: str
    confidence: float
    steps: List[ReasoningStep]
    evidence: List[str]
    is_valid: bool


# ============== Base Engine ==============

class ReasoningEngine:
    """推理引擎基类"""
    
    def __init__(self, name: str):
        self.name = name
    
    def reason(self, query: str, context: Optional[Dict[str, Any]] = None) -> ReasoningResult:
        """执行推理"""
        raise NotImplementedError


# ============== Specific Engines ==============

class DeductiveReasoningEngine(ReasoningEngine):
    """演绎推理引擎"""
    
    def __init__(self):
        super().__init__("deductive")
    
    def reason(self, query: str, context: Optional[Dict[str, Any]] = None) -> ReasoningResult:
        # Simple pattern matching for demonstration
        steps = []
        
        # Extract premises from context
        premises = context.get("premises", []) if context else []
        
        # Generate conclusion
        if premises:
            conclusion = f"Based on the premises, {query}"
            confidence = 0.9
        else:
            conclusion = f"Cannot determine: {query}"
            confidence = 0.3
        
        steps.append(ReasoningStep(
            step_number=1,
            reasoning_type=ReasoningType.DEDUCTIVE,
            premise=", ".join(premises) if premises else "general knowledge",
            conclusion=conclusion,
            confidence=confidence,
            evidence=premises
        ))
        
        return ReasoningResult(
            reasoning_type=ReasoningType.DEDUCTIVE,
            conclusion=conclusion,
            confidence=confidence,
            steps=steps,
            evidence=premises,
            is_valid=len(premises) > 0
        )


class InductiveReasoningEngine(ReasoningEngine):
    """归纳推理引擎"""
    
    def __init__(self):
        super().__init__("inductive")
    
    def reason(self, query: str, context: Optional[Dict[str, Any]] = None) -> ReasoningResult:
        observations = context.get("observations", []) if context else []
        
        steps = []
        
        if len(observations) >= 2:
            # Find pattern
            conclusion = f"Pattern found: {observations}"
            confidence = min(0.9, 0.5 + len(observations) * 0.1)
        else:
            conclusion = "Insufficient observations"
            confidence = 0.3
        
        steps.append(ReasoningStep(
            step_number=1,
            reasoning_type=ReasoningType.INDUCTIVE,
            premise=str(observations),
            conclusion=conclusion,
            confidence=confidence,
            evidence=observations
        ))
        
        return ReasoningResult(
            reasoning_type=ReasoningType.INDUCTIVE,
            conclusion=conclusion,
            confidence=confidence,
            steps=steps,
            evidence=observations,
            is_valid=len(observations) >= 2
        )


class AbductiveReasoningEngine(ReasoningEngine):
    """溯因推理引擎"""
    
    def __init__(self):
        super().__init__("abductive")
    
    def reason(self, query: str, context: Optional[Dict[str, Any]] = None) -> ReasoningResult:
        observation = context.get("observation", "") if context else ""
        
        steps = []
        
        # Simple explanation generation
        explanation = f"Possible explanation for '{observation}': {query}"
        confidence = 0.6
        
        steps.append(ReasoningStep(
            step_number=1,
            reasoning_type=ReasoningType.ABDUCTIVE,
            premise=observation,
            conclusion=explanation,
            confidence=confidence,
            evidence=[observation]
        ))
        
        return ReasoningResult(
            reasoning_type=ReasoningType.ABDUCTIVE,
            conclusion=explanation,
            confidence=confidence,
            steps=steps,
            evidence=[observation],
            is_valid=bool(observation)
        )


class CausalReasoningEngine(ReasoningEngine):
    """因果推理引擎"""
    
    def __init__(self):
        super().__init__("causal")
    
    def reason(self, query: str, context: Optional[Dict[str, Any]] = None) -> ReasoningResult:
        cause = context.get("cause", "") if context else ""
        effect = context.get("effect", "") if context else ""
        
        steps = []
        
        if cause and effect:
            conclusion = f"Because {cause}, therefore {effect}"
            confidence = 0.85
        else:
            conclusion = f"Analyzing cause-effect relationship for: {query}"
            confidence = 0.5
        
        steps.append(ReasoningStep(
            step_number=1,
            reasoning_type=ReasoningType.CAUSAL,
            premise=f"cause: {cause}, effect: {effect}",
            conclusion=conclusion,
            confidence=confidence,
            evidence=[cause, effect]
        ))
        
        return ReasoningResult(
            reasoning_type=ReasoningType.CAUSAL,
            conclusion=conclusion,
            confidence=confidence,
            steps=steps,
            evidence=[cause, effect],
            is_valid=bool(cause and effect)
        )


class MultiHopReasoningEngine(ReasoningEngine):
    """多跳推理引擎"""
    
    def __init__(self):
        super().__init__("multi_hop")
        self._hops = 3  # default
    
    def reason(self, query: str, context: Optional[Dict[str, Any]] = None) -> ReasoningResult:
        facts = context.get("facts", []) if context else []
        hops = context.get("hops", self._hops)
        
        steps = []
        current = query
        
        for i in range(min(hops, len(facts)) if facts else hops):
            # Each hop builds on previous
            step = ReasoningStep(
                step_number=i + 1,
                reasoning_type=ReasoningType.MULTI_HOP,
                premise=current,
                conclusion=f"Hop {i+1}: Derived from facts",
                confidence=0.9 - (i * 0.2),
                evidence=[facts[i]] if i < len(facts) else []
            )
            steps.append(step)
            current = step.conclusion
        
        conclusion = f"Multi-hop reasoning completed in {len(steps)} steps"
        
        return ReasoningResult(
            reasoning_type=ReasoningType.MULTI_HOP,
            conclusion=conclusion,
            confidence=0.7,
            steps=steps,
            evidence=facts,
            is_valid=len(steps) > 0
        )


# ============== Main Service ==============

class ReasoningService:
    """
    统一推理服务
    
    支持多种推理类型:
    - 演绎 (Deductive)
    - 归纳 (Inductive)
    - 溯因 (Abductive)
    - 因果 (Causal)
    - 多跳 (Multi-hop)
    
    使用示例:
    ```python
    service = ReasoningService()
    
    # 演绎推理
    result = service.deductive("All men are mortal. Socrates is a man.", 
                               context={"premises": ["All men are mortal", "Socrates is a man"]})
    
    # 归纳推理  
    result = service.inductive("What pattern emerges?", 
                               context={"observations": ["The sun rises", "The sun sets"]})
    
    # 多跳推理
    result = service.multi_hop("A related to B, B related to C", 
                               context={"facts": ["A→B", "B→C"], "hops": 2})
    ```
    """
    
    def __init__(self):
        # Initialize engines
        self._engines: Dict[ReasoningType, ReasoningEngine] = {
            ReasoningType.DEDUCTIVE: DeductiveReasoningEngine(),
            ReasoningType.INDUCTIVE: InductiveReasoningEngine(),
            ReasoningType.ABDUCTIVE: AbductiveReasoningEngine(),
            ReasoningType.CAUSAL: CausalReasoningEngine(),
            ReasoningType.MULTI_HOP: MultiHopReasoningEngine(),
        }
        
        # Default engine
        self._default_engine = ReasoningType.DEDUCTIVE
    
    def set_default(self, reasoning_type: ReasoningType) -> None:
        """设置默认推理类型"""
        if reasoning_type in self._engines:
            self._default_engine = reasoning_type
    
    def reason(
        self, 
        query: str, 
        reasoning_type: Optional[ReasoningType] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ReasoningResult:
        """执行推理"""
        rt = reasoning_type or self._default_engine
        engine = self._engines.get(rt, self._engines[ReasoningType.DEDUCTIVE])
        
        return engine.reason(query, context)
    
    # Convenience methods
    
    def deductive(self, query: str, context: Optional[Dict[str, Any]] = None) -> ReasoningResult:
        """演绎推理"""
        return self.reason(query, ReasoningType.DEDUCTIVE, context)
    
    def inductive(self, query: str, context: Optional[Dict[str, Any]] = None) -> ReasoningResult:
        """归纳推理"""
        return self.reason(query, ReasoningType.INDUCTIVE, context)
    
    def abductive(self, query: str, context: Optional[Dict[str, Any]] = None) -> ReasoningResult:
        """溯因推理"""
        return self.reason(query, ReasoningType.ABDUCTIVE, context)
    
    def causal(self, query: str, context: Optional[Dict[str, Any]] = None) -> ReasoningResult:
        """因果推理"""
        return self.reason(query, ReasoningType.CAUSAL, context)
    
    def multi_hop(self, query: str, context: Optional[Dict[str, Any]] = None) -> ReasoningResult:
        """多跳推理"""
        return self.reason(query, ReasoningType.MULTI_HOP, context)
    
    # Analysis
    
    def analyze_query(self, query: str) -> ReasoningType:
        """分析查询类型"""
        query_lower = query.lower()
        
        # Pattern matching for reasoning type detection
        if any(kw in query_lower for kw in ["because", "therefore", "cause", "effect", "所以", "因为"]):
            return ReasoningType.CAUSAL
        elif any(kw in query_lower for kw in ["all", "every", "must", "所有", "必然"]):
            return ReasoningType.DEDUCTIVE
        elif any(kw in query_lower for kw in ["pattern", "usually", "often", "模式", "通常"]):
            return ReasoningType.INDUCTIVE
        elif any(kw in query_lower for kw in ["explain", "why", "原因", "解释"]):
            return ReasoningType.ABDUCTIVE
        elif any(kw in query_lower for kw in ["related", "connected", "related to", "关联"]):
            return ReasoningType.MULTI_HOP
        
        return ReasoningType.DEDUCTIVE  # default
    
    def auto_reason(self, query: str, context: Optional[Dict[str, Any]] = None) -> ReasoningResult:
        """自动选择推理类型"""
        reasoning_type = self.analyze_query(query)
        return self.reason(query, reasoning_type, context)


# ============== Factory ==============

def get_reasoning_service() -> ReasoningService:
    """获取推理服务实例"""
    return ReasoningService()
