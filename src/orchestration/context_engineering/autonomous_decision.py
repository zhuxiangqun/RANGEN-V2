"""
Autonomous Decision Loop Optimizer
基于 Anthropic 原则的 Agent 自主决策优化

核心思想：
1. 让 Agent 自主决定何时使用工具
2. 提供决策启发式，而非硬编码规则
3. 支持渐进式探索
4. 平衡速度与准确性
"""
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time


class DecisionType(Enum):
    """决策类型"""
    RETRIEVE = "retrieve"       # 需要获取信息
    ANALYZE = "analyze"         # 需要分析
    PLAN = "plan"              # 需要规划
    EXECUTE = "execute"         # 需要执行
    VALIDATE = "validate"       # 需要验证
    FINALIZE = "finalize"       # 可以结束


@dataclass
class Decision:
    """决策结果"""
    decision_type: DecisionType
    confidence: float  # 0-1 信心度
    reasoning: str
    suggested_action: str
    alternative: Optional[str] = None


@dataclass
class LoopState:
    """循环状态"""
    iteration: int
    total_iterations: int
    accumulated_context: str
    tool_calls: List[Dict[str, Any]]
    last_result: Optional[str] = None
    confidence_history: List[float] = field(default_factory=list)


class AutonomousDecisionEngine:
    """
    自主决策引擎
    
    帮助 Agent 在每个循环迭代中做出更好的决策：
    1. 分析当前状态
    2. 评估是否需要更多信息
    3. 选择最佳行动
    4. 判断是否可以结束
    """
    
    def __init__(
        self,
        max_iterations: int = 10,
        confidence_threshold: float = 0.8,
        context_growth_limit: int = 5000
    ):
        self.max_iterations = max_iterations
        self.confidence_threshold = confidence_threshold
        self.context_growth_limit = context_growth_limit
        
        # 决策历史
        self.decisions: List[Decision] = []
        
        # 状态
        self.state = LoopState(
            iteration=0,
            total_iterations=0,
            accumulated_context="",
            tool_calls=[]
        )
    
    def should_continue(self, confidence: float, iteration: int) -> bool:
        """
        判断是否应该继续循环
        
        条件：
        1. 信心度未达到阈值
        2. 未达到最大迭代次数
        3. 有新的有用信息
        """
        if iteration >= self.max_iterations:
            return False
        
        if confidence >= self.confidence_threshold:
            return False
        
        # 检查是否有新进展
        if len(self.decisions) > 0:
            last = self.decisions[-1]
            if last.confidence >= confidence:
                # 没有新进展，可能陷入循环
                return False
        
        return True
    
    def analyze_and_decide(
        self,
        query: str,
        current_context: str,
        last_tool_result: Optional[str] = None,
        available_tools: Optional[List[str]] = None
    ) -> Decision:
        """
        分析当前状态并做出决策
        
        决策框架：
        1. 是否有足够信息回答？
        2. 需要什么类型的信息？
        3. 哪个工具最合适？
        """
        
        # 简单启发式决策
        reasoning_parts = []
        
        # 检查是否可以直接回答
        if self._can_answer_directly(query, current_context):
            reasoning_parts.append("有足够信息可以直接回答")
            return Decision(
                decision_type=DecisionType.FINALIZE,
                confidence=0.9,
                reasoning=". ".join(reasoning_parts),
                suggested_action="Final Answer"
            )
        
        # 检查是否需要检索
        if self._needs_retrieval(query, current_context):
            reasoning_parts.append("需要获取更多信息")
            return Decision(
                decision_type=DecisionType.RETRIEVE,
                confidence=0.7,
                reasoning=". ".join(reasoning_parts),
                suggested_action="search or retrieve"
            )
        
        # 检查是否需要分析
        if self._needs_analysis(query, current_context):
            reasoning_parts.append("需要深入分析")
            return Decision(
                decision_type=DecisionType.ANALYZE,
                confidence=0.7,
                reasoning=". ".join(reasoning_parts),
                suggested_action="analyze"
            )
        
        # 检查是否需要规划
        if self._needs_planning(query, current_context):
            reasoning_parts.append("需要制定计划")
            return Decision(
                decision_type=DecisionType.PLAN,
                confidence=0.7,
                reasoning=". ".join(reasoning_parts),
                suggested_action="plan"
            )
        
        # 检查是否需要验证
        if self._needs_validation(current_context):
            reasoning_parts.append("需要验证已有信息")
            return Decision(
                decision_type=DecisionType.VALIDATE,
                confidence=0.7,
                reasoning=". ".join(reasoning_parts),
                suggested_action="validate"
            )
        
        # 默认：需要执行
        return Decision(
            decision_type=DecisionType.EXECUTE,
            confidence=0.6,
            reasoning="需要执行操作",
            suggested_action="execute"
        )
    
    def _can_answer_directly(self, query: str, context: str) -> bool:
        """检查是否可以直接回答"""
        # 简单检查：上下文是否包含查询的关键信息
        query_words = set(query.lower().split())
        context_words = set(context.lower().split())
        
        # 至少匹配 50% 的查询词
        if query_words:
            match_ratio = len(query_words & context_words) / len(query_words)
            return match_ratio >= 0.5
        
        return False
    
    def _needs_retrieval(self, query: str, context: str) -> bool:
        """检查是否需要检索"""
        # 需要实时信息
        if any(kw in query.lower() for kw in ["最新", "最近", "current", "latest", "today"]):
            return True
        
        # 上下文信息不足
        if len(context) < 100:
            return True
        
        return False
    
    def _needs_analysis(self, query: str, context: str) -> bool:
        """检查是否需要分析"""
        # 复杂问题
        if any(kw in query.lower() for kw in ["为什么", "原因", "分析", "why", "analyze", "compare"]):
            return True
        
        # 上下文较长，可能需要理解
        if len(context) > 2000:
            return True
        
        return False
    
    def _needs_planning(self, query: str, context: str) -> bool:
        """检查是否需要规划"""
        # 多步骤任务
        if any(kw in query.lower() for kw in ["步骤", "流程", "实现", "步骤", "how to", "implement"]):
            return True
        
        return False
    
    def _needs_validation(self, context: str) -> bool:
        """检查是否需要验证"""
        # 包含重要声明或数字
        if any(kw in context.lower() for kw in ["确保", "验证", "确认", "verify", "confirm"]):
            return True
        
        return False
    
    def update_state(
        self,
        tool_name: str,
        tool_result: str,
        confidence: float
    ) -> None:
        """更新循环状态"""
        self.state.iteration += 1
        self.state.tool_calls.append({
            "tool": tool_name,
            "result": tool_result[:500],  # 截断
            "timestamp": time.time()
        })
        self.state.accumulated_context += f"\n{tool_result}"
        self.state.last_result = tool_result
        self.state.confidence_history.append(confidence)
    
    def get_loop_summary(self) -> Dict[str, Any]:
        """获取循环摘要"""
        return {
            "total_iterations": self.state.iteration,
            "tool_calls": len(self.state.tool_calls),
            "confidence_trend": self.state.confidence_history[-3:] if len(self.state.confidence_history) >= 3 else self.state.confidence_history,
            "last_tool": self.state.tool_calls[-1]["tool"] if self.state.tool_calls else None
        }
    
    def reset(self) -> None:
        """重置状态"""
        self.state = LoopState(
            iteration=0,
            total_iterations=0,
            accumulated_context="",
            tool_calls=[]
        )
        self.decisions = []


# 决策指导 prompt 生成器
def generate_decision_guidance(
    engine: AutonomousDecisionEngine,
    context_type: str = "general"
) -> str:
    """生成决策指导 prompt"""
    
    base_guidance = """
## Autonomous Decision Guidance

You have autonomy to decide when to use tools. Use this framework:

### Decision Framework

1. **Can I answer now?**
   - Do I have enough information?
   - Am I confident in my answer?
   → If YES: Final Answer
   
2. **What's missing?**
   - Need facts → retrieve
   - Need understanding → analyze  
   - Need plan → plan
   - Need verification → validate
   
3. **Am I making progress?**
   - Each tool call should add new information
   - If stuck, try different approach
   
### Stopping Conditions

- Confidence >= 80% → stop
- Max iterations reached → stop
- No new information gained → stop
"""
    
    # 根据上下文类型调整
    if context_type == "research":
        base_guidance += """

### Research Focus
- Prioritize retrieval for accuracy
- Verify sources when possible
- Document key findings
"""
    elif context_type == "coding":
        base_guidance += """

### Coding Focus
- Test before finalizing
- Understand error messages
- Verify syntax before execution
"""
    
    return base_guidance


# 全局实例
_engine: Optional[AutonomousDecisionEngine] = None


def get_decision_engine() -> AutonomousDecisionEngine:
    """获取决策引擎"""
    global _engine
    if _engine is None:
        _engine = AutonomousDecisionEngine()
    return _engine


__all__ = [
    "AutonomousDecisionEngine",
    "Decision",
    "DecisionType",
    "LoopState",
    "generate_decision_guidance",
    "get_decision_engine"
]
